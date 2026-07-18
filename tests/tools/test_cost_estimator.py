"""Unit tests for the reference-driven cost estimator in tools/cost_tracker.py.

`CostTracker.estimate_from_reference` and its motion-ratio helpers are the
governance-critical core behind the "announce exact cost before any paid call"
contract in AGENT_GUIDE.md, yet the existing phase0 contract test only exercises
the simple estimate/reserve/reconcile lifecycle. This module covers the
estimator's math directly: scene-density scaling, pacing-aware minimums,
narration WPM scaling, motion-ratio classification/fallback, clip coverage,
the retry buffer, the cost range, sample cost, and confidence.

Expected numeric values below were derived from the implementation and checked
by hand — see the inline arithmetic in each test.
"""

from __future__ import annotations

import pytest

from tools.cost_tracker import CostTracker


def _brief(
    *,
    ref_duration=120,
    total_scenes=20,
    pacing_style="steady_educational",
    scenes=None,
    word_count=300,
    source_type="youtube",
    replication=None,
):
    """Build a minimal VideoAnalysisBrief-shaped dict for the estimator."""
    brief: dict = {
        "source": {"duration_seconds": ref_duration, "type": source_type},
        "structure_analysis": {
            "total_scenes": total_scenes,
            "pacing_profile": {"pacing_style": pacing_style},
            "scenes": scenes if scenes is not None else [],
        },
        "narration_transcript": {"word_count": word_count},
    }
    if replication is not None:
        brief["replication_guidance"] = replication
    return brief


FULL_PLAN = {
    "image_generation": {"tool": "flux_fal", "cost_per_unit": 0.05},
    "video_generation": {"tool": "kling_fal", "cost_per_unit": 0.30, "clip_duration_seconds": 5},
    "tts": {"tool": "elevenlabs_tts", "cost_per_word": 0.00003},
    "music": {"tool": "music_gen", "cost_per_track": 0.10},
}


class TestSceneCountAndPacing:
    def test_scene_count_preserves_reference_cut_rate(self):
        # 20 scenes over 120s = 10 cuts/min. Scaling to 60s preserves the rate,
        # so density_based = round(10 * 60/60) = 10, well above the
        # steady_educational minimum of 5.
        tracker = CostTracker()
        result = tracker.estimate_from_reference(
            _brief(ref_duration=120, total_scenes=20), 60, {}
        )
        assert result["cuts_per_minute"] == 10.0
        assert result["estimated_scenes"] == 10

    def test_pacing_minimum_floors_a_sparse_reference(self):
        # A reference with few cuts must not collapse to a slideshow when the
        # pacing style is fast: rapid_fire has a floor of 10 scenes.
        tracker = CostTracker()
        result = tracker.estimate_from_reference(
            _brief(ref_duration=60, total_scenes=2, pacing_style="rapid_fire"),
            60,
            {},
        )
        # density_based = round(2 * 1) = 2, but the rapid_fire floor is 10.
        assert result["estimated_scenes"] == 10

    def test_zero_reference_duration_uses_default_cut_rate(self):
        tracker = CostTracker()
        result = tracker.estimate_from_reference(
            _brief(ref_duration=0, total_scenes=8, pacing_style="variable"),
            60,
            {},
        )
        assert result["cuts_per_minute"] == 4.0  # documented default


class TestNarration:
    def test_word_count_scales_from_reference_wpm(self):
        # 300 words over 120s = 150 WPM; a 60s target needs ~150 words.
        tracker = CostTracker()
        result = tracker.estimate_from_reference(
            _brief(ref_duration=120, word_count=300), 60, {}
        )
        assert result["estimated_words"] == 150

    def test_missing_narration_uses_default_pace(self):
        tracker = CostTracker()
        result = tracker.estimate_from_reference(
            _brief(word_count=0), 60, {}
        )
        # default conversational pace is 150 WPM -> ~150 words for 60s
        assert result["estimated_words"] == 150


class TestMotionRatioClassification:
    def test_classified_scene_types_averaged(self):
        # animation (1.0) + text_card (0.2), no unknowns -> mean 0.6.
        tracker = CostTracker()
        ratio, basis = tracker._estimate_motion_ratio(
            video_analysis_brief={},
            scenes_list=[{"visual_type": "animation"}, {"visual_type": "text_card"}],
            pacing_style="steady_educational",
        )
        assert ratio == 0.6
        assert "classified scene types" in basis

    def test_motion_ratio_clamped_to_ceiling(self):
        # All-animation would be 1.0 but the estimator caps motion ratio at 0.95.
        tracker = CostTracker()
        ratio, _ = tracker._estimate_motion_ratio(
            video_analysis_brief={},
            scenes_list=[{"visual_type": "animation"}] * 3,
            pacing_style="variable",
        )
        assert ratio == 0.95

    def test_unclassified_scenes_blend_with_fallback(self):
        # 1 classified animation (1.0) + 1 unclassified scene; slow_contemplative
        # fallback is 0.2 -> (1.0 + 0.2) / 2 = 0.6, and the basis says "blended".
        tracker = CostTracker()
        ratio, basis = tracker._estimate_motion_ratio(
            video_analysis_brief={},
            scenes_list=[{"visual_type": "animation"}, {"note": "no visual_type"}],
            pacing_style="slow_contemplative",
        )
        assert ratio == 0.6
        assert "blended" in basis


