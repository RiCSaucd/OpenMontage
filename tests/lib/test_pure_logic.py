"""Deterministic unit tests for three untested pure-logic lib modules.

These modules have no external dependencies and no I/O in their hot paths, so
they are the cheapest possible things to test — yet they carried zero coverage:

  * lib/verify_scene_pacing.py  — frame-accurate TerminalScene timing math
  * lib/shot_prompt_builder.py  — structured shot language -> generation prompt
  * lib/playbook_generator.py   — custom style playbook synthesis + validation

A regression in any of them silently degrades output (mistimed captions, samey
prompts, an invalid playbook) rather than crashing, which is exactly the kind of
bug a unit test catches cheaply.
"""

from __future__ import annotations

import math

import jsonschema
import pytest

from lib.verify_scene_pacing import Landmark, assert_alignment, step_duration, trace
from lib.shot_prompt_builder import build_batch_prompts, build_shot_prompt
from lib import playbook_generator as pg


# ======================================================================
# verify_scene_pacing
# ======================================================================


class TestStepDuration:
    def test_cmd_typing_plus_hold(self):
        # ceil(9 chars * 0.035 * 30fps) = 10 frames -> 10/30 + 0.3 hold.
        d = step_duration({"kind": "cmd", "text": "git clone"})
        assert d == pytest.approx(10 / 30 + 0.3)

    def test_cmd_respects_custom_type_speed_and_hold(self):
        step = {"kind": "cmd", "text": "abcd", "typeSpeed": 0.05, "holdSeconds": 1.0}
        frames = math.ceil(4 * 0.05 * 30)
        assert step_duration(step) == pytest.approx(frames / 30 + 1.0)

    def test_out_reveal_plus_hold(self):
        # reveal = max(2, ceil(0.08*30)=3) -> 3/30 + 0.15 hold.
        assert step_duration({"kind": "out", "text": "done"}) == pytest.approx(3 / 30 + 0.15)

    def test_pause_is_literal_seconds(self):
        assert step_duration({"kind": "pause", "seconds": 2.5}) == 2.5

    def test_pill_does_not_advance(self):
        assert step_duration({"kind": "pill", "text": "note"}) == 0.0

    def test_unknown_kind_raises(self):
        with pytest.raises(ValueError):
            step_duration({"kind": "banana"})


class TestTrace:
    def test_scene_start_offsets_landmarks(self):
        marks = trace([{"kind": "cmd", "text": "x"}], scene_start=10.0, quiet=True)
        assert marks[0] == Landmark(video_time=10.0, kind="CMD", text="x")

    def test_pills_do_not_advance_cursor(self):
        # Two overlay pills before a command must not push the command's time.
        steps = [
            {"kind": "pill", "text": "a"},
            {"kind": "pill", "text": "b"},
            {"kind": "cmd", "text": "x"},
        ]
        marks = trace(steps, scene_start=10.0, quiet=True)
        assert [m.video_time for m in marks] == [10.0, 10.0, 10.0]

    def test_cursor_advances_across_pause(self):
        steps = [
            {"kind": "cmd", "text": "git clone repo"},
            {"kind": "pause", "seconds": 3},
            {"kind": "cmd", "text": "make setup"},
        ]
        marks = trace(steps, scene_start=0.0, quiet=True)
        first = step_duration(steps[0])
        assert marks[1].video_time == pytest.approx(first + 3, abs=0.01)


class TestAssertAlignment:
    def _steps(self):
        return [
            {"kind": "cmd", "text": "git clone repo"},
            {"kind": "pause", "seconds": 3},
            {"kind": "cmd", "text": "make setup"},
        ]

    def test_passes_when_cue_has_nearby_landmark(self):
        marks = trace(self._steps(), scene_start=0.0, quiet=True)
        cue_time = marks[1].video_time
        # Should not raise: a narration cue lands right on the second command.
        assert_alignment(
            self._steps(),
            scene_start=0.0,
            scene_end=marks[1].video_time + 5.0,
            narration_cues=[(cue_time, "seg run make setup")],
            tolerance=1.0,
        )

    def test_raises_when_cue_has_no_nearby_landmark(self):
        with pytest.raises(AssertionError):
            assert_alignment(
                self._steps(),
                scene_start=0.0,
                scene_end=60.0,
                narration_cues=[(45.0, "seg way off")],
                tolerance=1.0,
            )

    def test_raises_on_overflow(self):
        # Steps run ~4s but the scene window is only 1s -> overflow.
        with pytest.raises(AssertionError):
            assert_alignment(
                self._steps(),
                scene_start=0.0,
                scene_end=1.0,
                narration_cues=[],
                tolerance=1.0,
            )


# ======================================================================
# shot_prompt_builder
# ======================================================================


