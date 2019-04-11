#!/usr/bin/python

__author__ = "Manuel Belmadani"
__copyright__ = "Copyright 2017, The Pavlidis Lab., Michael Smith Laboratories, University of British Columbia"
__credits__ = ["Manuel Belmadani"]
__license__ = "LGPL"
__version__ = "1.0.1"
__maintainer__ = "Manuel Belmadani"
__email__ = "manuel.belmadani@msl.ubc.ca"
__status__ = "Production"
__description__ = "Parse MINiML file for RNA-Seq/miRNA-Seq datasets files to be downloaded."

import sys
import xml.etree.ElementTree
from collections import defaultdict

filepath= None
if len(sys.argv) < 2:
    print "Usage:"
    print sys.argv[0], "GSEXXXXXX"
    exit(-1)
else:
    filepath = sys.argv[1]

root = xml.etree.ElementTree.parse(filepath).getroot()
DUMMY="{http://www.ncbi.nlm.nih.gov/geo/info/MINiML}"

SAMPLE_NODE = DUMMY+"Sample"
TYPE_NODE = DUMMY+"Type" # Should be SRA
LIBRARYSTRAT_NODE = DUMMY+"Library-Strategy" # Should be RNA-Seq
RELATION_NODE = DUMMY+"Relation" # Type should be SRA, Target should have the SRX

ACCEPTED_LIBRARYSTRAT = ["RNA-Seq", "miRNA-Seq", "MeDIP-Seq"]
ACCEPTED_RELATIONS = ["SRA"]

GSM_SRX = defaultdict(list)

def tabulate(root):
    for x in root.findall(SAMPLE_NODE):
        SAMPLE_ID = x.get("iid")
        #print SAMPLE_ID        

        for y in x.findall(LIBRARYSTRAT_NODE):
            targets = []
            REJECT = False
            if y.text not in ACCEPTED_LIBRARYSTRAT:
                #print "Rejected on Library strategy.", y.text
                REJECT = True
                continue
            else:
                # Data is RNA-Seq (or other accepted formats.)            
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
            
