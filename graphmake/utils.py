import os
import subprocess

class Utils():
    """
    Utility class to do text and file parsing
    """
    
    def __init__(self, root="./report/"):
        self.root = root

        if not os.path.isdir(self.root):
            os.mkdir(self.root)


    def to_file(self, content, destination):
        if not destination:
            print content
            return
        elif not destination.endswith(".tsv"):
            destination += ".tsv"

        destination = os.path.join(self.root, destination)
        with open(destination, 'a') as f:
            f.write(content)
            f.write("\n")

    def rm(self, destination):        
        open(os.path.join(self.root, destination), 'w').close()
    
    def write(self, 
              LIST, 
              destination=None,           
              compute_average=True,
              SEP="\t"):
        """
        Write to standard out in TSV
        """
        def avg(l): return ( sum(l, 0.0) / len(l) ) # Compute average for a list
        if compute_average:
            LIST = LIST + [str(avg(  [float(x) for x in LIST[1:]]  ))]

        self.to_file(SEP.join(LIST), destination)

    def subwrite(self,            
                 HEADERS,
                 STEPS,
                 _values,
                 destination):
        """
        Use a predifined HEADER but with different row names (STEPS) and values (_values)
        """

        values = zip(*_values) # Transpose
        self.write(HEADERS, destination, compute_average=False)
        for i in range(len(STEPS)):
            STEP = STEPS[i]
            value_tuple = values[i]

            data_slice = [STEP] + list(value_tuple)
            self.write(data_slice, destination)
            


    def get_fastqc_reads(self,path):
        """
        Read fastqc output file until total sequence count is encountered.
        """
        with open(path, 'r') as f: 
            for line in f:
                if "Total Sequences" in line:
                    count = line.strip().split()[-1]
                    return count

    def get_star_reads(self,path):
        """
        Read STAR Aligner file until uniquely, multiple and unmapped sequences alignments are encountered.
        RETURNS [unique, multiple, too many, unmapped]
        """
        unique = 0
        multiple = 0
        too_many = 0
        with open(path, 'r') as f: 
            for line in f:
                if "Uniquely mapped reads number" in line:
                    unique = line.strip().split()[-1]
                elif "Number of reads mapped to multiple loci" in line:
                    multiple = line.strip().split()[-1]
                elif "Number of reads mapped to too many loci" in line:
                    too_many = line.strip().split()[-1]
                elif "Number of input reads" in line:
                    total = line.strip().split()[-1]

        unmapped = str(int(total) - int(unique) - int(multiple) - int(too_many))
        return [unique, total,  multiple, too_many, unmapped]
                    
    def get_ht_reads(self,path):
        """
        Get total number of gene counts for HTSeqs
        RETURNS [total, no_feature, ambiguous]
        """
        
        output = subprocess.Popen([ "./total_htcount.sh " + path ], stdout=subprocess.PIPE, shell=True, stderr=subprocess.STDOUT).communicate()[0]

        total = output.strip()
        no_feature = 0
        ambiguous = 0
        with open(path, 'r') as f: 
            for line in f:
                if "__no_feature" in line:
                    no_feature = line.strip().split()[-1]
                elif "__ambiguous" in line:
                    ambiguous = line.strip().split()[-1]
            return [total, no_feature, ambiguous]
                    
