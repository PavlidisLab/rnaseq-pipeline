#' ---
#' title: "Load Configs (R version)"
#' author: "Manuel Belmadani"
#' date: "November 28th 2016"
#' description: "Load project configuration variables for R scripts."
#' ---
#'

CONFIGS_PATH <- "common.cfg"
system("sh load_configs.sh")
CONFIGS <- read.csv(CONFIGS_PATH, sep="=", header=FALSE, col.names=c("Key", "Value") )
CONFIGS

KEY='ROOT_DIR'
for (KEY in CONFIGS$Key){
    BEFORE <- paste0("[$]",KEY)
    AFTER <- CONFIGS$Value[ which(CONFIGS$Key == KEY) ]
    CONFIGS$Value <- gsub(BEFORE, AFTER, CONFIGS$Value)
}

# CONFIGS after shell expansion
KV <- CONFIGS
CONFIGS <- list()
for ( i in 1:nrow(KV) ){
    KEY <- as.character(KV$Key[i])
    VALUE <- as.character(KV$Value[i])
    if (grepl("#", KEY)) {
      next
    }
    assign(KEY,VALUE)
    print(paste("ASSIGNED", KEY, "TO", VALUE))
}

#print("Created variable CONFIGS")
#print("Available configurations:")
#print(KV$Key)

print("Configurations loaded for Rscript.")
