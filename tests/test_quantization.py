import unittest
import numpy as np
from cnn_tutorial.quantization import dense_chw_to_hwc, quantize_int8


class QuantizationContracts(unittest.TestCase):
    def test_dense_layout_preserves_function_on_non_square_features(self):
        rng = np.random.default_rng(19)
        features = rng.normal(size=(4, 2, 3, 5))
        weight = rng.normal(size=(7, 30))
        expected = features.reshape(4, -1) @ weight.T
        actual = features.transpose(0, 2, 3, 1).reshape(4, -1) @ dense_chw_to_hwc(weight, 2, 3, 5)
        np.testing.assert_allclose(actual, expected, atol=1e-12)
        with self.assertRaises(ValueError):
            dense_chw_to_hwc(weight, 3, 3, 5)

    def test_round_saturate_and_reject_invalid_inputs(self):
        np.testing.assert_array_equal(quantize_int8([-200, -1.5, -.5, .5, 1.5, 200], 1., 0),
                                      [-128, -2, 0, 0, 2, 127])
        np.testing.assert_array_equal(quantize_int8([0, 1], 1 / 255, -128), [-128, 127])
        for scale in [0, -1, float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                quantize_int8([0], scale, 0)
        with self.assertRaises(ValueError):
            quantize_int8([float('nan')], 1, 0)
        with self.assertRaises(ValueError):
            quantize_int8([0], 1, 128)
