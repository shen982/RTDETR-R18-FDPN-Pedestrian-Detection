# Reproduction and release boundary

The public repository contains the manuscript and selected, path-free summaries. The complete runnable runtime and checkpoints are currently distributed only as **local course-submission archives**, not as GitHub assets. An independent reader cannot reproduce training from this repository alone. This distinction is intentional and should remain explicit until the uploads are verified.

## Local archives

The local package provides `code.zip`, `weights_initial_penn.zip`, `weights_public_e30.zip`, `weights_public_e100.zip`, `weights_ablation.zip`, and `weights_robustness.zip`. Check the sizes and SHA-256 values in [`weights/ARCHIVES.json`](../weights/ARCHIVES.json) before extraction. The archives are not Git-tracked or publicly linked here.

The code archive contains the modified Ultralytics-derived runtime, model configurations, scripts, split metadata, and archived experiment records. The runtime's AGPL-3.0 notices and the FDPN source attribution must be retained. Permission to publicly redistribute the supplied FDPN bundle has not yet been established; the local package should not be mirrored without a rights review.

## Re-running a local submission bundle

From a fresh directory containing the local archives, extract `code.zip` and the required weight archive into the same parent directory. The `snapshot/` prefix appears in both archives. Then, inside `snapshot/`, run the read-only checks before any GPU job:

```bash
python scripts/submission_reproduce.py --action check --dataset penn --model baseline
python scripts/submission_reproduce.py --action check --dataset penn --model fdpn
```

The read-only check verifies file existence and hashes a checkpoint against an archived entry when available. It does not authenticate configuration or split hashes against frozen values, nor does it prove that a new training run will reproduce the paper values. For new training and evaluation, follow the `docs/REPRODUCTION_QUICKSTART.md` inside the local code archive and write to a new output directory.

Datasets must be obtained from their original providers. The study uses a fixed 120/25/25 Penn--Fudan split and fixed person-only VOC2007 and COCO2017 subsets; these are not full official-benchmark evaluations. The 100-epoch subset extensions were exploratory after 30-epoch inspection. The paper reports matched comparisons and the limits of the evidence.
