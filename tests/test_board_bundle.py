"""Byte-level round trip guards the generated firmware data boundary."""
import contextlib
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
from scripts.export_board_bundle import export_bundle, sha


class BoardBundleContracts(unittest.TestCase):
    def fixture(self, root):
        src = root / "source"
        (src / "golden").mkdir(parents=True)
        blob = bytes(range(256)) * 2
        (src / "gesture_int8.tflite").write_bytes(blob)
        quant = {"scale": 1 / 255, "zero_point": -128, "dtype": "int8"}
        report = {"tflite_sha256": sha(blob), "acceptance_drop_at_most_2pp": True,
                  "float_tensor_count": 0, "input_quantization": quant, "output_quantization": quant}
        manifest = {"model_sha256": sha(blob), "input_shape": [1,64,64,1],
                    "classes": ["paper","rock","scissors"], "input_quantization": quant,
                    "output_quantization": quant, "vectors": []}
        for i in range(3):
            vector = {}
            for side, data in (("input", bytes(range(256)) * 16), ("output", bytes([0,128,255]))):
                name = f"{i}_{side}.bin"
                (src / "golden" / name).write_bytes(data)
                vector.update({f"{side}_file": name, f"{side}_sha256": sha(data)})
            manifest["vectors"].append(vector)
        for name, data in (("report.json", report), ("graph_audit.json", {}), ("golden/manifest.json", manifest)):
            (src / name).write_text(json.dumps(data), encoding="utf-8")
        return src, blob

    def test_c_arrays_preserve_unsigned_model_and_signed_fixtures(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            src, blob = self.fixture(root)
            with contextlib.redirect_stdout(io.StringIO()):
                package = export_bundle(src, root / "bundle")
            text = (root / "bundle/cnn_gesture_data.cc").read_text()
            for name, expected in (("cnn_model_data", blob),
                                   ("cnn_golden_0_input", bytes(range(256))*16),
                                   ("cnn_golden_0_output", bytes([0,128,255]))):
                body = re.search(rf"{name}\[\d+\] = \{{(.*?)\}}", text, re.S).group(1)
                values = [int(v) for v in re.findall(r"-?\d+", body)]
                self.assertEqual(bytes(v & 255 for v in values), expected)
                if name.endswith("output"):
                    self.assertEqual(values, [0,-128,-1])
            for name, digest in package["files"].items():
                self.assertEqual(sha((root / "bundle" / name).read_bytes()), digest)
            with self.assertRaises(FileExistsError):
                export_bundle(src, root / "bundle")

    def test_corrupt_input_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            src, _ = self.fixture(root)
            (src / "golden/0_input.bin").write_bytes(b"corrupt")
            with self.assertRaises(ValueError):
                export_bundle(src, root / "bundle")
            self.assertFalse((root / "bundle").exists())
