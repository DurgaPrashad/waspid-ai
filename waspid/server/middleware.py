# DEPRECATED: This module is deprecated and will be removed in a future release.
# Please use waspid.app_server.middleware instead.
#
# For backward compatibility, this module re-exports from waspid.app_server.middleware.

from waspid.app_server.middleware import (
    CacheControlMiddleware,
    InMemoryRateLimiter,
    LocalhostCORSMiddleware,
    RateLimitMiddleware,
)

__all__ = [
    'LocalhostCORSMiddleware',
    'CacheControlMiddleware',
    'InMemoryRateLimiter',
    'RateLimitMiddleware',
]
