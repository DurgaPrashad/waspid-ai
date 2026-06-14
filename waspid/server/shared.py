# Waspid AI OS
# DEPRECATED: This module is deprecated and will be removed in a future release.
# Please use waspid.app_server.shared instead.
#
# For backward compatibility, this module re-exports from waspid.app_server.shared.

from waspid.app_server.shared import (
    SecretsStoreImpl,
    SettingsStoreImpl,
    server_config,
    server_config_interface,
)

__all__ = [
    'server_config_interface',
    'server_config',
    'SettingsStoreImpl',
    'SecretsStoreImpl',
]
