# Week 03 Observations

## Task 1
The root DNS server does not store the final IP address for every domain. Instead, it tells the resolver which DNS server to query next. If a delegation has no glue record, my resolver resolves the NS hostname first, which requires an extra resolution walk for that NS name. In the www.korea.ac.kr capture, both delegations included glue, so this added 0 extra lookups in that run. My resolver contacted 3 DNS servers, while a normal laptop usually sends one query to its recursive resolver.

## Task 2
When I checked the DNS responses, a delegation response gave information about which DNS server to query next, while the final response contained the actual IP address. I classified a site as third-party when the final CNAME zone differed from the original site's zone, but this rule incorrectly classified www.wikipedia.org because wikimedia.org is operated by the same organization. Among 10 CDN-hosted sites, 7 returned different IP addresses depending on the resolver or network, which supports DNS steering but does not prove that the returned server is actually the closest one.

## Task 3
The baseline cache stores all DNS information for 60 seconds, so a short real TTL can cause expired IP addresses to be returned (correctness problem), while a long real TTL can cause unnecessary DNS queries (performance problem). www.microsoft.com was handled worst because its TTL is only 20 seconds and it is queried frequently. Using the actual TTL reduced stale answers from 266 to 0 and upstream queries from 325 to 275; 275 is the minimum because the first request for each name and the first request after each TTL expiration must contact upstream.
