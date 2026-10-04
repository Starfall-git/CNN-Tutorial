"""Export frozen PyTorch weights and separate calibration/evaluation tensors.

Run in CNN-Tutorial; the TensorFlow environment only needs NumPy NPZ files.
No pickle is required to load these exchange files.
"""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import torch
from torch.utils.data import DataLoader
from cnn_tutorial.data import CLASSES, GestureDataset, sha256
from cnn_tutorial.model import GrayGestureCNN


def prepare_conversion(checkpoint_path, data_root, output_dir):
    checkpoint_path, data_root, output_dir = map(Path, (checkpoint_path, data_root, output_dir))
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    config = checkpoint["config"]
    manifest_path = data_root / config["manifest_file"]
    if sha256(manifest_path) != checkpoint["manifest_sha256"]:
        raise ValueError("Training manifest has changed")
    if checkpoint["classes"] != list(CLASSES):
        raise ValueError("Class order mismatch")
    model = GrayGestureCNN(width=config["width"])
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    output_dir.mkdir(parents=True, exist_ok=False)
    weights = {name: value.cpu().numpy() for name, value in model.state_dict().items()}
    np.savez(output_dir / "weights.npz", **weights)
    # Calibration is sampled only from the model's training pool.
    train = GestureDataset(data_root, "train", manifest_file=config["manifest_file"])
    rng = np.random.default_rng(42)
    indices = []
    for label in range(len(CLASSES)):
        pool = [i for i, row in enumerate(train.rows) if row["label"] == label]
        indices.extend(rng.choice(pool, size=min(100, len(pool)), replace=False).tolist())
    calibration = torch.stack([train[i][0] for i in indices]).numpy().transpose(0, 2, 3, 1)
    np.savez(output_dir / "calibration.npz", images=calibration)
    test = GestureDataset(data_root, "test", manifest_file=config["manifest_file"])
    calibration_hashes = {train.rows[i]["sha256"] for i in indices}
    if calibration_hashes & {row["sha256"] for row in test.rows}:
        raise ValueError("Calibration/test content overlap")
    images, labels, logits = [], [], []
    with torch.inference_mode():
        for x, y in DataLoader(test, batch_size=64):
            images.append(x.numpy().transpose(0, 2, 3, 1))
            labels.append(y.numpy())
            logits.append(model(x).numpy())
    np.savez(output_dir / "evaluation.npz", images=np.concatenate(images),
             labels=np.concatenate(labels), torch_logits=np.concatenate(logits))
    manifest = {"checkpoint_sha256": sha256(checkpoint_path), "data_manifest_sha256": sha256(manifest_path),
                "width": config["width"], "classes": list(CLASSES), "shape": [1, 64, 64, 1],
                "input_contract": "PIL grayscale L, bilinear resize 64x64, float32 /255; NHWC exchange",
                "calibration_samples": len(indices), "calibration_source": "training split only",
                "calibration_paths": [train.rows[i]["path"] for i in indices],
                "evaluation_samples": len(test), "evaluation_source": "official test; never calibration",
                "files": {name: sha256(output_dir / name) for name in ("weights.npz", "calibration.npz", "evaluation.npz")}}
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ("width", "calibration_samples", "evaluation_samples", "files")}, indent=2))
    return manifest


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    prepare_conversion(root / "artifacts/v0.2-grouped-study/refit/best.pt", root / "data/rps", root / "artifacts/v0.3-conversion-input")
