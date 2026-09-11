"""Fixture-driven parse tests for stock_sources base + adapters.

The stock_sources package (base protocol + 14 source adapters) drives the
documentary-montage corpus builder, yet only helper-level coverage existed for
Wikimedia/Unsplash. Here we cover:

  * the shared `base` types (Candidate.clip_id, SearchFilters defaults),
  * the package discovery/catalog/summary surface,
  * the pure rendition-picking helpers in the Pexels and NASA adapters, and
  * each adapter's response-normalization path, driven by a fake `requests.get`
    so no network is touched.

The goal is to lock the JSON-to-Candidate mapping: a schema drift in a source's
API response, or a regression in rendition selection, should fail here.
"""

from __future__ import annotations

import pytest

from tools.video.stock_sources import (
    all_sources,
    available_sources,
    get_source,
    source_catalog,
    source_summary,
)
from tools.video.stock_sources.base import Candidate, SearchFilters
from tools.video.stock_sources.nasa import (
    NasaSource,
    _encode_url_path,
    _pick_image_url,
    _pick_video_url,
    _sanitize_source_id,
)
from tools.video.stock_sources.pexels import (
    PexelsSource,
    _pick_video_rendition,
    _slug_tags_from_url,
)


# Adapters do a lazy `import requests` inside each method, and another test in
# the suite deletes `requests` from sys.modules, so a held module reference can
# go stale. Patching the string target "requests.get" resolves the live module
# from sys.modules at patch time, matching what the adapter imports at call time.


class _FakeResponse:
    """Minimal stand-in for a requests.Response with a JSON body."""

    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


# ----------------------------------------------------------------------
# base protocol types
# ----------------------------------------------------------------------


class TestBaseTypes:
    def test_clip_id_is_source_prefixed(self):
        cand = Candidate(
            source="pexels",
            source_id="123",
            source_url="u",
            download_url="d",
            kind="video",
        )
        assert cand.clip_id == "pexels_123"

    def test_search_filters_defaults(self):
        f = SearchFilters()
        assert f.kind == "video"
        assert f.per_page == 20
        assert f.page == 1
        assert f.min_duration is None and f.max_duration is None


# ----------------------------------------------------------------------
# package discovery surface
# ----------------------------------------------------------------------


class TestPackageDiscovery:
    def test_core_adapters_are_discovered(self):
        names = {s.name for s in all_sources()}
        assert {"pexels", "nasa"} <= names

    def test_available_is_subset_of_all(self):
        all_names = {s.name for s in all_sources()}
        avail_names = {s.name for s in available_sources()}
        assert avail_names <= all_names

    def test_source_summary_counts_match_catalog(self):
        catalog = source_catalog()
        summary = source_summary()
        assert summary["total"] == len(catalog)
        assert summary["configured"] == sum(
            1 for e in catalog if e["status"] == "available"
        )
        assert (
            summary["configured"] + len(summary["unavailable_source_names"])
            == summary["total"]
        )

    def test_catalog_entries_have_discoverability_fields(self):
        for entry in source_catalog():
            assert entry["name"]
            assert entry["status"] in ("available", "unavailable")
            assert isinstance(entry["supports"], dict)
            assert entry["install_instructions"]

    def test_get_source_roundtrip_and_unknown(self):
        assert get_source("pexels").name == "pexels"
        with pytest.raises(KeyError):
            get_source("does-not-exist")


# ----------------------------------------------------------------------
# Pexels
# ----------------------------------------------------------------------


class TestPexelsHelpers:
    def test_pick_largest_rendition_within_cap(self):
        files = [
            {"file_type": "video/mp4", "width": 640, "link": "sd"},
            {"file_type": "video/mp4", "width": 1920, "link": "hd"},
            {"file_type": "video/mp4", "width": 3840, "link": "uhd"},  # above cap
            {"file_type": "image/jpeg", "width": 1000, "link": "img"},  # not video
            {"file_type": "video/mp4", "width": 1280},  # no link
        ]
        assert _pick_video_rendition(files)["link"] == "hd"

    def test_pick_rendition_respects_min_width(self):
        files = [
            {"file_type": "video/mp4", "width": 640, "link": "sd"},
            {"file_type": "video/mp4", "width": 1920, "link": "hd"},
        ]
        assert _pick_video_rendition(files, min_width=1000)["link"] == "hd"

    def test_pick_rendition_returns_none_when_no_video(self):
        assert _pick_video_rendition([{"file_type": "audio/mp3", "width": 10, "link": "a"}]) is None

    def test_slug_tags_strips_trailing_id(self):
        url = "https://www.pexels.com/video/aerial-view-of-city-at-night-3571264/"
        assert _slug_tags_from_url(url) == "aerial view of city at night"

    def test_slug_tags_empty_on_unparseable(self):
        assert _slug_tags_from_url("") == ""