class TestShotPromptBuilder:
    def test_layers_assemble_in_order(self):
        scene = {
            "shot_language": {
                "lens_mm": 35,
                "depth_of_field": "shallow",
                "shot_size": "close_up",
                "camera_movement": "dolly_in",
                "lighting_key": "golden_hour",
                "color_temperature": "warm",
            },
            "description": "A lighthouse on a cliff",
            "texture_keywords": ["weathered stone", "sea spray"],
        }
        style = {"mood": "nostalgic", "visual_language": {"aesthetic": "muted film grain"}}
        prompt = build_shot_prompt(scene, style)

        assert prompt.startswith("35mm lens, shallow depth of field with bokeh")
        assert "close-up focusing on face or detail" in prompt
        assert "slow dolly in toward subject" in prompt
        assert "A lighthouse on a cliff. weathered stone, sea spray" in prompt
        assert "warm golden hour sunlight" in prompt
        assert prompt.endswith("Style: muted film grain")

    def test_static_movement_is_omitted(self):
        prompt = build_shot_prompt(
            {"description": "plain", "shot_language": {"shot_size": "wide",
                                                       "camera_movement": "static"}}
        )
        assert "static" not in prompt
        assert prompt == "wide shot capturing full scene. plain"

    def test_unknown_enum_falls_back_to_raw_value(self):
        prompt = build_shot_prompt(
            {"description": "d", "shot_language": {"shot_size": "dutch_angle_madeup"}}
        )
        assert "dutch_angle_madeup" in prompt

    def test_description_only_scene(self):
        assert build_shot_prompt({"description": "just this"}) == "just this"

    def test_batch_skips_transitions_and_keeps_ids(self):
        scenes = [
            {"id": "s1", "description": "a", "shot_language": {}, "hero_moment": True},
            {"id": "s2", "type": "transition", "description": "b"},
        ]
        out = build_batch_prompts(scenes)
        assert [o["scene_id"] for o in out] == ["s1"]
        assert out[0]["hero_moment"] is True


# ======================================================================
# playbook_generator
# ======================================================================


class TestPlaybookGenerator:
    def test_generate_maps_tone_to_category(self):
        pb = pg.generate_playbook("Test Corp", {"tone": "corporate", "mood": "bold"})
        assert pb["identity"]["name"] == "Test Corp"
        assert pb["identity"]["category"] == "motion-graphics"
        assert pb["identity"]["mood"] == "bold"

    def test_generate_applies_color_and_font_overrides(self):
        pb = pg.generate_playbook(
            "Branded",
            {
                "tone": "cinematic",
                "colors": {"primary": "#111111", "background": "#000000"},
                "fonts": {"headings": "Poppins", "body": "Lora"},
            },
        )
        assert pb["visual_language"]["color_palette"]["primary"] == ["#111111"]
        assert pb["visual_language"]["color_palette"]["background"] == "#000000"
        assert pb["typography"]["headings"]["font"] == "Poppins"
        assert pb["typography"]["body"]["font"] == "Lora"

    def test_minimal_playbook_mood_presets_differ(self):
        dark = pg._create_minimal_playbook("D", {"mood": "dark"})
        warm = pg._create_minimal_playbook("W", {"mood": "warm"})
        assert dark["visual_language"]["color_palette"]["background"] == "#0F172A"
        assert warm["visual_language"]["color_palette"]["background"] == "#FFFBEB"

    def test_generated_playbook_is_schema_valid(self):
        # save_playbook validates against schemas/styles/playbook.schema.json.
        # jsonschema.validate raising here would mean the generator emits an
        # invalid playbook — a real defect.
        pb = pg.generate_playbook("Schema Check", {"tone": "educational", "mood": "warm"})
        schema = pg._load_playbook_schema()
        jsonschema.validate(instance=pb, schema=schema)

    def test_save_and_load_roundtrip(self, tmp_path, monkeypatch):
        # Redirect the custom-styles dir so the test never writes into the repo.
        monkeypatch.setattr(pg, "CUSTOM_STYLES_DIR", tmp_path)
        pb = pg.generate_playbook("Round Trip", {"tone": "corporate", "mood": "playful"})

        saved = pg.save_playbook(pb, project_name="Round Trip Proj")
        assert saved.parent == tmp_path
        assert saved.name == "round-trip-proj.yaml"

        loaded = pg.load_existing_playbook("round-trip-proj")
        assert loaded["identity"]["name"] == "Round Trip"
        assert "round-trip-proj" in pg.list_playbooks()

    def test_save_rejects_invalid_playbook(self, tmp_path, monkeypatch):
        monkeypatch.setattr(pg, "CUSTOM_STYLES_DIR", tmp_path)
        with pytest.raises(jsonschema.ValidationError):
            pg.save_playbook({"identity": {"name": "broken"}}, project_name="broken")

    def test_load_unknown_playbook_raises(self):
        with pytest.raises(FileNotFoundError):
            pg.load_existing_playbook("no-such-playbook-xyz")
