# Checkpoint release guide

The five `public_weights_*.zip` archives are published as the [v1.0.0 GitHub Release](https://github.com/shen982/RTDETR-R18-FDPN-Pedestrian-Detection/releases/tag/v1.0.0). Do not add them to ordinary Git history. After downloading, compare their sizes and SHA-256 values with [`PUBLIC_ARCHIVES.json`](PUBLIC_ARCHIVES.json). GitHub's regular file limit is documented in [About large files on GitHub](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github); release assets are used for these archives.

## Assets and purpose

| Asset | Purpose | Approximate size |
| --- | --- | ---: |
| `public_weights_initial_penn.zip` | Initial Penn--Fudan baseline and FDPN runs | 157 MB |
| `public_weights_public_e30.zip` | 30-epoch VOC/COCO-person subset runs | 314 MB |
| `public_weights_public_e100.zip` | 100-epoch VOC/COCO-person subset runs | 315 MB |
| `public_weights_ablation.zip` | Component ablations | 246 MB |
| `public_weights_robustness.zip` | Three-seed Penn--Fudan study and neck control | 718 MB |

The public assets differ from the original course-submission archives: private machine-path prefixes in checkpoint pickle metadata were replaced with an equal-length public prefix. Tensor-storage members are byte-identical to the originals. All 22 public checkpoints have now been loaded and evaluated on their exact test partitions; the archived metrics were reproduced within `1e-6` on an RTX 3090. The originals remain unchanged. Current public hashes and run mappings are in `reproduction/ASSETS.json` and `reproduction/RUNS.json`; original archive hashes remain in `weights/ARCHIVES.json` for provenance.

## Maintainer publication record

1. The source/runtime commit is `ee353f0` and the release tag is `v1.0.0`.
2. The five **public** weight ZIPs, runtime ZIP, and `PUBLIC_ARCHIVES.json` are attached to that release; the original `weights_*.zip` archives are not attached.
3. GitHub reports the following uploaded byte counts: 156,967,156; 313,898,734; 314,968,129; 245,742,964; and 718,220,237 bytes for the five weight archives, respectively. These match the local manifest.
4. Do not revise the numerical paper results merely because checkpoint paths were redacted.

For complete independent evaluation, use `python scripts/reproduce.py prepare --suite all`, then `python scripts/reproduce.py evaluate --suite all --device 0 --output reproduced_all`. This downloads runtime v5 and the exact dataset archives from v1.1.0, plus the existing v1.0.0 weights. See [the installation guide](../docs/REPRODUCTION.md). Use trusted checkpoint files and the published SHA-256 manifest.
