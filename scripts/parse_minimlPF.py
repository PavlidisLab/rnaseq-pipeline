#!/usr/bin/python

__author__ = "Manuel Belmadani"
__copyright__ = "Copyright 2017, The Pavlidis Lab., Michael Smith Laboratories, University of British Columbia"
__credits__ = ["Manuel Belmadani"]
__license__ = "LGPL"
__version__ = "1.0.0"
__maintainer__ = "Manuel Belmadani"
__email__ = "manuel.belmadani@msl.ubc.ca"
__status__ = "Production"
__description__ = "Download a platform specific RNA-Seq dataset by parsing the MINiML files."

# TODO: This should really just be an extension of parse_miniml.py

import sys
import xml.etree.ElementTree
from collections import defaultdict

filepath= None
if len(sys.argv) < 3:
    print "Usage:"
    print sys.argv[0], "GSEXXXXXX", "GPLXXXXXX"
    exit(-1)
else:
    filepath = sys.argv[1]
    platform = sys.argv[2]

root = xml.etree.ElementTree.parse(filepath).getroot()
DUMMY="{http://www.ncbi.nlm.nih.gov/geo/info/MINiML}"

SAMPLE_NODE = DUMMY+"Sample"
TYPE_NODE = DUMMY+"Type" # Should be SRA
LIBRARYSTRAT_NODE = DUMMY+"Library-Strategy" # Should be RNA-Seq
RELATION_NODE = DUMMY+"Relation" # Type should be SRA, Target should have the SRX
PLATFORM_NODE = DUMMY+"Platform-Ref"

ACCEPTED_LIBRARYSTRAT = ["RNA-Seq"]
ACCEPTED_RELATIONS = ["SRA"]
#ACCEPTED_PLATFORMS = ["GPL17021", "GPL18694"]
ACCEPTED_PLATFORMS = [platform]


GSM_SRX = defaultdict(list)

def tabulate(root):
    for x in root.findall(SAMPLE_NODE):
        SAMPLE_ID = x.get("iid")
        #print SAMPLE_ID

        REJECT = False
        for y,z in zip(x.findall(LIBRARYSTRAT_NODE), x.findall(PLATFORM_NODE)):
            targets = []

            if y.text not in ACCEPTED_LIBRARYSTRAT or \
               z.get("ref") not in ACCEPTED_PLATFORMS:
                #print "Rejected on Library strategy."
                REJECT = True
                continue
            else:
                REJECT = False
            
            # Data has not been rejected
            #  E.g. Data is RNA-Seq (or other accepted formats.)
            targets = []
            for y in x.findall(RELATION_NODE):
                if y.get("type") not in ACCEPTED_RELATIONS:
                    #print "Rejected on relation type:", y.get("type")                
                    pass
                else:
                    targets.append(y.get("target"))
                        
        #print "Relation:", targets
        if len(targets) < 1: continue
        for target in targets:
            GSM_SRX[SAMPLE_ID].append(target)

    return GSM_SRX

d = tabulate(root)
for key in d.keys():
    v = d[key]
    for value in v:
        print key, value
            
