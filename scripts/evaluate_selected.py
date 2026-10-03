"""Evaluate exactly the frozen selected checkpoint, without changing selection."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cnn_tutorial.data import sha256
from cnn_tutorial.training import test_checkpoint


def evaluate_selected(study_dir, data_root):
    study_dir = Path(study_dir)
    selection = json.loads((study_dir / "selection.json").read_text(encoding="utf-8"))
    if selection["plan_sha256"] != sha256(study_dir / "plan.json"):
        raise ValueError("The frozen experiment plan has changed")
    run = study_dir / selection["selected"]
    if selection["checkpoint_sha256"] != sha256(run / "best.pt"):
        raise ValueError("The selected checkpoint has changed")
    destination = study_dir / "selected_test.json"
    if destination.exists():
        raise FileExistsError("Selected test already evaluated; read its stored report")
    metrics = test_checkpoint(data_root, run)
    report = {"selected": selection["selected"], "selection_sha256": sha256(study_dir / "selection.json"),
              "metrics": metrics,
              "interpretation": "Official test retained from v0.1, already observed; retrospective benchmark, not new camera acceptance"}
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    print(json.dumps(evaluate_selected(root / "artifacts" / "v0.2-grouped-study", root / "data" / "rps"), indent=2))
