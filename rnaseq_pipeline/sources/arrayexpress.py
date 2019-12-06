import urllib
import os
from os.path import join

import luigi
import pandas as pd

from ..config import rnaseq_pipeline
from ..utils import WrapperTask

cfg = rnaseq_pipeline()

class DownloadArrayExpressFastq(luigi.Task):
    sample_id = luigi.Parameter()
    fastq_url = luigi.Parameter()

    resources = {'array_express_http_connections': 1}

    def run(self):
        with self.output().temporary_path() as dest_filename:
            urllib.urlretrieve(self.fastq_url,
                               reporthook=lambda numblocks, blocksize, totalsize: self.set_progress_percentage(100.0 * numblocks * blocksize / totalsize),
                               filename=dest_filename)

    def output(self):
        return luigi.LocalTarget(join(cfg.OUTPUT_DIR, cfg.DATA, 'arrayexpress', self.sample_id, os.path.basename(self.fastq_url)))

class DownloadArrayExpressSample(WrapperTask):
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()
    fastq_urls = luigi.ListParameter()

    def requires(self):
        return [DownloadArrayExpressFastq(self.sample_id, fastq_url) for fastq_url in self.fastq_urls]

class DownloadArrayExpressExperiment(WrapperTask):
    """
    Download all the related ArrayExpress sample to this ArrayExpress experiment.
    """
    experiment_id = luigi.Parameter()

    def requires(self):
        ae_df = pd.read_csv('http://www.ebi.ac.uk/arrayexpress/files/{0}/{0}.sdrf.txt'.format(self.experiment_id), sep='\t')
        # FIXME: properly handle the order of paired FASTQs
        return [DownloadArrayExpressSample(experiment_id=self.experiment_id, sample_id=sample_id, fastq_urls=s['Comment[FASTQ_URI]'].sort_values().tolist())
                for sample_id, s in ae_df.groupby('Comment[ENA_SAMPLE]')]
