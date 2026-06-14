# Waspid AI OS
# DEPRECATED: This module is deprecated and will be removed in a future release.
# Please use waspid.app_server.app instead.
#
# For backward compatibility, this module re-exports the app from waspid.app_server.app.
# Note: This module does NOT include middleware setup. Use waspid.server.listen or
# waspid.app_server.app directly for the fully configured application.

from waspid.app_server.app import (
    app,
    authentication_error_handler,
    combine_lifespans,
    mcp_app,
)

__all__ = ['app', 'mcp_app', 'combine_lifespans', 'authentication_error_handler']
