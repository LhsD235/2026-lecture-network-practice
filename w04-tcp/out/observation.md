# Week 04 Observations

## Task 1
I used Stop-and-Wait ARQ because it is simple and guarantees ordered delivery with retransmission and sequence numbers. Sending 2,000 bytes with an 8-byte payload requires at least 250 data packets; the default seed used 323 transmission attempts (1.292x the minimum), while seed 999 used 299, and both runs ended with IDENTICAL data. Loss was the dominant observed failure mode (40 losses versus 8 duplicates in the default run); sequence numbers and ACK checking also prevented duplication and reordering from corrupting the final data.

## Task 2
For the first TCP connection, frames 1, 2, and 3 were SYN, SYN-ACK, and ACK. The raw ISNs were 3005983774 for the client and 2725286180 for the server; nonzero, different ISNs help distinguish packets from different TCP connections. The client advertised a 2,704,896-byte receive window before frame 261, while the maximum observed server Bytes in Flight was 203,086 bytes, so the receive window was not filled; Wi-Fi measured 125.89 Mbps median throughput, 7% spread, and 9.2 ms median handshake time, while hotspot measured 51.47 Mbps, 14%, and 54.7 ms respectively.

## Task 3
FixedWindow had the highest goodput at 986.8/1000 slots, but it caused 37.4% loss, 2,340 retransmissions, and an average queue of 8.8, so it achieved speed by keeping the link congested and wasting transmissions. With a 50% loss backoff, my controller reached 862.2 goodput and a 3.2 average queue; using a gentler 75% backoff increased goodput to 972.8 but also increased the average queue to 4.9 and loss to 0.5%. Over the last 500 ACKs, the window ranged from 18.97 to 31.94 with an average of 25.66, which is close to the link's roughly 20-packet pipe plus its 10-packet queue.
