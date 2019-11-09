import datetime
import os
from os.path import join
from subprocess import check_output
import urllib
import tarfile
import shlex
from glob import glob
import tempfile

import pandas as pd
import luigi
import luigi.task
from luigi.contrib.external_program import ExternalProgramTask
from bioluigi.scheduled_external_program import ScheduledExternalProgramTask

from scheduler.miniml_utils import extract_rnaseq_gsm

class WrapperTask(luigi.WrapperTask):
    """
    Extension to luigi.WrapperTask to inherit the dependencies outputs as well
    as the completion condition.
    """
    def output(self):
        return luigi.task.getpaths(self.requires())

# see luigi.cfg for details
class rnaseq_pipeline(luigi.Config):
    ASSEMBLIES = luigi.Parameter()

    OUTPUT_DIR = luigi.Parameter()
    METADATA = luigi.Parameter()
    DATA = luigi.Parameter()
    DATAQCDIR = luigi.Parameter()
    ALIGNDIR = luigi.Parameter()
    ALIGNQCDIR = luigi.Parameter()
    QUANTDIR = luigi.Parameter()

    PREFETCH_EXE = luigi.Parameter()
    PREFETCH_ARGS = luigi.Parameter()
    SRA_PUBLIC_DIR = luigi.Parameter()

    FASTQC_EXE = luigi.Parameter()

    FASTQDUMP_EXE = luigi.Parameter()

    STAR_PATH = luigi.Parameter()

    RSEM_DIR = luigi.Parameter()

    GEMMACLI = luigi.Parameter()
    GEMMA_LIB = luigi.Parameter()
    JAVA_HOME = luigi.Parameter()
    JAVA_OPTS = luigi.Parameter()

    def asenv(self, attrs):
        return {attr: getattr(self, attr) for attr in attrs}

class PrefetchSRR(ExternalProgramTask):
    """
    Prefetch a SRR sample using prefetch
    """
    srr = luigi.Parameter()

    # FIXME: prefetch sometimes fail and will leave heavy temporary files
    # behind
    retry_count = 5

    def program_args(self):
        return [rnaseq_pipeline().PREFETCH_EXE] + shlex.split(rnaseq_pipeline().PREFETCH_ARGS) + [self.srr]

    def output(self):
        return luigi.LocalTarget(join(rnaseq_pipeline().SRA_PUBLIC_DIR, '{}.sra'.format(self.srr)))

class ExtractSRR(ScheduledExternalProgramTask):
    """
    Download FASTQ
    """
    gse = luigi.Parameter()
    gsm = luigi.Parameter()
    srr = luigi.Parameter()

    paired_reads = luigi.BoolParameter()

    scheduler = 'slurm'
    scheduler_extra_args = ['--partition', 'All']
    walltime = datetime.timedelta(hours=2)
    cpus = 1
    memory = 1

    def requires(self):
        return PrefetchSRR(self.srr)

    def program_args(self):
        # FIXME: this is not atomic
        # FIXME: use fasterq-dump
        return [rnaseq_pipeline().FASTQDUMP_EXE,
                '--gzip',
                '--clip',
                '--skip-technical',
                '--readids',
                '--dumpbase',
                '--split-files',
                '--outdir', join(rnaseq_pipeline().OUTPUT_DIR, rnaseq_pipeline().DATA, self.gse, self.gsm),
                self.input().path]

    def output(self):
        if self.paired_reads:
            return [luigi.LocalTarget(join(rnaseq_pipeline().OUTPUT_DIR, rnaseq_pipeline().DATA, self.gse, self.gsm, self.srr + '_1.fastq.gz')),
                    luigi.LocalTarget(join(rnaseq_pipeline().OUTPUT_DIR, rnaseq_pipeline().DATA, self.gse, self.gsm, self.srr + '_2.fastq.gz'))]
        else:
            return [luigi.LocalTarget(join(rnaseq_pipeline().OUTPUT_DIR, rnaseq_pipeline().DATA, self.gse, self.gsm, self.srr + '_1.fastq.gz'))]

class DownloadGSMMetadata(luigi.Task):
    gsm = luigi.Parameter()

    resources = {'geo_http_connections': 1}

    def run(self):
        with self.output().temporary_path() as dest_filename:
            urllib.urlretrieve('https://trace.ensembl98.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&amp;db=sra&amp;rettype=runinfo&amp;term={}'.format(self.gsm),
                    filename=dest_filename)

    def output(self):
        return luigi.LocalTarget(join(rnaseq_pipeline().OUTPUT_DIR, rnaseq_pipeline().METADATA, '{}.csv'.format(self.gsm)))

