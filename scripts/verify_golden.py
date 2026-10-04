"""Replay saved signed-byte fixtures in the isolated TensorFlow environment."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import tensorflow as tf


def verify(model_dir):
    model_dir = Path(model_dir)
    golden_dir = model_dir / "golden"
    manifest = json.loads((golden_dir / "manifest.json").read_text(encoding="utf-8"))
    blob = (model_dir / "gesture_int8.tflite").read_bytes()
    if hashlib.sha256(blob).hexdigest() != manifest["model_sha256"]:
        raise ValueError("Golden fixtures belong to a different model")
    interpreter = tf.lite.Interpreter(model_content=blob, num_threads=1)
    interpreter.allocate_tensors()
    inp, out = interpreter.get_input_details()[0], interpreter.get_output_details()[0]
    results = []
    for vector in manifest["vectors"]:
        for side in ("input", "output"):
            path = golden_dir / vector[f"{side}_file"]
            if hashlib.sha256(path.read_bytes()).hexdigest() != vector[f"{side}_sha256"]:
                raise ValueError(f"Corrupted fixture: {path.name}")
        x = np.fromfile(golden_dir / vector["input_file"], dtype=np.int8).reshape(manifest["input_shape"])
        expected = np.fromfile(golden_dir / vector["output_file"], dtype=np.int8)
        interpreter.set_tensor(inp["index"], x)
        interpreter.invoke()
        actual = interpreter.get_tensor(out["index"])[0]
        np.testing.assert_array_equal(actual, expected)
        results.append({"class": vector["true_class"], "exact_bytes_match": True, "output": actual.tolist()})
    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_dir", type=Path, nargs="?", default=Path(__file__).resolve().parents[1] / "artifacts/v0.3-int8")
    verify(parser.parse_args().model_dir)
