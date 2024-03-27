from typing import Type

from m5.objects import (
    BasePrefetcher,
    Cache,
    Clusivity,
    StridePrefetcher,
)


class L3Cache(Cache):
    """
    A simple L3 Cache with default values.
    """

    def __init__(
        self,
        size: str,
        assoc: int = 32,
        tag_latency: int = 15,
        data_latency: int = 15,
        response_latency: int = 1,
        mshrs: int = 26,
        tgts_per_mshr: int = 8,
        writeback_clean: bool = False,
        clusivity: Clusivity = "mostly_incl",
        PrefetcherCls: Type[BasePrefetcher] = StridePrefetcher
    ):
        super().__init__()
        self.size = size
        self.assoc = assoc
        self.tag_latency = tag_latency
        self.data_latency = data_latency
        self.response_latency = response_latency
        self.mshrs = mshrs
        self.tgts_per_mshr = tgts_per_mshr
        self.writeback_clean = writeback_clean
        self.clusivity = clusivity
        self.prefetcher = PrefetcherCls()