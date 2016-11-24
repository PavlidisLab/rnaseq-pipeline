#!/space/opt/bin/Rscript

#############################################################################################
# Description: For a given GEO GSE identifier, retreive all matching SRA SRR fastq files.   #
#############################################################################################

source("http://bioconductor.org/biocLite.R")
library(DBI)
#biocLite( c("SRAdb", "GEOquery"),  lib="~/R/")
library("SRAdb", lib="~/R/")
library("GEOquery", lib="~/R/")
library("plyr", lib="~/R/")
library(doMC)
#library("RSQLite", lib="~/R/")
#require(RH2)

wprint <- function(X, file = "default.log", append = TRUE){
  print(X)
  write(X, file, append=TRUE)
}


CORES <- parallel:::detectCores()
DRY <- TRUE # This means: If file exists; don't redownload it.

########################################################
## Prepare environment
########################################################

# Set wd
# setwd("/misc/pipeline42/NeuroGem/pipeline")


# Set up database connection for SRAdb
sqlfile <- "/misc/pipeline42/NeuroGem/pipeline/SRAmetadb.sqlite"
if(!file.exists(sqlfile)) sqlfile <<- getSRAdbFile()

dbcon = dbConnect(RSQLite::SQLite(), sqlfile)

GEO_ID <- commandArgs(TRUE)[1] #e.g 'GSE48138'
#GEO_ID <- "GSE12946"
#GEO_ID <- "GSE80336"
OUTPUT_PATH <- commandArgs(TRUE)[2] #e.g. fastq
if (is.na(OUTPUT_PATH)){
  OUTPUT_PATH <- GEO_ID
}
if (is.na(OUTPUT_PATH)){
   OUTPUT_PATH <- "default_fastq" # Default output is fastq from where ever you're working from.
}

dir.create(OUTPUT_PATH, showWarnings=FALSE)
LOGFILE <- paste0(OUTPUT_PATH, "/", "fastq-dump-", GEO_ID, ".log")

########################################################################
## Obtain the GEO Matrix S4 object
########################################################################

gse <- getGEO(GEO=GEO_ID, destdir=OUTPUT_PATH, GSEMatrix=FALSE)

## Obtain list of GEO Samples
SAMPLE_LIST <- names(gse@gsms)

# SRA_logic <- gse@gsms[[SAMPLE_LIST[1]]]@header$type
# SRA_boolean <- SRA_logic == "SRA"

## Obtain only SRXnnnnnnn
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
  countSamples <- countSamples + 1
  #SRX <- c()
  #for (n in 1:ncol(df[sample,])) {
  #  SRX <- c(SRX, as.vector(df[sample,][n]))    
  #}    
  #filteredSRX <- SRX[grepl(keepFilter, x = SRX)]
    
  ## Obtain only the identifer
  #clippedSRX <- gsub(
  #  pattern = ".*term=", 
  #  replacement = "", 
  #  x = filteredSRX
  #)
  
  #SRAs <- c(SRAs, clippedSRX)
  #=================================================#  
  #SRXs <- unique(SRAs)
  #SRRs <- sraConvert(SRXs,'run',dbcon)
  #SRRs <- unique(SRRs$run)

  ## Obtain list of SRRs based on an input SRX
  SRX <- SRA_EXPERIMENTS[countSamples]
  SRX <- strsplit(SRA_EXPERIMENTS[countSamples], "/")[[1]][length(strsplit(SRA_EXPERIMENTS[countSamples], "/")[[1]]) ]
  SRRs <- sraConvert(SRX, 'run', dbcon)$run

  wprint("Fetching fastq for:", LOGFILE)
  wprint(SRRs, LOGFILE)

  SEQUENCE_OUTPUT = paste0(OUTPUT_PATH, "/", sample, "/", SRX)
  dir.create(SEQUENCE_OUTPUT, showWarnings=FALSE)
  CMDS <- adply(.data = SRRs,
               .margins = 1,
               .fun = function(X) {
                   #CMD <- paste("/misc/pipeline42/NeuroGem/pipeline/sratoolkit/bin/fastq-dump --outdir ",SEQUENCE_OUTPUT," --gzip --skip-technical  --readids --dumpbase --split-files --clip", X)
                   CMD <- paste("/misc/pipeline42/NeuroGem/install/wonderdump.sh", X, SEQUENCE_OUTPUT)

                   # Not needed with WONDERDUMP #EXPECTED_PATH <- paste0(SEQUENCE_OUTPUT,"/",X,"_1.fastq.gz")                   
                   #if (file.exists(EXPECTED_PATH) && DRY == TRUE){
                   #  wprint(paste0("Skipping already downloaded ", X, " at ", EXPECTED_PATH), LOGFILE)                     
                   #} else {
                   #  wprint(paste0("Queuing download for ", X, " at: ", EXPECTED_PATH), LOGFILE)
                     return(CMD)
                   #}                                      
                 }
               )
  COMMANDS <- c(COMMANDS, CMDS$V1)
}

wprint(paste("Expecting to download", length(COMMANDS), "runs from SRA."), LOGFILE)
wprint("Commands prepared. Launching parallelized downloader...", LOGFILE)

# Prepare parallelization
doMC::registerDoMC(cores=CORES) # or however many cores you have access to
system.time(
            adply(.data = COMMANDS, 
                  .margins = 1, 
                  .fun =function(X) {                                                      
                    # Append the command to the log
                    wprint(X, file = LOGFILE, append = TRUE)
                    #Sys.sleep(2)
                    # Call fastq-dump/wonderdump
                    system( X )           
                  }, 
                  .parallel = TRUE
                  )
            )

wprint(paste("Extracted FastQ for", GEO_ID), LOGFILE)

