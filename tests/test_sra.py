from os.path import join, dirname
from xml.etree import ElementTree

import pytest

from rnaseq_pipeline.sources.sra import DownloadSraExperimentMetadata, DownloadSraProjectRunInfo, read_xml_metadata, \
    SequencingFileType, DownloadSraExperiment, read_runinfo

test_data_dir = join(dirname(__file__), 'data')

I1, I2, R1, R2 = SequencingFileType.I1, SequencingFileType.I2, SequencingFileType.R1, SequencingFileType.R2
R3 = SequencingFileType.R3
R4 = SequencingFileType.R4

single_cell_datasets = ['GSE274829',
                        'GSE302153',
                        'GSE247070',
                        'GSE297721',
                        'GSE297666',
                        'GSE296027',
                        'GSE295459',
                        'GSE283187',
                        'GSE272344',
                        'GSE272062',
                        'GSE263191',
                        'GSE247963',
                        'GSE268343',
                        'GSE249268',
                        'GSE279548',
                        'GSE261494',
                        'GSE280296',
                        'GSE261596',
                        'GSE267764',
                        'GSE287769',
                        'GSE163314',
                        'GSE254044',
                        'GSE214244',
                        'GSE202704',
                        'GSE181989',
                        'GSE218316',
                        'GSE196929',
                        'GSE198891',
                        'GSE174667',
                        'GSE212527',
                        'GSE141784',
                        'GSE247695',
                        'GSE233276',
                        'GSE232309',
                        'GSE212505',
                        'GSE179135',
                        'GSE264408',
                        'GSE283268',
                        'GSE242271',
                        'GSE205049',
                        'GSE255460',
                        'GSE184506',
                        'GSE222510',
                        'GSE222647',
                        'GSE268642',
                        'GSE173242',
                        'GSE241349',
                        'GSE284797',
                        'GSE180672',
                        'GSE240687',
                        'GSE234421',
                        'GSE234419',
                        'GSE226822',
                        'GSE226072',
                        'GSE216766',
                        'GSE213364',
                        'GSE212351',
                        'GSE157985',
                        'GSE219280',
                        'GSE263392',
                        'GSE266033',
                        'GSE275205',
                        'GSE254104',
                        'GSE235193',
                        'GSE230451',
                        'GSE234278',
                        'GSE245339',
                        'GSE235490',
                        'GSE227515',
                        'GSE212576',
                        'GSE269499',
                        'GSE218572',
                        'GSE237816']

@pytest.fixture(params=single_cell_datasets)
def single_cell_datasets_fixture(request):
    return request.param

def test_read_xml_metadata(single_cell_datasets_fixture):
    dataset = single_cell_datasets_fixture
    meta = read_xml_metadata(join(test_data_dir, dataset + '.xml'))
    assert len(meta) > 0
    common_layout = {}

    for run in meta:
        # make sure that all runs within an experiment share the same layout
        if run.srx not in common_layout:
            common_layout[run.srx] = run.layout
        # the order does not matter
        assert set(run.layout) == set(common_layout[run.srx])

def test_read_xml_metadata_GSE247070():
    meta = read_xml_metadata(join(test_data_dir, 'GSE247070.xml'))
    for run in meta:
        if run.srx in ['SRR26686276'
                       'SRR26686277'
                       'SRR26686278'
                       'SRR26686279'
                       'SRR26686280'
                       'SRR26686281'
                       'SRR26686282'
                       'SRR26686283'
                       'SRR26686284'
                       'SRR26686285'
                       'SRR26686286'
                       'SRR26686287'
                       'SRR26686288'
                       'SRR26686289'
                       'SRR26686290'
                       'SRR26686291']:
            assert run.layout == [I1, R1, R2]
        if run.srx in ['SRR26686292',
                       'SRR26686293',
                       'SRR26686294',
                       'SRR26686295',
                       'SRR26686296',
                       'SRR26686297',
                       'SRR26686298',
                       'SRR26686299',
                       'SRR26686300',
                       'SRR26686301',
                       'SRR26686302',
                       'SRR26686303',
                       'SRR26686304',
                       'SRR26686305',
                       'SRR26686306',
                       'SRR26686307']:
            assert run.layout == [R1, R2, I1, I2]

def test_read_xml_metadata_GSE297721():
    """
    This is a typical case where I1 and I2 are the same size and thus impossible to tell apart if the inputs to
    fastq-load.py are lacking. When that happens, we want to assume that the layout is I1, I2, R1, R2.
    """
    meta = read_xml_metadata(join(test_data_dir, 'GSE297721.xml'))
    for run in meta:
        assert run.layout == [I1, I2, R1, R2]

