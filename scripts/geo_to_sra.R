#' ---
#' title: "GEO to FASTQ"
#' author: "Manuel Belmadani"
#' date: "November 25th 2016"
#' description: "Given a GSE accession number, retreive all .sra files for SRR and extract the fastq files. "
#' ---

###
# Check parameters before anything else.
#
if ( is.na(commandArgs(TRUE)[1]) ){
  # print Usage menu.
  me <- sub(".*=", "", commandArgs()[4])
  print("Usage:")
  print( paste("Rscript", me, "GSE123456 <Optional, OUTPUT_DIRECTORY>") )
  q(save="no")
}
###
# Load project common variables

#CONFIGFILE <- paste0(getwd(), "/
setwd("../etc/")
CONFIGFILE<-"load_configs.R"
source( CONFIGFILE )

print(getwd())
print("COnfigs loaded")
###
# Load libraries
source("http://bioconductor.org/biocLite.R")
library("DBI") #, lib="~/R/")
library("SRAdb") #, lib="~/R/")
#biocLite("SRAdb") #, lib="~/R/")
library("GEOquery") #, lib="~/R/")
library("plyr") #, lib="~/R/")
library("doMC") #, lib="~/R/")


here <- paste0(ROOT_DIR, "/scripts/")
setwd(here)
# Configure SSL
#httr::config(ssl_verifypeer = FALSE)


# Function definitions
wprint <- function(X, file = "default-GEO.log", append = TRUE){
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
#sqlfile <- paste0(DATA,"/","SRAmetadb.sqlite")
sqlfile <- paste0("./","SRAmetadb.sqlite")
# If file is not downloaded, redownloaded.
if(!file.exists(sqlfile)){
  wprint(paste("SRAmetadb does not exists. Downloading at", sqlfile))
  #sqlfile <<- getSRAdbFile(destdir=DATA,
  #                         method="wget",
  #                         )
  system(paste("wget -O https://dl.dropboxusercontent.com/u/51653511/SRAmetadb.sqlite.gz --no-check-certificate && gunzip -c SRAmetadb.sqlite.gz > ", sqlfile) )
  
} else {
  wprint(paste("SRAmetadb exists at", sqlfile,"; no need to redownload unless GEO samples were recently updated."))
}

library("RSQLite")
dbcon <- dbConnect(DBI::dbDriver("SQLite"),
                   dbname = sqlfile)

# Prepare parameters
GEO_ID <- commandArgs(TRUE)[1] #e.g "GSE12946"
OUTPUT_PATH <- commandArgs(TRUE)[2] #e.g. fastq

if (is.na(OUTPUT_PATH)){
  OUTPUT_PATH <- GEO_ID # If no output directory is provided, use the GEO_ID.
}
if (is.na(OUTPUT_PATH)){
   OUTPUT_PATH <- "default_fastq" # Default output is fastq from where ever you're working from.
}

# FIXME: Do we want to override this?
OUTPUT_PATH <- paste0( DATA, "/", OUTPUT_PATH)


# Create output directories
dir.create(OUTPUT_PATH, showWarnings=FALSE)
LOGFILE <- paste0(OUTPUT_PATH, "/", "fastq-dump-", GEO_ID, ".log")

# Obtain maximum number of cores
CORES <- NCPU_NICE #parallel:::detectCores()
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

    print(paste("sraConvert for", SRX))
    SRRs <- sraConvert(SRX, 'run', dbcon)$run

    wprint("Fetching fastq for:", LOGFILE)
    wprint(SRRs, LOGFILE)
    
    SEQUENCE_OUTPUT = paste0(OUTPUT_PATH, "/", sample, "/", SRX)
    dir.create(SEQUENCE_OUTPUT, showWarnings=FALSE)

    # Assemble commands using wonderdump.sh
    CMDS <- adply(.data = SRRs,
                  .margins = 1,
                  .fun = function(X) {
                      CMD <- paste(WONDERDUMP_EXE, X, SEQUENCE_OUTPUT)                      
                      return(CMD)
                 }
               )
    COMMANDS <- c(COMMANDS, CMDS$V1)
}
wprint(paste("Expecting to download", length(COMMANDS), "runs from SRA."), LOGFILE)
wprint("Commands prepared. Launching parallelized downloader...", LOGFILE)

# Prepare parallel execution of commands
doMC::registerDoMC(cores=NCPU_NICE) # or however many cores you have access to
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

