# Task 2 — Address, NAT, and DHCP report

Measurements were collected on home Wi-Fi on 2026-09-28 and on a phone
hotspot on 2026-10-06 (Asia/Seoul).

## Part A — Home Wi-Fi address and NAT

- Interface IPv4 address: `192.168.35.43`
- Mask: `255.255.255.0` (`/24`)
- Default gateway and DHCP server: `192.168.35.1`
- Public address reported by api.ipify.org: `123.212.146.211`

`192.168.35.43 AND 255.255.255.0 = 192.168.35.0`, so the subnet is
`192.168.35.0/24`. Its broadcast address is `192.168.35.255`, and its ordinary
usable-host interval is `192.168.35.1` through `192.168.35.254`. This agrees
with Task 1's `network_range` result.

The gateway `192.168.35.1` is inside the usable interval. A directly configured
gateway must be on-link so that the host can resolve its link-layer address and
send it a frame without first needing another router.

The interface address is RFC 1918 private space, while `123.212.146.211` is a
public address. Their difference proves at least one NAT. The first public
traceroute hop follows the home gateway, so one customer-edge NAT is the
best-supported count. To rule out a second upstream NAT, the router's WAN
address must be checked: a private or `100.64.0.0/10` WAN address would prove an
additional upstream/CGNAT layer.

## Part B — Home Wi-Fi versus phone hotspot

The phone hotspot assigned `172.20.10.2/28`, with network
`172.20.10.0/28`, usable interval `172.20.10.1`–`172.20.10.14`, broadcast
`172.20.10.15`, and gateway/DHCP server `172.20.10.1`. The outside service saw
`117.111.5.127`.

Both the private and public addresses changed. The private address changed
because the phone runs a different DHCP-controlled local subnet from the home
router. The public address changed because traffic left through the mobile
carrier instead of the home ISP. The private hotspot address and different
public address prove at least one NAT between the laptop and the Internet. A
second carrier NAT is possible, but it can be proved only by comparing the
phone's carrier-facing address with `117.111.5.127`.

## Part C — DHCP DORA captured on the phone hotspot

`dhcp.pcapng` is this machine's own Wi-Fi capture, taken while releasing and
renewing the hotspot lease. TShark found all four messages:

| Message | Source | Destination | Offered/client address |
|---|---|---|---|
| Discover | `0.0.0.0` | `255.255.255.255` | — |
| Offer | `172.20.10.1` | `172.20.10.2` | `172.20.10.2` |
| Request | `0.0.0.0` | `255.255.255.255` | — |
| ACK | `172.20.10.1` | `172.20.10.2` | `172.20.10.2` |

Discover uses source `0.0.0.0` because the client does not yet own a usable
IPv4 address. It broadcasts to `255.255.255.255` because it also does not yet
know the DHCP server or its subnet.

The server offered a 3,600-second (one-hour) lease. By the ACK, the server knows
the offered client address and the client's link-layer identity, and this
client can receive the unicast reply, so the ACK is sent from `172.20.10.1` to
`172.20.10.2`. Normally the client starts renewal at half the lease, about
1,800 seconds in this capture.
