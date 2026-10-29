# Public runtime source archive

[`public_runtime_code_v4.zip`](public_runtime_code_v4.zip) is a curated source archive, not a model checkpoint. It contains the modified Ultralytics-derived runtime, the attributed FDPN extraction, selected model configurations, scripts, split manifests, the upstream AGPL-3.0 license text, and a public checkpoint manifest. It excludes original dataset images, weights, and raw experiment records with private machine paths.

| File | Size | SHA-256 |
| --- | ---: | --- |
| `public_runtime_code_v4.zip` | 4.17 MB (decimal; 3.98 MiB) | `b379ee46a55eb490da24371069ca7693dcf5daa48eb5a1568cce0d72044f3abb` |

The ZIP passed CRC checks and an internal per-file SHA-256 manifest verification. Together with the **locally prepared path-redacted** `public_weights_initial_penn.zip`, its baseline and FDPN read-only checkpoint checks succeeded. The manifest maps all 22 public checkpoints while preserving original hashes in separate provenance fields. These checks do not load a model or rerun inference; a compatible Python/PyTorch/CUDA environment and original dataset images are still required for independent training or testing.

The original local `code.zip` is **not** published here because it contains machine-specific paths and additional raw experiment records. The public checkpoint assets are attached to the [v1.0.0 reproducibility release](https://github.com/shen982/RTDETR-R18-FDPN-Pedestrian-Detection/releases/tag/v1.0.0); do not substitute their hashes for this curated archive's hash. See [reproduction notes](../docs/REPRODUCTION.md) and [provenance notes](../LICENSES.md).
