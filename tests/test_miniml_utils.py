from os.path import join, dirname

from rnaseq_pipeline.miniml_utils import *

test_data_dir = join(dirname(__file__), 'data')

def test_collect_geo_samples():
    collect_geo_samples(join(test_data_dir, 'GSE100007_family.xml'))
    collect_geo_samples(join(test_data_dir, 'GSM69846.xml'))

def test_collect_geo_samples_info():
    collect_geo_samples_info(join(test_data_dir, 'GSE100007_family.xml'))
    collect_geo_samples_info(join(test_data_dir, 'GSM69846.xml'))
