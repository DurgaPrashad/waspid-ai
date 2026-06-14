# Waspid AI OS
from server.auth.sheets_client import GoogleSheetsClient

from waspid.app_server.utils.logger import waspid_logger


def test_import():
    assert waspid_logger is not None
    assert GoogleSheetsClient is not None
