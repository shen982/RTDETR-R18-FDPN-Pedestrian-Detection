"""FDPN feature-focusing component extracted from the supplied bundle.

The bundle documentation attributes the Focusing Diffusion Pyramid Network to
its author, Bilibili user “魔傀面具”, and labels it as self-developed. The
experiment runtime uses the integrated copy under ``vendor/RTDETR-main``.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from ..common import Conv, autopad


class ADown(nn.Module):
    """Two-branch average/max-pooling downsampler used by FocusFeature."""

    def __init__(self, c1: int, c2: int) -> None:
        super().__init__()
        hidden = c2 // 2
        self.cv1 = Conv(c1 // 2, hidden, 3, 2, 1)
        self.cv2 = Conv(c1 // 2, hidden, 1, 1, 0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = torch.nn.functional.avg_pool2d(x, 2, 1, 0, False, True)
        x1, x2 = x.chunk(2, dim=1)
        x1 = self.cv1(x1)
        x2 = torch.nn.functional.max_pool2d(x2, 3, 2, 1)
        x2 = self.cv2(x2)
        return torch.cat((x1, x2), dim=1)


class FocusFeature(nn.Module):
    """Align three pyramid levels, then aggregate multi-kernel depthwise context."""

    def __init__(
        self,
        inc: tuple[int, int, int],
        kernel_sizes: tuple[int, int, int, int] = (5, 7, 9, 11),
        e: float = 0.5,
    ) -> None:
        super().__init__()
        hidden = int(inc[1] * e)
        self.conv1 = nn.Sequential(nn.Upsample(scale_factor=2), Conv(inc[0], hidden, 1))
        self.conv2 = Conv(inc[1], hidden, 1) if e != 1 else nn.Identity()
        self.conv3 = ADown(inc[2], hidden)
        channels = hidden * 3
        self.dw_conv = nn.ModuleList(
            nn.Conv2d(channels, channels, kernel_size=k, padding=autopad(k), groups=channels)
            for k in kernel_sizes
        )
        self.pw_conv = Conv(channels, channels)

    def forward(self, x: tuple[torch.Tensor, torch.Tensor, torch.Tensor]) -> torch.Tensor:
        high, middle, low = x
        aligned = torch.cat([self.conv1(high), self.conv2(middle), self.conv3(low)], dim=1)
        context = torch.sum(
            torch.stack([aligned] + [layer(aligned) for layer in self.dw_conv], dim=0),
            dim=0,
        )
        return aligned + self.pw_conv(context)
