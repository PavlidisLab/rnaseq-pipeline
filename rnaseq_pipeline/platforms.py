from abc import abstractmethod
from bioluigi.tasks import cutadapt

class Platform:
    def __init__(self, instrument):
        self.instrument = instrument

    @abstractmethod
    def get_trim_single_end_reads_task(r1, dest, **kwargs):
        pass

    @abstractmethod
    def get_trim_paired_reads_task(r1,r2, r1_dest, r2_dest, **kwargs):
        pass

class BgiPlatform(Platform):
    # http://seqanswers.com/forums/showthread.php?t=87647 led to a document
    # from BGI mentioning to the following sequences:
    FORWARD_FILTER = 'AAGTCGGAGGCCAAGCGGTCTTAGGAAGACAA'
    REVERSE_FILTER = 'AAGTCGGATCGTAGCCATGTCGTTCTGTGAGCCAAGGAGTTG'

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
        raise NotImplementedError('Trimming paired reads is not supported for this platform.')

class IlluminaPlatform(Platform):
    UNIVERSAL_ADAPTER = 'AGATCGGAAGAGC'

    @staticmethod
    def get_trim_single_end_reads_task(r1, dest, **kwargs):
        return cutadapt.TrimReads(
                r1,
                dest,
                adapter_3prime=IlluminaPlatform.UNIVERSAL_ADAPTER,
                **kwargs)

    @staticmethod
    def get_trim_paired_reads_task(r1, r2, r1_dest, r2_dest, **kwargs):
        return cutadapt.TrimPairedReads(
                r1, r2,
                r1_dest, r2_dest,
                adapter_3prime=IlluminaPlatform.UNIVERSAL_ADAPTER,
                reverse_adapter_3prime=IlluminaPlatform.UNIVERSAL_ADAPTER,
                **kwargs)
