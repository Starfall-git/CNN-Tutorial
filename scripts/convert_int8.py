"""CPU TensorFlow conversion; run only in CNN-Tutorial-Quant.

Fails before claiming success if FP32 equivalence or integer graph audit fails.
The desktop interpreter does not prove FPGA TFLite Micro compatibility.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
import numpy as np
import tensorflow as tf
from cnn_tutorial.quantization import dense_chw_to_hwc, quantize_int8
from tflite_audit import audit_flatbuffer


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def convert(input_dir, output_dir):
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(f"Use a new output directory: {output_dir}")
    manifest = json.loads((input_dir / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["files"].items():
        if digest(input_dir / name) != expected:
            raise ValueError(f"Input checksum mismatch: {name}")
    weights = np.load(input_dir / "weights.npz", allow_pickle=False)
    calibration = np.load(input_dir / "calibration.npz", allow_pickle=False)["images"]
    evaluation = np.load(input_dir / "evaluation.npz", allow_pickle=False)
    width = manifest["width"]
    inputs = tf.keras.Input(batch_shape=(1, 64, 64, 1), name="gray_roi")
    x = inputs
    conv_layers = []
    for i, channels in zip((0, 3, 6), (width, width * 2, width * 4)):
        layer = tf.keras.layers.Conv2D(channels, 3, padding="same", activation="relu", name=f"conv_{i}")
        x = layer(x)
        conv_layers.append((i, layer))
        x = tf.keras.layers.MaxPool2D(2)(x)
    x = tf.keras.layers.AveragePooling2D(2)(x)
    x = tf.keras.layers.Flatten()(x)
    dense = tf.keras.layers.Dense(3, name="logits")
    model = tf.keras.Model(inputs, dense(x))
    for i, layer in conv_layers:
        layer.set_weights([weights[f"features.{i}.weight"].transpose(2, 3, 1, 0), weights[f"features.{i}.bias"]])
    # Reorder the flattened feature dimension CHW -> HWC, then transpose IO.
    dense_weights = dense_chw_to_hwc(weights["classifier.weight"], width * 4, 4, 4)
    dense.set_weights([dense_weights, weights["classifier.bias"]])
    keras_logits = np.concatenate([model(x[None], training=False).numpy() for x in evaluation["images"]])
    float_error = float(np.max(np.abs(keras_logits - evaluation["torch_logits"])))
    np.testing.assert_allclose(keras_logits, evaluation["torch_logits"], rtol=1e-4, atol=1e-4)
    if not np.array_equal(keras_logits.argmax(1), evaluation["torch_logits"].argmax(1)):
        raise ValueError("PyTorch/Keras predicted classes differ")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = lambda: ([sample[None]] for sample in calibration)
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    converter.inference_input_type = tf.int8
    converter.inference_output_type = tf.int8
    blob = converter.convert()
    audit = audit_flatbuffer(blob)
    interpreter = tf.lite.Interpreter(model_content=blob, num_threads=1)
    interpreter.allocate_tensors()
    input_detail, output_detail = interpreter.get_input_details()[0], interpreter.get_output_details()[0]
    if input_detail["dtype"] != np.int8 or output_detail["dtype"] != np.int8:
        raise ValueError("Model I/O is not INT8")
    tensors = interpreter.get_tensor_details()
    floats = [d["name"] for d in tensors if np.issubdtype(d["dtype"], np.floating)]
    if floats:
        raise ValueError(f"Unexpected float tensors: {floats}")
    scale, zero = input_detail["quantization"]
    out_scale, out_zero = output_detail["quantization"]
    if scale <= 0 or out_scale <= 0:
        raise ValueError("Invalid quantization scales")
    predictions = []
    integer_logits = []
    raw_outputs = []
    for sample in evaluation["images"]:
        quantized = quantize_int8(sample, scale, zero)
        interpreter.set_tensor(input_detail["index"], quantized[None])
        interpreter.invoke()
        raw = interpreter.get_tensor(output_detail["index"])[0]
        raw_outputs.append(raw.copy())
        logits = (raw.astype(np.float32) - out_zero) * out_scale
        predictions.append(int(logits.argmax()))
        integer_logits.append(logits)
    labels = evaluation["labels"]
    float_accuracy = float(np.mean(keras_logits.argmax(1) == labels))
    int8_accuracy = float(np.mean(np.asarray(predictions) == labels))
    confusion = np.bincount(labels * 3 + np.asarray(predictions), minlength=9).reshape(3, 3)
    operations = [op["name"] for op in audit["operations"]]
    recall = np.diag(confusion) / confusion.sum(1)
    precision = np.divide(np.diag(confusion), confusion.sum(0), out=np.zeros(3), where=confusion.sum(0) != 0)
    f1 = np.divide(2 * precision * recall, precision + recall, out=np.zeros(3), where=precision + recall != 0)
    report = {"tensorflow": tf.__version__, "checkpoint_sha256": manifest["checkpoint_sha256"],
              "conversion_input_manifest_sha256": digest(input_dir / "manifest.json"),
              "float_max_absolute_error": float_error, "float_class_agreement": 1.0,
              "fp32_accuracy": float_accuracy, "int8_accuracy": int8_accuracy,
              "accuracy_drop_percentage_points": 100 * (float_accuracy - int8_accuracy),
              "int8_confusion_matrix": confusion.tolist(), "bytes": len(blob), "operations": operations,
              "classes": manifest["classes"], "int8_macro_f1": float(f1.mean()),
              "int8_per_class_recall": recall.tolist(), "evaluation_samples": len(labels),
              "operator_codes": audit["operator_codes"], "tensor_type_counts": audit["tensor_type_counts"],
              "input_quantization": {"scale": scale, "zero_point": zero, "dtype": "int8"},
              "output_quantization": {"scale": out_scale, "zero_point": out_zero, "dtype": "int8"},
              "float_tensor_count": 0, "calibration_samples": len(calibration),
              "board_compatibility_verified": False,
              "acceptance_drop_at_most_2pp": (float_accuracy - int8_accuracy) <= 0.02}
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "gesture_int8.tflite").write_bytes(blob)
    report["tflite_sha256"] = digest(output_dir / "gesture_int8.tflite")
    (output_dir / "graph_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    # Deterministic alignment vectors: first official example of each class.
    # These are evaluation fixtures; they are never fed to the calibrator.
    golden_dir = output_dir / "golden"
    golden_dir.mkdir()
    vectors = []
    for label, name in enumerate(manifest["classes"]):
        index = int(np.flatnonzero(labels == label)[0])
        image = quantize_int8(evaluation["images"][index], scale, zero)
        raw = raw_outputs[index]
        input_name, output_name = f"{name}_input.bin", f"{name}_output.bin"
        image.tofile(golden_dir / input_name)
        raw.tofile(golden_dir / output_name)
        vectors.append({"evaluation_index": index, "true_class": name,
                        "predicted_class": manifest["classes"][predictions[index]],
                        "input_file": input_name, "output_file": output_name,
                        "input_sha256": digest(golden_dir / input_name),
                        "output_sha256": digest(golden_dir / output_name),
                        "output_int8": raw.tolist()})
    golden = {"model_sha256": report["tflite_sha256"], "classes": manifest["classes"],
              "input_shape": [1, 64, 64, 1], "layout": "NHWC", "dtype": "signed int8",
              "input_quantization": report["input_quantization"],
              "output_quantization": report["output_quantization"], "vectors": vectors,
              "comparison": "Exact bytes for desktop replay; record target byte errors and argmax separately"}
    (golden_dir / "manifest.json").write_text(json.dumps(golden, indent=2), encoding="utf-8")
    (output_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    np.savez(output_dir / "comparison.npz", keras_logits=keras_logits, int8_logits=np.asarray(integer_logits),
             output_int8=np.asarray(raw_outputs), labels=labels)
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    import argparse
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=root / "artifacts/v0.3-conversion-input")
    parser.add_argument("--output-dir", type=Path, default=root / "artifacts/v0.3-int8")
    args = parser.parse_args()
    convert(args.input_dir, args.output_dir)
