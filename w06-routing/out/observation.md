# Week 6 observations

## Task 1

Equal-cost paths use the alphabetically smaller first hop, giving a stable and
repeatable table. A production router may install multiple equal-cost next hops
(ECMP) instead. From `u`, the next hop for `w` is `x`: `u-x-y-w` costs 3 while
the direct `u-w` link costs 5. After `u-x` fails, the next hops for `w`, `x`,
`y`, and `z` change to `v`; the next hop for `v` remains `v`.

## Task 2

The local private gateway is hop 1 (`192.168.35.1`) and the path enters the
public ISP at hop 2 (`123.212.146.1`). The domestic destination stops replying
after hop 7, so the precise destination-side handoff cannot be named from this
capture alone.

The Stanford path reaches Hong Kong at hop 9, Tokyo at hop 12, and Seattle at
hop 14. The Tokyo-to-Seattle transition and roughly 100 ms increase indicate a
trans-Pacific submarine segment, although traceroute alone cannot prove the
specific physical cable. The `1.1.1.1` anycast route took 13 hops and only about
5-8 ms at the destination, indicating that BGP selected a nearby Korean replica
rather than Cloudflare's distant origin.

`* * *` can mean that an intermediate router deliberately drops or rate-limits
TTL-expired ICMP replies even though it still forwards packets. It can also mean
real loss, filtering, or a failure on the path. If later hops answer, the silent
router is usually just not answering traceroute rather than a broken route.

Before the cut, every router had learned a network to which it had no direct
link. For example, `r1` reached `172.22.0.0/16` through both `r2` and `r3` with
equal cost 20. After the `r1-r2` link was cut, `r1` removed the path through
`172.19.0.3` and retained the working path through `172.20.0.3`. This is OSPF
reconvergence rather than a packet carrying its complete route.

Link-down and link-restoration reconvergence were both recorded as 1 second.
The link was administratively disabled, so FRR received an immediate interface
event instead of waiting for the normal dead interval. In addition, the script
polls once per second, so it cannot distinguish two sub-second results. Thus the
measurement is consistent with immediate link-state notification, but it does
not measure dead-timer expiry; a silent packet-loss experiment and a finer timer
would be required for that measurement.

Raising `r1`'s `eth0` OSPF cost from 10 to 100 also reconverged in the recorded
1 second. `r1` stopped using its direct `eth0` path and sent traffic through
`eth1`; `r3` likewise changed its route toward `172.19.0.0/16`. A cost change
does not wait for failure detection: the new LSA can be flooded and SPF run at
once. The one-second polling resolution hides any smaller difference between
this result and the administrative link events.

## Task 3

The incremental router keeps the distance to each node, the chosen parent, and
the shortest-path-tree edges in addition to the forwarding table, which costs
O(V) extra memory. A removed or more expensive non-tree edge is skipped. A new
or cheaper edge is tested against the saved endpoint distances, and strict
improvements are propagated locally; ambiguous equal-cost changes and changes
to a used tree edge fall back to a full SPF.

The result was correct after all 1,000 events and avoided 71% of full SPF runs
(290 versus 1,001). It was still slower in this Python benchmark because copying
dictionaries, maintaining metadata, and checking incremental cases add overhead.
A real router can still prefer this design because avoiding large bursts of full
SPF CPU work improves control-plane responsiveness and reconvergence stability;
it trades modest memory and bookkeeping for bounded work during link flaps.
