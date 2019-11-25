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

"""
Utilities for querying various informations from MINiML metadata.
"""

ns = {'miniml': 'http://www.ncbi.nlm.nih.gov/geo/info/MINiML'}

def collect_geo_samples_with_rnaseq_data(f):
    """
    Extract all GSM identifiers relating to RNA-Seq experiments.
    """
    root = xml.etree.ElementTree.parse(f).getroot()

    gsm_identifiers = set()

    for x in root.findall('miniml:Sample', ns):
        gsm_id = x.find("miniml:Accession[@database='GEO']", ns)
        library_strategy = x.find('miniml:Library-Strategy', ns)
        sra_relation = x.find("miniml:Relation[@type='SRA']", ns)
        if gsm_id is None or library_strategy is None or sra_relation is None:
            continue
        if library_strategy.text == 'RNA-Seq':
            gsm_identifiers.add(gsm_id.text)

    return gsm_identifiers

def collect_geo_samples_info(f):
    """
    Collect information related to all the GSM identifier stored.

    Currently, this maps GEO Samples to their corresponding GEO Platforms and
    SRA project.
    """
    root = xml.etree.ElementTree.parse(f).getroot()
    sample_geo_metadata = {}
    for sample in root.findall('miniml:Sample', ns):
        gse_id = sample.find("miniml:Accession[@database='GEO']", ns)
        platform_id = sample.find('miniml:Platform-Ref', ns)
        sra_relation = sample.find("miniml:Relation[@type='SRA']", ns)
        if gse_id is None or platform_id is None or sra_relation is None:
            continue
        sample_geo_metadata[gse_id.text] = (platform_id.get('ref'), sra_relation.get('target'))
    return sample_geo_metadata
