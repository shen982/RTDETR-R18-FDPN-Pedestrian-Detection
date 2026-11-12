# Manuscript source and build

The final course submission is [the Chinese PDF with bilingual front matter](chinese_version/陈佳旭_多核上下文聚焦融合_课程论文.pdf). Its [source and build instructions](chinese_version/README.md) are included. This six-page revision expands the paired-seed, ablation-parameter and training-budget analysis. The earlier English edition below covers the same experiments and is retained for reference.

`main.pdf` is the seven-page English IEEEtran manuscript. `main.tex`, `references.bib`, the active figures, all referenced tables, and a local copy of the IEEEtran class/bibliography style are included so the paper can be inspected and rebuilt.

From this directory, install Tectonic or an IEEEtran-compatible LaTeX toolchain, then run:

```bash
make
```

The repository does not bundle the platform-specific TeX binary or font cache. Rebuilding the PDF does not train or evaluate a detector. The first-page footer contains only one clickable GitHub URL, aligned at the lower left. The [reproduction guide](../docs/REPRODUCTION.md) covers all exact datasets, 22 selected weights, source, evaluation and retraining. See also the [repository README](../README.md) and [provenance notes](../LICENSES.md).
