import luigi
import os
from subprocess import call
from shutil import copyfile
from base64 import b64encode
import uuid

from gemmaclient import GemmaClientAPI
#from meta import ExcavateFQ
#from meta import LogAssembly

class BaseTask(luigi.Task):
    here = os.path.dirname(os.path.realpath(__file__))
    commit_dir = os.path.dirname(os.path.realpath(__file__)) + "/commit"
    wd = here + "/../Pipelines/rsem/"
    MODES = os.getenv("MODES")
    SCRIPTS = os.getenv("SCRIPTS")

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
        return DownloadGSE(self.gse, self.nsamples)
        
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
            
        quantDir = os.environ['QUANTDIR'] + "/"
        countDir = os.environ['COUNTDIR'] + "/"

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
            self.method = os.getenv("GEMMACLI").split(" ")
            #self.method_args = ["addGEOData", "-u",  os.getenv("GEMMAUSERNAME"), "-p", os.getenv("GEMMAPASSWORD"), "-e", self.gse, "--allowsuper"]
            self.method_args = ["addGEOData", "-u",  os.getenv("GEMMAUSERNAME"), "-p", os.getenv("GEMMAPASSWORD"), "-e", self.gse]
            if self.allowsuper:
                self.method_args += ["--allowsuper"]

        except Exception as e:
            print "$GEMMACLI/GEMMAUSERNAME/GEMMPASSWORD appear to not all be set. Please set environment variables."
            raise e                

        print "INFO: Method => " + str(self.method_args)

    def requires(self):        
        self.init()
        return CountGSE(self.gse, self.nsamples)

    def output(self):
        return luigi.LocalTarget(self.commit_dir + "/checkgemma_%s.tsv" % self.gse)

    def run(self):
        prejob = self.method + []
        job = self.method + self.method_args

        # Call job
        try:
            g = GemmaClientAPI(dataset=self.gse)
            username, password = [os.getenv(x) for x in ["GEMMAUSERNAME", "GEMMAPASSWORD"] ]
            g.setCredentials(username, password)

            ret = 0
            if g.isEmpty():
                print self.gse  + " is not created in Gemma."                
                try:
                    print "Attempting to create experiment for " + self.gse
                    ret = call(job)
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
            foo1 = os.getenv("GEMMACLI").split(" ")

            # foo2 = os.getenv("GEMMAUSERNAME")
            # foo3 = os.getenv("GEMMAPASSWORD")
            # if None in [foo1, foo2, foo3]:
            #     raise Exception("At least one Gemma parameter is None!")
        
        except Exception as e:
            print "$GEMMACLI/GEMMAUSERNAME/GEMMPASSWORD appear to not all be set. Please set environment variables."
            raise e                
            
        try:
            PATH = os.getenv("COUNTDIR")
            TAXONS = ['human', 'mouse', 'rat']
            MODES = os.getenv("MODES").split(",")
            SCRIPTS = os.getenv("SCRIPTS")
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
            ret = call(job)
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
        SCRIPTS = os.getenv("SCRIPTS")
        self.base_method = SCRIPTS + "/" + "pipeline_metadata.sh"
        self.alignment_method = SCRIPTS + "/" + "alignment_metadata.sh"
        self.qc_method = SCRIPTS + "/" + "qc_report.sh"
        
        self.method_args = [self.gse]
        
        self.metadataDir = os.environ['METADATA'] + "/" + self.gse
        print "INFO: METADATA DIRECTORY => ", os.environ['METADATA']

    def requires(self):        
        self.init()
        return CountGSE(self.gse, self.nsamples)

    def output(self):
        return luigi.LocalTarget(self.commit_dir + "/metadata_%s.tsv" % self.gse)

    def run(self):
        # Change working directory
        try:
            os.chdir(os.environ['SCRIPTS'])
            print "Entered:", os.environ['SCRIPTS']
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

class DownloadGSE(BaseTask):    

    method_arrayexpress = os.getenv('SCRIPTS') + "/arrayexpress_to_fastq.sh"
    method_gse =  os.getenv('SCRIPTS') + "/GSE_to_fastq.sh"
    method = None

    GEO_TOKENS = ["GSE"]

    def output(self):
        uniqueID = ""
        if int(self.ignorecommit) == 1:
            uuid_tag = str(uuid.uuid1())
            print "INFO: Ignoring previous commits. Current job UUID tag:", uuid_tag
            uniqueID = "_" + uuid_tag # Skipping commit logic.

        return luigi.LocalTarget(self.commit_dir + "/download" +uniqueID+ "_%s.tsv" % self.gse)

    def run(self):
        # TODO: Figure wheter to call the GEO or ArrayExpress script more explicitely
        if any([ TOKEN in self.gse for TOKEN in self.GEO_TOKENS ]):
            self.method = self.method_gse
        else:
            self.method = self.method_arrayexpress

        # Call job
        job = [self.method, self.gse]
        ret = call(job)

        if ret:
            exit("Job '{}' failed with exit code {}.".format( " ".join(job), ret))

        # Commit output
        with self.output().open('w') as out_file:                    
                 out_file.write(self.gse+"\n")