class DownloadGSM(luigi.Task):
    """
    Download all SRR related to a GSM
    """
    gse = luigi.Parameter()
    gsm = luigi.Parameter()

    def requires(self):
        return DownloadGSMMetadata(self.gsm)

    def run(self):
        # this will raise an error of no samples are related
        df = pd.read_csv(self.input().path)

        # Some GSM happen to have many related samples and we cannot
        # realistically investigate why that is. Our best bet at this point
        # is that the latest SRR properly represents the sample
        latest_run = df.sort_values('Run', ascending=False).iloc[0]

        yield ExtractSRR(self.gse, self.gsm, latest_run.Run, latest_run.LibraryLayout == 'PAIRED')

    def output(self):
        if self.requires().complete():
            try:
                return next(self.run()).output()
            except pd.errors.EmptyDataError:
                return []
        else:
            return []

class DownloadGSEMetadata(luigi.Task):
    gse = luigi.Parameter()

    resources = {'geo_ftp_connections': 1}

    def run(self):
        destdir = os.path.dirname(self.output().path)
        metadata_xml_tgz = join(destdir, '{}_family.xml.tgz'.format(self.gse))
        metadata_xml = join(destdir, '{}_family.xml'.format(self.gse))

        # download compressed metadata
        urllib.urlretrieve('ftp://ftp.ensembl98.nlm.nih.gov/geo/series/{0}/{1}/miniml/{1}_family.xml.tgz'.format(self.gse[:-3] + 'nnn', self.gse),
                           filename=metadata_xml_tgz)

        # extract metadata
        # FIXME: this is not atomic
        with tarfile.open(metadata_xml_tgz, 'r:gz') as tf:
            tf.extract('{}_family.xml'.format(self.gse), destdir)

    def output(self):
        return luigi.LocalTarget(join(rnaseq_pipeline().OUTPUT_DIR, rnaseq_pipeline().METADATA, '{}_family.xml'.format(self.gse)))

class DownloadGSE(luigi.Task):
    """
    Download all GSM related to a GSE
    """
    gse = luigi.Parameter()

    def requires(self):
        return DownloadGSEMetadata(self.gse)

    def run(self):
        gsms = extract_rnaseq_gsm(self.input().path)
        if not gsms:
            raise ValueError('No RNA-Seq samples relates to {}.'.format(self.gse))
        yield [DownloadGSM(self.gse, gsm) for gsm in gsms]

    def output(self):
        if self.requires().complete():
            # FIXME: this is ugly
            try:
                return [task.output() for task in next(self.run())]
            except:
                return []
        else:
            return []

class DownloadArrayExpressFastq(luigi.Task):
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()
    fastq_url = luigi.Parameter()

    resources = {'array_express_http_connections': 1}

    def run(self):
        with self.output().temporary_path() as dest_filename:
            urllib.urlretrieve(self.fastq_url, filename=dest_filename)

    def output(self):
        return luigi.LocalTarget(join(rnaseq_pipeline().OUTPUT_DIR, rnaseq_pipeline().DATA, self.experiment_id, self.sample_id, os.path.basename(self.fastq_url)))

class DownloadArrayExpressSample(WrapperTask):
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()
    fastq_urls = luigi.ListParameter()

    def requires(self):
        return [DownloadArrayExpressFastq(self.experiment_id,  self.sample_id, fastq_url) for fastq_url in self.fastq_urls]

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

class DownloadLocalSample(luigi.Task):
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()

    def output(self):
        # we sort to make sure that pair ends are in correct order
        return [luigi.LocalTarget(f) for f in sorted(glob(join(rnaseq_pipeline().OUTPUT_DIR, rnaseq_pipeline().DATA, self.experiment_id, self.sample_id, '*.fastq.gz')))]

class DownloadLocalExperiment(WrapperTask):
    experiment_id = luigi.Parameter()

    def requires(self):
        return [DownloadLocalSample(self.experiment_id, os.path.basename(f))
                for f in glob(join(rnaseq_pipeline().OUTPUT_DIR, rnaseq_pipeline().DATA, self.experiment_id, '*'))]

class DownloadSample(WrapperTask):
    """
    This is a generic task for downloading an individual sample in an
    experiment.
    """
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()

    def requires(self):
        if self.experiment_id.startswith('GSE'):
            return DownloadGSM(self.experiment_id, self.sample_id)
        elif self.experiment_id.startswith('E-MTAB'):
            return DownloadArrayExpressSample(self.experiment_id, self.sample_id)
        else:
            return DownloadLocalSample(self.experiment_id, self.sample_id)

