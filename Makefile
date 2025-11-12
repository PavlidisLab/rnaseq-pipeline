DESTDIR :=
PREFIX := /usr

CONDA := conda
PIP := pip

all: scripts contrib/RSEM

contrib/RSEM:
	$(MAKE) -C $@

scripts:
	$(MAKE) -C $@

install: install-python install-systemd-units install-RSEM install-scripts install-conda-env install-fish-completion

install-fish-completion:
	mkdir -p "${DESTDIR}/etc/fish/completions"
	install -m644 data/luigi.fish "${DESTDIR}/etc/fish/completions/"

install-scripts:
	$(MAKE) -C scripts install

install-python:
	$(PIP) install --prefix="${DESTDIR}${PREFIX}" .

install-systemd-units:
	mkdir -p "${DESTDIR}/etc/systemd/system/"
	install -m644 data/systemd/*.{service,timer} "${DESTDIR}/etc/systemd/system/"
	@echo "Remember to run 'systemctl override rnaseq-pipeline-viewer' and 'systemctl override rnaseq-pipeline-worker@' and set CONDA_BIN, CONDA_ENV, GEMMA_USERNAME and GEMMA_PASSWORD environment variables."

install-RSEM:
	$(MAKE) -C contrib/RSEM install prefix="${DESTDIR}${PREFIX}"

install-conda-env: environment.yml
	mkdir -p "${DESTDIR}/share/rnaseq-pipeline/"
	$(CONDA) env create -p "${DESTDIR}${PREFIX}/share/rnaseq-pipeline/conda-env" -f environment.yml

clean:
	$(MAKE) -C contrib/RSEM clean
	$(MAKE) -C scripts clean

.PHONY: all scripts contrib/RSEM install install-python install-systemd-unit install-RSEM
