"""Readable training/evaluation; validation selects weights, test never does."""
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import random
import time

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from .data import CLASSES, GestureDataset, sha256
from .model import GrayGestureCNN, profile_model


@dataclass
class TrainConfig:
    epochs: int = 25
    batch_size: int = 64
    learning_rate: float = 0.001
    weight_decay: float = 0.0001
    seed: int = 42
    augment: bool = True
    width: int = 8
    augment_policy: str = "basic"
    manifest_file: str = "manifest.json"
    init_features_from: str | None = None


def seed_everything(seed):
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(min(4, os.cpu_count() or 1))


def make_loaders(root, config):
    # num_workers=0 works reliably in Windows Jupyter notebooks.
    generator = torch.Generator().manual_seed(config.seed)
    train = DataLoader(GestureDataset(root, "train", config.augment, config.manifest_file, config.augment_policy),
                       batch_size=config.batch_size, shuffle=True, generator=generator, num_workers=0)
    val = DataLoader(GestureDataset(root, "val", manifest_file=config.manifest_file), batch_size=config.batch_size, num_workers=0)
    return train, val


def train_epoch(model, loader, optimizer, device):
    model.train()
    total_loss, correct, count = 0.0, 0, 0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad(set_to_none=True)
        logits = model(images)
        loss = nn.functional.cross_entropy(logits, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * labels.numel()
        correct += (logits.argmax(1) == labels).sum().item()
        count += labels.numel()
    return {"loss": total_loss / count, "accuracy": correct / count}


@torch.inference_mode()
def evaluate(model, loader, device):
    model.eval()
    classes = getattr(loader.dataset, "classes", CLASSES)
    matrix = torch.zeros(len(classes), len(classes), dtype=torch.int64)
    total_loss = 0.0
    for images, labels in loader:
        logits = model(images.to(device))
        total_loss += nn.functional.cross_entropy(logits, labels.to(device), reduction="sum").item()
        predicted = logits.argmax(1).cpu()
        matrix += torch.bincount(labels * len(classes) + predicted,
                                 minlength=len(classes) ** 2).reshape(len(classes), len(classes))
    return metrics_from_confusion(matrix.numpy(), total_loss, classes)


def metrics_from_confusion(matrix, total_loss=None, classes=CLASSES):
    matrix = np.asarray(matrix)
    true_positives = np.diag(matrix)
    precision = true_positives / np.maximum(matrix.sum(0), 1)
    recall = true_positives / np.maximum(matrix.sum(1), 1)
    f1 = 2 * precision * recall / np.maximum(precision + recall, 1e-12)
    result = {"samples": int(matrix.sum()), "accuracy": float(true_positives.sum() / matrix.sum()),
              "macro_f1": float(f1.mean()), "confusion_matrix": matrix.tolist(),
              "per_class": {name: {"precision": float(precision[i]), "recall": float(recall[i]),
                                     "f1": float(f1[i]), "support": int(matrix[i].sum())}
                            for i, name in enumerate(classes)}}
    if total_loss is not None:
        result["loss"] = total_loss / matrix.sum().item()
    return result


def fit(root, run_dir, config=None):
    config = config or TrainConfig()
    if config.epochs < 1:
        raise ValueError("At least one epoch is required")
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=False)
    seed_everything(config.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train, val = make_loaders(root, config)
    classes = train.dataset.classes
    if val.dataset.classes != classes:
        raise ValueError("Train/validation class order differs")
    model = GrayGestureCNN(num_classes=len(classes), width=config.width).to(device)
    init_sha = None
    if config.init_features_from:
        source_path = Path(config.init_features_from)
        previous = torch.load(source_path, map_location="cpu", weights_only=True)
        if previous["config"].get("width", 8) != config.width:
            raise ValueError("Pretrained feature width differs")
        features = {name: tensor for name, tensor in previous["state_dict"].items()
                    if name.startswith("features.")}
        missing, unexpected = model.load_state_dict(features, strict=False)
        if unexpected or any(not name.startswith("classifier.") for name in missing):
            raise ValueError("Pretrained feature layers differ")
        init_sha = sha256(source_path)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, config.epochs)
    history, best_key, best_epoch = [], (-1.0, float("-inf")), 0
    started = time.perf_counter()
    manifest_hash = sha256(Path(root) / config.manifest_file)
    for epoch in range(1, config.epochs + 1):
        train_metrics = train_epoch(model, train, optimizer, device)
        val_metrics = evaluate(model, val, device)
        row = {"epoch": epoch, "lr": optimizer.param_groups[0]["lr"],
               "train_loss": train_metrics["loss"], "train_accuracy": train_metrics["accuracy"],
               "val_loss": val_metrics["loss"], "val_accuracy": val_metrics["accuracy"]}
        history.append(row)
        key = (val_metrics["accuracy"], -val_metrics["loss"])
        if key > best_key:
            best_key, best_epoch = key, epoch
            torch.save({"state_dict": model.state_dict(), "config": asdict(config),
                        "classes": list(classes), "epoch": epoch, "manifest_sha256": manifest_hash,
                        "initial_feature_checkpoint_sha256": init_sha},
                       run_dir / "best.pt")
        scheduler.step()
        print(f"epoch {epoch:02d}: train={row['train_accuracy']:.3%}, val={row['val_accuracy']:.3%}, val_loss={row['val_loss']:.4f}", flush=True)
        (run_dir / "history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    checkpoint = torch.load(run_dir / "best.pt", map_location=device, weights_only=True)
    model.load_state_dict(checkpoint["state_dict"])
    summary = {"config": asdict(config), "device": str(device), "torch": str(torch.__version__),
               "cuda": torch.version.cuda, "best_epoch": best_epoch, "seconds": time.perf_counter() - started,
               "manifest_sha256": manifest_hash, "validation": evaluate(model, val, device),
               "initial_feature_checkpoint_sha256": init_sha,
               "complexity": profile_model(model)}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return model, history, summary


def test_checkpoint(root, run_dir):
    run_dir = Path(run_dir)
    checkpoint = torch.load(run_dir / "best.pt", map_location="cpu", weights_only=True)
    manifest_file = checkpoint["config"].get("manifest_file", "manifest.json")
    if checkpoint["manifest_sha256"] != sha256(Path(root) / manifest_file):
        raise ValueError("Dataset manifest changed since training")
    model = GrayGestureCNN(num_classes=len(checkpoint["classes"]),
                           width=checkpoint["config"].get("width", 8))
    model.load_state_dict(checkpoint["state_dict"])
    loader = DataLoader(GestureDataset(root, "test", manifest_file=manifest_file), batch_size=64)
    if tuple(checkpoint["classes"]) != loader.dataset.classes:
        raise ValueError("Test class order differs from checkpoint")
    result = evaluate(model, loader, "cpu")
    result["checkpoint_sha256"] = sha256(run_dir / "best.pt")
    result["scope"] = ("independent AR0135 capture sessions"
                       if "empty" in checkpoint["classes"] else
                       "official synthetic RPS test; not camera/subject generalization")
    (run_dir / "test_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
