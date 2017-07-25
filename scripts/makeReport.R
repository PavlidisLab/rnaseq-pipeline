#' ---
#' title: "Report for gene/isoform counts."
#' author: "Manuel Belmadani"
#' date: "January 9th 2017"
#' description: "For one count matrix, generate statistics to describe relations between samples. For two count matrices, generate statistics to describe relations between matrices."
#' ---

###
# Imports
#library(qtlcharts)
library(corrplot)
library(Hmisc)
###

###
# Check parameters before anything else.
#
if ( is.na(commandArgs(TRUE)[1]) ){
  # print Usage menu.
  me <- sub(".*=", "", commandArgs()[4])
  print("Usage:")
  print( paste("Rscript", me, "GSE123456.countMatrix.genes") )
  q(save="no")
}
LOGFILE <- "plots/report.txt"
###

###
# Functions
perSampleReport <- function(counts){
  ## Report
  sampleSummary <- summary(counts[ ,2:ncol(counts) ])
  wprint( "------Summary of sample expression counts.------" )
  wprint(sampleSummary)
  wprint( "------------------------------------------------" )
  wprint( "" )
  
  # Calculate ranked correlation between samples.
  correlation <- cor(counts, method="spearman")
  
  wprint( "------Summary of correlation scores.      ------" )
  wprint(summary(correlation))
  wprint( "------------------------------------------------" )
  wprint( "" )
  # Calculate standard deviation accross samples.
  deviationsByGene <- apply(counts, 1, sd)

  wprint( "-----Summary of standard deviation by Gene.-----" )
  wprint(summary(deviationsByGene))
  wprint( "------------------------------------------------" )
  wprint( "" )
  ##

  ## Plotting
  # Plot matrix of correlation scores (Samples x Samples)
  plotCorrelation(correlation)
  
  # Plot histogram of per gene count deviation.
  plotDeviationByGene(deviationsByGene)

  # Plot reverse cumulative distribution.
  plotReverseCumulativeDistribution(deviationsByGene)
  ##
}

plotCorrelation <- function(x){
  # Plot correlation between samples.
  png(filename="plots/correlations.png")
  corrplot(x)
  dev.off()
}

plotDeviationByGene <- function(x) {
  # Plot a histogram for a vector of std. deviations.
  r <- hist(x)
  
  png(filename="plots/deviationsByGene.png")
  plot(r$breaks[-1], r$counts, log='y',
       xlab='Std.Dev.',
       ylab='Genes',
       main='Gene distribution by Std.Dev.'
       )  
  dev.off()
}

plotReverseCumulativeDistribution <- function(x){
  # Compute and plot the reverse cumulative distribution
  f <- ecdf(x)
  png(filename="plots/recd.png")
  plot(1-f(x),
       x,
       type='p',
       xlab='Genes',
       ylab='Std.Dev.',
       main='Std.Dev. per Gene'
       )
  dev.off()
}

loadCounts <- function(file) {
  # Returns a table of counts, Samples X Genes|Isoform
  counts <- read.csv(file, sep="\t", header=TRUE)
  rownames(counts) <- counts$X
  ss <- subset(counts, select=-c(X))
  return(ss)
}

# Function definitions
wprint <- function(X, file = LOGFILE, append = TRUE){
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
  capture.output(X, file = file, append = append)  
}

###

###
# Load parameters
file1 <- commandArgs(TRUE)[1] # e.g "GSE123456.countMatrix.genes"
file2 <- commandArgs(TRUE)[2] # Idem.

counts1 <- loadCounts(file1)
if (is.null(file2)) {
  counts2 <- loadCounts(file2)
} else {
  counts2 <- NULL
}
###


###
# Main

# Per-sample ranked correlation.
write("=======  RNA-seq count report =======", LOGFILE, append=FALSE)
perSampleReport(counts1)
