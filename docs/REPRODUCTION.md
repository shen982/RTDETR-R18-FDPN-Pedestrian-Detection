# Reproduction and release boundary

The public repository contains the manuscript, selected path-free summaries, an attributed FDPN operator extraction, model YAMLs, reproduction entry points, and a curated [runtime source ZIP](../artifacts/README.md). The checkpoint archives and complete raw experiment records are not in this Git history. Path-redacted weight archives are prepared locally for a separate release but are not yet public. An independent reader cannot reproduce the paper results from this repository alone: a compatible environment, original dataset images, and trusted checkpoints are still required.

## Local archives

The local submission package provides the original `code.zip`, `weights_initial_penn.zip`, `weights_public_e30.zip`, `weights_public_e100.zip`, `weights_ablation.zip`, and `weights_robustness.zip`. Check their sizes and SHA-256 values in [`weights/ARCHIVES.json`](../weights/ARCHIVES.json). The original archives are not Git-tracked or publicly linked here. The public, path-safe `artifacts/public_runtime_code_v4.zip` and the five `public_weights_*.zip` archives are **different** files with hashes in [`weights/PUBLIC_ARCHIVES.json`](../weights/PUBLIC_ARCHIVES.json). Only the runtime ZIP is presently in this Git repository.

The original local code archive contains the modified Ultralytics-derived runtime, model configurations, scripts, split metadata, and archived experiment records. The public runtime ZIP retains source, selected configurations, split manifests, and upstream AGPL-3.0 license text while excluding raw records with machine paths. The FDPN source attribution must be retained. The maintainer has stated authorization to redistribute the supplied FDPN module; the unmodified local `code.zip` should not be mirrored wholesale without a separate release audit.

## Re-running a local submission bundle

From a fresh directory containing the public runtime ZIP and the corresponding trusted `public_weights_initial_penn.zip`, extract both into the same parent directory. The `snapshot/` prefix appears in both archives. The public runtime's `snapshot/MANIFEST.json` has the **public**, path-redacted checkpoint hashes; `snapshot/ORIGINAL_RUN_MANIFEST.json` preserves the original records for provenance. Then, inside `snapshot/`, run the read-only checks before any GPU job:

```bash
python scripts/submission_reproduce.py --action check --dataset penn --model baseline
python scripts/submission_reproduce.py --action check --dataset penn --model fdpn
```

Both Penn--Fudan commands above passed after fresh extraction of the public runtime and public weight archive. The read-only check verifies file existence and hashes a checkpoint against an archived entry when available. It does not load the model, authenticate configuration or split hashes against frozen values, or prove that a new training run will reproduce the paper values. For new training and evaluation, prepare the images using the published scripts and write to a new output directory; the archived local quickstart provides additional environment notes.

Datasets must be obtained from their original providers. The study uses a fixed 120/25/25 Penn--Fudan split and fixed person-only VOC2007 and COCO2017 subsets; these are not full official-benchmark evaluations. The 100-epoch subset extensions were exploratory after 30-epoch inspection. The paper reports matched comparisons and the limits of the evidence.
