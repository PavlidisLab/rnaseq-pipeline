import luigi
from luigi.contrib.external_program import ExternalProgramTask
import os
from subprocess import call, check_output
from shutil import copyfile
from base64 import b64encode
import uuid
from os.path import join
from gemmaclient import GemmaClientAPI
import pandas as pd
import urllib
from subprocess import check_call
import gzip
import tarfile
from miniml_utils import extract_rnaseq_gsm

# see luigi.cfg for details
class rnaseq_pipeline(luigi.Config):
    MODES = luigi.Parameter()
    SCRIPTS = luigi.Parameter()
    USERNAME = luigi.Parameter()
    ROOT_DIR = luigi.Parameter()
    RESULTS_DIR = luigi.Parameter()
    SCRATCH_DIR = luigi.Parameter()
    ASSEMBLIES = luigi.Parameter()
    REQUIREMENTS = luigi.Parameter()
    SCRIPTS = luigi.Parameter()
    DATA = luigi.Parameter()
    BAM_DIR = luigi.Parameter()
    FASTQHEADERS_DIR = luigi.Parameter()
    BACKFILL_DIR = luigi.Parameter()
    LOGS = luigi.Parameter()
    METADATA = luigi.Parameter()
    METADATA_DELIM = luigi.Parameter()
    MDL = luigi.Parameter()
    VENV = luigi.Parameter()
    QUANTDIR = luigi.Parameter()
    ERCCDIR = luigi.Parameter()
    TMPDIR = luigi.Parameter()
    COUNTDIR = luigi.Parameter()
    STAR_KEEP_BAM = luigi.Parameter()
    REPROCESS = luigi.Parameter()
    CLEARLOGS = luigi.Parameter()
    WONDERDUMP_EXE = luigi.Parameter()
    FASTQC_EXE = luigi.Parameter()
    FASTQDUMP_EXE = luigi.Parameter()
    FASTQDUMP_SPLIT = luigi.Parameter()
    FASTQDUMP_READIDS = luigi.Parameter()
    FASTQDUMP_BACKFILL = luigi.Parameter()
    PREFETCH_EXE = luigi.Parameter()
    PREFETCH_MAXSIZE = luigi.Parameter()
    SRA_CACHE = luigi.Parameter()
    MULTIQC_EXE = luigi.Parameter()
    BAMTOFASTQ = luigi.Parameter()
    SEQPURGE = luigi.Parameter()
    RSEM_DIR = luigi.Parameter()
    STAR_PATH = luigi.Parameter()
    STAR_EXE = luigi.Parameter()
    REFERENCE_BUILD = luigi.Parameter()
    STAR_DEFAULT_REFERENCE = luigi.Parameter()
    STAR_REFERENCE_GTF = luigi.Parameter()
    STAR_MAX_BAM_RAM = luigi.Parameter()
    STAR_SAM_MAPPING = luigi.Parameter()
    # STAR_SAM_MAPPING = luigi.Parameter()
    STAR_SHARED_MEMORY = luigi.Parameter()
    NCPU = luigi.Parameter()
    NCPU_ALL = luigi.Parameter()
    NCPU_NICE = luigi.Parameter()
    NJOBS = luigi.Parameter()
    NTASKS = luigi.Parameter()
    MACHINES = luigi.Parameter()
    MACHINES_DOWNLOAD = luigi.Parameter()
    DEFAULT_MATE_SOURCE = luigi.Parameter()
    DEFAULT_MATE_REPLACEMENT = luigi.Parameter()

    def asenv(self, attrs):
        return {attr: getattr(self, attr) for attr in attrs}

class BaseTask(luigi.Task):
    here = os.path.dirname(os.path.realpath(__file__))
    commit_dir = os.path.dirname(os.path.realpath(__file__)) + "/commit"
    wd = here + "/../Pipelines/rsem/"
    MODES = rnaseq_pipeline().MODES
    SCRIPTS = rnaseq_pipeline().SCRIPTS

    # Para meters
    gse = luigi.Parameter()
    nsamples = luigi.IntParameter(default=0)
    scope = luigi.Parameter(default="genes")
    ignorecommit = luigi.Parameter(default=False)
    allowsuper = luigi.Parameter(default=False)

