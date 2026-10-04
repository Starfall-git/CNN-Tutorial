"""Export frozen TFLite and signed golden vectors as portable C++11 data.

This contains no FPGA register map, accelerator configuration or guessed arena.
Run after convert_int8.py and verify_golden.py; output directories never overwrite.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil


def sha(data):
    return hashlib.sha256(data).hexdigest()


def array_definition(name, data, signed=False):
    values = [(v if v < 128 else v - 256) if signed else v for v in data]
    rows = [", ".join(str(v) for v in values[i:i + 16]) for i in range(0, len(values), 16)]
    dtype = "int8_t" if signed else "uint8_t"
    return f"alignas(16) const {dtype} {name}[{len(data)}] = {{\n  " + ",\n  ".join(rows) + "\n};\n"


def export_bundle(model_dir, output_dir):
    model_dir, output_dir = Path(model_dir), Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite: {output_dir}")
    report = json.loads((model_dir / "report.json").read_text(encoding="utf-8"))
    manifest = json.loads((model_dir / "golden/manifest.json").read_text(encoding="utf-8"))
    model = (model_dir / "gesture_int8.tflite").read_bytes()
    if sha(model) != manifest["model_sha256"] or sha(model) != report["tflite_sha256"]:
        raise ValueError("Model identity does not match report/golden fixtures")
    if manifest["input_shape"] != [1, 64, 64, 1] or manifest["classes"] != ["paper", "rock", "scissors"]:
        raise ValueError("Unexpected model contract")
    if not report["acceptance_drop_at_most_2pp"] or report["float_tensor_count"] != 0:
        raise ValueError("Model did not pass desktop quantization acceptance")
    for side in ("input", "output"):
        if report[f"{side}_quantization"] != manifest[f"{side}_quantization"]:
            raise ValueError("Report/golden quantization contract mismatch")
    buffers = []
    for i, vector in enumerate(manifest["vectors"]):
        for side, size in (("input", 4096), ("output", 3)):
            # Reject directory traversal in a modified manifest.
            name = vector[f"{side}_file"]
            if Path(name).name != name:
                raise ValueError("Fixture file must be a plain filename")
            data = (model_dir / "golden" / name).read_bytes()
            if len(data) != size or sha(data) != vector[f"{side}_sha256"]:
                raise ValueError(f"Invalid fixture: {name}")
            buffers.append((f"cnn_golden_{i}_{side}", data))
    if len(buffers) != 6:
        raise ValueError("Expected three complete golden vector pairs")
    # Validate everything before creating the output directory.
    output_dir.mkdir(parents=True)
    shutil.copy2(model_dir / "gesture_int8.tflite", output_dir)
    shutil.copytree(model_dir / "golden", output_dir / "golden")
    for filename in ("report.json", "graph_audit.json"):
        shutil.copy2(model_dir / filename, output_dir)
    header = """// Generated model contract. C-compatible declarations; compile .cc as C++11.
#ifndef CNN_GESTURE_DATA_H
#define CNN_GESTURE_DATA_H
#include <stdint.h>
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
#define CNN_INPUT_BYTES 4096
#define CNN_OUTPUT_CLASSES 3
#define CNN_GOLDEN_COUNT 3
extern const uint8_t cnn_model_data[];
extern const size_t cnn_model_data_len;
extern const char* const cnn_class_names[CNN_OUTPUT_CLASSES];
extern const float cnn_input_scale, cnn_output_scale;
extern const int32_t cnn_input_zero_point, cnn_output_zero_point;
"""
    definitions = '#include "cnn_gesture_data.h"\n' + array_definition("cnn_model_data", model)
    definitions += f"const size_t cnn_model_data_len = {len(model)};\n"
    definitions += 'const char* const cnn_class_names[3] = {"paper", "rock", "scissors"};\n'
    for side in ("input", "output"):
        q = report[f"{side}_quantization"]
        definitions += f"const float cnn_{side}_scale = {q['scale']:.17e}f;\n"
        definitions += f"const int32_t cnn_{side}_zero_point = {q['zero_point']};\n"
    for name, data in buffers:
        header += f"extern const int8_t {name}[{len(data)}];\n"
        definitions += array_definition(name, data, signed=True)
    header += '#ifdef __cplusplus\n}\n#endif\n#endif\n'
    (output_dir / "cnn_gesture_data.h").write_text(header, encoding="ascii")
    (output_dir / "cnn_gesture_data.cc").write_text(definitions, encoding="ascii")
    (output_dir / "README.md").write_text("""# Stage 5 static inference input package

Compile cnn_gesture_data.cc once as C++11 or newer; include its header in firmware.
Model bytes are aligned to 16 bytes. Do not link a second copy from TinyML Generator.
Inputs and expected outputs are signed int8. NHWC input: [1,64,64,1].
Class order: paper, rock, scissors. Output contains logits, not probabilities.

1. Check model schema and register the operators listed in graph_audit.json.
2. Allocate the arena using the actual target runtime; no arena size is guessed here.
3. Assert input/output shapes, dtypes and scale/zero point against the constants.
4. Copy each cnn_golden_N_input to the interpreter input and invoke once.
5. Log every output byte, max absolute byte difference, argmax and measured latency.
6. First compare software kernels, then accelerator kernels; record rounding differences.

Desktop golden replay has passed. Target compilation, execution and performance
have NOT been verified. These files do not configure clocks, DDR, AXI or pinout.
This is a closed-set three-class classifier; a no-hand input can still yield a class.
""", encoding="utf-8")
    package = {"model_sha256": sha(model), "target_verified": False,
               "files": {p.relative_to(output_dir).as_posix(): sha(p.read_bytes())
                         for p in sorted(output_dir.rglob("*")) if p.is_file()}}
    (output_dir / "bundle_manifest.json").write_text(json.dumps(package, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output_dir), "files": len(package["files"]), "model_sha256": sha(model)}, indent=2))
    return package


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=root / "artifacts/v0.3-int8")
    parser.add_argument("--output-dir", type=Path, default=root / "artifacts/v0.3-board-bundle")
    args = parser.parse_args()
    export_bundle(args.model_dir, args.output_dir)
