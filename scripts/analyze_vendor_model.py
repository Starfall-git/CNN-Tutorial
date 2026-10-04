"""Run the locally supplied Efinix analyzer without choosing FPGA settings."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def analyze(executable, model_dir):
    executable, model_dir = Path(executable).resolve(), Path(model_dir).resolve()
    model = model_dir / "gesture_int8.tflite"
    # 1/1 is a static-analysis probe, not a recommended hardware parallelism.
    result = subprocess.run([str(executable), str(model), "1", "1"], capture_output=True,
                            text=True, errors="replace", timeout=60, check=False)
    (model_dir / "vendor_analyzer.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    report = {"analyzer_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "model_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
              "probe_input_parallelism": 1, "probe_output_parallelism": 1,
              "return_code": result.returncode,
              "settings_generated": False, "hardware_verified": False}
    (model_dir / "vendor_analysis.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    result.check_returncode()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analyzer", type=Path, default=root / "refs/TinyML/tools/tinyml_generator/bin/tflite.exe")
    parser.add_argument("--model-dir", type=Path, default=root / "artifacts/v0.3-int8")
    args = parser.parse_args()
    analyze(args.analyzer, args.model_dir)