class PrefetchSRR(ExternalProgramTask):
    """
    Prefetch a SRR sample using prefetch
    """
    srr = luigi.Parameter()

    # FIXME: prefetch sometimes fail and will leave heavy temporary files
    # behind
    retry_count = 5

    resources = {'cpu': 1}

    def program_environment(self):
        # ensures that SRA Toolkit dumps content in scratch
        return {'HOME': '/cosmos/scratch'}

    def program_args(self):
        return [rnaseq_pipeline().PREFETCH_EXE, self.srr]

    def output(self):
        return luigi.LocalTarget(join(rnaseq_pipeline().SRA_CACHE, '{}.sra'.format(self.srr)))

class ExtractSRR(ExternalProgramTask):
    """
    Download FASTQ
    """
    gse = luigi.Parameter()
    gsm = luigi.Parameter()
    srr = luigi.Parameter()

    resources = {'cpu': 1}

    def requires(self):
        return PrefetchSRR(self.srr)

    def program_environment(self):
        # ensures that SRA Toolkit dumps content in scratch
        return {'HOME': '/cosmos/scratch'}

    def program_args(self):
        return [rnaseq_pipeline().PREFETCH_EXE, self.srr]

    def program_args(self):
        # FIXME: this is not atomic
        return [rnaseq_pipeline().FASTQDUMP_EXE,
                '--gzip', '--clip',
                '--skip-technical',
                rnaseq_pipeline().FASTQDUMP_READIDS,
                '--dumpbase',
                rnaseq_pipeline().FASTQDUMP_SPLIT,
                '--outdir', os.path.dirname(self.output().path),
                self.input().path]

    def output(self):
        return luigi.LocalTarget(join(rnaseq_pipeline().DATA, self.gse, self.gsm, self.srr + '_1.fastq.gz'))

class DownloadGSMMetadata(luigi.Task):
    gse = luigi.Parameter()
    gsm = luigi.Parameter()

    def run(self):
        # TODO: find a nicer way to query this data
        with self.output().temporary_path() as dest_filename:
            urllib.urlretrieve('https://trace.ncbi.nlm.nih.gov/Traces/sra/sra.cgi?save=efetch&amp;db=sra&amp;rettype=runinfo&amp;term={}'.format(self.gsm),
                               filename=dest_filename)

    def output(self):
        return luigi.LocalTarget(join(rnaseq_pipeline().DATA, self.gse, 'METADATA', '{}.csv'.format(self.gsm)))

class DownloadGSM(ExternalProgramTask):
    """
    Download all SRR related to a GSM
    """
    gse = luigi.Parameter()
    gsm = luigi.Parameter()

    def requires(self):
        return DownloadGSMMetadata(self.gse, self.gsm)

    def run(self):
        # find all SRA runs associated to this GSM
        df = pd.read_csv(self.input().path)
        yield [ExtractSRR(self.gse, self.gsm, run.Run) for _, run in df.iterrows()]

    def output(self):
        # this needs to be satisfied first
        if not self.input().exists():
            return self.input()

        df = pd.read_csv(self.input().path)
        return [ExtractSRR(self.gse, self.gsm, run.Run).output()
                    for _, run in df.iterrows()]

class DownloadGSEMetadata(luigi.Task):
    gse = luigi.Parameter()

    def run(self):
        # download compressed metadata
        if not os.path.exists(metadata_xml_tgz):
            # ensure that the download path exists
            self.output().makedirs()
            with self.output().temporary_path() as dest_filename:
                urllib.urlretrieve('ftp://ftp.ncbi.nlm.nih.gov/geo/series/{0}/{1}/miniml/{1}_family.xml.tgz'.format(self.gse[:-3] + 'nnn', self.gse),
                                   filename=dest_filename)

        # extract metadata
        with tarfile.open(metadata_xml_tgz, 'r:gz') as tf:
            tf.extract('{}_family.xml'.format(self.gse), os.path.dirname(self.output().path))

    def output(self):
        return luigi.LocalTarget(join(rnaseq_pipeline().DATA, self.gse, 'METADATA', '{}_family.xml'.format(self.gse)))

class DownloadGSE(luigi.Task):
    """
    Download all GSM related to a GSE
    """
    gse = luigi.Parameter()

    def requires(self):
        return DownloadGSEMetadata(self.gse)

    def run(self):
        # parse MINiML format to get GSM and download each of them
        yield [DownloadGSM(self.gse, gsm)
                for gsm in extract_rnaseq_gsm(self.input().path)]

    def output(self):
        # this needs to be satisfied first
        if not self.input().exists():
            return self.input()
        else:
            return [DownloadGSM(self.gse, gsm).output()
                        for gsm in extract_rnaseq_gsm(self.input().path)]

