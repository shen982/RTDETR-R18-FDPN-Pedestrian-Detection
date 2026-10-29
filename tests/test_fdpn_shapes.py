"""CPU-only smoke tests for the public FocusFeature extraction.

These tests verify tensor interfaces, not detection quality or paper metrics.
"""

import torch

from src.modules.neck import FocusFeature


def test_first_focus_shape():
    focus = FocusFeature((256, 256, 128)).eval()
    with torch.no_grad():
        output = focus((torch.zeros(1, 256, 8, 8),
                        torch.zeros(1, 256, 16, 16),
                        torch.zeros(1, 128, 32, 32)))
    assert output.shape == (1, 384, 16, 16)


def test_refocus_shape():
    focus = FocusFeature((256, 384, 256)).eval()
    with torch.no_grad():
        output = focus((torch.zeros(1, 256, 8, 8),
                        torch.zeros(1, 384, 16, 16),
                        torch.zeros(1, 256, 32, 32)))
    assert output.shape == (1, 576, 16, 16)