class DownloadExperiment(WrapperTask):
    """
    This is a generic task that detects which kind of experiment is intended to
    be downloaded so that downstream tasks can process regardless of the data
    source.
    """
    experiment_id = luigi.Parameter()

    def requires(self):
        if self.experiment_id.startswith('GSE'):
            return DownloadGSE(self.experiment_id)
        elif self.experiment_id.startswith('E-MTAB'):
            return DownloadArrayExpressExperiment(self.experiment_id)
        else:
            return DownloadLocalExperiment(self.experiment_id)

class QualityControlSample(ScheduledExternalProgramTask):
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()

    scheduler = 'slurm'
    scheduler_extra_args = ['--partition', 'All']
    walltime = datetime.timedelta(hours=2)
    cpus = 1
    memory = 2

    def requires(self):
        return DownloadSample(self.experiment_id, self.sample_id)

    def program_args(self):
        args = [rnaseq_pipeline().FASTQC_EXE, '--outdir', os.path.dirname(self.output()[0].path)]

        args.extend(f.path for f in self.input())

        return args

    def run(self):
        for out in self.output():
            out.makedirs()
        return super(QualityControlSample, self).run()

    def output(self):
        destdir = join(rnaseq_pipeline().OUTPUT_DIR, rnaseq_pipeline().DATAQCDIR, self.experiment_id, self.sample_id)
        # FIXME: replace should be anchored end of string
        return [luigi.LocalTarget(join(destdir, '{}_fastqc.html'.format(os.path.basename(f.path).replace('.fastq.gz', ''))))
                    for f in self.input()]

class PrepareReference(ExternalProgramTask):
    """
    Prepare a STAR/RSEM reference.
    """
    taxon = luigi.Parameter(default='human')
    genome_build = luigi.Parameter(default='hg38')
    reference_build = luigi.Parameter(default='ensembl98')

    resources = {'cpus': 16, 'memory': 32}

    def program_args(self):
        return [join(rnaseq_pipeline().RSEM_DIR, 'rsem-prepare-reference'),
                join(rnaseq_pipeline().ASSEMBLIES, '{}_{}'.format(self.genome_build, self.reference_build, '*.gtf')),
                '--star',
                '--star-path', rnaseq_pipeline().STAR_PATH,
                '-p', self.resources['cpu'],
                join(rnaseq_pipeline().ASSEMBLIES, '{}_{}'.format(self.genome_build, self.reference_build, 'primary_assembly.fa')),
                self.output().path]

    def output(self):
        return luigi.LocalTarget(join(rnaseq_pipeline().ASSEMBLIES, 'runtime/{}_{}/{}_0'.format(self.genome_build, self.reference_build, self.taxon)))

