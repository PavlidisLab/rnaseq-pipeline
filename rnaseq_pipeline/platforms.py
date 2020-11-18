from abc import abstractmethod
from bioluigi.tasks import cutadapt

class Platform:
    def __init__(self, instrument=None):
        self.instrument = instrument

    @abstractmethod
    def get_trim_single_end_reads_task(r1, dest, **kwargs):
        pass

    @abstractmethod
    def get_trim_paired_reads_task(r1,r2, r1_dest, r2_dest, **kwargs):
        pass

class BgiPlatform(Platform):
    @staticmethod
    def get_trim_single_end_reads_task(r1, dest, **kwargs):
        return cutadapt.TrimReads(
                r1,
                dest,
                adapter_3prime='AGATCGGAAGAGC',
                **kwargs)

    @staticmethod
    def get_trim_paired_reads_task(r1,r2, r1_dest, r2_dest, **kwargs):
        return cutadapt.TrimPairedReads(
                r1, r2,
                r1_dest, r2_dest,
                adapter_3prime='AGATCGGAAGAGC',
                **kwargs)

class IlluminaPlatform(Platform):
    @staticmethod
    def get_trim_single_end_reads_task(r1, dest, **kwargs):
        return cutadapt.TrimReads(
                r1,
                dest,
                adapter_3prime='AGATCGGAAGAGC',
                **kwargs)

    @staticmethod
    def get_trim_paired_reads_task(r1,r2, r1_dest, r2_dest, **kwargs):
        return cutadapt.TrimPairedReads(
                r1, r2,
                r1_dest, r2_dest,
                adapter_3prime='AGATCGGAAGAGC',
                **kwargs)
