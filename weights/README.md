# Checkpoint archive manifest

[`ARCHIVES.json`](ARCHIVES.json) records the sizes, member counts, SHA-256 hashes, and CRC checks for the local code and checkpoint archives. The checkpoint ZIP files are intentionally **not** in ordinary Git history and have not yet been uploaded as public release assets. No GitHub download URL is claimed.

The model files are only for trusted local reproduction. Loading PyTorch checkpoints uses Python serialization; do not load untrusted weight files. See [reproduction notes](../docs/REPRODUCTION.md) and the paper for the exact evaluation scope.
