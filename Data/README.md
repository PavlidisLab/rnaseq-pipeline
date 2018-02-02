## What's in here?

This is an example/default location to store data in. You can change this with `etc/common.cfg`.

By default, the download scripts in `scripts/` and the scheduler will know to download data in `$DATA`, and the pipelines will know to look here if only a GEO series (e.g. GSEnnnnn) or ArrayExpress (E-MTAB-xxxxxx) ID is given.

The structure here should be `SERIES/SAMPLES/RUNS`. For example, 
```
Data/GSE99331/
              GSM2644261/
                        SRR6449897_1.fastq.gz*
                        SRR6449897_2.fastq.gz*
                        SRR6449897.sra*
                        SRR6449898_1.fastq.gz*
                        SRR6449898_2.fastq.gz*
                        SRR6449898.sra*
                         ...
                        SRR6449900_1.fastq.gz*
                        SRR6449900_2.fastq.gz*
                        SRR6449900.sra*
              GSM2644262/ ...
              GSM2644263/ ...
                ...
              GSM2644270/ ...
     GSE65766/
              GSM1605008/ ...
              GSM1605009/ ...
              GSM1605010/ ...
                ...           
```

The `.sra` files are downloaded from GEO and extracted with fastq-dump (wrapped in `Requirements/wonderdump.sh`.)

`arrayexpress_to_fastq.sh` works similarily but with ArrayExpress data, except gzipped fastq files are downloaded directly.

`SRP_to_fastq.sh` can also be used to download an SRA Project using the SRPxxxx identifier. 
