# Assemblies

## About
Indexes for assemblies are generated using `rsem-prepare-reference` from RSEM. 

The script `rsem_make_star_reference.sh` included in this respository can take in an Illumina iGenome and produce an RSEM ready transcriptome. The resulting transcriptomes are stored in `Assemblies/runtime`.

The source assemblies are Illumina iGenomes downloaded from: http://support.illumina.com/sequencing/sequencing_software/igenome.html

Commonly used assemblies:
```
	# Mouse NCBIm37 (Ensembl)	
	ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Mus_musculus/Ensembl/NCBIM37/Mus_musculus_Ensembl_NCBIM37.tar.gz

	# Mouse GRCm38 (Ensembl)
	ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Mus_musculus/Ensembl/GRCm38/Mus_musculus_Ensembl_GRCm38.tar.gz

	# Human GRCh37 (Ensembl)
	ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Homo_sapiens/Ensembl/GRCh37/Homo_sapiens_Ensembl_GRCh37.tar.gz

	# Human GRCh38 (NCBI)
	ftp://igenome:G3nom3s4u@ussd-ftp.illumina.com/Homo_sapiens/NCBI/GRCh38/Homo_sapiens_NCBI_GRCh38.tar.gz
```

### Generating a runtime assembly
`./rsem_make_star_reference.sh SPECIESNAME /path/to/iGenome/Organism/Version/`

Example:
`./rsem_make_star_reference.sh human Assemblies/Homo_sapiens/NCBI/GRCh38/`

Output:
`Assemblies/runtime/human_ref38/human_0*`

Make sure that RSEM is installed and compilled. RSEM should be cloned from the linked submodule, then built with the `make` command from inside the RSEM directory.

Also make sure that RSEM correctly identified by the configuration file of this pipeline (`etc/common.cfg`). In general, it should simply be: `RSEM_DIR="$REQUIREMENTS/RSEM"`, assuming `$REQUIREMENTS` is also confirgured to point to the Requirements directory.

