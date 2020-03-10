from rnaseq_pipeline.utils import *

def test_parse_illumina_fastq_header():
    fastq_header = IlluminaFastqHeader.parse('NIRVANA:127:C08GPACXX:4:1101:1487:2137')
    assert fastq_header.device == 'NIRVANA'
    IlluminaFastqHeader.parse('NIRVANA:127:C08GPACXX:4:1101:1487:2137')
    IlluminaFastqHeader.parse('HS32_14737:1:2104:16434:41647')
