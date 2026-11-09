# Reproduce the paper

The submission is the English [paper](../paper/main.pdf). This repository provides its source, exact study datasets, all 22 selected checkpoints, configurations, and recorded training/test evidence. Checkpoints remain in **v1.0.0**; complete datasets and the portable runtime are in **v1.1.0**. The program uses both releases automatically.

## Install

Use **Python 3.11 on Linux x86_64**. The frozen runtime contains a CPython 3.11 Linux PyWavelets extension. The original experiments use PyTorch 2.7.1, CUDA 12.6, and an RTX 3090; other devices can introduce numerical differences. Allocate about 5 GB for downloads and extracted files, plus the Python environment and new training outputs.

```bash
git clone https://github.com/shen982/RTDETR-R18-FDPN-Pedestrian-Detection.git
cd RTDETR-R18-FDPN-Pedestrian-Detection
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu126
python -m pip install -r requirements-reproduce.txt
```

For evaluation without an NVIDIA GPU, replace the PyTorch index URL with `https://download.pytorch.org/whl/cpu` and pass `--device cpu` below. Training uses CUDA. Source and dependency overlays load from the extracted snapshot; no separately installed Ultralytics package is needed.

## Download and verify

```bash
python scripts/reproduce.py list --suite all
python scripts/reproduce.py prepare --suite all
python scripts/reproduce.py verify --suite all
```

The program downloads nine SHA-256-verified assets and safely extracts them under `reproduction_workspace/snapshot/`. It checks every frozen source/data file and selected checkpoint. Default suite `primary` selects the nine three-seed Penn--Fudan runs; `quick` selects the two historical initial runs. Use `--workspace /path/on/a/large/disk` consistently to relocate all downloads, data, weights and results.

All URLs, byte counts and hashes are in [ASSETS.json](../reproduction/ASSETS.json). [RUNS.json](../reproduction/RUNS.json) maps each run to its exact configuration, checkpoint, seed, budget and metrics. Public checkpoints preserve original tensor bytes but redact machine paths; their hashes intentionally differ from the original variants in `weights/ARCHIVES.json`. If an extracted file was modified, use a fresh workspace to restore the released inputs.

## Evaluate checkpoints

```bash
# Principal comparison: baseline, CCFF-320 and FDPN, three seeds each.
python scripts/reproduce.py evaluate --suite primary --device 0 --output reproduced_primary
# All 22 runs.
python scripts/reproduce.py evaluate --suite all --device 0 --output reproduced_all
# A single run on CPU.
python scripts/reproduce.py evaluate --run penn_fdpn_e30_s2026 --device cpu --output reproduced_cpu
```

The evaluator creates a portable local data.yaml and evaluates the **test** split at size 416, batch 4, and full precision. Each run produces a log, evaluation outputs and result.json. The combined results.csv and summary.json compare metrics with the archive and calculate three-seed means and **sample** standard deviations. Numerical tolerance is `1e-6` on the raw 0--1 metric scale, not a statistical significance threshold. Mismatches are reported, never replaced with archived values. Existing output directories are protected.

```bash
python scripts/reproduce.py summarize --output reproduced_all
```

## Retrain from scratch

```bash
python scripts/reproduce.py train --run penn_baseline_e30_s2026 --device 0 --output trained_baseline
python scripts/reproduce.py evaluate --run penn_baseline_e30_s2026 --device 0 --weights trained_baseline/penn_baseline_e30_s2026/training/weights/best.pt --output tested_new_baseline
```

The run fixes the model YAML, split, seed, epochs, 416-pixel inputs and batch size 4. Training uses no pretrained weights, AdamW, learning rate/weight decay `1e-4`, final learning-rate ratio 1.0, three warm-up epochs, deterministic mode and no AMP. Remaining toolkit defaults come from the frozen runtime; historical effective arguments and full curves are in [evidence/runs/](../evidence/runs/). Training result.json reports **validation** metrics; the second command evaluates the selected best checkpoint on the held-out **test** split.

Use `train --suite primary` or `train --suite all` for a complete new study. Retraining is substantially more expensive than checkpoint evaluation. Hardware, dependencies and nondeterministic operations can alter trajectories despite equal seeds; exact historical training metrics are not guaranteed. Archived checkpoints remain required by verification for a custom-weight evaluation as the original comparison reference.

## Exact datasets

| Prepared dataset | Train / validation / test images | Train / validation / test person boxes |
| --- | --- | --- |
| Penn--Fudan | 120 / 25 / 25 | 294 / 65 / 64 |
| VOC2007-person450 | 300 / 50 / 100 | 482 / 77 / 152 |
| COCO2017-person450 | 300 / 50 / 100 | 748 / 121 / 297 |

All **1,070 images**, labels, exact split manifests, source annotations/provenance and dataset reports are supplied. VOC/COCO partitions each include 20% negative images and exclude images containing difficult/crowd persons. These are sampled single-class evaluations, not full official benchmarks. Frozen hashes avoid random resampling. Original dataset/image terms apply; COCO image URLs and individual licenses are in IMAGE_ATTRIBUTION.json.

## Evidence and validation boundaries

All 22 test records and training curves, with available completion/metadata files, are in [evidence/runs/](../evidence/runs/). Absolute paths are redacted; [RUN_RECORDS.json](../evidence/RUN_RECORDS.json) retains original and public-file hashes separately.

The runtime preserves attributed RT-DETR/FDPN source. Its only model-source portability change removes import-time CUDA allocations for fixed kernels in the unrelated MAC module. Evaluated baseline/FDPN tensors are unchanged.

The paper treats the three-seed Penn--Fudan comparison as principal evidence. Public-subset and component experiments remain exploratory single-seed results; test reuse, small partitions and unmatched computation limit generalization.

The [executed validation report](../evidence/reproduction_validation/README.md) records exact agreement for all 22 GPU evaluations, successful baseline/FDPN evaluation in a freshly installed CPU environment, and complete 30-epoch training checks for both architectures. CPU results show small AP differences from the recorded GPU metrics; precision/recall operating points can also change. Re-evaluation and installation checks do not guarantee identical retraining trajectories.
