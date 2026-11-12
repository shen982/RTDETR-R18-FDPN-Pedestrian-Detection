# Controlled Evaluation of Focus--Diffusion Feature Fusion for Data-Limited Pedestrian Detection

Jiaxu Chen · Department of Automation, North China Electric Power University, Baoding, China

Contact: 17736460722@163.com

课程提交稿：**[中文论文（含中英题目、署名、摘要和关键词）](paper/chinese_version/陈佳旭_多核上下文聚焦融合_课程论文.pdf)**。

The **[English edition](paper/main.pdf)** is also retained. This course project evaluates an existing FDPN configuration in RT-DETR-R18, with attribution to its source bundle and related focus--diffusion research. Its contributions are controlled evaluation and component analysis.

[Download the course PDF](https://github.com/shen982/RTDETR-R18-FDPN-Pedestrian-Detection/raw/refs/heads/main/paper/chinese_version/陈佳旭_多核上下文聚焦融合_课程论文.pdf) · [Download repository ZIP](https://github.com/shen982/RTDETR-R18-FDPN-Pedestrian-Detection/archive/refs/heads/main.zip)

The final course submission is the Chinese PDF under `paper/chinese_version/`, with bilingual front matter and a single lower-left GitHub link. Older tagged English paper releases are historical versions. Large datasets and checkpoints remain in the releases linked below.

## Main findings

| Dataset and protocol | Metric (%) | RT-DETR-R18 | FDPN | Difference (pp) |
| --- | --- | ---: | ---: | ---: |
| Penn--Fudan, 30 epochs, 3 seeds | AP50:95 | 41.31 | 42.54 | +1.22 |
| Penn--Fudan, 30 epochs, 3 seeds | AP50 | 65.59 | 64.17 | −1.42 |
| VOC2007-person450, 100 epochs | AP50:95 | 16.71 | 17.27 | +0.56 |
| COCO2017-person450, 100 epochs | AP50:95 | 6.92 | 8.11 | +1.19 |

Differences use unrounded values. FDPN exceeds the near-parameter-matched CCFF-320 control by 0.86 pp AP50:95 and adds 11.9% inference parameters over the baseline. VOC/COCO and ablation results are exploratory single-seed experiments on fixed person-only subsets. The paper discusses metric trade-offs, seed variability, test reuse and the limits of capacity controls.

## Reproduce

Follow **[the installation and reproduction guide](docs/REPRODUCTION.md)** for Python 3.11/Linux and pinned dependencies. Then:

```bash
python scripts/reproduce.py prepare --suite all
python scripts/reproduce.py evaluate --suite all --device 0 --output reproduced_all
```

The program downloads and checks the full runtime, all **1,070 exact study images with labels**, and **22 selected checkpoints**. It evaluates the test splits in fresh output directories, compares metrics with archived evidence, and summarizes three-seed results. CPU evaluation uses `--device cpu`. Retraining commands are documented.

[Executed validation](evidence/reproduction_validation/README.md): all 22 GPU evaluations exactly match their archived metrics; a clean CPU installation runs both architectures; baseline and FDPN each complete a 30-epoch training check. CPU metrics and new training trajectories can differ from the historical GPU records.

## Files and downloads

| Material | Location |
| --- | --- |
| Chinese course PDF, editable HTML, build scripts and figures | [paper/chinese_version/](paper/chinese_version/) |
| English PDF, LaTeX, figures, tables and bibliography | [paper/](paper/) |
| Runtime v5 and three exact dataset ZIPs | [v1.1.0 assets](https://github.com/shen982/RTDETR-R18-FDPN-Pedestrian-Detection/releases/tag/v1.1.0) |
| All five weight archives, 22 checkpoints | [v1.0.0 assets](https://github.com/shen982/RTDETR-R18-FDPN-Pedestrian-Detection/releases/tag/v1.0.0) |
| Every asset URL, byte count and SHA-256 | [reproduction/ASSETS.json](reproduction/ASSETS.json) |
| Run/configuration/data/weight/metric mapping | [reproduction/RUNS.json](reproduction/RUNS.json) |
| Complete training curves and held-out records | [evidence/runs/](evidence/runs/) |
| FDPN extraction and exact model YAMLs | [src/](src/), [configs/](configs/) |
| Attribution and runtime/dataset terms | [LICENSES.md](LICENSES.md) |

Weights download separately and are not embedded in the PDF or supplementary submission ZIP. Dataset images retain their original rights; the archives include provenance and COCO per-image attribution. Public checkpoints redact machine paths while preserving tensor bytes; use the public hashes.
