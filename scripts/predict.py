import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cnn_tutorial.inference import predict_roi

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classify a square grayscale/RGB hand ROI")
    parser.add_argument("checkpoint")
    parser.add_argument("image")
    args = parser.parse_args()
    print(json.dumps(predict_roi(args.checkpoint, args.image), indent=2))
