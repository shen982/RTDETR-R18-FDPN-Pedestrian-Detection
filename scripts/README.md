# Reproduction programs

Start with [docs/REPRODUCTION.md](../docs/REPRODUCTION.md).

- `reproduce.py`: download, verify, evaluate all 22 runs, aggregate three-seed results, or retrain the exact selected protocol.
- `evaluate_archived.py`: worker executed from the extracted frozen snapshot; uses local source, exact configuration and test split.
- `prepare_pennfudan.py` and `prepare_public_person_subsets.py`: historical source-data preparation/provenance. Prepared exact subsets are available in v1.1.0, so running these is unnecessary for checkpoint evaluation.
- `submission_reproduce.py`: legacy v1.0.0 entrypoint. Use the new workflow above for a complete independent reproduction.
