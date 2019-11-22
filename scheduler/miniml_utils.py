#!/usr/bin/python

__author__ = 'Manuel Belmadani'
__copyright__ = 'Copyright 2017, The Pavlidis Lab., Michael Smith Laboratories, University of British Columbia'
__credits__ = ['Manuel Belmadani']
__license__ = 'LGPL'
__version__ = '1.0.1'
__maintainer__ = 'Manuel Belmadani'
__email__ = 'manuel.belmadani@msl.ubc.ca'
__status__ = 'Production'
__description__ = 'Parse MINiML file for RNA-Seq/miRNA-Seq datasets files to be downloaded.'

import xml.etree.ElementTree

ns = {'miniml': 'http://www.ncbi.nlm.nih.gov/geo/info/MINiML'}


def find_rnaseq_geo_samples(f):
    """
    Extract all GSM identifiers relating to RNA-Seq experiments.
    """
    root = xml.etree.ElementTree.parse(f).getroot()

    gsm_identifiers = set()

    for x in root.findall('miniml:Sample', ns):
        gsm_id = x.find("miniml:Accession[@database='GEO']", ns).text
        library_strategy = x.find('miniml:Library-Strategy', ns).text
        sra_relations = x.findall("miniml:Relation[@type='SRA']", ns)
        if library_strategy == 'RNA-Seq' and sra_relations:
            gsm_identifiers.add(gsm_id)

    return gsm_identifiers

def collect_geo_samples_info(f):
    """
    Collect information related to all the GSM identifier stored.
    """
    root = xml.etree.ElementTree.parse(f).getroot()
    sample_geo_metadata = {}
    for sample in root.findall('miniml:Sample', ns):
        gse_id = sample.find("miniml:Accession[@database='GEO']", ns).text
        platform_id = sample.find('miniml:Platform-Ref', ns).get('ref')
        srx_uri = sample.find("miniml:Relation[@type='SRA']", ns).get('target')
        sample_geo_metadata[gse_id] = (gse_id, platform_id, srx_uri)
    return sample_geo_metadata
