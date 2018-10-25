#!/bin/bash
set -eu

ipcs \
    | grep $(whoami) \
    | cut -f1 -d" " \
    | xargs -I@ ipcrm -M @
