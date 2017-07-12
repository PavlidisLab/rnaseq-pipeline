import luigi
import os
from subprocess import call
from shutil import copyfile

class BaseTask(luigi.Task):
    here = os.path.dirname(os.path.realpath(__file__))
    commit_dir = os.path.dirname(os.path.realpath(__file__)) + "/commit"
    wd = here + "/../Pipelines/rsem/"
    MODES = os.getenv("MODES")

    # Para meters
    gse = luigi.Parameter()
    nsamples = luigi.Parameter()


class QcGSE(BaseTask):

    wd = BaseTask.here + "/../scripts/"

    method = "./qc_download.sh"    

    # Todo: Check taxon/assembly relation.

    def requires(self):
        return DownloadGSE(self.gse, self.nsamples)
        
    def output(self):
        return luigi.LocalTarget(self.commit_dir + "/qc_%s.tsv" % self.gse)

    def run(self):
        try:
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

        if ret != 0:
            exit("Job '{}' executed, but failed with exit code {}.".format( " ".join([str(x) for x in job]), ret))

        # Commit output
        with self.output().open('w') as out_file:                    
            out_file.write(self.gse+"\n")




class CountGSE(BaseTask):

    method = "./rsem_count.sh" # TODO: Generalize
    #wd = "."
    scope = "genes"


    def init(self):
        """
        Set paths and whatnot.
        """
        self.path_to_inputs = "quantified/" +str(self.gse)+ "/"
        self.count_source = self.path_to_inputs + "countMatrix.genes"
        self.count_destination = "quantified/counted/" +str(self.gse)+ "_counts.genes"
        self.fpkm_source = self.path_to_inputs + "fpkmMatrix.genes"
        self.fpkm_destination = "quantified/counted/" +str(self.gse)+ "_fpkm.genes"


    def requires(self):        
        self.init()
        return ProcessGSE(self.gse, self.nsamples)

    def output(self):
        return luigi.LocalTarget(self.commit_dir + "/count_%s.tsv" % self.gse)

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
            copyfile( self.count_source, self.count_destination)
            copyfile( self.fpkm_source, self.fpkm_destination)

        except Exception as e:
            print "EXCEPTION:", e, "with", " ".join(job)
            print e.message
            ret = -1

        if ret:
            exit("Job '{}' failed with exit code {}.".format( " ".join(job), ret))

        # Commit output
        with self.output().open('w') as out_file:                    
                 out_file.write(self.gse+"\n")



class ProcessGSE(BaseTask):

    method = "./multiple_rsem.sh" # TODO: Generalize

    def requires(self):
        return QcGSE(self.gse, self.nsamples)

    def output(self):
        return luigi.LocalTarget(self.commit_dir + "/process_%s.tsv" % self.gse)

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

    #method_geo = "../scripts/geo_to_sra.R" # TODO: Generalize
    #method_geo = "/space/grp/Pipelines/rnaseq-pipeline/scripts/geo_to_sra.R" # TODO: Generalize
    method_arrayexpres = "../scripts/arrayexpress_to_fastq.R"
    method_gse = "/space/grp/Pipelines/rnaseq-pipeline/scripts/GSE_to_fastq.sh"
    method = None

    GEO_TOKENS = ["GSE"]

    def output(self):
        return luigi.LocalTarget(self.commit_dir + "/download_%s.tsv" % self.gse)

    def run(self):
        # TODO: Figure wheter to call the GEO or ArrayExpress script
        if any([ TOKEN in self.gse for TOKEN in self.GEO_TOKENS ]):
            self.method = self.method_gse
        else:
            self.method = self.method_arrayexpress

        # Call job
        #job = ["Rscript", self.method, self.gse] 
        #job = ['ssh', 'chalmers', 'cd', '/space/grp/Pipelines/rnaseq-pipeline/scripts/', '&&', "Rscript", self.method, self.gse]
        job = [self.method, self.gse]
        ret = call(job)

        if ret:
            exit("Job '{}' failed with exit code {}.".format( " ".join(job), ret))

        # Commit output
        with self.output().open('w') as out_file:                    
                 out_file.write(self.gse+"\n")
