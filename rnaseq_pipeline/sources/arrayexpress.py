import os
from functools import lru_cache
from os.path import join
from typing import List
from urllib.request import urlretrieve

import luigi
import pandas as pd
from bioluigi.tasks.utils import TaskWithOutputMixin
from luigi.task import WrapperTask

from ..config import Config
from ..platforms import IlluminaPlatform
from ..rnaseq_utils import detect_layout
from ..targets import DownloadRunTarget

cfg = Config()

@lru_cache()
def retrieve_metadata(experiment_id):
    # TODO: store metadata locally
    metadata_url = f'https://www.ebi.ac.uk/arrayexpress/files/{experiment_id}/{experiment_id}.sdrf.txt'
    ae_df = pd.read_csv(metadata_url, sep='\t')
    ae_df = ae_df[ae_df['Comment[LIBRARY_STRATEGY]'] == 'RNA-Seq']
    return ae_df

class DownloadArrayExpressFastq(luigi.Task):
    sample_id: str = luigi.Parameter()
    fastq_url: str = luigi.Parameter()

    resources = {'array_express_http_connections': 1}

    def run(self):
        with self.output().temporary_path() as dest_filename:
            urlretrieve(self.fastq_url,
                        reporthook=lambda numblocks, blocksize, totalsize: self.set_progress_percentage(
                            100.0 * numblocks * blocksize / totalsize),
                        filename=dest_filename)

    def output(self):
        return luigi.LocalTarget(
            join(cfg.OUTPUT_DIR, cfg.DATA, 'arrayexpress', self.sample_id, os.path.basename(self.fastq_url)))

class DownloadArrayExpressRun(luigi.Task):
    experiment_id: str = luigi.Parameter()
    sample_id: str = luigi.Parameter()
    run_id: str = luigi.Parameter()
    fastq_filenames: List[str] = luigi.ListParameter()
    fastq_urls: List[str] = luigi.ListParameter()

    @property
    def platform(self):
        # TODO: detect platforms from ArrayExpress metadata
        return IlluminaPlatform('HiSeq 2500')

    def run(self):
        ae_df = retrieve_metadata(self.experiment_id)
        run_metadata = ae_df[ae_df['ENA_RUN'] == self.run_id]

        yield [DownloadArrayExpressRun(experiment_id=self.experiment_id, sample_id=self.sample_id, run_id=run_id,
                                       fastq_filenames=s['SUBMITTED_FILE_NAME'], fastq_urls=s['FASTQ_URI'])
               for run_id, s in ae_df.groupby('Comment[ENA_RUN')]

    def requires(self):
        return [DownloadArrayExpressFastq(self.sample_id, fastq_url) for fastq_url in self.fastq_urls]

    def output(self):
        return DownloadRunTarget(self.run_id, [i.path for i in self.input()],
                                 detect_layout(self.run_id, self.fastq_filenames))

class DownloadArrayExpressSample(luigi.Task):
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()

    @property
    def platform(self):
        return IlluminaPlatform('HiSeq 2500')

    def run(self):
        ae_df = retrieve_metadata(self.experiment_id)
        sample_metadata = ae_df[ae_df['ENA_SAMPLE'] == self.sample_id]
        yield [DownloadArrayExpressRun(experiment_id=self.experiment_id, sample_id=self.sample_id, run_id=run_id)
               for run_id, s in sample_metadata.groupby('Comment[ENA_RUN]')]

class DownloadArrayExpressExperiment(TaskWithOutputMixin, WrapperTask):
    """
    Download all the related ArrayExpress sample to this ArrayExpress experiment.
    """
    experiment_id = luigi.Parameter()

    def run(self):
        ae_df = retrieve_metadata(self.experiment_id)
        # FIXME: properly handle the order of paired FASTQs
        yield [DownloadArrayExpressSample(experiment_id=self.experiment_id, sample_id=sample_id)
               for sample_id, s in ae_df.groupby('Comment[ENA_SAMPLE]')]
