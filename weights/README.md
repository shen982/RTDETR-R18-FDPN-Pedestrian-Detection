# Checkpoints

All **22** selected checkpoints are publicly downloadable in five v1.0.0 Release assets: initial_penn (2), public_e30 (4), public_e100 (4), ablation (3), robustness (9).

Use [scripts/reproduce.py](../scripts/reproduce.py) as described in [the guide](../docs/REPRODUCTION.md); it downloads and verifies the required archives automatically. Every run is mapped in [RUNS.json](../reproduction/RUNS.json), and all current asset hashes and URLs are in [ASSETS.json](../reproduction/ASSETS.json).

`PUBLIC_ARCHIVES.json` records v1.0.0 public variants. `ARCHIVES.json` records original local variants for provenance. Machine-path redaction changes checkpoint-file hashes while preserving tensor-storage bytes. Do not compare the public binaries against the original private-path hashes.

Weights are not embedded in the submitted PDF or supplementary ZIP.
