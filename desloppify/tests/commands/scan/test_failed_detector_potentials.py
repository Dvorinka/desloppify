"""#821: failed detectors keep prior scoring potential and mark reduced coverage."""

from __future__ import annotations

from types import SimpleNamespace

from desloppify.app.commands.scan.workflow import _restore_failed_detector_potentials


def test_preserves_prior_potential_for_failed_detector() -> None:
    state = {"potentials": {"typescript": {"other": 5}}}
    _restore_failed_detector_potentials(
        state,
        "typescript",
        coverage={"boilerplate_duplication": {"status": "reduced"}},
        potentials={"other": 5},
        prev_lang_potentials={"boilerplate_duplication": 69, "other": 5},
    )
    assert state["potentials"]["typescript"]["boilerplate_duplication"] == 69


def test_skips_detector_that_produced_potential() -> None:
    state = {"potentials": {"typescript": {}}}
    _restore_failed_detector_potentials(
        state,
        "typescript",
        coverage={"boilerplate_duplication": {"status": "reduced"}},
        potentials={"boilerplate_duplication": 10},
        prev_lang_potentials={"boilerplate_duplication": 69},
    )
    assert "boilerplate_duplication" not in state["potentials"]["typescript"]


def test_skips_full_coverage_detectors() -> None:
    state = {"potentials": {"typescript": {}}}
    _restore_failed_detector_potentials(
        state,
        "typescript",
        coverage={"boilerplate_duplication": {"status": "full"}},
        potentials={},
        prev_lang_potentials={"boilerplate_duplication": 69},
    )
    assert "boilerplate_duplication" not in state["potentials"]["typescript"]


def test_jscpd_failure_records_reduced_coverage(monkeypatch) -> None:
    """phase_boilerplate_duplication marks coverage reduced when jscpd fails."""
    import desloppify.languages._framework.base.shared_phases_review as review_mod

    lang = SimpleNamespace(
        zone_map=None,
        review_cache=None,
        name="typescript",
        detector_coverage={},
        complexity_map={},
    )
    monkeypatch.setattr(review_mod, "_resolve_detector_files", lambda _p, _l: [])
    monkeypatch.setattr(review_mod, "detect_with_jscpd", lambda _p: None)
    monkeypatch.setattr(review_mod, "_consume_prefetch_result", lambda *_a: None)

    issues, potentials = review_mod.phase_boilerplate_duplication(
        __import__("pathlib").Path("."), lang
    )

    assert issues == [] and potentials == {}
    record = lang.detector_coverage["boilerplate_duplication"]
    assert record["status"] == "reduced"
    assert record["tool"] == "jscpd"
