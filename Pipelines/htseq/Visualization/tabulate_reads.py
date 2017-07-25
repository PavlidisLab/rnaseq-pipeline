import os
import sys
from utils import Utils

EXPERIMENT="bipolar"
ROOT="/misc/pipeline42/mbelmadani/rnaseq/"

if len(sys.argv) > 2:
    EXPERIMENT = sys.argv[1]
    ROOT = sys.argv[2]    
else:
    sys.stderr.write("Missing parameters.")
    sys.stderr.write("Call the script as so:")
    sys.stderr.write(sys.argv[0] + "EXPERIMENT PIPELINE_OUTPUT_ROOTDIR")
    exit(1)

u = Utils(ROOT + "/reports")
WORKING_DIRECTORY= ROOT + "/" +EXPERIMENT + "/"
TEMP_PRETRIM="/home/bcallaghan/rnaseqproj2/out/fastqc/" # TODO: Move this elsewhere

DIR_FASTQC="FastqcReports"
DIR_HTSEQ="HTSeq"
DIR_STAR="StarAlign"
STAR_LOG="alignmentLog.final.out"


# Flush old files
filetags = ["summary", "aligns", "genecounts"] 
for x in filetags:
    u.rm(x + "_" + EXPERIMENT + ".tsv")

# Get list of sample identifiers
IDENTIFIERS=[ x for x in os.listdir(WORKING_DIRECTORY) if x.endswith("1")]
#print IDENTIFIERS, len(IDENTIFIERS)

# Write headers
HEADERS = ["Step"] + IDENTIFIERS + ["Avg"]
u.write(HEADERS, "summary_" + EXPERIMENT, compute_average=False)

# Count pretrims/samples (FastqcReports?)
reads = ["Pre-trimming"]
for IDENTIFIER in IDENTIFIERS:
    subpath = IDENTIFIER+"/"+IDENTIFIER+"_fastqc/fastqc_data.txt"
    path = os.path.join(TEMP_PRETRIM, subpath)
    reads += [u.get_fastqc_reads(path)]
u.write(reads, "summary_" + EXPERIMENT )

# Count posttrims/sample (FastqcReports)
reads = ["Post-trimming"]
for IDENTIFIER in IDENTIFIERS:
    IDENTIFIER_ROOT = os.path.join(WORKING_DIRECTORY, IDENTIFIER)
    
    path = os.path.join(IDENTIFIER_ROOT, DIR_FASTQC)
    subpath = "trimmed_"+IDENTIFIER+"_2P_fastqc/fastqc_data.txt"
    path = os.path.join(path, subpath)
    reads += [u.get_fastqc_reads(path)]
u.write(reads, "summary_" + EXPERIMENT )

# Count aligned/sample (StarAlign)
reads = ["Aligned"]
alignments = []
for IDENTIFIER in IDENTIFIERS:
    IDENTIFIER_ROOT = os.path.join(WORKING_DIRECTORY, IDENTIFIER)

    path = os.path.join(IDENTIFIER_ROOT, DIR_STAR)
    path = os.path.join(path, STAR_LOG)
    counts = u.get_star_reads(path)
    # TODO: Handle 'counts' for subgraphs
    reads += [counts[0]]
    alignments += [counts]
u.write(reads, "summary_" + EXPERIMENT )

STEPS = ["unique", "total", "multiple", "too_many", "unmapped"]
u.subwrite(HEADERS, STEPS, alignments, "aligns_" + EXPERIMENT)

# Count gene hits (HTSeq)
reads = ["Counts"]
alignments = []
for IDENTIFIER in IDENTIFIERS:
    IDENTIFIER_ROOT = os.path.join(WORKING_DIRECTORY, IDENTIFIER)

    _path = os.path.join(IDENTIFIER_ROOT, DIR_HTSEQ)
    path = os.path.join(_path, "output.sam")
    if not os.path.exists(path):
        # TODO: Fix this with consistent output names
        path = os.path.join(_path, "output.count")
        if not os.path.exists(path):
            sys.stderr.write( "ERROR: File does not exit : " + path ) 
            exit(-1)
    counts = u.get_ht_reads(path)

    reads += [counts[0]]
    alignments.append(counts)
u.write(reads, "summary_" + EXPERIMENT )

STEPS = ["gene", "no_feature", "ambiguous"]
u.subwrite(HEADERS, STEPS, alignments, "genecounts_" + EXPERIMENT)

## Subscript: Count (unique, mutli, unmapped)
# Count mapped/sample
