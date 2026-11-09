# Manuscript source and build

`main.pdf` is the seven-page English IEEEtran manuscript. `main.tex`, `references.bib`, the active figures, all referenced tables, and a local copy of the IEEEtran class/bibliography style are included so the paper can be inspected and rebuilt.

From this directory, install Tectonic or an IEEEtran-compatible LaTeX toolchain, then run:

```bash
make
```

The repository does not bundle the platform-specific TeX binary or font cache. Rebuilding the PDF does not train or evaluate a detector. The first-page footer includes a clickable GitHub link. The [reproduction guide](../docs/REPRODUCTION.md) covers all exact datasets, 22 selected weights, source, evaluation and retraining. See also the [repository README](../README.md) and [provenance notes](../LICENSES.md).
