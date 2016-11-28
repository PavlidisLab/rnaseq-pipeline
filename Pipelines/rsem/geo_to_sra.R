#' ---
#' title: "GEO to FASTQ"
#' author: "Manuel Belmadani"
#' date: "November 25th 2016"
#' description: "Given a GSE accession number, retreive all .sra files for SRR and extract the fastq files. "
#' ---

source("http://bioconductor.org/biocLite.R")
library("DBI")
library(SRAdb)
library("GEOquery")
library("plyr")
library("doMC")

# Function definitions

wprint <- function(X, file = "default.log", append = TRUE){
  # Prints text and also outputs it to a file.
  #
  # Args:
  #   X: A string of text.
  #   file: Outfile file.
  #   append: Wheter or not "file" should be appended or overwritten.
  #
  # Returns:
  #   Nothing
  print(X)
  write(X, file, append=TRUE)
}

########################################################
## Prepare environment
########################################################

# Set up database connection for SRAdb
sqlfile <- "SRAmetadb.sqlite"

# If file is not downloaded, redownloaded.
if(!file.exists(sqlfile)) sqlfile <<- getSRAdbFile()

dbcon = dbConnect(RSQLite::SQLite(), sqlfile)

# Prepare parameters
GEO_ID <- commandArgs(TRUE)[1] #e.g "GSE12946"
OUTPUT_PATH <- commandArgs(TRUE)[2] #e.g. fastq

if (is.na(OUTPUT_PATH)){
  OUTPUT_PATH <- GEO_ID # If no output directory is provided, use the GEO_ID.
}
if (is.na(OUTPUT_PATH)){
   OUTPUT_PATH <- "default_fastq" # Default output is fastq from where ever you're working from.
}

# Create output directories
dir.create(OUTPUT_PATH, showWarnings=FALSE)
LOGFILE <- paste0(OUTPUT_PATH, "/", "fastq-dump-", GEO_ID, ".log")

# Obtain maximum number of cores
CORES <- parallel:::detectCores()
DRY <- TRUE # If file exists; don't redownload it.


########################################################################
## Obtain the GEO Matrix S4 object
########################################################################

gse <- getGEO(GEO=GEO_ID, destdir=OUTPUT_PATH, GSEMatrix=FALSE)

## Obtain list of GEO Samples
SAMPLE_LIST <- names(gse@gsms)

# Obtain only SRXnnnnnnn behind supplementary files
SUPPLEMENTARIES <- names(gse@gsms[[SAMPLE_LIST[1]]]@header)[grepl("supplementary_file_", names(gse@gsms[[SAMPLE_LIST[1]]]@header))]
SRA_EXPERIMENTS <- c()
for (SUPPLEMENTARY in SUPPLEMENTARIES){
  SRA_EXPERIMENTS <- c(SRA_EXPERIMENTS, unlist(gse@gsms[[SAMPLE_LIST[1]]]@header[SUPPLEMENTARY]))
}
SRA_EXPERIMENTS <- SRA_EXPERIMENTS[grepl("sra/sra-instant/reads", SRA_EXPERIMENTS)]
#=================================================#

SRAs <- c()
countSamples <- 0
COMMANDS <- c()

for (sample in SAMPLE_LIST) {
    # Obtain list of SRR accessions based on an input SRX
    countSamples <- countSamples + 1
    
    SRX <- SRA_EXPERIMENTS[countSamples]
    SRX <- strsplit(SRA_EXPERIMENTS[countSamples], "/")[[1]][length(strsplit(SRA_EXPERIMENTS[countSamples], "/")[[1]]) ]
    SRRs <- sraConvert(SRX, 'run', dbcon)$run

    wprint("Fetching fastq for:", LOGFILE)
    wprint(SRRs, LOGFILE)
    
    SEQUENCE_OUTPUT = paste0(OUTPUT_PATH, "/", sample, "/", SRX)
    dir.create(SEQUENCE_OUTPUT, showWarnings=FALSE)

    # Assemble commands using wonderdump.sh
    CMDS <- adply(.data = SRRs,
                  .margins = 1,
                  .fun = function(X) {
                      CMD <- paste("/misc/pipeline42/NeuroGem/install/wonderdump.sh", X, SEQUENCE_OUTPUT)                      
                      return(CMD)
                 }
               )
    COMMANDS <- c(COMMANDS, CMDS$V1)
}
wprint(paste("Expecting to download", length(COMMANDS), "runs from SRA."), LOGFILE)
wprint("Commands prepared. Launching parallelized downloader...", LOGFILE)

# Prepare parallel execution of commands
doMC::registerDoMC(cores=CORES) # or however many cores you have access to
system.time(
            adply(.data = COMMANDS, 
                  .margins = 1, 
                  .fun =function(X) {                                                      
                    # Append the command to the log
                    wprint(X, file = LOGFILE, append = TRUE)
                    # Call fastq-dump/wonderdump
                    system( X )           
                  }, 
                  .parallel = TRUE
                  )
            )
wprint(paste("Extracted FastQ for", GEO_ID), LOGFILE)