class AlignSample(ScheduledExternalProgramTask):
    """
    The output of the task is a pair of isoform and gene quantification results
    processed by STAR and RSEM.
    """
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()

    taxon = luigi.Parameter(default='human')
    genome_build = luigi.Parameter(default='hg38')
    reference_build = luigi.Parameter(default='ensembl98')

    # TODO: handle strand-specific reads
    strand_specific = luigi.BoolParameter(default=False)

    scheduler = 'slurm'
    scheduler_extra_args = ['--partition', 'All']
    walltime = datetime.timedelta(days=1)
    cpus = 8
    memory = 32

    def requires(self):
        return [DownloadSample(self.experiment_id, self.sample_id), QualityControlSample(self.experiment_id, self.sample_id)]

    def run(self):
        for out in self.output():
            out.makedirs()
        return super(AlignSample, self).run()

    def program_args(self):
        args = [join(rnaseq_pipeline().RSEM_DIR, 'rsem-calculate-expression'), '-p', self.cpus]

        # FIXME: use local scratch for temporary files
        args.extend([
            '--time',
            '--star',
            '--star-path', rnaseq_pipeline().STAR_PATH,
            '--star-gzipped-read-file')

        if self.strand_specific:
            args.append('--strand-specific')

        sample_run, _ = self.input()

        fastqs = [mate.path for mate in sample_run]

        if len(fastqs) == 1:
            pass # single-ended (default)
        elif len(fastqs) == 2:
            args.append('--paired-end')
        else:
            raise ValueError('More than two input FASTQs are not supported.')

        args.extend(fastqs)

        # reference for alignments and quantifications
        args.append(join(rnaseq_pipeline().ASSEMBLIES, 'runtime/{}_{}/{}_0'.format(self.genome_build, self.reference_build, self.taxon)))

        # output prefix
        args.append(join(os.path.dirname(self.output()[0].path), self.sample_id))

        return args

    def output(self):
        destdir = join(rnaseq_pipeline().OUTPUT_DIR, rnaseq_pipeline().ALIGNDIR, '{}_{}'.format(self.genome_build, self.reference_build), self.experiment_id)
        return [luigi.LocalTarget(join(destdir, '{}.isoforms.results'.format(self.sample_id))),
                luigi.LocalTarget(join(destdir, '{}.genes.results'.format(self.sample_id)))]

class AlignExperiment(luigi.Task):
    """
    Align all the samples in a given experiment.

    The output is one sample alignment output per sample contained in the
    experiment.
    """
    experiment_id = luigi.Parameter()

    taxon = luigi.Parameter(default='human')
    genome_build = luigi.Parameter(default='hg38')
    reference_build = luigi.Parameter(default='ensembl98')

    def requires(self):
        return DownloadExperiment(self.experiment_id)

    def run(self):
        # FIXME: do this better
        yield [AlignSample(self.experiment_id, os.path.basename(os.path.dirname(sample[0].path)), self.taxon, self.genome_build, self.reference_build)
                    for sample in self.input()]

    def output(self):
        try:
            # FIXME: this is ugly
            return [task.output() for task in next(self.run())]
        except:
            return []

class CountExperiment(luigi.Task):
    """
    Combine the RSEM quantifications results from all the samples in a given
    experiment.

    The output is two matrices: counts and FPKM.
    """
    experiment_id = luigi.Parameter()

    taxon = luigi.Parameter(default='human')
    genome_build = luigi.Parameter(default='hg38')
    reference_build = luigi.Parameter(default='ensembl98')

    resources = {'cpus': 1}

    def requires(self):
        return AlignExperiment(self.experiment_id, self.taxon, self.genome_build, self.reference_build)

    def run(self):
        # FIXME: this is a hack
        keys = [align_task.sample_id for align_task in next(self.requires().run())]
        counts_df = pd.concat([pd.read_csv(gene.path, sep='\t', index_col=0).expected_count
            for isoform, gene in self.input()], keys=keys, axis=1)
        fpkm_df = pd.concat([pd.read_csv(gene.path, sep='\t', index_col=0).FPKM
            for isoform, gene in self.input()], keys=keys, axis=1)

        with self.output()[0].open('w') as f:
            counts_df.to_csv(f, sep='\t')

        with self.output()[1].open('w') as f:
            fpkm_df.to_csv(f, sep='\t')

    def output(self):
        destdir = join(rnaseq_pipeline().OUTPUT_DIR, rnaseq_pipeline().QUANTDIR, '{}_{}'.format(self.genome_build, self.reference_build))
        return [luigi.LocalTarget(join(destdir, '{}_counts.genes'.format(self.experiment_id))),
                luigi.LocalTarget(join(destdir, '{}_fpkm.genes'.format(self.experiment_id)))]

class SubmitExperimentToGemma(ExternalProgramTask):
    """
    Submit an experiment to Gemma.

    This will trigger the whole pipeline.

    The output is a confirmation that the data is effectively in Gemma.
    """
    experiment_id = luigi.Parameter()

    taxon = luigi.Parameter(default='human')
    genome_build = luigi.Parameter(default='hg38')
    reference_build = luigi.Parameter(default='ensembl98')

    resources = {'gemma_connections': 1}

    def requires(self):
        return CountExperiment(self.experiment_id, self.taxon, self.genome_build, self.reference_build)

    def program_environment(self):
        return rnaseq_pipeline().asenv(['GEMMA_LIB', 'JAVA_HOME', 'JAVA_OPTS'])

    def program_args(self):
        count, fpkm = self.input()
        return [rnaseq_pipeline().GEMMACLI, 'rnaseqDataAdd',
                '-u', os.getenv('GEMMAUSERNAME'),
                '-p', os.getenv('GEMMAPASSWORD'),
                '-e', self.experiment_id,
                '-a', 'Generic_{}_ensemblIds'.format(self.taxon),
                '-count', count.path,
                '-rpkm', fpkm.path]

    def run(self):
        ret = super(SubmitExperimentToGemma, self).run()
        with self.output().open('w'):
            pass
        return ret

    def output(self):
        return luigi.LocalTarget(join(rnaseq_pipeline().OUTPUT_DIR, 'submitted', '{}_{}'.format(self.genome_build, self.reference_build), self.experiment_id))

class SubmitExperimentsFromFileToGemma(WrapperTask):
    input_file = luigi.Parameter()
    def requires(self):
        return [SubmitExperimentToGemma(row.experiment_id, row.taxon, row.genome_build, row.reference_build)
                    for _, row in pd.read_csv(self.input_file, sep='\t').iterrows()]
