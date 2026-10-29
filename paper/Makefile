LOCAL_TECTONIC := third_party/tectonic-musl/tectonic
ifneq ($(wildcard $(LOCAL_TECTONIC)),)
TECTONIC ?= $(LOCAL_TECTONIC)
else
TECTONIC ?= tectonic
endif

export TEXINPUTS := third_party/IEEEtran/IEEEtran//:
export BSTINPUTS := third_party/IEEEtran/IEEEtran/bibtex//:
export BIBINPUTS := .:
export XDG_CACHE_HOME := third_party/tectonic-cache
export XDG_CONFIG_HOME := third_party/tectonic-config
export XDG_DATA_HOME := third_party/tectonic-data
export TECTONIC_CACHE_DIR := $(CURDIR)/third_party/tectonic-cache

.PHONY: all clean

all: main.pdf

main.pdf: main.tex references.bib figures/architecture_visio_revision.pdf figures/robustness_summary.pdf figures/initial_penn_curves_column.pdf $(wildcard tables/*.tex)
	$(TECTONIC) -X compile --keep-logs --keep-intermediates main.tex

clean:
	$(RM) main.aux main.bbl main.blg main.log main.out main.pdf
