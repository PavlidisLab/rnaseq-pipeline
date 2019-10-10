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

class BaseTask(luigi.Task):
    here = os.path.dirname(os.path.realpath(__file__))
    commit_dir = os.path.dirname(os.path.realpath(__file__)) + "/commit"
    wd = here + "/../Pipelines/rsem/"
    MODES = rnaseq_pipeline().MODES
    SCRIPTS = rnaseq_pipeline().SCRIPTS

    # Para meters
    gse = luigi.Parameter()
    nsamples = luigi.Parameter(default=0)
    scope = luigi.Parameter(default="genes")
    ignorecommit = luigi.Parameter(default=0)
    allowsuper = luigi.Parameter(default=False)

class QcGSE(BaseTask):

    wd = BaseTask.SCRIPTS + "/"

    method = "./qc_download.sh"

    # Todo: Check taxon/assembly relation.

    def requires(self):
        return DownloadExperiment(self.gse)

    def output(self):
        return luigi.LocalTarget(self.commit_dir + "/qc_%s.tsv" % self.gse)

    def run(self):
        try:
            print "Running from " + self.wd
            os.chdir(self.wd)

        except Exception as e:
            print "=======> QcGSE <=========="
            print e.message
            print "Error changing to", self.wd, "when in", os.getcwd()
            raise e

        # Call job
        try:
            job = [ self.method, self.gse, self.nsamples ]

            ret = None
            ret = call(job)

        except Exception as e:
            print "EXCEPTION:", e, "with", " ".join([str(x) for x in job])
            print "Message:",  e.message
            raise e

        if ret != 0:
            print "# Job '{}' executed, but failed with exit code {}.".format( " ".join([str(x) for x in job]), ret)
            exit(-1)

        # Commit output
        with self.output().open('w') as out_file:
            out_file.write(self.gse+"\n")




class CountGSE(BaseTask):

    method = "./rsem_count.sh" # TODO: Generalize

    def init(self):
        """
        Set paths and whatnot.
        """
        if self.scope is None:
            self.scope = "genes"

        quantDir = rnaseq_pipeline().QUANTDIR + "/"
        countDir = rnaseq_pipeline().COUNTDIR + "/"

        if 'SCOPE' in  os.environ.keys():
            self.scope = os.environ['SCOPE']

        if not os.path.isdir(countDir):
            os.mkdir(countDir)

        print "INFO: QUANTDIR => ", quantDir
        print "INFO: COUNTDIR => ", countDir

        self.path_to_inputs = quantDir + str(self.gse)+ "/"

        self.count_source = self.path_to_inputs + "countMatrix."+self.scope
        self.count_destination = countDir +str(self.gse)+ "_counts."+self.scope

        self.fpkm_source = self.path_to_inputs + "fpkmMatrix."+self.scope
        self.fpkm_destination = countDir  +str(self.gse)+ "_fpkm."+self.scope

        self.tpm_source = self.path_to_inputs + "tpmMatrix."+self.scope
        self.tpm_destination = countDir  +str(self.gse)+ "_tpm."+self.scope


    def requires(self):
        self.init()
        return ProcessGSE(self.gse, self.nsamples)

    def output(self):
        uniqueID=""
        if int(self.ignorecommit) == 1:
            print "INFO: Ignoring previous commits."
            uniqueID = "_" + str(uuid.uuid1()) # Skipping commit logic.

        return luigi.LocalTarget(self.commit_dir + "/count" + uniqueID + "_%s.tsv" % self.gse)

    def run(self):

        try:
            os.chdir(self.wd)
        except Exception as e:
            print "=======> CountGSE <=========="
            print e.message
            print "Error changing to", self.wd, "when in", os.getcwd()
            raise e


        # Call job
        try:
            job = [ self.method, self.path_to_inputs, self.scope ]
            ret = call(job)

            print "Copying files from (e.g. ", self.count_source, ") to destination (e.g. ", self.count_destination, ")."
            copyfile( self.count_source, self.count_destination)
            copyfile( self.fpkm_source, self.fpkm_destination)
            copyfile( self.tpm_source, self.tpm_destination)

            # Might as well do isoforms while we're here.
            job = [ self.method, self.path_to_inputs, "isoforms" ]
            ret = call(job)

        except Exception as e:
            print "EXCEPTION:", e, "with", " ".join(job)
            print e.message
            ret = -1

        if ret:
            exit("Job '{}' failed with exit code {}.".format( " ".join(job), ret))

        # Commit output
        with self.output().open('w') as out_file:
                 out_file.write(self.gse+"\n")


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

