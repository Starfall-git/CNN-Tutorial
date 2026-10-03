"""FP32 desktop inference for a pre-cropped square ROI (not detection)."""
from pathlib import Path

from PIL import Image
import torch

from .data import CLASSES, preprocess
from .model import GrayGestureCNN


def predict_roi(checkpoint_path, image_path):
    checkpoint = torch.load(Path(checkpoint_path), map_location="cpu", weights_only=True)
    if checkpoint["classes"] != list(CLASSES):
        raise ValueError("Checkpoint class order differs from the input/output contract")
    model = GrayGestureCNN()
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    with Image.open(image_path) as image:
        if image.width != image.height:
            raise ValueError("Crop a square hand ROI first; the classifier does not locate hands")
        tensor = torch.from_numpy(preprocess(image))[None]
    with torch.inference_mode():
        probabilities = model(tensor).softmax(1)[0]
    return {"predicted_class": CLASSES[int(probabilities.argmax())],
            "probabilities": {name: float(probabilities[i]) for i, name in enumerate(CLASSES)},
            "scope": "Closed-set RPS only; no background or unknown-gesture rejection"}
