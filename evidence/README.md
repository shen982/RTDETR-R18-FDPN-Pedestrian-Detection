# Experimental evidence

`runs/<run>/` contains the held-out test record, full epoch-by-epoch results.csv, effective training arguments and available experiment metadata/completion records for all 22 runs. The run names match [RUNS.json](../reproduction/RUNS.json).

Machine-specific paths are redacted. [RUN_RECORDS.json](RUN_RECORDS.json) records the original-source hash, public-file hash and whether redaction changed each file. Numerical results are preserved.

The existing aggregate summaries and exact split manifests support the paper's tables. Principal evidence is the three-seed Penn--Fudan comparison; historical initial, public-subset and ablation experiments must not be pooled as additional seeds.

Fresh checkpoint-evaluation outputs are recorded separately from the historical evidence. Read [the reproduction guide](../docs/REPRODUCTION.md) for scope and limitations.
