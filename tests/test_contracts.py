import tempfile
from pathlib import Path
import json
import unittest

import numpy as np
from PIL import Image
import torch

from cnn_tutorial.data import CLASSES, GestureDataset, preprocess
from cnn_tutorial.model import GrayGestureCNN, profile_model
from cnn_tutorial.training import metrics_from_confusion


class Contracts(unittest.TestCase):
    def test_preprocessing_range_shape_and_dtype(self):
        for pixel, expected in [(0, 0.0), (255, 1.0)]:
            x = preprocess(Image.new("RGB", (300, 300), (pixel,) * 3))
            self.assertEqual(x.shape, (1, 64, 64))
            self.assertEqual(x.dtype, np.float32)
            np.testing.assert_array_equal(x, expected)

    def test_forward_backward_and_parameter_budget(self):
        torch.manual_seed(42)
        model = GrayGestureCNN()
        logits = model(torch.rand(4, 1, 64, 64))
        self.assertEqual(tuple(logits.shape), (4, 3))
        loss = torch.nn.functional.cross_entropy(logits, torch.tensor([0, 1, 2, 0]))
        loss.backward()
        self.assertTrue(all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters()))
        self.assertLess(profile_model(model)["parameters"], 10000)

    def test_confusion_orientation_and_macro_f1(self):
        metrics = metrics_from_confusion([[2, 1, 0], [0, 2, 0], [1, 0, 3]])
        self.assertAlmostEqual(metrics["accuracy"], 7 / 9)
        self.assertAlmostEqual(metrics["per_class"]["paper"]["recall"], 2 / 3)
        self.assertAlmostEqual(metrics["per_class"]["scissors"]["precision"], 1.0)

    def test_validation_cannot_be_augmented(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.json").write_text(json.dumps({"classes": list(CLASSES),
                "rows": [{"split": "val", "path": "unused.png", "label": 0}]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "only on the training"):
                GestureDataset(root, "val", augment=True)


if __name__ == "__main__":
    unittest.main()
