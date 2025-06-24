from datetime import timedelta
from os.path import join, exists, getctime, getmtime
from time import time

import luigi

from .gemma import GemmaApi

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

class GemmaDatasetPlatform(luigi.Target):
    """
    Represents a platform associated to a Gemma dataset.
    """

    def __init__(self, dataset_short_name, platform):
        self.dataset_short_name = dataset_short_name
        self.platform = platform
        self._gemma_api = GemmaApi()

    def exists(self):
        # any platform associated must match
        return any(platform['shortName'] == self.platform
                   for platform in self._gemma_api.platforms(self.dataset_short_name))

    def __repr__(self):
        return 'GemmaDatasetPlatform(dataset_short_name={}, platform={})'.format(self.dataset_short_name, self.platform)

class GemmaDatasetHasBatch(luigi.Target):
    """
    Check if there is a BatchInformationFetchingEvent event attached
    """

    def __init__(self, dataset_short_name):
        self.dataset_short_name = dataset_short_name
        self._gemma_api = GemmaApi()

    def exists(self):
        return self._gemma_api.dataset_has_batch(self.dataset_short_name)

class ExpirableLocalTarget(luigi.LocalTarget):
    """
    A local target that can expire according to a TTL value

    The TTL can either be a timedelta of a float representing the number of
    seconds past the creation time of the target that it will be considered
    fresh. Once that delay expired, the target will not be considered as
    existing.

    By default, creation time is used as per os.path.getctime. Use the
    `use_mtime` parameter to use the modification time instead.
    """

    def __init__(self, path, ttl, use_mtime=False, format=None):
        super().__init__(path, format=format)
        if not isinstance(ttl, timedelta):
            self._ttl = timedelta(seconds=ttl)
        else:
            self._ttl = ttl
        self._use_mtime = use_mtime

    def is_stale(self):
        try:
            creation_time = getmtime(self.path) if self._use_mtime else getctime(self.path)
        except OSError:
            return False  # file is missing, assume non-stale
        return creation_time + self._ttl.total_seconds() < time()

    def exists(self):
        return super().exists() and not self.is_stale()
