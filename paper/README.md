# Manuscript source and build

`main.pdf` is the seven-page English IEEEtran manuscript. `main.tex`, `references.bib`, the active figures, all referenced tables, and a local copy of the IEEEtran class/bibliography style are included so the paper can be inspected and rebuilt.

From this directory, install Tectonic or an IEEEtran-compatible LaTeX toolchain, then run:

```bash
make
```

The repository does not bundle the platform-specific TeX binary or font cache. Rebuilding the PDF does not train or evaluate a detector. The source and path-redacted checkpoint assets are available through the [v1.0.0 reproducibility release](https://github.com/shen982/RTDETR-R18-FDPN-Pedestrian-Detection/releases/tag/v1.0.0). See the [repository README](../README.md) and [provenance notes](../LICENSES.md).