class DownloadArrayExpressSample(luigi.Task):
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()
    # TODO: remove this URL
    sample_url = luigi.Parameter()

    def run(self):
        with self.output().temporary_path() as dest_filename:
            urllib.urlretrieve(self.sample_url, filename=dest_filename)

    def output(self):
        return luigi.LocalTarget(join(rnaseq_pipeline().DATA, self.experiment_id, self.sample_id, os.path.basename(self.sample_url)))

class DownloadArrayExpressExperiment(luigi.Task):
    """
    Download all the related ArrayExpress sample to this ArrayExpress experiment.
    """
    experiment_id = luigi.Parameter()
    def run(self):
        ae_df = pd.read_csv('http://www.ebi.ac.uk/arrayexpress/files/{0}/{0}.sdrf.txt'.format(self.experiment_id), sep='\t')
        yield [DownloadArrayExpressSample(experiment_id=self.experiment_id, sample_id=s['Comment[ENA_RUN]'], sample_url=s['Comment[FASTQ_URI]'])
                for ix, s in ae_df.iterrows()]

class DownloadSample(luigi.Task):
    """
    This is a generic task for downloading an individual sample in an
    experiment.
    """
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()

    def requires(self):
        if self.experiment_id.startswith('GSE'):
            return DownloadGSM(self.experiment_id, self.sample_id)
        else:
            return DownloadArrayExpressSample(self.experiment_id, self.sample_id)

    def output(self):
        if self.experiment_id.startswith('GSE'):
            return DownloadGSM(self.experiment_id, self.sample_id).output()
        else:
            return DownloadArrayExpressSample(self.experiment_id, self.sample_id).output()

class DownloadExperiment(luigi.Task):
    """
    This is a generic task that detects which kind of experiment is intended to
    be downloaded so that downstream tasks can process regardless of the data
    source.
    """
    experiment_id = luigi.Parameter()
    def requires(self):
        if self.experiment_id.startswith('GSE'):
            return DownloadGSE(self.experiment_id)
        else:
            return DownloadArrayExpressExperiment(self.experiment_id)

    def output(self):
        if self.experiment_id.startswith('GSE'):
            return DownloadGSE(self.experiment_id).output()
        else:
            return DownloadArrayExpressExperiment(self.experiment_id).output()

class QcExperiment(ExternalProgramTask):
    experiment_id = luigi.Parameter()
    nsamples = luigi.IntParameter()

    resources = {'cpu': 1}

    def requires(self):
        return DownloadExperiment(self.experiment_id)

    def program_environment(self):
        return rnaseq_pipeline().asenv(['DATA', 'METADATA', 'MDL', 'DEFAULT_MATE_SOURCE', 'DEFAULT_MATE_REPLACEMENT', 'MODES'])

    def program_args(self):
        return [join(rnaseq_pipeline().SCRIPTS, 'qc_download.sh'), self.experiment_id, self.nsamples]

    def output(self):
        return luigi.LocalTarget(join(rnaseq_pipeline().DATA, self.experiment_id, 'qc-done'))

class AlignSample(ExternalProgramTask):
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()

    reference = luigi.Parameter(default='mouse')
    reference_build = luigi.Parameter(default='ensembl38')

    # this setup should allow us to run 16 parallel jobs
    resources = {'cpu': 4, 'mem': 32}

    def requires(self):
        # FIXME: put this in run
        self.output()[0].makedirs()
        check_output(['mkdir', '-p', join(rnaseq_pipeline().TMPDIR, self.experiment_id, self.sample_id)])
        return DownloadSample(self.experiment_id, self.sample_id)

    def program_args(self):
        args = [join(rnaseq_pipeline().RSEM_DIR, 'rsem-calculate-expression'), '-p', self.resources['cpu']]

        args.extend([
            '--time',
            '--star',
            '--star-path', rnaseq_pipeline().STAR_PATH,
            '--star-gzipped-read-file',
            '--temporary-folder', join(rnaseq_pipeline().TMPDIR, self.experiment_id, self.sample_id)])

        # FIXME
        if len(self.input()) == 1:
            pass # single-ended (default)
        elif len(self.input()) == 2:
            args.append('--paired-end')
        else:
            raise ValueError('More than 2 input FASTQs are not supported.')

        for fastq in self.input():
            args.append(fastq.path)

        # STAR reference
        args.append('/space/grp/Pipelines/rnaseq-pipeline/Assemblies/runtime/{0}_ref{1}/{0}_0'.format(self.reference, self.reference_build))

        # output
        args.append(join(rnaseq_pipeline().QUANTDIR, self.experiment_id, self.sample_id))

        args.extend([
            '--star-shared-memory', rnaseq_pipeline().STAR_SHARED_MEMORY,
            '--keep-intermediate-files'])

        return args

    def output(self):
        destdir = join(rnaseq_pipeline().QUANTDIR, self.experiment_id)
        return [luigi.LocalTarget(join(destdir, '{}.isoforms.results'.format(self.sample_id))),
                luigi.LocalTarget(join(destdir, '{}.genes.results'.format(self.sample_id)))]

