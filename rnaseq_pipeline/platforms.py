from abc import abstractmethod

from bioluigi.tasks import cutadapt

class Platform:
    """
    :param name: Platform common name
    """
    name = None

    @abstractmethod
    def get_trim_single_end_reads_task(r1, dest, **kwargs):
        pass

    @abstractmethod
    def get_trim_paired_reads_task(r1, r2, r1_dest, r2_dest, **kwargs):
        pass

class BgiPlatform(Platform):
    """
    BGI platform

    http://seqanswers.com/forums/showthread.php?t=87647 led to a document from
    BGI mentioning to the adapter sequences.
    """
    FORWARD_FILTER = 'AAGTCGGAGGCCAAGCGGTCTTAGGAAGACAA'
    REVERSE_FILTER = 'AAGTCGGATCGTAGCCATGTCGTTCTGTGAGCCAAGGAGTTG'

    name = 'BGI'

    def __init__(self, instrument):
        self.instrument = instrument

    def get_trim_single_end_reads_task(self, r1, dest, **kwargs):
        return cutadapt.TrimReads(
            r1,
            dest,
            adapter_3prime=BgiPlatform.FORWARD_FILTER,
            **kwargs)

    def get_trim_paired_reads_task(self, r1, r2, r1_dest, r2_dest, **kwargs):
        return cutadapt.TrimPairedReads(
            r1, r2,
            r1_dest, r2_dest,
            adapter_3prime=BgiPlatform.FORWARD_FILTER,
            reverse_adapter_3prime=BgiPlatform.REVERSE_FILTER,
            **kwargs)

class IlluminaPlatform(Platform):
    """
    Illumina platform
    """
    UNIVERSAL_ADAPTER = 'AGATCGGAAGAGC'

    name = 'Illumina'

    def __init__(self, instrument):
        self.instrument = instrument

    def get_trim_single_end_reads_task(self, r1, dest, **kwargs):
        return cutadapt.TrimReads(
            r1,
            dest,
            adapter_3prime=IlluminaPlatform.UNIVERSAL_ADAPTER,
            **kwargs)

    def get_trim_paired_reads_task(self, r1, r2, r1_dest, r2_dest, **kwargs):
        return cutadapt.TrimPairedReads(
            r1, r2,
            r1_dest, r2_dest,
            adapter_3prime=IlluminaPlatform.UNIVERSAL_ADAPTER,
            reverse_adapter_3prime=IlluminaPlatform.UNIVERSAL_ADAPTER,
            **kwargs)

class IlluminaNexteraPlatform(Platform):
    """
    Illumina Nextera platform
    """
    NEXTERA_ADAPTER = 'CTGTCTCTTATACACATCT'

    name = 'Illumina Nextera'

    def __init__(self, instrument):
        self.instrument = instrument

    def get_trim_single_end_reads_task(self, r1, dest, **kwargs):
        return cutadapt.TrimReads(
            r1,
            dest,
            cut=12,
            adapter_3prime=IlluminaNexteraPlatform.NEXTERA_ADAPTER,
            **kwargs)

    def get_trim_paired_reads_task(self, r1, r2, r1_dest, r2_dest, **kwargs):
        raise NotImplementedError
