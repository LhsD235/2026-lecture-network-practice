# Week 5 observations

## Task 1

- I treated both `/31` addresses as usable under RFC 3021 and a `/32` as one host; the main edge-case lesson was that the usual “exclude network and broadcast” rule is not universal.
- `10.20.30.70` matched the default route and the `/8`, `/16`, `/24`, and `/26` routes, so longest-prefix match chose `/26` (`lab-rack-2`).
- An exact duplicate prefix updates its next hop. The difficult design point was making masks and boundary cases correct with only 32-bit shifts, without `ipaddress`.

## Task 2

- Home Wi-Fi used `192.168.35.43/24` with public IP `123.212.146.211`; the phone hotspot used `172.20.10.2/28` with public IP `117.111.5.127`, so both the local DHCP subnet and Internet exit changed.
- A private/public mismatch proves at least one NAT, but traceroute alone cannot prove every translation layer; the router or phone's WAN address is needed to distinguish one NAT from upstream CGNAT.
- Capturing DORA required starting the capture before lease renewal. Discover was `0.0.0.0 -> 255.255.255.255`, and the server offered `172.20.10.2` for 3,600 seconds before ACK could be unicast.

## Task 3

- I grouped routes by prefix length and searched populated lengths from longest to shortest, reducing lookup from O(N) routes to O(P) populated lengths, where `P <= 33`, with O(N) route storage.
- The main difficulty was preserving correctness for the default route and duplicate prefixes while optimizing; all 20,000 answers matched and lookup was over 1,000× faster.
- A bitwise trie gives a deterministic walk of at most 32 bits and suits hardware, but CPython's C-implemented hash tables were faster here, showing that asymptotic structure and implementation cost must both be considered.
