"""An intentionally small CNN with a straightforward TFLite equivalent."""
import torch
from torch import nn


class GrayGestureCNN(nn.Module):
    """Input NCHW float32 in [0, 1], output three unnormalized class scores.

    Fixed 64x64 input. Explicit padding avoids PyTorch/TF SAME ambiguity.
    A 4x4 pooled grid retains finger location at a small parameter cost.
    """

    def __init__(self, num_classes=3):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 8, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(8, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.AvgPool2d(2),
        )
        self.classifier = nn.Linear(32 * 4 * 4, num_classes)

    def forward(self, x):
        return self.classifier(torch.flatten(self.features(x), 1))


def profile_model(model):
    """Count learned parameters and conv/linear multiply-accumulates only.

    Excludes pooling, activation, memory traffic and software overhead.
    This is a complexity count, never an FPGA timing prediction.
    """
    rows, handles = [], []

    def hook(name):
        def record(layer, inputs, output):
            macs = 0
            if isinstance(layer, nn.Conv2d):
                macs = output.numel() * (layer.in_channels // layer.groups) * layer.kernel_size[0] * layer.kernel_size[1]
            elif isinstance(layer, nn.Linear):
                macs = output.numel() * layer.in_features
            rows.append({"layer": name, "type": type(layer).__name__,
                         "output": list(output.shape), "macs": macs})
        return record

    for name, layer in model.named_modules():
        if name and not list(layer.children()):
            handles.append(layer.register_forward_hook(hook(name)))
    try:
        with torch.no_grad():
            model(torch.zeros(1, 1, 64, 64, device=next(model.parameters()).device))
    finally:
        for handle in handles:
            handle.remove()
    return {"parameters": sum(p.numel() for p in model.parameters()),
            "macs": sum(row["macs"] for row in rows), "layers": rows}
