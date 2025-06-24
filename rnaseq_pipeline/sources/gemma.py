import gzip
import logging
import os
from os.path import join

import luigi
from bioluigi.tasks.utils import DynamicTaskWithOutputMixin, DynamicWrapperTask
from luigi.util import requires

from .geo import DownloadGeoSample
from .sra import DownloadSraExperiment
from ..config import rnaseq_pipeline
from ..gemma import GemmaApi

logger = logging.getLogger(__name__)

cfg = rnaseq_pipeline()

class DownloadGemmaExperiment(DynamicTaskWithOutputMixin, DynamicWrapperTask):
    """
    Download an experiment described by a Gemma dataset using the REST API.

    Gemma itself does not retain raw data, so this task delegates the work to
    other sources.
    """
    experiment_id: str = luigi.Parameter()

    def __init__(self, *kwargs, **kwds):
        super().__init__(*kwargs, **kwds)
        self._gemma_api = GemmaApi()

    def run(self):
        data = self._gemma_api.samples(self.experiment_id)
        download_sample_tasks = []
        for sample in data:
            accession = sample['accession']['accession']
            external_database = sample['accession']['externalDatabase']['name']
            if external_database == 'GEO':
                download_sample_tasks.append(
                    DownloadGeoSample(accession, metadata=dict(experiment_id=self.experiment_id, sample_id=accession)))
            elif external_database == 'SRA':
                download_sample_tasks.append(DownloadSraExperiment(accession,
                                                                   metadata=dict(experiment_id=self.experiment_id,
                                                                                 sample_id=accession)))
            else:
                logger.warning('Downloading %s from %s is not supported.', accession, external_database)
                continue
        yield download_sample_tasks

@requires(DownloadGemmaExperiment)
class ExtractGemmaExperimentBatchInfo(luigi.Task):
    experiment_id: str

    def run(self):
        with self.output().open('w') as info_out:
            for sample in self.requires().requires():
                if not isinstance(sample, DownloadGeoSample):
                    logger.warning('Extracting batch info from %s is not supported.', sample)
                    continue

                if len(sample.output()) == 0:
                    logger.warning(
                        'GEO sample %s has no associated FASTQs from which batch information can be extracted.',
                        sample.sample_id)
                    continue

                # TODO: find a cleaner way to obtain the SRA run accession
                for fastq in sample.output():
                    # strip the two extensions (.fastq.gz)
                    fastq_name, _ = os.path.splitext(fastq.path)
                    fastq_name, _ = os.path.splitext(fastq_name)

                    fastq_id = os.path.basename(fastq_name)

                    platform_id, srx_uri = sample_geo_metadata[sample.sample_id]

                    with gzip.open(fastq.path, 'rt') as f:
                        fastq_header = f.readline().rstrip()

                    info_out.write('\t'.join([sample.sample_id, fastq_id, platform_id, srx_uri, fastq_header]) + '\n')

    def output(self):
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, 'fastq_headers', '{}.fastq-header'.format(self.experiment_id)))
