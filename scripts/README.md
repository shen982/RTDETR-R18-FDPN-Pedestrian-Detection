# Reproduction entry points

- `submission_reproduce.py` checks a trusted local checkpoint or launches an explicit new train/test run inside the **curated runtime source bundle** plus a compatible environment. Its read-only `check` action does not import Torch or allocate a GPU.
- `prepare_pennfudan.py` converts an official Penn--Fudan archive into the fixed detection split.
- `prepare_public_person_subsets.py` materializes the fixed VOC2007-person and COCO2017-person subsets from their original providers.

These scripts are published for inspection and audit. They are not advertised as a one-command reproduction from this repository alone: the full runtime, original dataset images, and trusted checkpoints are separate inputs. See [reproduction notes](../docs/REPRODUCTION.md).
