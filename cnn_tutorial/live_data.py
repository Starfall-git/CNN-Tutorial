"""Four-class session-held-out dataset from the r5 capture tool."""
import hashlib
import json
from pathlib import Path

from .live_capture import CLASSES


def build_manifest(root: Path, assignments: dict, filename="manifest.json") -> dict:
    root = Path(root)
    if set(assignments) != {"train", "val", "test"}:
        raise ValueError("Explicit train/val/test session lists are required")
    if any(not isinstance(assignments[k], list) or not assignments[k] for k in assignments):
        raise ValueError("Every split needs at least one capture session")
    assigned = {session: split for split, sessions in assignments.items() for session in sessions}
    if len(assigned) != sum(map(len, assignments.values())):
        raise ValueError("A session appears in multiple splits")
    rows, seen = [], {}
    for split, sessions in assignments.items():
        for session in sessions:
            folder = root / "sessions" / session
            if not folder.is_dir():
                raise FileNotFoundError(folder)
            for label, name in enumerate(CLASSES):
                metadata = sorted((folder / name).glob("*.json"))
                if not metadata:
                    raise ValueError(f"{split}/{session} lacks {name}; collect each class in every session")
                for path in metadata:
                    record = json.loads(path.read_text(encoding="utf-8"))
                    if (record["session"], record["label"], record["capture_geometry"]) != (
                        session, name, "r5-center512-nearest8"
                    ):
                        raise ValueError(f"Invalid record: {path}")
                    image = path.parent / record["roi"]
                    digest = hashlib.sha256(image.read_bytes()).hexdigest()
                    if digest != record["roi_sha256"]:
                        raise ValueError(f"ROI image changed after capture: {image}")
                    if digest in seen:
                        raise ValueError(f"Exact duplicate across records: {image}, {seen[digest]}")
                    seen[digest] = image
                    rows.append({"path": image.relative_to(root).as_posix(),
                                 "label": label, "class": name, "split": split,
                                 "sha256": digest, "session": session,
                                 "source": record["source"],
                                 "empty_kind": record.get("empty_kind")})
    manifest = {"classes": list(CLASSES), "image_size": 64,
                "preprocess": "already 64x64 grayscale nearest8 ROI; float32 /255; NCHW",
                "split_policy": "whole user-defined capture sessions; no temporal frame leakage",
                "session_assignments": assignments, "rows": rows}
    target = root / filename
    serialized = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if target.exists() and target.read_text(encoding="utf-8") != serialized:
        raise FileExistsError(f"Refusing to overwrite changed {target}")
    target.write_text(serialized, encoding="utf-8")
    return manifest
