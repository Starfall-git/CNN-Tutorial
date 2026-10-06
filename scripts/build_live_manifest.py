"""Make session-disjoint four-class manifest after real captures exist."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cnn_tutorial.live_data import build_manifest

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1] / "data/live_r6")
    parser.add_argument("--assignments", type=Path, required=True,
                        help='JSON: {"train":[sessions],"val":[sessions],"test":[sessions]}')
    args = parser.parse_args()
    manifest = build_manifest(args.root, json.loads(args.assignments.read_text(encoding="utf-8")))
    print({split: sum(r["split"] == split for r in manifest["rows"]) for split in ("train", "val", "test")})
