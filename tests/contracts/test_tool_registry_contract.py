"""Parametrized contract test over the entire discovered tool fleet.

The AGENT_GUIDE preflight protocol and the three capability selectors all rely
on every tool exposing a well-formed support envelope and a non-crashing
availability check. Most provider adapters (video/image/audio/avatar) have no
individual tests, so a single silently-wrong `status`, malformed dependency, or
`get_status()` that raises would break the preflight menu contract undetected.

This module discovers every registered tool once and asserts the envelope
invariants against each of them, so adding a new adapter that violates the
contract fails here rather than at a user's preflight.
"""

from __future__ import annotations

import os

import pytest

from tools.base_tool import (
    Determinism,
    ExecutionMode,
    ResumeSupport,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)
from tools.tool_registry import ToolRegistry

# Discover once at import time so we can parametrize per tool. A fresh registry
# (not the global singleton) keeps this independent of other tests' state.
_registry = ToolRegistry()
_registry.discover()
_TOOL_NAMES = sorted(_registry.list_all())

_VALID = {
    "status": {s.value for s in ToolStatus},
    "tier": {s.value for s in ToolTier},
    "stability": {s.value for s in ToolStability},
    "runtime": {s.value for s in ToolRuntime},
    "execution_mode": {s.value for s in ExecutionMode},
    "determinism": {s.value for s in Determinism},
    "resume_support": {s.value for s in ResumeSupport},
}

_DEP_PREFIXES = ("env:", "cmd:", "python:")


def test_discovery_found_tools():
    """Discovery must register a non-trivial fleet; an empty sweep is a bug."""
    assert len(_TOOL_NAMES) > 20, f"only discovered {_TOOL_NAMES}"


@pytest.mark.parametrize("tool_name", _TOOL_NAMES)
class TestToolContract:
    """Invariants every registered tool must satisfy."""

    def test_name_matches_registry_key(self, tool_name):
        assert _registry.get(tool_name).name == tool_name

    def test_get_status_does_not_raise(self, tool_name):
        # Availability detection is called at every preflight — it must never
        # throw, only report available/unavailable/degraded.
        status = _registry.get(tool_name).get_status()
        assert isinstance(status, ToolStatus)

    def test_get_info_enums_are_valid(self, tool_name):
        info = _registry.get(tool_name).get_info()
        for field, allowed in _VALID.items():
            assert info[field] in allowed, f"{tool_name}.{field}={info[field]!r}"

    def test_capability_and_provider_non_empty(self, tool_name):
        tool = _registry.get(tool_name)
        assert isinstance(tool.capability, str) and tool.capability
        assert isinstance(tool.provider, str) and tool.provider

    def test_dependencies_well_formed(self, tool_name):
        # Every dependency is a string, and the known prefixes must carry a
        # non-empty target (an "env:" with no var name silently never checks).
        for dep in _registry.get(tool_name).dependencies:
            assert isinstance(dep, str) and dep
            for prefix in _DEP_PREFIXES:
                if dep.startswith(prefix):
                    assert dep[len(prefix):], f"{tool_name}: empty dep target {dep!r}"

    def test_installable_deps_have_instructions(self, tool_name):
        # If a tool can be unavailable for a fixable reason, preflight needs
        # text to show the user (AGENT_GUIDE reads install_instructions).
        tool = _registry.get(tool_name)
        needs_setup = any(d.startswith(_DEP_PREFIXES) for d in tool.dependencies)
        if needs_setup:
            assert tool.install_instructions.strip(), tool_name

    def test_usage_location_is_a_real_file(self, tool_name):
        info = _registry.get(tool_name).get_info()
        assert os.path.isfile(info["usage_location"]), tool_name

    def test_list_fields_are_lists(self, tool_name):
        info = _registry.get(tool_name).get_info()
        for field in ("best_for", "not_good_for", "fallback_tools", "capabilities"):
            assert isinstance(info[field], list), f"{tool_name}.{field}"

    def test_fallbacks_resolve_to_real_tools(self, tool_name):
        tool = _registry.get(tool_name)
        candidates = list(tool.fallback_tools or [])
        if tool.fallback:
            candidates.append(tool.fallback)
        for fb in candidates:
            assert isinstance(fb, str) and fb, f"{tool_name}: bad fallback {fb!r}"
            assert _registry.get(fb) is not None, (
                f"{tool_name} declares fallback {fb!r} but no such tool is registered"
            )


class TestRegistryReports:
    """The aggregate reports preflight consumes must stay internally consistent."""

    def test_support_envelope_covers_every_tool(self):
        envelope = _registry.support_envelope()
        assert set(envelope) == set(_TOOL_NAMES)

    def test_capability_catalog_families_non_empty(self):
        catalog = _registry.capability_catalog()
        assert catalog
        for family, entries in catalog.items():
            assert family, "capability family key must be non-empty"
            assert isinstance(entries, list) and entries

    def test_provider_catalog_families_non_empty(self):
        catalog = _registry.provider_catalog()
        assert catalog
        for provider, entries in catalog.items():
            assert provider
            assert isinstance(entries, list) and entries

    def test_provider_menu_summary_shape(self):
        # The four fields AGENT_GUIDE tells the agent to translate at preflight.
        summary = _registry.provider_menu_summary()
        assert set(summary) >= {
            "composition_runtimes",
            "capabilities",
            "setup_offers",
            "runtime_warnings",
        }
        runtimes = summary["composition_runtimes"]
        for engine in ("ffmpeg", "remotion", "hyperframes"):
            assert isinstance(runtimes[engine], bool)