class AlignExperiment(luigi.Task):
    experiment_id = luigi.Parameter()
    nsamples = luigi.IntParameter()

    reference = luigi.Parameter(default='mouse')
    reference_build = luigi.Parameter(default='ensembl38')

    def requires(self):
        return QcExperiment(self.experiment_id, self.nsamples)

    def run(self):
        # FIXME: this is a hack, really, and it will not work with ArrayExpress
        yield [AlignSample(self.experiment_id, sample.gsm, self.reference, self.reference_build)
                    for sample in list(DownloadExperiment(self.experiment_id).requires().run())[0]]

    def output(self):
        return [AlignSample(self.experiment_id, sample.gsm, self.reference, self.reference_build).output()
                    for sample in list(DownloadExperiment(self.experiment_id).requires().run())[0]]

class CountExperiment(ExternalProgramTask):
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()

    reference = luigi.Parameter(default='mouse')
    reference_build = luigi.Parameter(default='ensembl38')

    scope = luigi.Parameter(default='genes')

    resources = {'cpu': 1}

    def requires(self):
        return AlignExperiment(self.experiment_id, self.sample_id, self.reference, self.reference_build)

    def program_args(self):
        return [join(rnaseq_pipeline().ROOT_DIR, 'Pipelines/rsem/rsem_count.sh'), join(rnaseq_pipeline().QUANTDIR, self.experiment_id), self.scope]

    def program_environment(self):
        return rnaseq_pipeline().asenv(['RSEM_DIR'])

    def output(self):
        destdir = join(rnaseq_pipeline().QUANTDIR, self.experiment_id)
        return [luigi.LocalTarget(join(destdir, '{}.countMatrix'.format(self.sample_id))),
                luigi.LocalTarget(join(destdir, '{}.tpmMatrix'.format(self.sample_id))),
                luigi.LocalTarget(join(destdir, '{}.fpkmMatrix'.format(self.sample_id)))]

class LoadGemmaGSE(BaseTask):
    """
    Load into Gemma.
    """
    method = None
    method_args = None

    def init(self):
        """
        Set CLI method.
        """
        try:
            # Check if GEMMACLI is set, otherwise problems will happen later.
            foo1 = rnaseq_pipeline().GEMMACLI.split(" ")

            # foo2 = rnaseq_pipeline().GEMMAUSERNAME")
            # foo3 = rnaseq_pipeline().GEMMAPASSWORD")
            # if None in [foo1, foo2, foo3]:
            #     raise Exception("At least one Gemma parameter is None!")

        except Exception as e:
            print "$GEMMACLI/GEMMAUSERNAME/GEMMPASSWORD appear to not all be set. Please set environment variables."
            raise e

        try:
            PATH = rnaseq_pipeline().COUNTDIR
            TAXONS = ['human', 'mouse', 'rat']
            MODES = rnaseq_pipeline().MODES.split(",")
            SCRIPTS = rnaseq_pipeline().SCRIPTS
            taxon = None

            for taxon_ in MODES :
                if taxon_ in TAXONS:
                    taxon = taxon_
                    break

            print "Using scripts from", SCRIPTS
            print "Loading matrices from", PATH
            print "Taxon:", taxon
            self.method = ["python", SCRIPTS+"/load_rnaseq_to_gemma.py"]
            self.method_args = ["--shortname", self.gse, "--taxon", taxon, "--path", PATH]

        except Exception as e:
            print "Error accessing environment variables."
            raise e

        print "INFO: Method => " + str(self.method_args)

    def requires(self):
        self.init()
        return CheckGemmaGSE(self.gse, self.nsamples)

    def output(self):
        uniqueID=""
        if int(self.ignorecommit) == 1:
            print "INFO: Ignoring previous commits."
            uniqueID = "_" + str(uuid.uuid1()) # Skipping commit logic.

        return luigi.LocalTarget(self.commit_dir + "/loadgemma" + uniqueID  + "_%s.tsv" % self.gse)

    def run(self):
        job = self.method + self.method_args

        # Call job
        try:
            print "Attempting to load experiment for " + self.gse
            print "JAVA_HOME:", rnaseq_pipeline().JAVA_HOME
            ret = call(job, env=os.environ.copy())
            print "Done."
        except Exception as e:
            print "EXCEPTION: Could not load Gemma experiment with '" + " ".join(job) + "' ."
            ret = -1

        if ret:
            print "Error code", ret, "."
            print ""
            exit( "LoadGemmaGSE failed for request '{}' with exit code {}.".format( " ".join(job), ret) )

        # Commit output
        with self.output().open('w') as out_file:
            out_file.write(" ".join(job) + "\n")

