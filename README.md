# Evaluating Focus--Diffusion Feature Fusion for Data-Limited Pedestrian Detection

Jiaxu Chen · Department of Automation, North China Electric Power University, Baoding, China

Contact: 17736460722@163.com

This repository accompanies an IEEEtran-style course manuscript on the integration and evaluation of an existing Focusing Diffusion Pyramid Network (FDPN) configuration in RT-DETR-R18. The FDPN topology is attributed to its source bundle and related focus--diffusion work; it is **not claimed as a new invention by this paper**.

## Paper and results

Read [the manuscript](paper/main.pdf) first. The primary comparison uses three Penn--Fudan training seeds and reports mean held-out AP, not the best seed.

| Dataset and protocol | Metric | RT-DETR-R18 | FDPN adaptation | Difference |
| --- | --- | ---: | ---: | ---: |
| Penn--Fudan, 30 epochs, 3 seeds | AP50:95 | 41.31 | 42.54 | +1.22 percentage points |
| Penn--Fudan, 30 epochs, 3 seeds | AP50 | 65.59 | 64.17 | −1.42 percentage points |
| VOC2007-person subset, 100 epochs | AP50:95 | 16.71 | 17.27 | +0.56 percentage points |
| COCO2017-person subset, 100 epochs | AP50:95 | 6.92 | 8.11 | +1.19 percentage points |

AP values are percentages. VOC and COCO rows are exploratory fixed-subset, single-seed comparisons, not full official-benchmark results. The 6.44-point initial Penn--Fudan single-run gain is supplementary and is not substituted for the three-seed mean. FDPN raises the evaluated model size from 19.87 M to 22.24 M parameters (about 11.9%). The observed benefit is metric- and setting-dependent.

## Repository guide

- [`paper/`](paper/README.md): the final English manuscript, LaTeX, figures, tables, and bibliography.
- [`src/`](src/README.md) and [`configs/`](configs/README.md): attributed FDPN operator extraction and the exact baseline, adaptation, control, and ablation model graphs.
- [`scripts/`](scripts/README.md) and [`tests/`](tests/test_fdpn_shapes.py): reproduction entry points and CPU-only module-interface checks.
- [`artifacts/public_runtime_code_v4.zip`](artifacts/README.md): path-safe full runtime **source** archive with a checkpoint manifest matched to the separately prepared public weight archives; no data images or checkpoints.
- [`evidence/`](evidence/README.md): public-ready aggregate statistics, subset manifests, and checksums. These summaries do not replace the complete local submission archive.
- [`docs/`](docs/REPRODUCTION.md): reproduction boundaries, sources, and required local archives.
- [`weights/`](weights/README.md): original and public-variant integrity manifests plus a release guide; no model binary is tracked in Git.
- [`LICENSES.md`](LICENSES.md): third-party attribution and redistribution boundaries.

## Release status and reproducibility

The paper, selected public-safe summaries, core FDPN extraction, model configurations, and selected reproduction scripts are available here. A curated runtime source ZIP is also provided under `artifacts/`; it omits machine-specific raw records and is not a complete software environment. Path-redacted checkpoint archives have been prepared and verified locally, but have **not yet** been uploaded or linked as public downloads. The maintainer has stated authorization to redistribute the supplied FDPN module; the original topology remains attributed to its source bundle. Do not infer weight availability from this repository.

Penn--Fudan, VOC2007, and COCO2017 images are not redistributed. The three-seed sample is small, the Penn--Fudan test partition was reused during exploration, and a near-parameter-matched widened-neck control cannot isolate every capacity effect. Read the manuscript's limitations alongside the positive AP50:95 results.

For a local course submission, use the accompanying verified `code.zip` and `weights_*.zip` archives plus their SHA-256 manifest. New runs should use fresh output names and never overwrite the archived records. See [reproduction notes](docs/REPRODUCTION.md).
