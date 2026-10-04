"""NumPy-only layout and boundary conversion, shared with the INT8 tutorial."""
import numpy as np


def dense_chw_to_hwc(weight, channels, height, width):
    """Preserve a linear function when Flatten changes from CHW to HWC."""
    weight = np.asarray(weight)
    if weight.ndim != 2 or weight.shape[1] != channels * height * width:
        raise ValueError("Dense weight does not match the feature shape")
    return weight.reshape(-1, channels, height, width).transpose(2, 3, 1, 0).reshape(-1, weight.shape[0])


def quantize_int8(values, scale, zero_point):
    """Round to nearest (ties to even), saturate, then cast; never wrap uint8."""
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError("Scale must be finite and positive")
    if not isinstance(zero_point, (int, np.integer)) or not -128 <= zero_point <= 127:
        raise ValueError("INT8 zero point must be an integer in [-128, 127]")
    values = np.asarray(values, dtype=np.float32)
    if not np.all(np.isfinite(values)):
        raise ValueError("Cannot quantize NaN or infinity")
    return np.clip(np.rint(values / scale) + zero_point, -128, 127).astype(np.int8)
