# DEPRECATED: This module is deprecated and will be removed in a future release.
# Please use waspid.app_server.app instead.
#
# For backward compatibility, this module re-exports the app from waspid.app_server.app.

from waspid.app_server.app import app

__all__ = ['app']
