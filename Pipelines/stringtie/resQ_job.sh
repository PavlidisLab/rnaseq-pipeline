#!/bin/bash

java -jar /space/bin/picard-tools-1.81/SamToFastq.jar  INPUT=/misc/pipeline42/mcgill/data/hg19_data/directional/B1-1_BA24_S185/accepted_hits.subsample.bam FASTQ=output_R1_.fq SECOND_END_FASTQ=output_R2_.fq