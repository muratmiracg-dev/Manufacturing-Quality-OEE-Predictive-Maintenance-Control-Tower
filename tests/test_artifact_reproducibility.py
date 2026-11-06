from __future__ import annotations

import importlib.util
import json
import warnings
from pathlib import Path

import joblib
import pytest
import sklearn
from sklearn.exceptions import InconsistentVersionWarning

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "compare_artifacts", ROOT / "scripts" / "compare_artifacts.py"
)
compare_artifacts = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(compare_artifacts)


def _tree(root: Path, files: dict[str, str]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (root / name).write_text(text, encoding="utf-8")
    return root


def test_float_noise_is_tolerated(tmp_path: Path) -> None:
    old = _tree(
        tmp_path / "old",
        {
            "p.csv": "shift_id,failure_probability\nSH-1,0.056359511510873934\n",
            "m.json": json.dumps({"oee": 0.8526647989314223, "counts": {"P1": 4}}),
        },
    )
    new = _tree(
        tmp_path / "new",
        {
            "p.csv": "shift_id,failure_probability\nSH-1,0.05635951151087432\n",
            "m.json": json.dumps({"oee": 0.8526647989314225, "counts": {"P1": 4}}),
        },
    )
    assert compare_artifacts.compare_trees(old, new) == []


def test_dependency_drift_is_reported(tmp_path: Path) -> None:
    # Values observed when artifacts built with scikit-learn 1.8 were rerun on 1.9.
    old = _tree(
        tmp_path / "old",
        {
            "priority.csv": "machine_id,failure_probability,priority\nMC-05,0.3413,P1\n",
            "metrics.json": json.dumps({"recommendation_counts": {"MONITOR": 7, "P1": 5}}),
            "gone.csv": "x\n1\n",
        },
    )
    new = _tree(
        tmp_path / "new",
        {
            "priority.csv": "machine_id,failure_probability,priority\nMC-05,0.3504,P2\n",
            "metrics.json": json.dumps({"recommendation_counts": {"MONITOR": 7, "P1": 4, "P2": 1}}),
        },
    )
    problems = "\n".join(compare_artifacts.compare_trees(old, new))
    assert "priority.csv: column 'failure_probability'" in problems
    assert "priority.csv: column 'priority'" in problems
    assert "metrics.json: $.recommendation_counts.P1: 5 != 4" in problems
    assert "metrics.json: $.recommendation_counts.P2: present on one side only" in problems
    assert "gone.csv: missing after regeneration" in problems


def test_structure_changes_are_reported(tmp_path: Path) -> None:
    old = _tree(tmp_path / "old", {"a.csv": "x,y\n1,2\n", "b.json": "[1, 2]"})
    new = _tree(tmp_path / "new", {"a.csv": "x,z\n1,2\n", "b.json": "[1]"})
    problems = compare_artifacts.compare_trees(old, new)
    assert any("columns differ" in item for item in problems)
    assert "b.json: $: length 2 != 1" in problems


def test_main_exit_codes(tmp_path: Path) -> None:
    old = _tree(tmp_path / "old", {"m.json": '{"v": 1.0}'})
    same = _tree(tmp_path / "same", {"m.json": '{"v": 1.0}'})
    drift = _tree(tmp_path / "drift", {"m.json": '{"v": 1.1}'})
    empty = _tree(tmp_path / "empty", {})
    assert compare_artifacts.main([str(old), str(same)]) == 0
    assert compare_artifacts.main([str(old), str(drift)]) == 1
    assert compare_artifacts.main([str(empty), str(same)]) == 1


def test_committed_model_bundle_matches_installed_scikit_learn() -> None:
    """The API unpickles this bundle; pickles are not portable across scikit-learn versions."""

    path = ROOT / "artifacts" / "model" / "champion_bundle.joblib"
    with warnings.catch_warnings():
        warnings.simplefilter("error", InconsistentVersionWarning)
        try:
            joblib.load(path)
        except InconsistentVersionWarning as exc:
            pytest.fail(
                f"champion_bundle.joblib was pickled with scikit-learn "
                f"{exc.original_sklearn_version}, installed {sklearn.__version__}; "
                "rerun the pipeline after dependency changes"
            )
