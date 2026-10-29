# Checkpoint archive manifest

[`ARCHIVES.json`](ARCHIVES.json) records the sizes, member counts, SHA-256 hashes, and CRC checks for the **original** local `code.zip` and checkpoint archives. [`PUBLIC_ARCHIVES.json`](PUBLIC_ARCHIVES.json) separately records the path-redacted public variants and the matching runtime ZIP. The five public checkpoint ZIPs are available in the [v1.0.0 GitHub Release](https://github.com/shen982/RTDETR-R18-FDPN-Pedestrian-Detection/releases/tag/v1.0.0); compare downloaded sizes and SHA-256 values before extraction. Follow the [release guide](RELEASE_GUIDE.md) for provenance and scope.

The model files are only for trusted local reproduction. Loading PyTorch checkpoints uses Python serialization; do not load untrusted weight files. See [reproduction notes](../docs/REPRODUCTION.md) and the paper for the exact evaluation scope.
