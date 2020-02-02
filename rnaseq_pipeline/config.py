import luigi

# see luigi.cfg for details
class rnaseq_pipeline(luigi.Config):
    GENOMES = luigi.Parameter()
    REFERENCES = luigi.Parameter()

    OUTPUT_DIR = luigi.Parameter()
    METADATA = luigi.Parameter()
    DATA = luigi.Parameter()
    DATAQCDIR = luigi.Parameter()
    ALIGNDIR = luigi.Parameter()
    ALIGNQCDIR = luigi.Parameter()
    QUANTDIR = luigi.Parameter()
    BATCHINFODIR = luigi.Parameter()

    PREFETCH_ARGS = luigi.Parameter()
    SRA_PUBLIC_DIR = luigi.Parameter()

    RSEM_DIR = luigi.Parameter()

    GEMMACLI = luigi.Parameter()
    GEMMA_LIB = luigi.Parameter()
    JAVA_HOME = luigi.Parameter()
    JAVA_OPTS = luigi.Parameter()

    SLACK_WEBHOOK_URL = luigi.OptionalParameter(default=None)

    def asenv(self, attrs):
        return {attr: getattr(self, attr) for attr in attrs}