def test_read_xml_metadata_GSE274763():
    """This is an example where indices were in a separate run than the reads."""
    meta = read_xml_metadata(join(test_data_dir, 'GSE274763.xml'))
    for run in meta:
        # these are the problematic runs
        if run.srx in ('SRX25689947', 'SRX25689948', 'SRX25689949', 'SRX25689950', 'SRX25689951', 'SRX25689952',
                       'SRX25689953', 'SRX25689954'):
            continue
        assert run.layout == [R1, R2, I1, I2]

def test_read_xml_metadata_GSE181021():
    """This dataset is identified as paired-end, but only has one read file (which is a BAM)."""
    # TODO: also GSE267933 GSE217511, GSE178257 and GSE253640
    meta = read_xml_metadata(join(test_data_dir, 'GSE181021.xml'))
    for run in meta:
        assert run.layout == [I1, R1, R2]

def test_read_xml_metadata_GSE283187():
    """This dataset has a sample with 3 reads (R1, R2, R3) and an index (I1)."""
    meta = read_xml_metadata(join(test_data_dir, 'GSE283187.xml'))
    for run in meta:
        if run.srr == 'SRR31555331':
            assert run.layout == [I1, R1, I2, R2]
        else:
            assert run.layout == [I1, R1, R2]

def test_read_xml_metadata_GSE174332():
    """In this dataset, the files passed to fastq-load.py were compressed."""
    meta = read_xml_metadata(join(test_data_dir, 'GSE174332.xml'))
    for run in meta:
        if run.srr == 'SRR14511669':
            assert run.layout == [I1, R1, R2]
        else:
            assert run.layout == [R1, R2, I1]

def test_read_xml_metadata_GSE104493():
    """This dataset has I1 reads with zero length"""
    meta = read_xml_metadata(join(test_data_dir, 'GSE104493.xml'))
    for run in meta:
        assert run.layout == [R1]

def test_read_xml_metadata_GSE125536():
    """This dataset does not have SRAFile entries, but it has fastq-load.py inputs which can be used as a fallback."""
    meta = read_xml_metadata(join(test_data_dir, 'GSE125536.xml'))
    for run in meta:
        assert run.layout == [R1, R2, R3, R4]

def test_read_xml_metadata_GSE128117():
    """This dataset has a sample with 3 reads (R1, R2, R3) and an index (I1)."""
    meta = read_xml_metadata(join(test_data_dir, 'GSE128117.xml'))
    for run in meta:
        assert run.layout == [R1]

def test_read_xml_metadata_SRX26261721():
    meta = read_xml_metadata(join(test_data_dir, 'SRX26261721.xml'))
    assert len(meta) == 2
    assert meta[0].srx == 'SRX26261721'
    assert meta[0].srr == 'SRR30863712'
    assert meta[0].is_paired
    assert meta[0].fastq_filenames == ['S1_L001_I1_001.fastq.gz',
                                       'S1_L001_I2_001.fastq.gz',
                                       'S1_L001_R1_001.fastq.gz',
                                       'S1_L001_R2_001.fastq.gz']
    assert meta[0].layout == [SequencingFileType.I1, SequencingFileType.I2, SequencingFileType.R1,
                              SequencingFileType.R2]

    assert meta[1].srx == 'SRX26261721'
    assert meta[1].srr == 'SRR30863713'
    assert meta[1].is_paired
    assert meta[1].fastq_filenames == ['S1_L002_I1_001.fastq.gz',
                                       'S1_L002_I2_001.fastq.gz',
                                       'S1_L002_R1_001.fastq.gz',
                                       'S1_L002_R2_001.fastq.gz']
    assert meta[1].layout == [SequencingFileType.I1, SequencingFileType.I2, SequencingFileType.R1,
                              SequencingFileType.R2]

