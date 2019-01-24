#!/usr/bin/python

__author__ = "Manuel Belmadani"
__copyright__ = "Copyright 2019, The Pavlidis Lab., Michael Smith Laboratories, University of British Columbia"
__credits__ = ["Manuel Belmadani"]
__license__ = "LGPL"
__version__ = "1.0.0"
__maintainer__ = "Manuel Belmadani"
__email__ = "manuel.belmadani@msl.ubc.ca"
__status__ = "Production"
__description__ = "Using an input xml MINIML file, make a table of GSM,GPL,SRX"

# TODO: This should really just be an extension of parse_miniml.py

import sys
import xml.etree.ElementTree
from collections import defaultdict

filepath = None
if len(sys.argv) != 2:
    print "Usage:"
    print sys.argv[0], "GSEXXXXXX.xml"
    exit(-1)
else:
    filepath = sys.argv[1]
    # platform = sys.argv[2]

root = xml.etree.ElementTree.parse(filepath).getroot()
DUMMY="{http://www.ncbi.nlm.nih.gov/geo/info/MINiML}"

SAMPLE_NODE = DUMMY+"Sample"
TYPE_NODE = DUMMY+"Type" # Should be SRA
LIBRARYSTRAT_NODE = DUMMY+"Library-Strategy" # Should be RNA-Seq
RELATION_NODE = DUMMY+"Relation" # Type should be SRA, Target should have the SRX
PLATFORM_NODE = DUMMY+"Platform-Ref"

ACCEPTED_LIBRARYSTRAT = ["RNA-Seq"]
ACCEPTED_RELATIONS = ["SRA"]
# ACCEPTED_PLATFORMS = [platform]
BLACKLISTED_PLATFORMS = []

# Dictionary structure: Sample ID -> GPL,RUN 
GSM_SRX = defaultdict(list)

def tabulate(root):
    for x in root.findall(SAMPLE_NODE):
        SAMPLE_ID = x.get("iid")
        REJECT = False
        matches = []

        for y,z in zip(x.findall(LIBRARYSTRAT_NODE), x.findall(PLATFORM_NODE)):
            # Check library strategy and platform compliance.
            if y.text not in ACCEPTED_LIBRARYSTRAT or \
               z.get("ref") in BLACKLISTED_PLATFORMS:
                REJECT = True
                continue
            else:
                # Data has not been rejected
                #  E.g. Data is RNA-Seq (or other accepted formats.)
                REJECT = False
                            
            for y in x.findall(RELATION_NODE):
                if y.get("type") not in ACCEPTED_RELATIONS:
                    # Skip relations that are not SRA
                    pass
                else:
                    matches.append(z.get("ref") + " " + y.get("target"))
                      
        # Iterate over matches to populated dictionary
        if len(matches) < 1: continue
        GSM_SRX[SAMPLE_ID] = matches        

    return GSM_SRX

d = tabulate(root)
for key in d.keys():
    v = d[key]
    for value in v:
        print key, value            
