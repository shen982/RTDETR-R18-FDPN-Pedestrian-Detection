# Inspected FDPN component

`modules/neck/fdpn.py` is a small, readable extraction of the FDPN `FocusFeature` and `ADown` operators used by the attributed source bundle. It is included with the maintainer's stated authorization to redistribute the supplied module and with the source attribution intact. The paper's own contribution is the RT-DETR-R18 integration study and evaluation, not authorship of the original FDPN topology.

`modules/common.py` contains the minimal convolution primitives needed to inspect or unit-test the extracted operator. The exact training graph is in [`configs/models/candidate_fdpn.yaml`](../configs/models/candidate_fdpn.yaml). The complete modified Ultralytics-derived runtime is **not** contained in this directory; a curated source ZIP is available under [`artifacts/`](../artifacts/README.md). Consult [reproduction notes](../docs/REPRODUCTION.md) before claiming a full rerun.
