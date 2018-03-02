#! /usr/local/bin/python2.7
# -*- coding: utf-8 -*-
__author__='jliu'
__maintainer__='mbelmadani'
__dateadded__='01-03-2018'
__description__="This script was added as part of the pipeline to load processed RNA-Seq experiments to Gemma."

import os

# entry point of script; after importing argparse.
def rnaseq_add():

    # read text file for experiments
    file = args.file

    # read the taxon
    taxon = args.taxon
    
    # read the count path
    if args.path:
        path = args.path

    # if a path isn't specified, use the current working directory.
    else:
        path = os.getcwd()
    
    with open(file) as file:
        EE_array = [line for line in file.read().splitlines()]

    # make sure file being read is closed
    if file:
        file.close()



    # print each gseid for diagnostic purposes
    for EE in EE_array:
        print "now parsing: {eeid}".format(eeid=EE)

    # run the commands
    for item in EE_array:

            # string to pass into bash shell
            bash_command = ("""$GEMMACMD rnaseqDataAdd -u $GEMMAUSERNAME -p $GEMMAPASSWORD -e {arg_item} -a Generic_{arg_taxon}_ensemblIds -count {arg_path}/{arg_item}_counts.genes -rpkm {arg_path}/{arg_item}_fpkm.genes""".format(arg_path = path, arg_taxon = taxon, arg_item=item))

            # execute command string
            os.system(bash_command)

    


# if we're running module as script, load argument parser.
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    # setup argument for destination of .txt file to parse from.
    parser.add_argument("-f", help = 'directory of file', dest = 'file', type = str)

    # setup argument for destination of count/rpkm files 
    parser.add_argument("-path", help = "the path where the count/rpkm data lies", dest = "path", type = str)

    # setup argument for taxon; options are human, mouse or rat.
    parser.add_argument("-taxon", help = 'taxon of experiment', dest = 'taxon', type = str)

    # variable that holds arguments; called from rnaseq_add()
    args = parser.parse_args()
    rnaseq_add()
