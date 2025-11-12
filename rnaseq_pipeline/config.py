from typing import Optional

import luigi

# see luigi.cfg for details
class Config(luigi.Config):
    @classmethod
    def get_task_family(cls):
        return 'rnaseq_pipeline'

    OUTPUT_DIR: str = luigi.Parameter(default='pipeline-output')

    GENOMES: str = luigi.Parameter(default='genomes')
    REFERENCES: str = luigi.Parameter(default='references')
    SINGLE_CELL_REFERENCES: str = luigi.Parameter(default='references-single-cell')
    METADATA: str = luigi.Parameter(default='metadata')
    DATA: str = luigi.Parameter(default='data')
    DATAQCDIR: str = luigi.Parameter(default='data-qc')
    ALIGNDIR: str = luigi.Parameter(default='aligned')
    QUANTDIR: str = luigi.Parameter(default='quantified')
    QUANT_SINGLE_CELL_DIR: str = luigi.Parameter(default='quantified-single-cell')
    BATCHINFODIR: str = luigi.Parameter(default='batch-info')

    RSEM_DIR: str = luigi.Parameter(default='contrib/RSEM')

    rsem_calculate_expression_bin: str = luigi.Parameter(default='contrib/RSEM/rsem-calculate-expression')

    SLACK_WEBHOOK_URL: Optional[str] = luigi.OptionalParameter(default=None)
