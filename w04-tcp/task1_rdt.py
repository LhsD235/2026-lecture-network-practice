#!/usr/bin/env python3
"""Week 4 · Task 1 — Build reliable delivery on top of an unreliable channel.

Textbook §3.4 (reliable data transfer) and §3.5 (TCP's sequence numbers).

`UnreliableChannel` below loses packets, reorders them, duplicates them, and
delays them. It is the network as §3.4 models it. Your job is to move a file
across it and have the bytes arrive intact and in order.

That is the whole of TCP's reliability story with the congestion control taken
out, and it is worth building once by hand before you ever trust a socket again.

    python3 task1_rdt.py --verify
"""
import argparse, hashlib, random

PAYLOAD = 8            # bytes per packet - small, so you see the sequencing


class UnreliableChannel:
    """Loses 10%, duplicates 3%, reorders, and delays. Deterministic by seed.

    You may not make it nicer. You may not read its internals. It is the only
    way your sender can reach your receiver.
    """

    def __init__(self, seed=246, loss=0.10, dup=0.03, reorder=0.10):
        self.rng = random.Random(seed)
        self.loss, self.dup, self.reorder = loss, dup, reorder
        self.wire = []          # packets in flight, in no particular order
        self.stats = {"sent": 0, "lost": 0, "duplicated": 0, "delivered": 0}

    def send(self, packet):
        """Hand a packet to the network. It may never come out."""
        self.stats["sent"] += 1
        if self.rng.random() < self.loss:
            self.stats["lost"] += 1
            return
        copies = 2 if self.rng.random() < self.dup else 1
        self.stats["duplicated"] += copies - 1
        for _ in range(copies):
            if self.rng.random() < self.reorder and self.wire:
                self.wire.insert(self.rng.randrange(len(self.wire)), packet)
            else:
                self.wire.append(packet)

    def receive(self):
        """Take the next packet out, or None if the network has nothing."""
        if not self.wire:
            return None
        self.stats["delivered"] += 1
        return self.wire.pop(0)


class Sender:
    """Your sender.

    Requirements are in task1.md. The short version:

      - break `data` into PAYLOAD-sized pieces and number them
      - retransmit what is not acknowledged
      - do not assume an ACK means what you think it means until you have
        checked the number on it

    You choose the protocol: stop-and-wait is the easiest to get right and the
    slowest; a sliding window is the point of §3.4.3. Say which you chose and
    why in observation.md.
    """

    def __init__(self, data_channel, ack_channel, data):
        self.data_channel = data_channel
        self.ack_channel = ack_channel

        # 원본 데이터를 PAYLOAD 크기로 나누고 번호 붙이기
        self.packets = []

        for i in range(0, len(data), PAYLOAD):
            seq = len(self.packets)
            piece = data[i:i + PAYLOAD]

            self.packets.append((seq, piece))

        # 현재 전송할 패킷 번호
        self.next_seq = 0

        # ACK를 기다리는 중인지
        self.waiting = False

        # 재전송을 위한 시간 관리
        self.elapsed = 0
        self.timeout = 5

    def step(self):
        # 모든 패킷의 ACK를 받았다면 종료
        if self.next_seq >= len(self.packets):
            return False

        # ACK 하나 확인
        ack = self.ack_channel.receive()

        # 현재 기다리는 패킷에 대한 ACK인지 확인
        if self.waiting and ack == ("ACK", self.next_seq):
            self.next_seq += 1
            self.waiting = False
            self.elapsed = 0

            # 마지막 패킷까지 확인받았다면 종료
            if self.next_seq >= len(self.packets):
                return False

        # 아직 보내지 않은 패킷 전송
        if not self.waiting:
            self.data_channel.send(self.packets[self.next_seq])
            self.waiting = True
            self.elapsed = 0

        # ACK를 기다리는 중
        else:
            self.elapsed += 1

            # 일정 시간 동안 ACK가 없으면 재전송
            if self.elapsed >= self.timeout:
                self.data_channel.send(self.packets[self.next_seq])
                self.elapsed = 0

        return True


class Receiver:
    """Stop-and-wait receiver."""

    def __init__(self, data_channel, ack_channel):
        self.data_channel = data_channel
        self.ack_channel = ack_channel

        # 다음에 받아야 할 패킷 번호
        self.expected_seq = 0

        # 순서대로 받은 데이터 저장
        self.received = bytearray()

    def step(self):
        # 네트워크에서 패킷 하나 받기
        packet = self.data_channel.receive()

        # 도착한 패킷이 없으면 종료
        if packet is None:
            return

        seq, payload = packet

        # 기다리던 번호가 도착했다면 데이터 저장
        if seq == self.expected_seq:
            self.received.extend(payload)

            # 해당 패킷을 정상적으로 받았다고 알림
            self.ack_channel.send(("ACK", seq))

            # 다음 번호를 기다림
            self.expected_seq += 1

        # 이미 받은 패킷이 중복 도착했다면
        elif seq < self.expected_seq:
            # 데이터는 다시 저장하지 않고 ACK만 재전송
            self.ack_channel.send(("ACK", seq))

        # 아직 받을 순서가 아닌 패킷은 저장하지 않음

    def data(self):
        return bytes(self.received)


# ------------------------------------------------------------------- harness
def verify(seed=246, size=2000, max_steps=200_000):
    original = bytes(random.Random(seed).getrandbits(8) for _ in range(size))
    up, down = UnreliableChannel(seed), UnreliableChannel(seed + 1)

    # Data goes out over `up`, ACKs come back over `down`. Both are unreliable.
    sender = Sender(up, down, original)
    receiver = Receiver(up, down)

    for _ in range(max_steps):
        alive = sender.step()
        receiver.step()
        if not alive and len(receiver.data() or b"") >= size:
            break

    got = receiver.data() or b""
    ok = hashlib.sha256(got).hexdigest() == hashlib.sha256(original).hexdigest()
    print(f"  bytes    sent {size}   received {len(got)}")
    print(f"  channel  {up.stats}")
    print(f"  result   {'IDENTICAL' if ok else 'CORRUPTED OR INCOMPLETE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    p.add_argument("--seed", type=int, default=246)
    a = p.parse_args()
    raise SystemExit(verify(a.seed) if a.verify else p.print_help())
