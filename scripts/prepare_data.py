import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cnn_tutorial.data import download_dataset, create_manifest

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1] / "data" / "rps"
    print(download_dataset(root))
    manifest = create_manifest(root)
    print({split: sum(r["split"] == split for r in manifest["rows"]) for split in ("train", "val", "test")})
