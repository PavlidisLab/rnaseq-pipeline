LOGDIR=logs-luigi-$(echo $(hostname) | cut -f1 -d".")
luigid --background --pidfile PIDFILE --logdir $LOGDIR/ --state-path STATE
chmod -R a+rw $LOGDIR
chmod a+rw $LOGDIR/*
