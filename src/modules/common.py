"""Minimal convolution primitives needed by the extracted neck modules."""

from __future__ import annotations

import torch
import torch.nn as nn


def autopad(kernel_size, padding=None, dilation=1):
    """Choose padding that preserves spatial dimensions at stride one."""
    if dilation > 1:
        kernel_size = (
            dilation * (kernel_size - 1) + 1
            if isinstance(kernel_size, int)
            else [dilation * (value - 1) + 1 for value in kernel_size]
        )
    if padding is None:
        padding = (
            kernel_size // 2
            if isinstance(kernel_size, int)
            else [value // 2 for value in kernel_size]
        )
    return padding


class Conv(nn.Module):
    """Conv2d followed by BatchNorm2d and an optional SiLU activation."""

    default_act = nn.SiLU()

    def __init__(self, c1, c2, k=1, s=1, p=None, g=1, d=1, act=True):
        super().__init__()
        self.conv = nn.Conv2d(c1, c2, k, s, autopad(k, p, d), groups=g, dilation=d, bias=False)
        self.bn = nn.BatchNorm2d(c2)
        self.act = self.default_act if act is True else act if isinstance(act, nn.Module) else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.act(self.bn(self.conv(x)))


class ConvTranspose(nn.Module):
    """ConvTranspose2d followed by BatchNorm2d and an optional SiLU activation."""

    default_act = nn.SiLU()

    def __init__(self, c1, c2, k=2, s=2, p=0, bn=True, act=True):
        super().__init__()
        self.conv_transpose = nn.ConvTranspose2d(c1, c2, k, s, p, bias=not bn)
        self.bn = nn.BatchNorm2d(c2) if bn else nn.Identity()
        self.act = self.default_act if act is True else act if isinstance(act, nn.Module) else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.act(self.bn(self.conv_transpose(x)))
