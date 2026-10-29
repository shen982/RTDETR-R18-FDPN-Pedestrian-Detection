# Model configurations

The YAML files in [`models/`](models/) define the matched RT-DETR-R18 baseline, the supplied FDPN adaptation, a widened original-neck capacity control, and the two single-seed component ablations reported in the paper. They preserve the original Ultralytics/RT-DETR provenance headers and FDPN source attribution.

These graph definitions require the modified Ultralytics-derived runtime available in the curated source ZIP under [`artifacts/`](../artifacts/README.md). The extracted Python operator under [`src/`](../src/) is for inspection and focused tests; by itself it is not a drop-in replacement for the entire runtime. The full checkpoint evaluation also requires the appropriate weight archive and fixed dataset split.

The YAMLs are retained byte-for-byte from the verified local experiment records so their SHA-256 values match all 22 archived run entries. This also preserves harmless trailing spaces in several source files.