class CheckGemmaGSE(BaseTask):
    """
    Check that the GSE is ready to be loaded in Gemma.
    """
    method = None
    method_args = None

    def init(self):
        """
        Set CLI method.
        """
        try:
            self.method = rnaseq_pipeline().GEMMACLI.split(" ")
            #self.method_args = ["addGEOData", "-u",  rnaseq_pipeline().GEMMAUSERNAME"), "-p", rnaseq_pipeline().GEMMAPASSWORD"), "-e", self.gse, "--allowsuper"]
            self.method_args = ["addGEOData", "-u",  rnaseq_pipeline().GEMMAUSERNAME, "-p", rnaseq_pipeline().GEMMAPASSWORD, "-e", self.gse]
            if self.allowsuper:
                self.method_args += ["--allowsuper"]

        except Exception as e:
            print "$GEMMACLI/GEMMAUSERNAME/GEMMPASSWORD appear to not all be set. Please set environment variables."
            raise e

        print "INFO: Method => " + str(self.method_args)

    def requires(self):
        self.init()
        return GatherMetadataGSE(self.gse, self.nsamples)

    def output(self):
        return luigi.LocalTarget(self.commit_dir + "/checkgemma_%s.tsv" % self.gse)

    def run(self):
        prejob = self.method + []
        job = self.method + self.method_args

        # Call job
        try:
            g = GemmaClientAPI(dataset=self.gse)
            username, password = rnaseq_pipeline().GEMMAUSERNAME, rnaseq_pipeline().GEMMAPASSWORD
            g.setCredentials(username, password)

            ret = 0
            if g.isEmpty():
                print self.gse  + " is not created in Gemma."
                try:
                    print "Attempting to create experiment for " + self.gse
                    ret = call(job, env=os.environ.copy())
                    print "Done."
                    print "Checking that the experiment exists."
                    g.clear()
                    if g.isEmpty():
                        print "Experiment doesn't appear to have been added."
                        ret = -1
                    else:
                        print "Experiment added."

                except Exception as e:
                    print "EXCEPTION: Could not create Gemma experiment with '" + " ".join(job) + "' ."
                    ret = -1
            else:
                print self.gse  + " exists and should be ready for upload."
                ret = 0

        except Exception as e:
            print "EXCEPTION:", e, "with checkGemma for", self.gse
            print e.message
            ret = -1

        if ret:
            print "Error code", ret, "."
            print ""
            exit( "CheckGemmaGSE failed for request '{}' with exit code {}.".format( g.getUrl(), ret) )

        # Commit output
        with self.output().open('w') as out_file:
                 out_file.write(g.toString()+"\n")

