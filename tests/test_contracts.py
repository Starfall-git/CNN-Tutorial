import tempfile
from pathlib import Path
import json
import unittest

import numpy as np
from PIL import Image
import torch

from cnn_tutorial.data import CLASSES, GestureDataset, preprocess, create_grouped_manifest, assert_group_separation
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

    def test_group_split_keeps_test_and_sequences_intact(self):
        rows = []
        for label, name in enumerate(CLASSES):
            for sequence in range(7):
                for frame in range(3):
                    rows.append({"class": name, "label": label, "path": f"raw/{name}/{name}{sequence:02d}-{frame:03d}.png",
                                 "split": "train", "sha256": f"fixture-{label}-{sequence}-{frame}"})
            rows.append({"class": name, "label": label, "path": f"test/{name}.png", "split": "test", "sha256": f"test-{label}"})
        source = {"rows": rows, "classes": list(CLASSES)}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = json.dumps(source)
            (root / "manifest.json").write_text(original, encoding="utf-8")
            grouped = create_grouped_manifest(root)
            self.assertEqual(original, (root / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual([r for r in rows if r["split"] == "test"],
                             [r for r in grouped["rows"] if r["split"] == "test"])
            self.assertEqual(grouped, create_grouped_manifest(root))
            self.assertEqual(sum(r["split"] == "val" for r in grouped["rows"]), 18)
            assert_group_separation(grouped)
            leak = dict(next(r for r in grouped["rows"] if r["split"] == "val"), split="train")
            grouped["rows"].append(leak)
            with self.assertRaisesRegex(ValueError, "leaks"):
                assert_group_separation(grouped)

    def test_wider_model_remains_under_small_parameter_budget(self):
        model = GrayGestureCNN(width=16)
        self.assertEqual(tuple(model(torch.rand(2, 1, 64, 64)).shape), (2, 3))
        self.assertLess(profile_model(model)["parameters"], 30000)


if __name__ == "__main__":
    unittest.main()
