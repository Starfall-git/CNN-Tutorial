"""Exact r5 camera ROI geometry and a conservative USB-HDMI surrogate."""
from pathlib import Path
import hashlib
import json
import os
import re
import uuid

import numpy as np
from PIL import Image

CLASSES = ("paper", "rock", "scissors", "empty")
WIDTH, HEIGHT = 1280, 720
ROI_X, ROI_Y, ROI_SIZE, STRIDE = 384, 104, 512, 8


def sample_board_roi(frame: Image.Image) -> Image.Image:
    """Select the same 4096 source coordinates as cnn_gray_snapshot.v.

    The USB capture card can add HDMI/MJPEG errors; this is not a bit-exact
    replacement for a raw APB snapshot, although its sample positions match.
    """
    if frame.size != (WIDTH, HEIGHT):
        raise ValueError(f"Expected uncropped {WIDTH}x{HEIGHT}, received {frame.size}")
    gray = np.asarray(frame.convert("L"), dtype=np.uint8)
    xs = ROI_X + 4 + STRIDE * np.arange(64)
    ys = ROI_Y + 4 + STRIDE * np.arange(64)
    return Image.fromarray(gray[np.ix_(ys, xs)].copy(), mode="L")


def save_sample(root: Path, session: str, label: str, frame: Image.Image,
                source: str, sequence: int, empty_kind: str | None = None) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,64}", session):
        raise ValueError("Session must be 3-64 letters, digits, _ or -")
    if label not in CLASSES:
        raise ValueError(f"Label must be one of {CLASSES}")
    if label == "empty" and empty_kind not in ("background", "other_hand"):
        raise ValueError("Empty samples need background or other_hand subtype")
    if label != "empty" and empty_kind is not None:
        raise ValueError("Empty subtype applies only to empty class")
    roi = sample_board_roi(frame)
    folder = Path(root) / "sessions" / session / label
    folder.mkdir(parents=True, exist_ok=True)
    stem = f"{sequence:06d}-{uuid.uuid4().hex[:8]}"
    full, small = folder / f"{stem}-frame.png", folder / f"{stem}-roi.png"
    if full.exists() or small.exists():
        raise FileExistsError(stem)
    temp_full, temp_small = folder / f"{stem}-frame.tmp", folder / f"{stem}-roi.tmp"
    frame.convert("RGB").save(temp_full, format="PNG")
    roi.save(temp_small, format="PNG")
    os.replace(temp_full, full)
    os.replace(temp_small, small)
    record = {"session": session, "label": label, "source": source,
              "empty_kind": empty_kind,
              "frame": full.name, "roi": small.name,
              "frame_sha256": hashlib.sha256(full.read_bytes()).hexdigest(),
              "roi_sha256": hashlib.sha256(small.read_bytes()).hexdigest(),
              "capture_geometry": "r5-center512-nearest8", "overlay_off_required": True}
    meta = folder / f"{stem}.json"
    meta.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record