class GatherMetadataGSE(BaseTask):
    method = ["bash", "-c"]
    method_args = None
    metadataDir = None

    def init(self):
        """
        Set paths and whatnot.
        """
        SCRIPTS = rnaseq_pipeline().SCRIPTS
        self.base_method = join(SCRIPTS, "rnaseq_pipeline_metadata.sh")
        self.alignment_method = join(SCRIPTS, "alignment_metadata.sh")
        self.qc_method = join(SCRIPTS, "qc_report.sh")

        self.method_args = [self.gse]

        self.metadataDir = join(rnaseq_pipeline().METADATA, self.gse)
        print "INFO: METADATA DIRECTORY => ", self.metadataDir

    def requires(self):
        self.init()
        return CountGSE(self.gse, self.nsamples)

    def output(self):
        return luigi.LocalTarget(self.commit_dir + "/metadata_%s.tsv" % self.gse)

    def run(self):
        # Change working directory
        try:
            os.chdir(rnaseq_pipeline().SCRIPTS)
            print "Entered:", os.getcwd()
        except Exception as e:
            print "=======> GatherMetadataGSE <=========="
            print e.message
            print "Error changing to", self.wd, "when in", os.getcwd()
            raise e

        # Create metadata directory for GSE
        try:
            print "JOB: Creating directory",self.metadataDir

            job = [ "mkdir", "-p", self.metadataDir ] # TODO: Doesn't need to be a subprocess.
            print "RUNNING: #" + " ".join(job)
            ret = call(job)
            job = None
            print "Done (retcode == " + str(ret) + ")"

        except Exception as e:
            print "EXCEPTION: Could not create directory at " + self.metadataDir
            raise e

        # Call base metadata gathering job
        try:
            print "JOB: Generating base metadata at:"
            base_metadata_file = self.metadataDir + "/" + self.gse + ".base.metadata"
            print "\t" + base_metadata_file

            f = open(base_metadata_file,"wb")
            ferr = open("/dev/null", 'wb')
            job = [ self.base_method ] + self.method_args
            print "RUNNING: #" + " ".join(job)
            ret = call(job, stdout=f, stderr=ferr)
            job = None
            f.close()
            print "Done (retcode == " + str(ret) + ")"

        except NotImplementedError as e:
            print "EXCEPTION: Gathering base metadata", e, "with", " ".join(job)
            print e.message
            ret = -1
            raise e

        # Call alignment metadata job
        try:
            print "JOB: Gathering STAR metadata to", self.metadataDir

            job = [ self.alignment_method ] + self.method_args
            print "RUNNING: #" + " ".join(job)
            ret = call(job)
            job = None
            print "Done (retcode == " + str(ret) + ")"

        except Exception as e:
            print "EXCEPTION: Gathering STAR metadata", e, "with", " ".join(job)
            print e.message
            ret = -1
            raise e

        # Call alignment metadata job
        try:
            print "Gathering FastQC reports to", self.metadataDir
            job = [ self.qc_method ] + self.method_args
            print "RUNNING: #" + " ".join(job)
            ret = call(job)
            job = None
            print "Done."

        except Exception as e:
            print "EXCEPTION: Gathering FastQC metadata", e, "with", " ".join(job)
            print e.message
            ret = -1
            raise e

        if ret:
            print "Error code", ret,"."
            print ""
            exit("Job '{}' failed with exit code {}.".format( " ".join(job), ret))

        # Commit output
        with self.output().open('w') as out_file:
                 out_file.write(self.gse+"\n")


class PurgeGSE(BaseTask):
    """
    After metadata has been gathered, get rid of raw data (DATA), bam files/STAR alignment.
    """
    method = "rm"
    method_args = "-rf"

    def init(self):
        """
        Set paths and whatnot.
        """
        dataDir = os.environ['DATA']
        tmpDir = os.environ['TMPDIR']
        quantDir = os.environ['QUANTDIR']
        self.purgeDirs = []

        print "INFO: DATADIR => ", dataDir

        # TODO: Possibly, quant dir?
        for purgeDir in [dataDir, tmpDir]:
            self.purgeDirs.append( purgeDir + "/" + str(self.gse)+ "/" )

    def requires(self):
        self.init()
        return GatherMetadataGSE(self.gse, self.nsamples)

    def output(self):
        return luigi.LocalTarget(self.commit_dir + "/purge_%s.tsv" % self.gse)

    def run(self):

        try:
            os.chdir(self.wd)
        except Exception as e:
            print "=======> CountGSE <=========="
            print e.message
            print "Error changing to", self.wd, "when in", os.getcwd()
            raise e

        # Call jobs
        for purgeDir in self.purgeDirs:
            try:
                # Create DIR in case it doesn't exist.
                job = [ "mkdir", "-p", purgeDir ]
                ret = call(job)

                # Purge purgeDir
                job = [ self.method, self.method_args, purgeDir ]
                print "Deleting files from:", purgeDir
                print "JOB:" + " ".join(job)
                ret = call(job)
                print "Done."

            except Exception as e:
                print "EXCEPTION:", e, "with", " ".join(job)
                print e.message
                ret = -1

            if ret:
                print "Error code", ret,"."
                print ""
                exit("Job '{}' failed with exit code {}.".format( " ".join(job), ret))

        # Commit output
        with self.output().open('w') as out_file:
            out_file.write(self.gse+"\n")
