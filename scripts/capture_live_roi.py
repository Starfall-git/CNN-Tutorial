"""Collect labeled r5 ROI frames through the existing USB HDMI capture card.

Close the GUI preview first so this process can open the card and COM port.
The script verifies 100%/no-crop geometry and turns inference/overlay off.
"""
import argparse
from dataclasses import asdict
from pathlib import Path
import sys
import time

import cv2
from cv2_enumerate_cameras import enumerate_cameras
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cnn_tutorial.live_capture import CLASSES, save_sample  # noqa: E402


def run(args):
    fpga = ROOT.parent / "CNN-Tutorial-FPGA"
    if not (fpga / "host/client.py").exists():
        raise FileNotFoundError("CNN-Tutorial-FPGA clone is needed for UART control")
    sys.path.insert(0, str(fpga))
    from host.client import SerialClient

    client = SerialClient(args.port)
    capture = None
    old = None
    try:
        status = client.get_status()
        if status.isp_flags != 0:
            raise RuntimeError("Disable Sobel/other ISP effects before capturing raw training frames")
        geometry = client.get_geometry()
        expected = dict(vertical=False, horizontal=False, x=0, y=0,
                        width=1280, height=720, numerator=1, denominator=1, faults=0)
        if any(getattr(geometry, key) != value for key, value in expected.items()):
            raise RuntimeError(f"Restore unflipped 100% full-frame view first: {asdict(geometry)}")
        old = client.get_cnn()
        client.set_cnn(False, False)
        devices = [(c.index, c.name) for c in enumerate_cameras(cv2.CAP_DSHOW)]
        index = args.device
        if index is None:
            matches = [i for i, name in devices if "hagibis" in name.lower()]
            if len(matches) != 1:
                raise RuntimeError(f"Choose --device from available capture devices: {devices}")
            index = matches[0]
        capture = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not capture.isOpened():
            raise RuntimeError("USB capture card is busy; close its GUI preview first")
        capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        print(f"Capturing {args.label} in session {args.session}; keep the pose in the center ROI.", flush=True)
        saved, next_at, failures = 0, time.monotonic() + args.delay, 0
        deadline = time.monotonic() + args.timeout
        while saved < args.count and time.monotonic() < deadline:
            ok, bgr = capture.read()
            if not ok:
                failures += 1
                if failures >= 30:
                    raise RuntimeError("No HDMI frames; check the capture card and cable")
                continue
            failures = 0
            if time.monotonic() < next_at:
                continue
            frame = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
            record = save_sample(args.output, args.session, args.label, frame,
                                 "HDMI-UVC-MJPEG; AI overlay disabled", saved,
                                 args.empty_kind)
            saved += 1
            print(f"{saved}/{args.count}: {record['roi']}", flush=True)
            next_at = time.monotonic() + args.interval
        if saved != args.count:
            raise TimeoutError(f"Captured only {saved}/{args.count} before timeout")
    finally:
        if capture is not None:
            capture.release()
        try:
            if old is not None:
                client.set_cnn(bool(old.requested & 1), bool(old.requested & 2))
        finally:
            client.transport.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, help="One person/background/lighting session ID")
    parser.add_argument("--label", choices=CLASSES, required=True)
    parser.add_argument("--empty-kind", choices=("background", "other_hand"))
    parser.add_argument("--count", type=int, default=40)
    parser.add_argument("--interval", type=float, default=0.8)
    parser.add_argument("--delay", type=float, default=3.0)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--device", type=int)
    parser.add_argument("--port", default="COM8")
    parser.add_argument("--output", type=Path, default=ROOT / "data/live_r6")
    args = parser.parse_args()
    if args.count < 1 or args.interval < 0.3 or args.delay < 0 or args.timeout <= 0:
        parser.error("Use count>=1, interval>=0.3s, delay>=0, timeout>0")
    if args.label == "empty" and not args.empty_kind:
        parser.error("--label empty requires --empty-kind background or other_hand")
    run(args)