class ProcessGSE(BaseTask):

    method = "./multiple_rsem.sh" # TODO: Generalize

    def requires(self):
        return QcGSE(self.gse, self.nsamples)

    def output(self):
        uniqueID=""
        if int(self.ignorecommit) == 1:
            print "INFO: Ignoring previous commits."
            uniqueID = "_" + str(uuid.uuid1()) # Skipping commit logic.

        return luigi.LocalTarget(self.commit_dir + "/process" +uniqueID+ "_%s.tsv" % self.gse)

    def run(self):
        try:
            os.chdir(self.wd)
        except Exception as e:
            print "Error changing to", self.wd, "when in", os.getcwd()
            raise e

        MODES = "MODES='"+BaseTask.MODES+"'"
        # Call job
        try:
            job = [self.method, self.gse, self.gse]
            ret = call(job, env=os.environ)

        except Exception as e:
            print "=======> ProcessGSE <=========="
            print e.message
            print "EXCEPTION:", e, "with", " ".join(job)

            ret = -1

        if ret:
            exit("Job '{}' failed with exit code {}.".format( " ".join(job), ret))

        # Commit output
        with self.output().open('w') as out_file:
                 out_file.write(self.gse+"\n")

class DownloadSRR(ExternalProgramTask):
    gse = luigi.Parameter()
    sra = luigi.Parameter()
    srr = luigi.Parameter()

    def program_environment(self):
        return {'DATA': rnaseq_pipeline().DATA,
                'LOGS': rnaseq_pipeline().LOGS,
                'MACHINES': rnaseq_pipeline().MACHINES,
                'NCPU_ALL': rnaseq_pipeline().NCPU_ALL,
                'WONDERDUMP_EXE': rnaseq_pipeline().WONDERDUMP_EXE,
                'PREFETCH_EXE': rnaseq_pipeline().PREFETCH_EXE,
                'PREFETCH_MAXSIZE': rnaseq_pipeline().PREFETCH_MAXSIZE,
                'SRA_CACHE': rnaseq_pipeline().SRA_CACHE,
                'FASTQHEADERS_DIR': rnaseq_pipeline().FASTQHEADERS_DIR,
                'FASTQDUMP_EXE': rnaseq_pipeline().FASTQDUMP_EXE,
                'FASTQDUMP_SPLIT': rnaseq_pipeline().FASTQDUMP_SPLIT,
                'FASTQDUMP_READIDS': rnaseq_pipeline().FASTQDUMP_READIDS,
                'FASTQDUMP_BACKFILL': rnaseq_pipeline().FASTQDUMP_BACKFILL,
                'HOME': '/cosmos/scratch'}

    def program_args(self):
        return [rnaseq_pipeline().WONDERDUMP_EXE, self.srr, join(rnaseq_pipeline().DATA, self.gse, self.sra)]

    def output(self):
        return luigi.LocalTarget(join(rnaseq_pipeline().DATA, self.gse, self.sra, '{}.sra'.format(self.srr)))

class DownloadGSE(luigi.Task):
    gse = luigi.Parameter()

    def run(self):
        method = join(rnaseq_pipeline().SCRIPTS, "GSE_to_fastq.sh")
        out = check_output([method, self.gse], env={'DATA': rnaseq_pipeline().DATA, 'LOGS': rnaseq_pipeline().LOGS, 'MACHINES': rnaseq_pipeline().MACHINES})
        yield [DownloadSRR(self.gse, line.split(',')[1], line.split(',')[0]) for line in out.splitlines()]

class DownloadArrayExpressSample(luigi.Task):
    experiment_id = luigi.Parameter()
    sample_id = luigi.Parameter()
    sample_url = luigi.Parameter()

    def run(self):
        check_call(['mkdir', '-p', join(rnaseq_pipeline().DATA, self.experiment_id, self.sample_id)])
        dest_filename = join(rnaseq_pipeline().DATA, self.experiment_id, self.sample_id, os.path.basename(self.sample_url))
        urllib.urlretrieve(self.sample_url, filename=dest_filename + '.tmp')
        os.rename(dest_filename + '.tmp', dest_filename)

    def output(self):
        return luigi.LocalTarget(join(rnaseq_pipeline().DATA, self.experiment_id, self.sample_id, os.path.basename(self.sample_url)))

class DownloadArrayExpress(luigi.Task):
    experiment_id = luigi.Parameter()

    def run(self):
        ae_df = pd.read_csv('http://www.ebi.ac.uk/arrayexpress/files/{0}/{0}.sdrf.txt'.format(self.experiment_id), sep='\t')
        yield [DownloadArrayExpressSample(experiment_id=self.experiment_id, sample_id=s['Comment[ENA_RUN]'], sample_url=s['Comment[FASTQ_URI]'])
                for ix, s in ae_df.iterrows()]

class DownloadExperiment(luigi.Task):
    """
    This is a generic task that detects which kind of experiment is intended to
    be downloaded so that downstream tasks can process regardless of the data
    source.
    """
    experiment_id = luigi.Parameter()
    def run(self):
        if self.experiment_id.startswith('GSE'):
            yield DownloadGSE(self.experiment_id)
        else:
            yield DownloadArrayExpress(self.experiment_id)
