import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image
import torch

from cnn_tutorial.data import GestureDataset
from cnn_tutorial.live_capture import CLASSES, sample_board_roi, save_sample
from cnn_tutorial.live_data import build_manifest
from cnn_tutorial.model import GrayGestureCNN
from cnn_tutorial.training import evaluate
from torch.utils.data import DataLoader


class LiveCaptureContracts(unittest.TestCase):
    def test_sample_coordinates_match_r5_rtl(self):
        yy, xx = np.indices((720, 1280))
        gray = ((xx * 3 + yy * 5) & 255).astype(np.uint8)
        result = np.asarray(sample_board_roi(Image.fromarray(gray)))
        self.assertEqual(result.shape, (64, 64))
        np.testing.assert_array_equal(result,
                                      gray[np.ix_(108 + 8 * np.arange(64),
                                                  388 + 8 * np.arange(64))])

    def test_session_isolation_and_four_class_loader(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sessions = ["room_a", "room_b", "room_c"]
            for si, session in enumerate(sessions):
                for ci, label in enumerate(CLASSES):
                    image = Image.new("RGB", (1280, 720), (17 + si * 50 + ci * 10,) * 3)
                    save_sample(root, session, label, image, "test", si * 4 + ci,
                                "background" if label == "empty" else None)
            assignments = {"train": [sessions[0]], "val": [sessions[1]], "test": [sessions[2]]}
            manifest = build_manifest(root, assignments)
            self.assertEqual(len(manifest["rows"]), 12)
            self.assertEqual(tuple(manifest["classes"]), CLASSES)
            with self.assertRaises(ValueError):
                build_manifest(root, {"train": ["room_a"], "val": ["room_a"], "test": ["room_c"]})
            val = GestureDataset(root, "val")
            self.assertEqual(val.classes, CLASSES)
            model = GrayGestureCNN(num_classes=4)
            result = evaluate(model, DataLoader(val, batch_size=4), "cpu")
            self.assertEqual(len(result["confusion_matrix"]), 4)
            self.assertIn("empty", result["per_class"])


if __name__ == "__main__":
    unittest.main()
