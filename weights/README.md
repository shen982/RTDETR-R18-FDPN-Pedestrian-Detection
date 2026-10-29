# Checkpoint archive manifest

[`ARCHIVES.json`](ARCHIVES.json) records the sizes, member counts, SHA-256 hashes, and CRC checks for the **original** local `code.zip` and checkpoint archives. [`PUBLIC_ARCHIVES.json`](PUBLIC_ARCHIVES.json) separately records the path-redacted, locally prepared public variants and the matching runtime ZIP. The checkpoint ZIP files are intentionally **not** in ordinary Git history and have not yet been uploaded as public release assets. No GitHub weight-download URL is claimed. Follow the [release guide](RELEASE_GUIDE.md) when publishing them.

The model files are only for trusted local reproduction. Loading PyTorch checkpoints uses Python serialization; do not load untrusted weight files. See [reproduction notes](../docs/REPRODUCTION.md) and the paper for the exact evaluation scope.
