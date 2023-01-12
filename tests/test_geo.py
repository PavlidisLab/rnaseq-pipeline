from rnaseq_pipeline.sources.geo import match_geo_platform
from rnaseq_pipeline.platforms import IlluminaPlatform

def test_parse_illumina_platform():
    platform = match_geo_platform('GPL30172')
    assert isinstance(platform, IlluminaPlatform)
    assert platform.name == 'Illumina'
    assert platform.instrument == 'NextSeq 2000'

