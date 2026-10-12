from __future__ import annotations

import socket


def local_ipv4_addresses() -> list[str]:
    """All non-loopback IPv4 addresses assigned to this machine, sorted."""
    addresses: set[str] = set()

    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None):
            addr = info[4][0]
            if _is_usable_ipv4(addr):
                addresses.add(addr)
    except Exception:
        pass

    try:
        if socket.gethostbyname_ex(socket.gethostname()):
            for addr in socket.gethostbyname_ex(socket.gethostname())[2]:
                if _is_usable_ipv4(addr):
                    addresses.add(addr)
    except Exception:
        pass

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            addresses.add(s.getsockname()[0])
    except Exception:
        pass

    return sorted(addresses)


def _is_usable_ipv4(addr: str) -> bool:
    if ":" in addr:
        return False
    if addr.startswith("127."):
        return False
    if addr.startswith("169.254."):
        return False
    try:
        socket.inet_aton(addr)
        return True
    except OSError:
        return False


def host_addresses(port: int) -> list[dict]:
    return [
        {"ip": ip, "url": f"http://{ip}:{port}", "type": "LAN"}
        for ip in local_ipv4_addresses()
    ]
