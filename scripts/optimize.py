"""Bounded, predeclared experiment; no official test access during selection."""
from dataclasses import asdict
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cnn_tutorial.data import create_grouped_manifest, sha256
from cnn_tutorial.training import TrainConfig, fit

ROOT = Path(__file__).resolve().parents[1]


def run_study(study_dir):
    study_dir = Path(study_dir)
    study_dir.mkdir(parents=True, exist_ok=False)
    data = ROOT / "data" / "rps"
    manifest = create_grouped_manifest(data)
    candidates = {
        "grouped-control": TrainConfig(manifest_file="manifest_grouped.json"),
        "small-affine": TrainConfig(epochs=60, augment_policy="affine", manifest_file="manifest_grouped.json"),
        "wide-affine": TrainConfig(epochs=60, width=16, augment_policy="affine", manifest_file="manifest_grouped.json"),
    }
    plan = {"candidates": {name: asdict(config) for name, config in candidates.items()},
            "selection": "validation accuracy descending, validation loss ascending, parameter count ascending",
            "manifest_sha256": sha256(data / "manifest_grouped.json"),
            "held_out_groups": manifest["held_out_groups"], "test_used_for_selection": False}
    (study_dir / "plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    summaries = {}
    for name, config in candidates.items():
        print(f"Candidate: {name}", flush=True)
        _, _, summaries[name] = fit(data, study_dir / name, config)
    winner = min(summaries, key=lambda name: (-summaries[name]["validation"]["accuracy"],
                 summaries[name]["validation"]["loss"], summaries[name]["complexity"]["parameters"]))
    selection = {"selected": winner, "plan_sha256": sha256(study_dir / "plan.json"),
                 "checkpoint_sha256": sha256(study_dir / winner / "best.pt"),
                 "candidates": summaries, "official_test_evaluated": False}
    (study_dir / "selection.json").write_text(json.dumps(selection, indent=2), encoding="utf-8")
    print("Frozen selection:", winner, flush=True)
    return selection


if __name__ == "__main__":
    run_study(ROOT / "artifacts" / "v0.2-grouped-study")
