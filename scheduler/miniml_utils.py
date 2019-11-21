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

def extract_rnaseq_gsm(f):
    """
    Extract all SRX identifiers relating to RNA-Seq experiments.
    """
    root = xml.etree.ElementTree.parse(f).getroot()
    DUMMY="{http://www.ncbi.nlm.nih.gov/geo/info/MINiML}"

    SAMPLE_NODE = DUMMY+"Sample"
    TYPE_NODE = DUMMY+"Type" # Should be SRA
    LIBRARYSTRAT_NODE = DUMMY+"Library-Strategy" # Should be RNA-Seq
    RELATION_NODE = DUMMY+"Relation" # Type should be SRA, Target should have the SRX

    ACCEPTED_LIBRARYSTRAT = ["RNA-Seq", "miRNA-Seq", "MeDIP-Seq", "ncRNA-Seq"]
    ACCEPTED_RELATIONS = ["SRA"]

    gsm_identifiers = set()

    for x in root.findall(SAMPLE_NODE):
        gsm = x.get("iid")

        is_rnaseq = any(y.text in ACCEPTED_LIBRARYSTRAT for y in x.findall(LIBRARYSTRAT_NODE))
        has_sra = any(y.get('type') in ACCEPTED_RELATIONS for y in x.findall(RELATION_NODE))

        # Data is RNA-Seq (or other accepted formats.)
        # print "Accepted Library strategy for", y.text
        if is_rnaseq and has_sra:
            gsm_identifiers.add(gsm)

    return gsm_identifiers
