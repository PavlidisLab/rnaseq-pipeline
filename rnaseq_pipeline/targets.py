import enum
import logging
import shutil
from datetime import timedelta
from os.path import join, exists, getctime, getmtime
from time import time
from typing import Optional

import luigi

from .gemma import gemma_api

logger = logging.getLogger(__name__)

class RsemReference(luigi.Target):
    """
    Represents the target of rsem-prepare-reference script.
    """

    def __init__(self, path, taxon):
        self.path = path
        self.taxon = taxon

    @property
    def prefix(self):
        return join(self.path, '{}_0'.format(self.taxon))

    def exists(self):
        exts = ['chrlist', 'grp', 'idx.fa', 'n2g.idx.fa', 'seq', 'ti', 'transcripts.fa']
        return all(exists(self.prefix + '.' + ext)
                   for ext in exts)

class GemmaDataVectorType(enum.StrEnum):
    """Data vector types in Gemma"""
    RAW = 'ubic.gemma.model.expression.bioAssayData.RawExpressionDataVector'
    SINGLE_CELL = 'ubic.gemma.model.expression.bioAssayData.SingleCellExpressionDataVector'
    PROCESSED = 'ubic.gemma.model.expression.bioAssayData.ProcessedExpressionDataVector'

class GemmaDatasetQuantitationType(luigi.Target):
    """Represents a quantitation type associated to a Gemma dataset."""

    def __init__(self,
                 dataset: int | str,
                 quantitation_type: Optional[int | str] = None,
                 vector_type: Optional[GemmaDataVectorType] = None):
        """
        :param dataset: The dataset identifier to lookup (either ID or short name)
        :param quantitation_type: The identifier of the quantitation type (either name or ID) or the preferred one of
        set to None.
        :param vector_type: The type of vector to consider, or any if set to None.
        """
        self.dataset = dataset
        self.quantitation_type = quantitation_type
        self.vector_type = vector_type

    def exists(self):
        return any(
            (quantitation_type['id'] == self.quantitation_type or quantitation_type['name'] == self.quantitation_type
             if self.quantitation_type else quantitation_type['isPreferred'])
            and (quantitation_type['vectorType'] == self.vector_type.value if self.vector_type else True)
            for quantitation_type in gemma_api.quantitation_types(self.dataset))

    def __repr__(self):
        return f'GemmaDatasetQuantitationType(dataset={self.dataset}, quantitation_type={self.quantitation_type}, vector_type={self.vector_type})'

class GemmaDatasetHasBatch(luigi.Target):
    """
    Check if there is a BatchInformationFetchingEvent event attached
    """

    def __init__(self, dataset_short_name):
        self.dataset_short_name = dataset_short_name

    def exists(self):
        return gemma_api.dataset_has_batch(self.dataset_short_name)

class ExpirableLocalTarget(luigi.LocalTarget):
    """
    A local target that can expire according to a TTL value

    The TTL can either be a timedelta of a float representing the number of
    seconds past the creation time of the target that it will be considered
    fresh. Once that delay expired, the target will not be considered as
    existing.

    By default, change time is used as per os.path.getctime. Use the
    `use_mtime` parameter to use the modification time instead.
    """

    ttl: timedelta
    use_mtime: bool

    def __init__(self, path, ttl, use_mtime=False, **kwargs):
        super().__init__(path, **kwargs)
        if not isinstance(ttl, timedelta):
            self.ttl = timedelta(seconds=ttl)
        else:
            self.ttl = ttl
        self.use_mtime = use_mtime

    def is_stale(self):
        try:
            creation_time = getmtime(self.path) if self.use_mtime else getctime(self.path)
        except OSError:
            return False  # file is missing, assume non-stale
        return creation_time + self.ttl.total_seconds() < time()

    def exists(self):
        return super().exists() and not self.is_stale()

    def __repr__(self):
        return f'ExpirableLocalTarget(path={self.path}, format={self.format}, fs={self.fs}, ttl={self.ttl}, use_mtime={self.use_mtime})'

class DownloadRunTarget(luigi.Target):
    run_id: str
    files: list[str]
    layout: list[str]
    output_dir: Optional[str]

    _targets: list[luigi.LocalTarget]

    def __init__(self, run_id, files, layout, output_dir=None):
        """
        :param run_id: A run identifier
        :param files:  The output files of a run (e.g. R1.fastq.gz, R2.fastq.gz)
        :param layout: The layout of the files (e.g. R1, R2, L1, L2, but also R3, R4, etc.)
        :param output_dir: Directory in which all the files from the run are organized. If this is specified, remove()
        will remove the directory instead of removing each target individually.
        """
        if len(files) != len(layout):
            raise ValueError('The number of files must match the layout.')
        self.run_id = run_id
        self.files = files
        self.layout = layout
        self.output_dir = output_dir
        self._targets = [luigi.LocalTarget(f) for f in files]

    def exists(self):
        return all(t.exists() for t in self._targets)

    def remove(self):
        if self.output_dir:
            if exists(self.output_dir):
                try:
                    shutil.rmtree(self.output_dir)
                    logger.info('Removed %s.', self.output_dir)
                except OSError:
                    logger.exception('Failed to remove %s.', self.output_dir)
        else:
            for t in self._targets:
                if t.exists():
                    try:
                        t.remove()
                        logger.info('Removed %s.', repr(t))
                    except OSError:
                        logger.exception('Failed to remove %s.', repr(t))

    def __repr__(self):
        return f"DownloadRunTarget(run_id={self.run_id}, files={self.files}, layout={'|'.join(self.layout)})"