class TestMotionRatioFallback:
    def test_pacing_style_baseline(self):
        tracker = CostTracker()
        ratio, basis = tracker._fallback_motion_ratio(
            video_analysis_brief={}, pacing_style="rapid_fire"
        )
        assert ratio == 0.8
        assert "not been enriched" in basis

    def test_short_form_source_bumps_ratio(self):
        # steady_educational baseline is 0.35, but a tiktok source floors it at 0.7.
        tracker = CostTracker()
        ratio, _ = tracker._fallback_motion_ratio(
            video_analysis_brief={"source": {"type": "tiktok"}},
            pacing_style="steady_educational",
        )
        assert ratio == 0.7

    def test_motion_required_floor(self):
        tracker = CostTracker()
        ratio, _ = tracker._fallback_motion_ratio(
            video_analysis_brief={"replication_guidance": {"motion_required": True}},
            pacing_style="steady_educational",
        )
        assert ratio == 0.6

    def test_cinematic_pipeline_floor(self):
        tracker = CostTracker()
        ratio, _ = tracker._fallback_motion_ratio(
            video_analysis_brief={
                "replication_guidance": {"suggested_pipeline": "cinematic"}
            },
            pacing_style="slow_contemplative",
        )
        assert ratio == 0.55

    def test_empty_scene_list_routes_to_fallback(self):
        # No classified scenes at all -> estimator uses the fallback path.
        tracker = CostTracker()
        ratio, basis = tracker._estimate_motion_ratio(
            video_analysis_brief={"source": {"type": "youtube"}},
            scenes_list=[],
            pacing_style="rapid_fire",
        )
        assert ratio == 0.8
        assert "not been enriched" in basis


class TestLineItemsAndTotals:
    @pytest.fixture
    def result(self):
        tracker = CostTracker()
        return tracker.estimate_from_reference(
            _brief(
                ref_duration=120,
                total_scenes=20,
                pacing_style="steady_educational",
                scenes=[{"visual_type": "animation"}, {"visual_type": "text_card"}],
                word_count=300,
            ),
            60,
            FULL_PLAN,
        )

    def test_line_items_cover_every_planned_category(self, result):
        cats = {item["category"] for item in result["line_items"]}
        assert cats == {"image_generation", "video_generation", "tts_narration", "music"}

    def test_image_quantity_includes_retry_buffer(self, result):
        # estimated_images = max(10, round(10 * 1.5)) = 15; with the 1.3 retry
        # multiplier -> round(15 * 1.3) = 20 units at $0.05 = $1.00.
        img = next(i for i in result["line_items"] if i["category"] == "image_generation")
        assert img["quantity"] == 20
        assert img["total_usd"] == 1.0

    def test_video_clip_coverage_and_buffer(self, result):
        # motion_ratio 0.6 -> 36s of motion / 5s clips = 7 clips of coverage;
        # with retry buffer round(7 * 1.3) = 9 clips at $0.30 = $2.70.
        assert result["estimated_clips"] == 7
        vid = next(i for i in result["line_items"] if i["category"] == "video_generation")
        assert vid["quantity"] == 9
        assert vid["total_usd"] == 2.7

    def test_total_and_range(self, result):
        # subtotal = 1.00 + 2.70 + 0.0045 + 0.10 = 3.8045
        assert result["total_usd"] == 3.8045
        # low divides out the retry buffer; high adds 15%.
        assert result["total_range_usd"]["low"] == pytest.approx(3.8045 / 1.3, abs=1e-4)
        assert result["total_range_usd"]["high"] == pytest.approx(3.8045 * 1.15, abs=1e-4)

    def test_sample_cost_is_two_scenes_worth(self, result):
        # sample fraction = 2 / estimated_scenes(10) = 0.2 of subtotal.
        assert result["sample_cost_usd"] == pytest.approx(3.8045 * 0.2, abs=1e-4)

    def test_confidence_high_with_scenes_and_narration(self, result):
        assert result["confidence"] == "high"


class TestConfidenceLevels:
    def test_medium_confidence_with_only_narration(self):
        tracker = CostTracker()
        result = tracker.estimate_from_reference(
            _brief(scenes=[], word_count=300), 60, {}
        )
        assert result["confidence"] == "medium"

    def test_low_confidence_with_neither_signal(self):
        tracker = CostTracker()
        result = tracker.estimate_from_reference(
            _brief(scenes=[], word_count=0), 60, {}
        )
        assert result["confidence"] == "low"


class TestPlanGating:
    def test_no_tool_plan_yields_no_line_items(self):
        tracker = CostTracker()
        result = tracker.estimate_from_reference(_brief(), 60, {})
        assert result["line_items"] == []
        assert result["total_usd"] == 0.0

    def test_tts_skipped_when_too_few_words(self):
        # estimated_words <= 10 must not emit a TTS line item.
        tracker = CostTracker()
        result = tracker.estimate_from_reference(
            _brief(ref_duration=600, word_count=1),  # ~0.1 WPM -> 0 words for 60s
            60,
            {"tts": {"tool": "elevenlabs_tts", "cost_per_word": 0.00003}},
        )
        cats = {item["category"] for item in result["line_items"]}
        assert "tts_narration" not in cats
