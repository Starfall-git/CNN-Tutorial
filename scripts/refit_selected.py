"""Refit on all official training images using only the frozen dev choice.

No validation scoring or early stopping after combining train + validation.
Epoch count comes from the selected dev checkpoint, LR horizon from its config.
"""
from dataclasses import asdict
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import torch
from torch.utils.data import DataLoader
from cnn_tutorial.data import CLASSES, GestureDataset, sha256
from cnn_tutorial.model import GrayGestureCNN, profile_model
from cnn_tutorial.training import TrainConfig, seed_everything, train_epoch


def refit_selected(study_dir, data_root):
    study_dir, data_root = Path(study_dir), Path(data_root)
    selection = json.loads((study_dir / "selection.json").read_text(encoding="utf-8"))
    if selection["plan_sha256"] != sha256(study_dir / "plan.json"):
        raise ValueError("Frozen plan changed")
    summary = selection["candidates"][selection["selected"]]
    source_checkpoint = study_dir / selection["selected"] / "best.pt"
    if sha256(source_checkpoint) != selection["checkpoint_sha256"]:
        raise ValueError("Selected checkpoint changed")
    source_config = TrainConfig(**summary["config"])
    manifest = json.loads((data_root / source_config.manifest_file).read_text(encoding="utf-8"))
    if sha256(data_root / source_config.manifest_file) != summary["manifest_sha256"]:
        raise ValueError("Development manifest changed")
    for row in manifest["rows"]:
        if row["split"] == "val":
            row["split"] = "train"
    manifest["split_policy"] = "all official training images; no validation; official test unchanged"
    manifest.pop("held_out_groups", None)
    filename = "manifest_refit.json"
    manifest_path = data_root / filename
    serialized = json.dumps(manifest, indent=2)
    if manifest_path.exists() and manifest_path.read_text(encoding="utf-8") != serialized:
        raise FileExistsError("Refit manifest exists with different contents")
    manifest_path.write_text(serialized, encoding="utf-8")
    config = TrainConfig(**{**asdict(source_config), "epochs": summary["best_epoch"], "manifest_file": filename})
    run = study_dir / "refit"
    run.mkdir(exist_ok=False)
    protocol = {"config": asdict(config), "lr_horizon": source_config.epochs,
                "selection_sha256": sha256(study_dir / "selection.json"),
                "weights": "fresh seeded initialization, final epoch saved; no validation selection",
                "official_test_used_for_training": False}
    (run / "protocol.json").write_text(json.dumps(protocol, indent=2), encoding="utf-8")
    seed_everything(config.seed)
    dataset = GestureDataset(data_root, "train", True, filename, config.augment_policy)
    loader = DataLoader(dataset, batch_size=config.batch_size, shuffle=True,
                        generator=torch.Generator().manual_seed(config.seed))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = GrayGestureCNN(width=config.width).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, source_config.epochs)
    history = []
    for epoch in range(1, config.epochs + 1):
        metrics = train_epoch(model, loader, optimizer, device)
        history.append({"epoch": epoch, "lr": optimizer.param_groups[0]["lr"], **metrics})
        scheduler.step()
        print(f"refit {epoch}/{config.epochs}: train={metrics['accuracy']:.3%}", flush=True)
        (run / "history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    torch.save({"state_dict": model.state_dict(), "config": asdict(config), "classes": list(CLASSES),
                "epoch": config.epochs, "manifest_sha256": sha256(manifest_path),
                "selection_method": "refit final epoch from frozen development protocol"}, run / "best.pt")
    report = {"config": asdict(config), "train_samples": len(dataset),
              "checkpoint_sha256": sha256(run / "best.pt"), "manifest_sha256": sha256(manifest_path),
              "complexity": profile_model(model), "validation": None}
    (run / "summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    print(json.dumps(refit_selected(root / "artifacts" / "v0.2-grouped-study", root / "data" / "rps"), indent=2))
