#ps ux | grep [l]uigid | cut -f2 -d" " | xargs kill -9
ps ux | grep luigi[d] | grep -P " $SCHEDULER_PORT " | sed -e "s|\\W\+|,|g" | cut -f2 -d"," | xargs kill -9
