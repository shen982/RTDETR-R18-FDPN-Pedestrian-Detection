# Checkpoint release guide

The five `public_weights_*.zip` archives are prepared **locally**, not yet uploaded. Do not add them to ordinary Git history or advertise a download URL until the assets are visible on the repository's Releases page and their downloaded SHA-256 values match [`PUBLIC_ARCHIVES.json`](PUBLIC_ARCHIVES.json). GitHub's regular file limit is documented in [About large files on GitHub](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github); use release assets for these archives.

## Assets and purpose

| Asset | Purpose | Approximate size |
| --- | --- | ---: |
| `public_weights_initial_penn.zip` | Initial Penn--Fudan baseline and FDPN runs | 157 MB |
| `public_weights_public_e30.zip` | 30-epoch VOC/COCO-person subset runs | 314 MB |
| `public_weights_public_e100.zip` | 100-epoch VOC/COCO-person subset runs | 315 MB |
| `public_weights_ablation.zip` | Component ablations | 246 MB |
| `public_weights_robustness.zip` | Three-seed Penn--Fudan study and neck control | 718 MB |

The public assets differ from the original course-submission archives: private machine-path prefixes in checkpoint pickle metadata were replaced with an equal-length public prefix. Tensor-storage members are byte-identical to the originals. The Penn--Fudan baseline and FDPN original/public checkpoints were also loaded locally on CPU and their model `state_dict` tensors compared equal. The other 20 checkpoints have been verified at the archive-member byte level, not by separate model-load tests. The originals remain unchanged. Both the public and original hashes appear in the runtime's `snapshot/MANIFEST.json` and `snapshot/ORIGINAL_RUN_MANIFEST.json` respectively.

## Maintainer publication checklist

1. Push the Git commit containing `artifacts/public_runtime_code_v4.zip`, source, configs, scripts, and this guide.
2. Create a GitHub Release for a new tag after that commit. Attach the five **public** weight ZIPs from the local `submission_release/` directory; do not attach the original `weights_*.zip` archives.
3. Download or independently hash the visible assets and compare byte counts and SHA-256 digests with [`PUBLIC_ARCHIVES.json`](PUBLIC_ARCHIVES.json). Check that each asset name appears exactly once and that all five are downloadable.
4. Only then add actual Release links to the repository README and paper availability statement. Record the release tag and preferably the commit identifier. Do not revise the numerical paper results merely because the checkpoint paths were redacted.

To reproduce the read-only integrity check, extract [`public_runtime_code_v4.zip`](../artifacts/public_runtime_code_v4.zip) and the required public weight ZIP into one fresh parent directory, then run `python snapshot/scripts/submission_reproduce.py --action check --dataset penn --model baseline` or `--model fdpn`. Original dataset images and a compatible Python/PyTorch/CUDA environment are still required for evaluation or training. PyTorch checkpoints use pickle serialization; load only trusted files.
