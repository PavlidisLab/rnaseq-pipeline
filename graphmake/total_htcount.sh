#!/bin/bash
grep "^ENSG" $1 | awk '{print $2}' | paste -sd+ | bc