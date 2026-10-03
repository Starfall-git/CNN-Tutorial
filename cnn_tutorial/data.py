"""Download provenance, deterministic splits and one preprocessing contract."""
import hashlib
import json
from pathlib import Path
import random
import shutil
import urllib.request
import zipfile

import numpy as np
from PIL import Image, ImageEnhance, ImageOps
import torch
from torch.utils.data import Dataset

CLASSES = ("paper", "rock", "scissors")
ARCHIVES = {
    "train": ("https://storage.googleapis.com/download.tensorflow.org/data/rps.zip", "rps", 2520),
    "test": ("https://storage.googleapis.com/download.tensorflow.org/data/rps-test-set.zip", "rps-test-set", 372),
}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_dataset(root):
    """HTTPS only; cache validated ZIPs, reject traversal before extraction."""
    root = Path(root).resolve()
    raw = root / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    provenance = {}
    for split, (url, folder, expected_count) in ARCHIVES.items():
        archive = raw / (folder + ".zip")
        if not archive.exists():
            part = archive.with_suffix(".zip.part")
            print(f"Downloading {url}", flush=True)
            with urllib.request.urlopen(url, timeout=60) as response, part.open("wb") as target:
                shutil.copyfileobj(response, target)
            with zipfile.ZipFile(part) as bundle:
                if bundle.testzip() is not None:
                    raise ValueError("ZIP CRC verification failed")
            part.replace(archive)
        with zipfile.ZipFile(archive) as bundle:
            for entry in bundle.infolist():
                target = (raw / entry.filename).resolve()
                if not target.is_relative_to(raw.resolve()):
                    raise ValueError("Unsafe ZIP member")
            if not (raw / folder).is_dir():
                bundle.extractall(raw)
        count = sum(len(list((raw / folder / name).glob("*.png"))) for name in CLASSES)
        if count != expected_count:
            raise ValueError(f"{folder}: expected {expected_count} PNGs, got {count}")
        provenance[split] = {"url": url, "sha256": sha256(archive), "images": count}
    (root / "downloads.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")
    return provenance


def create_manifest(root, seed=42, val_fraction=0.2):
    """Split the official training pool, preserving the official test pool.

    Random image split is only a teaching baseline: it is NOT a subject/session
    generalization protocol. Manifest and content hashes make it auditable.
    """
    if not 0 < val_fraction < 1:
        raise ValueError("val_fraction must lie between 0 and 1")
    root = Path(root)
    rng = random.Random(seed)
    rows = []
    seen = {}
    for source, (_, folder, _) in ARCHIVES.items():
        for label, name in enumerate(CLASSES):
            paths = sorted((root / "raw" / folder / name).glob("*.png"))
            if not paths:
                raise FileNotFoundError(f"Download dataset first: {folder}/{name}")
            rng.shuffle(paths)
            nval = max(1, round(len(paths) * val_fraction))
            for i, path in enumerate(paths):
                split = "test" if source == "test" else ("val" if i < nval else "train")
                digest = sha256(path)
                if digest in seen:
                    raise ValueError(f"Duplicate content detected: {path} and {seen[digest]}")
                seen[digest] = str(path)
                rows.append({"path": path.relative_to(root).as_posix(), "label": label,
                             "class": name, "split": split, "sha256": digest})
    manifest = {"seed": seed, "classes": list(CLASSES), "image_size": 64,
                "preprocess": "PIL L -> bilinear 64x64 -> float32 /255; NCHW",
                "split_policy": "stratified image split; official test untouched", "rows": rows}
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def preprocess(image):
    image = image.convert("L").resize((64, 64), Image.Resampling.BILINEAR)
    return np.asarray(image, dtype=np.float32)[None, :, :].copy() / 255.0


class GestureDataset(Dataset):
    def __init__(self, root, split, augment=False):
        self.root = Path(root)
        manifest = json.loads((self.root / "manifest.json").read_text(encoding="utf-8"))
        if manifest["classes"] != list(CLASSES):
            raise ValueError("Manifest class order mismatch")
        self.rows = [row for row in manifest["rows"] if row["split"] == split]
        if not self.rows:
            raise ValueError(f"Empty split: {split}")
        if augment and split != "train":
            raise ValueError("Augmentation is allowed only on the training split")
        self.augment = augment
        # Small dataset: cache decoded grayscale images, avoid repeated disk IO.
        self.images = []
        for row in self.rows:
            with Image.open(self.root / row["path"]) as im:
                self.images.append(im.convert("L").resize((64, 64), Image.Resampling.BILINEAR))

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        image = self.images[index]
        if self.augment:
            if random.random() < 0.5:
                image = ImageOps.mirror(image)
            image = image.rotate(random.uniform(-12, 12), resample=Image.Resampling.BILINEAR, fillcolor=255)
            image = ImageEnhance.Brightness(image).enhance(random.uniform(0.85, 1.15))
        return torch.from_numpy(preprocess(image)), self.rows[index]["label"]
