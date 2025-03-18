import luigi

from rnaseq_pipeline.platforms import IlluminaPlatform
from rnaseq_pipeline.sources.geo import match_geo_platform, DownloadGeoSampleMetadata, \
    DownloadGeoSeriesMetadata
from rnaseq_pipeline.utils import remove_task_output

def test_parse_illumina_platform():
    platform = match_geo_platform('GPL30172')
    assert isinstance(platform, IlluminaPlatform)
    assert platform.name == 'Illumina'
    assert platform.instrument == 'NextSeq 2000'

def test_download_geo_sample_metadata():
    t = DownloadGeoSampleMetadata('GSM6753395')
    remove_task_output(t)
    assert not t.complete()
    luigi.build([t], local_scheduler=True)
    assert t.complete()

def test_download_geo_series_metadata():
    t = DownloadGeoSeriesMetadata('GSE220114')
    remove_task_output(t)
    luigi.build([t], local_scheduler=True)
    assert t.complete()
