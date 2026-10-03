import argparse
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cnn_tutorial.training import TrainConfig, fit, test_checkpoint

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=25)
    parser.add_argument("--run", default="rps-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    parser.add_argument("--test", action="store_true", help="Evaluate held-out test after model selection")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    run = root / "artifacts" / args.run
    fit(root / "data" / "rps", run, TrainConfig(epochs=args.epochs))
    if args.test:
        print(test_checkpoint(root / "data" / "rps", run))
