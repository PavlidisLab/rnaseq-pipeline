from scheduler.miniml_utils import find_rnaseq_geo_samples, collect_geo_samples_info

def test_extract_rnaseq_gsm():
    assert len(find_rnaseq_geo_samples('tests/data/GSE100007_family.xml')) > 0

def test_collect_geo_samples_info():
    assert len(collect_geo_samples_info('tests/data/GSE100007_family.xml')) > 0
