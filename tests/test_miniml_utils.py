from rnaseq_pipeline.miniml_utils import *

def test_collect_geo_samples():
    collect_geo_samples('tests/data/GSE100007_family.xml')
    collect_geo_samples('tests/data/GSM69846.xml')

def test_collect_geo_samples_info():
    collect_geo_samples_info('tests/data/GSE100007_family.xml')
    collect_geo_samples_info('tests/data/GSM69846.xml')
