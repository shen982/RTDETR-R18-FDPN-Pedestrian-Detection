# Public-safe experiment summaries

This directory contains selected machine-readable statistics and dataset split manifests from the local archive. The original raw run JSON, full configuration snapshots, curves, and checkpoint mapping remain in the local course-submission package. Those raw files can contain machine-specific absolute paths and have not been copied wholesale into this public repository.

- `audit_report.json`: summary checks for the reported experiments.
- `robustness/publication_statistics.json`: three-seed Penn--Fudan values, means, sample standard deviations, and checkpoint/test hashes.
- `public_multidataset_e100/summary.json`: the fixed-subset 100-epoch comparison.
- `fdpn_ablation/summary.json`: component-sensitivity summary.
- `datasets/*/split_manifest.json`: split definitions, without original images.

The values in the paper are traceable to the archived held-out test records and checkpoint SHA-256 hashes in the local submission package; the public checkpoint variants and their hashes are available in the [v1.0.0 reproducibility release](https://github.com/shen982/RTDETR-R18-FDPN-Pedestrian-Detection/releases/tag/v1.0.0). This public subset is an audit aid, not a claim that dataset images or a preconfigured environment are redistributed.
