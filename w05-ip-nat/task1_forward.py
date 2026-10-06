#!/usr/bin/env python3
"""Week 5 · Task 1 — Subnets and longest-prefix match.

Textbook §4.3.2 (IPv4 addressing, CIDR) and §4.3.3 (forwarding).

Two things a router does with every packet: work out which prefixes the
destination falls inside, and pick the longest one. The second is the whole
of "longest prefix match", and it is the reason the internet's routing table
can hold a million entries and still be answerable.

You build both, from integers up. No `ipaddress` module - that library is
exactly the thing you are supposed to understand this week.

    python3 task1_forward.py --verify
"""
import argparse


UINT32_MASK = 0xFFFFFFFF

#32비트 정수로 변환(문자열 -> 정수)
def _parse_ipv4(address):
    """Convert dotted-decimal IPv4 to an unsigned 32-bit integer."""
    if not isinstance(address, str):
        raise ValueError("IPv4 address must be a string")
    #.을 기준으로 분리
    parts = address.split(".")
    if len(parts) != 4:
        raise ValueError(f"invalid IPv4 address: {address!r}")

    value = 0
    for part in parts:
        # Requiring decimal digits avoids accepting signs, hex, or empty octets.
        if not part or not part.isascii() or not part.isdecimal():
            raise ValueError(f"invalid IPv4 address: {address!r}")
        octet = int(part, 10)
        if octet > 255:
            raise ValueError(f"IPv4 octet out of range: {part!r}")
        value = (value << 8) | octet
    return value

#_parse_ipv4의 반대 작업(정수 -> 문자열)
def _format_ipv4(address):
    return ".".join(str((address >> shift) & 0xFF)
                    for shift in (24, 16, 8, 0))


def _mask(prefix_len):
    return 0 if prefix_len == 0 else (UINT32_MASK << (32 - prefix_len)) & UINT32_MASK


def parse_cidr(cidr):
    """'163.152.6.0/24' -> (network as int, prefix length).

    Requirements: reject a prefix length outside 0-32, and reject an address
    whose host bits are set when they should not be (163.152.6.5/24 is a
    common way to write a host, but it is not a network).
    """
    if not isinstance(cidr, str) or cidr.count("/") != 1:
        raise ValueError(f"invalid CIDR block: {cidr!r}")
    address_text, prefix_text = cidr.split("/", 1)
    if not prefix_text or not prefix_text.isascii() or not prefix_text.isdecimal():
        raise ValueError(f"invalid prefix length: {prefix_text!r}")
    prefix_len = int(prefix_text, 10)
    if not 0 <= prefix_len <= 32:
        raise ValueError("prefix length must be between 0 and 32")

    address = _parse_ipv4(address_text)
    mask = _mask(prefix_len)
    network = address & mask
    if address != network:
        raise ValueError(f"host bits are set in {cidr!r}")
    return network, prefix_len


def network_range(cidr):
    """'163.152.6.0/24' -> (first usable, last usable, broadcast) as strings.

    Careful at the edges. /31 and /32 do not have a usable host range in the
    ordinary sense - decide what you return and say so in observation.md.
    """
    network, prefix_len = parse_cidr(cidr)
    broadcast = network | (UINT32_MASK ^ _mask(prefix_len))

    # RFC 3021 treats both addresses of a /31 as usable on point-to-point
    # links.  A /32 denotes one host.  For both cases the usable interval is
    # therefore the complete block; for /0..../30, exclude network/broadcast.
    if prefix_len >= 31:
        first, last = network, broadcast
    else:
        first, last = network + 1, broadcast - 1
    return _format_ipv4(first), _format_ipv4(last), _format_ipv4(broadcast)


class ForwardingTable:
    """Longest-prefix-match forwarding.

    add(cidr, next_hop)  ·  lookup(address) -> next_hop or None

    The default route 0.0.0.0/0 matches everything and is the shortest prefix,
    so it must lose to any other match. If two entries have the same prefix
    length, the table is malformed - say what you do.
    """

    def __init__(self):
        # A key is a unique route prefix. Re-adding it updates its next hop.
        self._routes = {}

    def add(self, cidr, next_hop):
        network, prefix_len = parse_cidr(cidr)
        self._routes[(network, prefix_len)] = next_hop

    def lookup(self, address):
        value = _parse_ipv4(address)
        best_len = -1
        best_hop = None
        for (network, prefix_len), next_hop in self._routes.items():
            if prefix_len > best_len and value & _mask(prefix_len) == network:
                best_len = prefix_len
                best_hop = next_hop
        return best_hop


# ------------------------------------------------------------------- harness
RANGE_CASES = [
    ("192.168.0.0/24",  "192.168.0.1",   "192.168.0.254",  "192.168.0.255"),
    ("10.0.0.0/8",      "10.0.0.1",      "10.255.255.254", "10.255.255.255"),
    ("172.16.32.0/20",  "172.16.32.1",   "172.16.47.254",  "172.16.47.255"),
    ("203.0.113.64/26", "203.0.113.65",  "203.0.113.126",  "203.0.113.127"),
]

TABLE = [
    ("0.0.0.0/0",       "default-gw"),
    ("10.0.0.0/8",      "campus"),
    ("10.20.0.0/16",    "eng-building"),
    ("10.20.30.0/24",   "lab-floor"),
    ("10.20.30.64/26",  "lab-rack-2"),
    ("192.168.1.0/24",  "home"),
]

LOOKUP_CASES = [
    ("10.20.30.70",   "lab-rack-2"),     # inside all four 10.x entries
    ("10.20.30.10",   "lab-floor"),
    ("10.20.99.1",    "eng-building"),
    ("10.99.0.1",     "campus"),
    ("8.8.8.8",       "default-gw"),
    ("192.168.1.77",  "home"),
]


def verify():
    fails = 0
    for cidr, first, last, bcast in RANGE_CASES:
        try:
            got = network_range(cidr)
        except NotImplementedError:
            print("  network_range is still a stub"); return 1
        except Exception as e:
            print(f"  FAIL  {cidr:<18} raised {e!r}"); fails += 1; continue
        ok = tuple(got) == (first, last, bcast)
        print(f"  {'ok  ' if ok else 'FAIL'}  {cidr:<18} {got}")
        fails += not ok

    t = ForwardingTable()
    try:
        for cidr, hop in TABLE:
            t.add(cidr, hop)
    except NotImplementedError:
        print("  ForwardingTable is still a stub"); return 1

    for addr, expect in LOOKUP_CASES:
        got = t.lookup(addr)
        ok = got == expect
        print(f"  {'ok  ' if ok else 'FAIL'}  {addr:<16} -> {got}  (want {expect})")
        fails += not ok

    print(f"\n  {len(RANGE_CASES) + len(LOOKUP_CASES) - fails}"
          f"/{len(RANGE_CASES) + len(LOOKUP_CASES)} ok")
    return 1 if fails else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    raise SystemExit(verify() if a.verify else p.print_help())
