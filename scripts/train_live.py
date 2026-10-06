"""Train the four-class AR0135 model after session-disjoint captures exist."""
import argparse
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cnn_tutorial.training import TrainConfig, fit, test_checkpoint

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--data", type=Path, default=root / "data/live_r6")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--run", type=Path,
                        default=root / "artifacts" / ("live-r6-" + datetime.now().strftime("%Y%m%d-%H%M%S")))
    parser.add_argument("--init-features", type=Path, default=root / "artifacts/v0.2-grouped-study/refit/best.pt")
    parser.add_argument("--test", action="store_true", help="Only after model selection is frozen")
    args = parser.parse_args()
    config = TrainConfig(epochs=args.epochs, augment_policy="camera",
                         init_features_from=str(args.init_features) if args.init_features else None)
    fit(args.data, args.run, config)
    if args.test:
        print(test_checkpoint(args.data, args.run))
