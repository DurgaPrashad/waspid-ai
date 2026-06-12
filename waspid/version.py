# DEPRECATED: This module is deprecated and will be removed in a future release.
# Please use waspid.app_server.version instead.
#
# For backward compatibility, this module re-exports from waspid.app_server.version.

from waspid.app_server.version import __package_name__, __version__, get_version

__all__ = ['__package_name__', '__version__', 'get_version']
