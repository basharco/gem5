from m5.objects import (
    BadAddr,
    BaseXBar,
    SystemXBar,
    Port,
    Cache,
    L2XBar
)

from ....isas import ISA
from ....utils.override import *
from ...boards.abstract_board import AbstractBoard
from .abstract_classic_cache_hierarchy import AbstractClassicCacheHierarchy
from ..abstract_three_level_cache_hierarchy import AbstractThreeLevelCacheHierarchy
from .caches.l1dcache import L1DCache
from .caches.l1icache import L1ICache
from .caches.l2cache import L2Cache
from .caches.l3cache import L3Cache
from .caches.mmu_cache import MMUCache

class PrivateL1PrivateL2SharedL3CacheHierarchy(AbstractClassicCacheHierarchy):
    """
    A cache setup where each core has a private L1 Data and Instruction Cache
    and a private L2 Cache, and a L3 Cache is shared with all cores. The shared
    L3 cache is mostly inclusive with respect to the split I/D L1 and MMU
    caches.
    """

    @staticmethod
    def _get_default_membus() -> SystemXBar:
        """
        A method used to obtain the default memory bus of 64 bit in width for
        the PrivateL1PrivateL2SharedL3 CacheHierarchy.

        :returns: The default memory bus for the PrivateL1PrivateL2
                  CacheHierarchy.

        """
        membus = SystemXBar(width=64)
        membus.badaddr_responder = BadAddr()
        membus.default = membus.badaddr_responder.pio
        return membus
    
    def __init__(
        self,
        l1d_size: str,
        l1i_size: str,
        l2_size: str,
        l3_size: str,
        l1d_assoc: int = 8,
        l1i_assoc: int = 8,
        l2_assoc: int = 16,
        l3_assoc: int = 32,
        membus: BaseXBar = _get_default_membus.__func__(),
    ) -> None:
        AbstractClassicCacheHierarchy.__init__(self=self)
        AbstractThreeLevelCacheHierarchy.__init(
            self,
            l1d_size=l1d_size,
            l1i_size=l1i_size,
            l2_size=l2_size,
            l3_size=l3_size,
            l1d_assoc=l1d_assoc,
            l1i_assoc=l1i_assoc,
            l2_assoc=l2_assoc,
            l3_assoc=l3_assoc
        )

        self.membus = membus

    @overrides(AbstractClassicCacheHierarchy)
    def get_mem_side_port(self) -> Port:
        return self().get_mem_side_port()
    
    @overrides(AbstractClassicCacheHierarchy)
    def get_cpu_side_port(self) -> Port:
        return self().get_cpu_side_port()
    
    @overrides(AbstractClassicCacheHierarchy)
    def incorporate_cache(self, board: AbstractBoard) -> None:
        board.connect_system_port(self.membus.cpu_side_ports)

        for _, port in board.get_memory().get_memory_ports():
            self.membus.mem_side_ports = port

        self.l1icaches = [
            L1ICache(
                size=self._l1i_size,
                assoc=self._l1i_assoc, # defaults ot 8
                tag_latency=1, # defaults to 1
                data_latency=1, # defaults to 1
                response_latency=1, # defaults to 1
                mshrs=8, # defaults to 16
                tgts_per_mshr=20, # defaults to 20
                writeback_clean=True, # defaults to True
                # PrefetcherCls=
            )
            for _ in range(board.get_processor().get_num_cores())
        ]
        self.l1dcaches = [
            L1DCache(
                size=self._l1i_size,
                assoc=self._l1i_assoc, # defaults ot 8
                tag_latency=1, # defaults to 1
                data_latency=1, # defaults to 1
                response_latency=1, # defaults to 1
                mshrs=8, # defaults to 16
                tgts_per_mshr=20, # defaults to 20
                writeback_clean=True, # defaults to True
                # PrefetcherCls=
            )
            for _ in range(board.get_processor().get_num_cores())
        ]
        self.l2buses = [
            L2XBar() for i in range(board.get_processor().get_num_cores())
        ]
        self.l2caches = [
            L2Cache(
                size=self._l2_size,
                assoc=self._l2_assoc, # defaults ot 16
                tag_latency=10, # defaults to 10
                data_latency=10, # defaults to 10
                response_latency=1, # defaults to 1
                mshrs=20, # defaults to 20
                tgts_per_mshr=12, # defaults to 12
                writeback_clean=False, # defaults to False
                clusivity="mostly_incl", # defaults to "mostly_incl"
                # PrefetcherCls=
            )
            for _ in range(board.get_processor().get_num_cores())
        ]
        self.l3bus = L2XBar()
        self.l3cache = L3Cache(
            size=self._l2_size,
            assoc=self._l2_assoc, # defaults ot 32
            tag_latency=15, # defaults to 15
            data_latency=15, # defaults to 15
            response_latency=1, # defaults to 1
            mshrs=26, # defaults to 26
            tgts_per_mshr=8, # defaults to 8
            writeback_clean=False, # defaults to False
            clusivity="mostly_incl", # defaults to "mostly_incl"
            # PrefetcherCls=
        )
        # ITLB Page walk caches
        self.iptw_caches = [
            MMUCache(
                size="8KiB",
                assoc=4, # defaults to 4
                tag_latency=1, # defaults to 1
                data_latency=1, # defaults to 1
                response_latency=1, # defaults to 1
                mshrs = 20, # defaults to 20
                tgts_per_mshr = 12, # defaults to 12
                writeback_clean=True # defaults to clean
            )
            for _ in range(board.get_processor().get_num_cores())
        ]
        # DTLB Page walk caches
        self.dptw_caches = [
            MMUCache(
                size="8KiB",
                assoc=4, # defaults to 4
                tag_latency=1, # defaults to 1
                data_latency=1, # defaults to 1
                response_latency=1, # defaults to 1
                mshrs = 20, # defaults to 20
                tgts_per_mshr = 12, # defaults to 12
                writeback_clean=True # defaults to clean
            )
            for _ in range(board.get_processor().get_num_cores())
        ]

        if board.has_coherent_io():
            self._setup_io_cache(board)

        for i, cpu in enumerate(board.get_processor().get_cores()):
            cpu.connect_icache(self.l1icaches[i].cpu_side)
            cpu.connect_dcache(self.l1dcaches[i].cpu_side)

            self.l1icaches[i].mem_side = self.l2buses[i].cpu_side_ports
            self.l1dcaches[i].mem_side = self.l2buses[i].cpu_side_ports

            self.l2buses[i].mem_side_ports = self.l2caches[i].cpu_side

            self.l2caches[i].mem_side = self.l3bus.cpu_side_ports

            cpu.connect_walker_ports(
                self.iptw_caches[i].cpu_side, self.dptw_caches[i].cpu_side
            )

            if board.get_processor().get_isa() == ISA.X86:
                int_req_port = self.membus.mem_side_ports
                int_resp_port = self.membus.cpu_side_ports
                cpu.connect_interrupt(int_req_port, int_resp_port)
            else:
                cpu.connect_interrupt()

        self.l3bus.mem_side_ports = self.l3cache.cpu_side
        self.l3cache.mem_side = self.membus.cpu_side_ports

    def _setup_io_cache(self, board: AbstractBoard) -> None:
        """Create a cache for coherent I/O connections"""
        self.iocache = Cache(
            assoc=8,
            tag_latency=50,
            data_latency=50,
            response_latency=50,
            mshrs=20,
            size="1kB",
            tgts_per_mshr=12,
            addr_ranges=board.mem_ranges,
        )
        self.iocache.mem_side = self.membus.cpu_side_ports
        self.iocache.cpu_side = board.get_mem_side_coherent_io_port()