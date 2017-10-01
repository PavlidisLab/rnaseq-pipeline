LOGDIR=logs-luigi-$(echo $(hostname) | cut -f1 -d".")
UUID=$(uuidgen)

mkdir -p PIDS

luigid --background --pidfile PIDS/$UUID --logdir $LOGDIR/ --state-path STATE 
chmod -R a+rw $LOGDIR
chmod a+rw $LOGDIR/*
