#!/usr/bin/env python3
"""Week 4 · Task 3 — Beat the fixed window.

Textbook §3.7.

`FixedWindow` is a sender that never adapts. It picks a window and keeps it,
forever, no matter what the network says back. It is not a strawman: it is what
you get if you skip congestion control entirely, and it was the internet's
actual failure mode in October 1986.

Write `YourControl` and beat it on the harness:

    python3 bench.py
    python3 bench.py --yours

The interface is two events and one number:

    .window        how many packets you are willing to have in flight
    .on_ack()      one packet made it there and back
    .on_loss()     a packet was dropped, or timed out waiting for its ACK

That is all the information a real TCP sender has. It cannot see the queue,
it cannot see the link rate, and neither can you. You infer them from these
two events, which is the entire idea of §3.7.
"""


class FixedWindow:
    """Send 64 packets at a time and never listen."""

    def __init__(self):
        self.window = 64

    def on_ack(self):
        pass

    def on_loss(self):
        pass


class YourControl:
    """Slow Start + AIMD congestion control."""

    def __init__(self):
        self.window = 1.0
        self.ssthresh = 16.0

    def on_ack(self):
        if self.window < self.ssthresh:
            # Slow Start: 빠르게 증가
            self.window += 1.0
        else:
            # Congestion Avoidance: 천천히 증가
            self.window += 1.0 / self.window

    def on_loss(self):
        # 손실을 감지하면 윈도를 절반으로 감소
        self.ssthresh = max(2.0, self.window * 0.75)
        self.window = self.ssthresh