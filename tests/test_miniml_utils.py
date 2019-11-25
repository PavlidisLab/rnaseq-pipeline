from scheduler.miniml_utils import *

def test_extract_rnaseq_gsm():
    collect_geo_samples_with_rnaseq_data('tests/data/GSE100007_family.xml')

def test_collect_geo_samples_info():
    collect_geo_samples_info('tests/data/GSE100007_family.xml')
