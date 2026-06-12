"""Outbound URL validation (SSRF protection).

Webhook-style connections store a user-supplied URL that the server
POSTs to. Without validation an attacker on a multi-tenant deployment
could point it at internal services (databases, sandbox control APIs)
or cloud metadata endpoints. This module rejects such URLs.

Checked at connection creation (fast feedback) and again at execution
time (defense in depth — DNS may change between save and use).
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

# Hostnames that must never be targets regardless of resolution.
_BLOCKED_HOSTS = {
    'localhost',
    'metadata.google.internal',
    'metadata.goog',
}


class UnsafeUrlError(ValueError):
    """The URL points somewhere the server must not call."""


def _is_blocked_ip(ip_text: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_text)
    except ValueError:
        return True  # unparseable resolution result: refuse
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def validate_outbound_url(url: str) -> None:
    """Raise UnsafeUrlError unless the URL is a safe public HTTPS target."""
    try:
        parsed = urlparse(url)
    except ValueError as exc:
        raise UnsafeUrlError(f'invalid URL: {exc}')

    if parsed.scheme != 'https':
        raise UnsafeUrlError('only https:// webhook URLs are allowed')
    host = parsed.hostname
    if not host:
        raise UnsafeUrlError('URL has no host')
    if host.lower().rstrip('.') in _BLOCKED_HOSTS:
        raise UnsafeUrlError(f'host not allowed: {host}')

    # Literal IP in the URL.
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        if _is_blocked_ip(host):
            raise UnsafeUrlError(f'IP address not allowed: {host}')
        return

    # Resolve the hostname and check every address it maps to.
    try:
        infos = socket.getaddrinfo(host, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise UnsafeUrlError(f'cannot resolve host {host}: {exc}')
    for info in infos:
        address = info[4][0]
        if _is_blocked_ip(address):
            raise UnsafeUrlError(
                f'host {host} resolves to a non-public address ({address})'
            )
