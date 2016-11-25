# The following packages are required to download GEO data.

source("http://bioconductor.org/biocLite.R")
install.packages("BiocInstaller", repos="http://bioconductor.org/packages/3.4/bioc")
biocLite("SRAdb")
biocLite("GEOquery")

install.packages("DBI")
install.packages("plyr")
install.packages("doMC")
