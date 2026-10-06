"""Download provenance, deterministic splits and one preprocessing contract."""
import hashlib
import json
import math
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
    def __init__(self, root, split, augment=False, manifest_file="manifest.json", augment_policy="basic"):
        self.root = Path(root)
        manifest = json.loads((self.root / manifest_file).read_text(encoding="utf-8"))
        allowed = (list(CLASSES), list(CLASSES) + ["empty"])
        if manifest["classes"] not in allowed:
            raise ValueError("Manifest class order mismatch")
        self.classes = tuple(manifest["classes"])
        self.rows = [row for row in manifest["rows"] if row["split"] == split]
        if not self.rows:
            raise ValueError(f"Empty split: {split}")
        if augment and split != "train":
            raise ValueError("Augmentation is allowed only on the training split")
        self.augment = augment
        if augment_policy not in ("basic", "affine", "camera"):
            raise ValueError("Unknown augmentation policy")
        self.augment_policy = augment_policy
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
            if self.augment_policy == "affine":
                image = affine_augment(image)
                image = ImageEnhance.Contrast(image).enhance(random.uniform(0.7, 1.3))
                image = ImageEnhance.Brightness(image).enhance(random.uniform(0.7, 1.3))
            elif self.augment_policy == "camera":
                # Preserve a realistic border color for dark AR0135 scenes.
                fill = int(np.median(np.asarray(image)))
                image = image.rotate(random.uniform(-10, 10),
                                     resample=Image.Resampling.BILINEAR, fillcolor=fill)
                image = ImageEnhance.Contrast(image).enhance(random.uniform(0.75, 1.3))
                image = ImageEnhance.Brightness(image).enhance(random.uniform(0.7, 1.3))
            else:
                image = image.rotate(random.uniform(-12, 12), resample=Image.Resampling.BILINEAR, fillcolor=255)
                image = ImageEnhance.Brightness(image).enhance(random.uniform(0.85, 1.15))
        return torch.from_numpy(preprocess(image)), self.rows[index]["label"]


def affine_augment(image):
    """Inverse affine mapping: rotation +/-25deg, scale .8-1.15, shift +/-10%."""
    angle = math.radians(random.uniform(-25, 25))
    scale = random.uniform(0.8, 1.15)
    shift_x, shift_y = random.uniform(-6.4, 6.4), random.uniform(-6.4, 6.4)
    a, b = math.cos(angle) / scale, math.sin(angle) / scale
    center_x, center_y = image.width / 2, image.height / 2
    coefficients = (a, b, center_x - a * (center_x + shift_x) - b * (center_y + shift_y),
                    -b, a, center_y + b * (center_x + shift_x) - a * (center_y + shift_y))
    return image.transform(image.size, Image.Transform.AFFINE, coefficients,
                           resample=Image.Resampling.BILINEAR, fillcolor=255)


def create_grouped_manifest(root, seed=42, filename="manifest_grouped.json"):
    """Hold out whole filename sequences; these are NOT verified subject IDs.

    Preserve the original manifest and official test membership. Per class,
    seven known source sequences -> five train / two validation sequences.
    """
    root = Path(root)
    source = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    rows = [dict(row) for row in source["rows"]]
    rng = random.Random(seed)
    held_out = {}
    for name in CLASSES:
        class_rows = [r for r in rows if r["class"] == name and r["split"] != "test"]
        for row in class_rows:
            row["group"] = Path(row["path"]).stem.rsplit("-", 1)[0]
        groups = sorted({r["group"] for r in class_rows})
        if len(groups) != 7:
            raise ValueError(f"Expected seven source sequences for {name}, got {len(groups)}")
        rng.shuffle(groups)
        held_out[name] = sorted(groups[:2])
        for row in class_rows:
            row["split"] = "val" if row["group"] in held_out[name] else "train"
    manifest = {k: v for k, v in source.items() if k != "rows"}
    manifest.update(seed=seed, split_policy="filename sequence holdout; not verified subjects",
                    held_out_groups=held_out, source_manifest_sha256=sha256(root / "manifest.json"), rows=rows)
    assert_group_separation(manifest)
    destination = root / filename
    serialized = json.dumps(manifest, indent=2)
    if destination.exists() and destination.read_text(encoding="utf-8") != serialized:
        raise FileExistsError("A different grouped manifest already exists; choose a new filename")
    destination.write_text(serialized, encoding="utf-8")
    return manifest


def assert_group_separation(manifest):
    assignments = {}
    for row in manifest["rows"]:
        if row["split"] == "test":
            continue
        key = (row["class"], row["group"])
        if key in assignments and assignments[key] != row["split"]:
            raise ValueError(f"Group leaks across splits: {key}")
        assignments[key] = row["split"]
