"""Drive the unmodified official TinyML Generator with Efinity's Python.

Equivalent to selecting a model, choosing parameters and pressing Generate.
Qt widgets stay hidden; vendor output is never hand-authored.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def generate(generator, model, output, in_parallel=4, out_parallel=4):
    generator, model, output = (Path(p).resolve() for p in (generator, model, output))
    output.relative_to((ROOT / "artifacts").resolve())
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    # Efinity Windows bundles only qwindows, not the offscreen Qt plugin.
    os.environ["QT_QPA_PLATFORM"] = "windows"
    os.chdir(generator.parent)
    sys.path.insert(0, str(generator.parent))
    spec = importlib.util.spec_from_file_location("official_tinyml_generator", generator)
    vendor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vendor)
    vendor.app = vendor.QApplication([])
    window = vendor.Widget()
    window.current_dir = str(output)
    window.model_file = str(model)
    window.file.setText(str(model))
    # Conservative first candidate; measured timing/resource reports decide later changes.
    for name, value in (("CONV_DEPTHW_STD_IN_PARALLEL", in_parallel),
                        ("CONV_DEPTHW_STD_OUT_PARALLEL", out_parallel)):
        vendor.p2[name]["qval"].setValue(value)
    analyzer = generator.parent / "bin/tflite.exe"
    probe = subprocess.run([str(analyzer), str(model), str(in_parallel), str(out_parallel), "128"],
                           capture_output=True, timeout=120, check=True)
    (output / "analyzer.log").write_bytes(probe.stdout + probe.stderr)
    window.parse_model()
    window.tflite_gen = True
    window.generate()
    generated = Path(window.op_path)
    required = [generated / "tinyml_core0_define.v",
                generated / f"{model.stem}_model_data.cc",
                generated / f"{model.stem}_model_data.h"]
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(path)
    cc = required[1].read_text()
    reconstructed = bytes(int(v, 16) for v in re.findall(r"0x([0-9a-fA-F]{2})", cc))
    if reconstructed != model.read_bytes():
        raise ValueError("Generated model array differs from frozen TFLite")
    report = {"generator": str(generator), "model": str(model),
              "generator_sha256": hashlib.sha256(generator.read_bytes()).hexdigest(),
              "analyzer_sha256": hashlib.sha256(analyzer.read_bytes()).hexdigest(),
              "model_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
              "model_array_byte_exact": True,
              "parameters": {k: v["val"] for k, v in vendor.p2.items()},
              "files": {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in required},
              "hardware_verified": False, "board_verified": False}
    (output / "generator.log").write_text(window.E.toPlainText(), encoding="utf-8")
    (output / "generation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=ROOT / "refs/TinyML/upstream-2026.1/tools/tinyml_generator/tinyml_generator.py")
    parser.add_argument("--model", type=Path, default=ROOT / "artifacts/v0.3-int8/gesture_int8.tflite")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--in-parallel", type=int, choices=range(1,129), default=4)
    parser.add_argument("--out-parallel", type=int, choices=range(1,129), default=4)
    args = parser.parse_args()
    generate(args.generator, args.model, args.output, args.in_parallel, args.out_parallel)
