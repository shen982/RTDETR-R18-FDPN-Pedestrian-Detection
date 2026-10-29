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
- [`evidence/`](evidence/README.md): public-ready aggregate statistics, subset manifests, and checksums. These summaries do not replace the complete local submission archive.
- [`docs/`](docs/REPRODUCTION.md): reproduction boundaries, sources, and required local archives.
- [`weights/`](weights/README.md): integrity manifest for the checkpoint archives; no model binary is tracked in Git.
- [`LICENSES.md`](LICENSES.md): third-party attribution and redistribution boundaries.

## Release status and reproducibility

The paper and selected public-safe summaries are available here. The full source snapshot and checkpoint archives remain in the separately prepared **local course-submission package**. They have **not** been uploaded to this repository or linked as public downloads. The supplied FDPN bundle's redistribution permission must be checked before its source is published; attribution alone is not a license. Do not infer code or weight availability from the existence of this repository.

Penn--Fudan, VOC2007, and COCO2017 images are not redistributed. The three-seed sample is small, the Penn--Fudan test partition was reused during exploration, and a near-parameter-matched widened-neck control cannot isolate every capacity effect. Read the manuscript's limitations alongside the positive AP50:95 results.

For a local course submission, use the accompanying verified `code.zip` and `weights_*.zip` archives plus their SHA-256 manifest. New runs should use fresh output names and never overwrite the archived records. See [reproduction notes](docs/REPRODUCTION.md).
