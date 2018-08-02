#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
__author__='jliu'
__maintainer__='mbelmadani'
__dateadded__='01-03-2018'
__description__="This script was added as part of the pipeline to load processed RNA-Seq experiments to Gemma."

import os

COUNT_PATH="../COUNTS/"


def rnaseq_add():
    """
    Call the gemma command line script and upload available count matrices from the pipeline.
    """
    bash_command = ("""$GEMMACLI rnaseqDataAdd -u $GEMMAUSERNAME -p $GEMMAPASSWORD """ +
                    """-e {arg_shortname} -a Generic_{arg_taxon}_ensemblIds -count {arg_path}/{arg_shortname}_counts.genes -rpkm {arg_path}/{arg_shortname}_fpkm.genes""".format(
            arg_path = args.path, 
            arg_taxon = args.taxon, 
            arg_shortname= args.shortname))

    print "Executing:"
    print bash_command

    retcode = os.system(bash_command)

    return retcode
        


if __name__ == '__main__':
    import argparse

    TAXONS = ['human', 'mouse', 'rat']

    # TODO: Need to get eeid from last API call when checking if Gemma already has the exp.
    parser = argparse.ArgumentParser()
    parser.add_argument("--shortname", help = 'Prefix to count/fpkm matrices name (e.g. GSE12345).', dest = 'shortname', type = str)
    parser.add_argument("--taxon", help = 'Taxon of experiment (Currently supported: '+ ",".join(TAXONS) +')', dest = 'taxon', type = str)
    parser.add_argument("--path", help = 'Directory where counts are stored.', dest = 'path', type = str, default=None)

    # Parse arguments to args object
    args = parser.parse_args()

    if args.taxon not in TAXONS:
        print "Unknown taxon", args.taxon
        print "Please use one from", TAXONS
        exit(-1)
    
    retcode = rnaseq_add()
    if retcode != 0:
        raise Exception("[ERROR] load_rnaseq_to_gemma.py; non-zero return code. ")
