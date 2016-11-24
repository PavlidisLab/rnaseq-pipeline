#!/space/opt/bin/Rscript

#############################################################################################
# Description: For a given ArrayExpress identifier, retreive all FASTQ files.               #
#############################################################################################

source("http://bioconductor.org/biocLite.R")
library("doMC")
library("RCurl")
library("plyr", lib="~/R/")

CORES <- parallel:::detectCores()

wprint <- function(X, file = "default.log", append = TRUE){
  print(X)
  write(X, file, append=TRUE)
}

AE_ID <- commandArgs(TRUE)[1] #e.g "E-MTAB-4092"
OUTPUT_PATH <- commandArgs(TRUE)[2] #e.g. arrayexpress_default

if (is.na(OUTPUT_PATH)){
  OUTPUT_PATH <- AE_ID
}
if (is.na(OUTPUT_PATH)){
   OUTPUT_PATH <- "default_arrayexpress" # Default output is fastq from where ever you're working from.
}
dir.create(OUTPUT_PATH, showWarnings=FALSE)
LOGFILE <- paste0(OUTPUT_PATH, "/", "wget-", AE_ID, ".log")

#AE_ID <- "E-MTAB-4092"

SAMPLE_MATRIX_URL <- paste0("http://www.ebi.ac.uk/arrayexpress/files/",AE_ID,"/",AE_ID,".sdrf.txt")
SAMPLE_MATRIX_TEXT <- getURL(SAMPLE_MATRIX_URL)
SAMPLES_CSV <-read.csv(text = SAMPLE_MATRIX_TEXT, sep='\t')

processAE <- function(ROW){
  FASTQ <- ROW["Comment.FASTQ_URI."]
  SAMPLE <- ROW['Comment.ENA_RUN.']

  FASTQ_OUTPUT <-  paste0(OUTPUT_PATH, "/", SAMPLE)
  dir.create(FASTQ_OUTPUT, showWarnings=FALSE)
  
  COMMAND <- paste0("wget -P ", FASTQ_OUTPUT, " ", FASTQ)
  return(COMMAND)
}

COMMANDS <- apply(SAMPLES_CSV, 1, FUN=processAE)

wprint(paste("Expecting to download", length(COMMANDS), "runs from ArrayExpress."), LOGFILE)
wprint("Commands prepared. Launching parallelized downloader...", LOGFILE)

# Prepare parallelization
doMC::registerDoMC(cores=CORES) # or however many cores you have access to
system.time(
            adply(.data = COMMANDS, 
                  .margins = 1, 
                  .fun =function(X) {                                                      
                    # Append the command to the log
                    wprint(X, file = LOGFILE, append = TRUE)
                    # Call wget
                    system( X )           
                  }, 
                  .parallel = TRUE
                  )
            )

wprint(paste("Extracted FastQ for", AE_ID), LOGFILE)

