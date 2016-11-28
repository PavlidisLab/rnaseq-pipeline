# The following packages are required to download GEO data.

source("http://bioconductor.org/biocLite.R")
install.packages("devtools", dependencies = TRUE)

# Insalling openssl
install.packages("openssl", configure.vars='INCLUDE_DIR=/home/ppavlidis/anaconda2/include/ LIB_DIR=/home/ppavlidis/anaconda2/lib/')
install.packages("httr")

biocLite("SRAdb")
biocLite("GEOquery")

install.packages("RSQLite")
install.packages("DBI")
install.packages("plyr")
install.packages("doMC")