def test_SRX18986686():
    """This dataset has been submitted as BAMs, so we must use bamtofastq to extract FASTQs."""
    meta = read_xml_metadata(join(test_data_dir, 'SRX18986686.xml'))
    assert len(meta) == 1
    for run in meta:
        assert run.layout == [I1, R1, R2]
        assert run.use_bamtofastq
        assert run.fastq_filenames == [
            'bamtofastq_S1_L001_I1_001.fastq.gz',
            'bamtofastq_S1_L001_R1_001.fastq.gz',
            'bamtofastq_S1_L001_R2_001.fastq.gz']
        assert (run.bam_fastq_filenames == [
            's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L001_I1_001.fastq.gz',
            's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L001_R1_001.fastq.gz',
            's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L001_R2_001.fastq.gz',
            's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L002_I1_001.fastq.gz',
            's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L002_R1_001.fastq.gz',
            's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L002_R2_001.fastq.gz',
            's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L003_I1_001.fastq.gz',
            's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L003_R1_001.fastq.gz',
            's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L003_R2_001.fastq.gz',
            's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L004_I1_001.fastq.gz',
            's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L004_R1_001.fastq.gz',
            's10_MissingLibrary_1_HG3T5BGX2/bamtofastq_S1_L004_R2_001.fastq.gz',
            's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L001_I1_001.fastq.gz',
            's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L001_R1_001.fastq.gz',
            's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L001_R2_001.fastq.gz',
            's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L002_I1_001.fastq.gz',
            's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L002_R1_001.fastq.gz',
            's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L002_R2_001.fastq.gz',
            's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L003_I1_001.fastq.gz',
            's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L003_R1_001.fastq.gz',
            's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L003_R2_001.fastq.gz',
            's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L004_I1_001.fastq.gz',
            's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L004_R1_001.fastq.gz',
            's10_MissingLibrary_1_HHJT3BGX2/bamtofastq_S1_L004_R2_001.fastq.gz',
            's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L001_I1_001.fastq.gz',
            's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L001_R1_001.fastq.gz',
            's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L001_R2_001.fastq.gz',
            's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L002_I1_001.fastq.gz',
            's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L002_R1_001.fastq.gz',
            's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L002_R2_001.fastq.gz',
            's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L003_I1_001.fastq.gz',
            's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L003_R1_001.fastq.gz',
            's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L003_R2_001.fastq.gz',
            's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L004_I1_001.fastq.gz',
            's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L004_R1_001.fastq.gz',
            's10_MissingLibrary_1_HYHJ7BGXY/bamtofastq_S1_L004_R2_001.fastq.gz'])

@pytest.mark.skip('This run lacks statistics, reach out to SRA curators?')
def test_SRX17676975():
    runs = read_xml_metadata(join(test_data_dir, 'SRX17676975.xml'))
    assert len(runs) == 9

def test_GSE271769():
    runs = read_xml_metadata(join(test_data_dir, 'GSE271769.xml'))
    assert len(runs) == 16

    task = DownloadSraExperiment(srx='SRX25247848')
    task.run()

def test_SRX25247847():
    runs = read_xml_metadata(join(test_data_dir, 'SRX25247847.xml'))
    assert len(runs) == 1

def test_SRX26528278():
    runs = read_xml_metadata(join(test_data_dir, 'SRX26528278.xml'))
    assert len(runs) == 1

def test_SRR14827398():
    runs = read_xml_metadata(join(test_data_dir, 'SRR14827398.xml'))
    for run in runs:
        assert run.layout == [R1]

def test_SRX26188816():
    runs = read_xml_metadata(join(test_data_dir, 'SRX26188816.xml'))
    assert len(runs) == 1
    for run in runs:
        assert run.layout == [R1]

def test_read_runinfo():
    meta = read_runinfo(join(test_data_dir, 'SRX26261721.runinfo'))
    assert len(meta) == 2
    assert len(meta.columns) == 47
    assert meta.Run.tolist() == ['SRR30863712', 'SRR30863713']

def test_read_runinfo_no_header():
    meta = read_runinfo(join(test_data_dir, 'SRX12752257.runinfo'))
    assert len(meta) == 1
    assert len(meta.columns) == 47
    assert meta.Run.tolist() == ['SRR16550084']

def test_download_single_cell():
    task = DownloadSraExperimentMetadata(srx='SRX26261721')
    task.run()
    tree = ElementTree.parse(task.output().path)
    task2 = DownloadSraExperiment(srx='SRX26261721')
    task2.run()
    for run in task2.output():
        assert len(run.files) == 4
        assert run.layout == ('I1', 'I2', 'R1', 'R2')

def test_download_sra_experiment_run_info():
    task = DownloadSraExperimentMetadata(srx='SRX12752257')
    task.run()
    contents = task.output().open('r').read()
    assert contents
    assert task.complete()

def test_download_sra_project_run_info():
    task = DownloadSraProjectRunInfo(srp='SRP342859')
    task.run()
    contents = task.output().open('r').read()
    assert contents
    assert task.complete()
