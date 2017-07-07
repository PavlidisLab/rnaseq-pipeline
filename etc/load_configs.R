#' ---
#' title: "Load Configs (R version)"
#' author: "Manuel Belmadani"
#' date: "November 28th 2016"
#' description: "Load project configuration variables for R scripts."
#' ---
#'

CONFIGS_PATH_CLEAN <- system("sh ../etc/load_configs.sh 2>&1 | tail -n1 | cut -d\"'\" -f2  " ,
                             intern=TRUE)
print(paste("Configurations generated at:", CONFIGS_PATH_CLEAN))

print(paste0("TMP config file created at ", CONFIGS_PATH_CLEAN))
CONFIGS <- read.csv(CONFIGS_PATH_CLEAN, sep="=", header=FALSE, col.names=c("Key", "Value") )
CONFIGS

KEY='ROOT_DIR'
for (KEY in CONFIGS$Key){
    BEFORE <- paste0("[$]",KEY)
    for ( TOREPLACE in which(CONFIGS$Key == KEY) ){
        AFTER <- CONFIGS$Value[ TOREPLACE ]
        CONFIGS$Value <- gsub(BEFORE, AFTER, CONFIGS$Value)
    }
}

# CONFIGS after shell expansion
KV <- CONFIGS
#CONFIGS <- list()
for ( i in 1:nrow(KV) ){
    KEY <- as.character(KV$Key[i])
    VALUE <- as.character(KV$Value[i])
    #print(paste("PRESIGNED", KEY, "TO", VALUE))
    
    if (grepl("#", KEY) | length(gsub(x=VALUE, pattern=" ", replacement="")) < 1) {
      next
    }

    if (KEY == "NCPU_NICE"){
       # FIXME: Hack. Couldn't get the subshell expansion to work elegantly.
        VALUE <- sqrt(NCPU)
    } else {
       # print(paste("Attemtping to convert VALUE", VALUE))
       VALUE <- system( paste0("VAR=", VALUE, " && echo $VAR"), intern=TRUE)
    }
    


    if (length(VALUE) < 1){
        next
    }    

    if (grepl(pattern="^\\d+$", VALUE)){
        VALUE <- as.numeric(VALUE)
    }
    
    assign(KEY,VALUE)
    print(paste("ASSIGNED", KEY, "TO", VALUE))
}

#print("Created variable CONFIGS")
#print("Available configurations:")
#print(KV$Key)

print("Configurations loaded for Rscript.")
