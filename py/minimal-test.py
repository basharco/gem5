from gem5.components.cachehierarchies.classic.private_l1_shared_l2_cache_hierarchy import PrivateL1SharedL2CacheHierarchy


cache_heirarchy = PrivateL1SharedL2CacheHierarchy(
    l1d_size="64kB",
    l1i_size="32kB",
    l2_size="2mB",
    l1d_assoc=16,
    l1i_assoc=8,
    l2_assoc=16
)