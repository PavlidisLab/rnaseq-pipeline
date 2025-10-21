from typing import Optional

import luigi

# see luigi.cfg for details
class rnaseq_pipeline(luigi.Config):
    task_namespace = ''

    GENOMES: str = luigi.Parameter()

    OUTPUT_DIR: str = luigi.Parameter()
    REFERENCES: str = luigi.Parameter()
    SINGLE_CELL_REFERENCES: str = luigi.Parameter()
    METADATA: str = luigi.Parameter()
    DATA: str = luigi.Parameter()
    DATAQCDIR: str = luigi.Parameter()
    ALIGNDIR: str = luigi.Parameter()
    QUANTDIR: str = luigi.Parameter()
    BATCHINFODIR: str = luigi.Parameter()

    RSEM_DIR: str = luigi.Parameter()

    rsem_calculate_expression_bin: str = luigi.Parameter()

    SLACK_WEBHOOK_URL: Optional[str] = luigi.OptionalParameter(default=None)
