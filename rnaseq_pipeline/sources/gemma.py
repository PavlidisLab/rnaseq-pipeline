import logging

import luigi

from bioluigi.tasks.utils import DynamicTaskWithOutputMixin, DynamicWrapperTask
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