class TestPexelsSearchParsing:
    @pytest.fixture(autouse=True)
    def _api_key(self, monkeypatch):
        monkeypatch.setenv("PEXELS_API_KEY", "test-key")

    def test_video_search_normalizes_and_filters(self, monkeypatch):
        payload = {
            "videos": [
                {
                    "id": 123,
                    "url": "https://www.pexels.com/video/rainy-street-999/",
                    "duration": 8,
                    "width": 1920,
                    "height": 1080,
                    "image": "thumb.jpg",
                    "user": {"name": "Jane", "url": "u"},
                    "video_files": [
                        {"file_type": "video/mp4", "width": 1920, "link": "dl.mp4",
                         "fps": 30, "quality": "hd"}
                    ],
                },
                {  # filtered out by min_duration
                    "id": 124,
                    "url": "x",
                    "duration": 2,
                    "video_files": [
                        {"file_type": "video/mp4", "width": 1280, "link": "y.mp4"}
                    ],
                },
            ]
        }
        monkeypatch.setattr("requests.get", lambda *a, **k: _FakeResponse(payload))

        results = PexelsSource().search(
            "rain", SearchFilters(kind="video", min_duration=5)
        )
        assert len(results) == 1
        c = results[0]
        assert c.clip_id == "pexels_123"
        assert c.kind == "video"
        assert c.creator == "Jane"
        assert c.duration == 8.0
        assert c.download_url == "dl.mp4"
        assert c.source_tags == "rainy street"
        assert c.extra["fps"] == 30

    def test_image_search_prefers_large2x(self, monkeypatch):
        payload = {
            "photos": [
                {
                    "id": 55,
                    "url": "https://www.pexels.com/photo/cat-55/",
                    "width": 4000,
                    "height": 3000,
                    "photographer": "Ada",
                    "alt": "a sleepy cat",
                    "src": {"large2x": "big.jpg", "original": "orig.jpg", "medium": "m.jpg"},
                }
            ]
        }
        monkeypatch.setattr("requests.get", lambda *a, **k: _FakeResponse(payload))

        results = PexelsSource().search("cat", SearchFilters(kind="image"))
        assert len(results) == 1
        c = results[0]
        assert c.kind == "image"
        assert c.download_url == "big.jpg"
        assert c.duration == 0.0
        assert c.creator == "Ada"
        assert c.source_tags == "a sleepy cat"

    def test_image_search_respects_min_width(self, monkeypatch):
        payload = {
            "photos": [
                {"id": 1, "url": "u", "width": 500, "height": 400,
                 "src": {"large2x": "small.jpg"}},
            ]
        }
        monkeypatch.setattr("requests.get", lambda *a, **k: _FakeResponse(payload))
        results = PexelsSource().search(
            "x", SearchFilters(kind="image", min_width=1920)
        )
        assert results == []


# ----------------------------------------------------------------------
# NASA
# ----------------------------------------------------------------------


class TestNasaHelpers:
    def test_video_url_priority_prefers_orig(self):
        urls = [
            "http://x/PIA~small.mp4",
            "http://x/PIA~orig.mp4",
            "http://x/PIA~large.mp4",
            "http://x/PIA~thumb.jpg",
        ]
        assert _pick_video_url(urls) == "http://x/PIA~orig.mp4"

    def test_video_url_fallback_to_any_mp4(self):
        assert _pick_video_url(["http://x/foo.mp4"]) == "http://x/foo.mp4"

    def test_video_url_none_when_no_video(self):
        assert _pick_video_url(["http://x/foo.jpg"]) == ""

    def test_image_url_priority(self):
        urls = ["http://x/a~large.jpg", "http://x/a~orig.jpg"]
        assert _pick_image_url(urls) == "http://x/a~orig.jpg"

    def test_sanitize_source_id_makes_fs_safe(self):
        assert _sanitize_source_id("As11-40-5874 (The Eagle) ") == "As11-40-5874_The_Eagle"

    def test_sanitize_source_id_empty_becomes_unknown(self):
        assert _sanitize_source_id("   ") == "unknown"

    def test_encode_url_path_quotes_spaces_only(self):
        assert _encode_url_path("https://x.gov/a b/c.mp4") == "https://x.gov/a%20b/c.mp4"


class TestNasaSearchParsing:
    def test_hydrate_candidate_follows_asset_manifest(self, monkeypatch):
        search_payload = {
            "collection": {
                "items": [
                    {
                        "href": "https://images-api.nasa.gov/asset/PIA123",
                        "data": [
                            {
                                "nasa_id": "PIA123",
                                "media_type": "video",
                                "title": "Mars flyover",
                                "description": "desc",
                                "keywords": ["mars", "orbit"],
                                "center": "JPL",
                            }
                        ],
                        "links": [{"rel": "preview", "href": "prev.jpg"}],
                    }
                ]
            }
        }
        manifest = ["https://x/PIA123~orig.mp4", "https://x/PIA123~thumb.jpg"]

        def fake_get(url, *args, **kwargs):
            return _FakeResponse(manifest if "asset" in url else search_payload)

        monkeypatch.setattr("requests.get", fake_get)

        results = NasaSource().search("mars", SearchFilters(kind="video"))
        assert len(results) == 1
        c = results[0]
        assert c.clip_id == "nasa_PIA123"
        assert c.kind == "video"
        assert c.download_url == "https://x/PIA123~orig.mp4"
        assert c.thumbnail_url == "prev.jpg"
        assert c.source_tags == "Mars flyover desc mars orbit"
        assert c.source_url == "https://images.nasa.gov/details/PIA123"

    def test_item_without_data_is_skipped(self, monkeypatch):
        search_payload = {"collection": {"items": [{"href": "h", "data": []}]}}
        monkeypatch.setattr(
            "requests.get", lambda *a, **k: _FakeResponse(search_payload)
        )
        assert NasaSource().search("mars", SearchFilters(kind="video")) == []
