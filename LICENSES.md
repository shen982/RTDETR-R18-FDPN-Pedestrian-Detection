# Third-Party and Provenance Notes

- `third_party/IEEEtran/` was obtained from the CTAN IEEEtran package. Its files contain the applicable LPPL notices.
- `third_party/tectonic-musl/tectonic` is the Tectonic 0.15.0 static Linux build used only as a local build tool. Tectonic is distributed under the MIT License.
- The experiment runtime is based on a modified Ultralytics 8.0.201-derived source tree whose configuration headers state AGPL-3.0. Preserve the upstream notices when distributing the runtime or derivative source.
- `third_party/licenses/AGPL-3.0.txt` is the verbatim license text fetched from the upstream Ultralytics v8.0.201 tag. It accompanies Ultralytics-derived runtime components; it is not a blanket license declaration for the paper or every third-party module in the supplied bundle.
- FDPN was extracted from the supplied RT-DETR improvement bundle. The bundle attributes the implementation to its original provider. This paper reports integration and empirical evaluation and does not claim authorship of the topology.
- The repository maintainer has stated that they hold authorization to redistribute the supplied FDPN module. That statement does not turn the original FDPN topology into a new contribution of this paper.
- The architecture diagram is a native-vector redraw of the implemented RT-DETR-R18 / FDPN graph. It retains attribution to Zhao et al. (CVPR 2024), the supplied implementation, and Luo et al. (Computers, Materials & Continua, 2026). Historical source schematics remain reference material; the active paper figure is not presented as an original invention.
- The architecture insets embed the Penn--Fudan held-out image FudanPed00001 and its recorded FDPN prediction at display confidence 0.50. Original image rights remain with the dataset and image rights holders. No generative redraw of the people, scene, or predicted boxes is used.
- Papers under `references/papers/` are local reference copies and are not part of the paper submission archive.
- Public person subsets derive from official VOC2007 and COCO2017 sources. The package redistributes split and annotation metadata and experiment records, not dataset image archives. Original rights remain with the respective holders.
- Quantitative figures and tables are generated from archived run records. The adaptation drawing is not evidence that FDPN was invented by the course-paper author.
