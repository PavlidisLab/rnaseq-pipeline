import os
from subprocess import call
from subprocess import Popen, PIPE
import glob
import re
import shutil
import sys 
import time

experiment = "bipolar"
outpath = "/misc/pipeline42/mbelmadani/rnaseq/"
MAX_THREADS = 4

if len(sys.argv) > 2:
	experiment = sys.argv[1]
	outpath = sys.argv[2]
else:
	sys.stderr.write("MISSING ARGUMENTS")
	sys.stderr.write("python "+ sys.argv[0] + " EXPERIMENT OUTPUT_PATH"  )
	sys.exit(1)

procs = []
for i in glob.glob(outpath + '/'+experiment+'/C*_1/*C*1P.txt'):
	sampfile1 = i
	sampfile2 = i.replace("1P.txt","2P.txt")

	starout = os.path.dirname(sampfile1)
	starout = os.path.join(starout, "StarAlign/")
	if not os.path.exists(starout):
		os.mkdir(starout)
	starout = os.path.join(starout, "alignment")
	
	print "Launching", sampfile1, ". Writing to", starout
	
	command = "/space/bin/STAR-STAR_2.4.0h/bin/Linux_x86_64_static/STAR --genomeDir /misc/pipeline42/reference_data --runThreadN 16 --readFilesIn " + sampfile1 + " " +  sampfile2 + " --outFileNamePrefix " + starout + " --outSAMtype BAM Unsorted"
	
	procs.append( Popen( command.split() ) )
	term = [p.poll() for p in procs]
	while term.count(None) == MAX_THREADS: #len(term):
		print "Sleeping, blocked by", MAX_THREADS, "jobs."
		time.sleep(30)

print "Launched everything"
#os.system("/space/bin/STAR-STAR_2.4.0h/bin/Linux_x86_64_static/STAR --genomeDir /misc/pipeline42/reference_data --runThreadN 16 --readFilesIn " + sampfile1 + " " +  sampfile2 + " --outFileNamePrefix " + starout + " --outSAMtype BAM Unsorted")


