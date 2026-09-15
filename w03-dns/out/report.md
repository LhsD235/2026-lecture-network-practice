# Task 2 Report

## Part A - Wireshark

- Delegation response: packet 2
- Packet 1 query and packet 2 response had the same transaction ID: 0x12ab.
- Final A-record answer: packet 6
- Largest DNS response: packet 2, 394 bytes
- Packet 2 was largest because the root response contained multiple NS records and glue addresses.

## Part B - CDN / DNS steering

Rule: if the final CNAME zone differs from the original site's zone, classify it as third-party.

| Site | Chain length | Final zone | Third party? | Rule verdict |
|---|---:|---|---|---|
| www.microsoft.com | 2 | akamaiedge.net | yes | third-party (correct) |
| www.netflix.com | 1 | netflix.com | no | first-party (correct) |
| www.adobe.com | 2 | akamai.net | yes | third-party (correct) |
| www.cnn.com | 1 | fastly.net | yes | third-party (correct) |
| www.apple.com | 3 | akamaiedge.net | yes | third-party (correct) |
| www.korea.ac.kr | 0 | korea.ac.kr | no | first-party (correct) |
| www.stanford.edu | 1 | netlifyglobalcdn.com | yes | third-party (correct) |
| www.bbc.co.uk | 2 | fastly.net | yes | third-party (correct) |
| www.spotify.com | 1 | fastly.net | yes | third-party (correct) |
| www.github.com | 1 | github.com | no | first-party (correct) |
| www.wikipedia.org | 1 | wikimedia.org | no | third-party (wrong) |
| www.nytimes.com | 3 | fastly.net | yes | third-party (correct) |

## Steering result

7 of 10 CDN-hosted sites answered with a different address set for a different resolver or network.

The two measurement networks were home Wi-Fi and a phone hotspot.

## Rule failure

The simple zone-comparison rule misclassified www.wikipedia.org. Its CNAME ends at dyna.wikimedia.org, so the names differ, but Wikipedia and Wikimedia are part of the same organization rather than an unrelated third-party CDN.
