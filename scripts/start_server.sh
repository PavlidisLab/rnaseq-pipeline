#!/bin/bash

luigid --background --pidfile luigid-$(hostname).pid --logdir logs --state-path luigid-state-$(hostname).pickle
