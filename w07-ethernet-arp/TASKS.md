# 7주차 실습 · ARP와 스위칭

이론 연결 - **7-2 · MAC 주소와 ARP** (§6.4.1) · **7-2 · 스위치 자가 학습** (§6.4.3)

제출 위치 - `w07-ethernet-arp/out/`

```bash
mkdir -p w07-ethernet-arp/out
```

---

## 태스크 1 · ARP 표를 비우고 되살아나는 순서 보기

### 지금 상태

```bash
# macOS · Linux
arp -an | tee out/arp-before.txt
# Windows
arp -a | Tee-Object out/arp-before.txt
```

### 비우기 (관리자 권한)

```bash
# macOS
sudo arp -a -d
# Linux
sudo ip -s -s neigh flush all
# Windows (관리자 PowerShell)
netsh interface ip delete arpcache
```

### 잠시 쓰고 다시 보기

브라우저로 아무 사이트나 한 번 열고 30초 뒤에 다시 봅니다.

```bash
arp -an | tee out/arp-after.txt
```

**볼 것** - 거의 언제나 **게이트웨이가 가장 먼저** 되살아납니다.

왜 그런지 생각해 보세요. 바깥으로 나가는 모든 패킷이 게이트웨이를 거칩니다.
장표 `w07-l-arp` 에서 "같은 서브넷이 아니면 게이트웨이의 MAC 으로 보낸다"고 한 것이
표에 그대로 나타납니다. **내 트래픽이 실제로 어디로 가는지**를 이 표가 말해 줍니다.

---

## 태스크 2 · 요청은 브로드캐스트, 응답은 유니캐스트

### 캡처는 호스트 Wireshark 로

1. 필터 `arp` 로 캡처 시작
2. 위의 ARP 표 비우기를 다시 한 번
3. 아무 사이트나 접속
4. `out/arp.pcapng` 로 저장

### 분석은 컨테이너에서

```bash
tshark -r out/arp.pcapng -Y arp \
  -T fields -e frame.number -e arp.opcode \
  -e eth.src -e eth.dst -e arp.src.proto_ipv4 -e arp.dst.proto_ipv4 \
  | tee out/arp.txt
```

**볼 것** - 목적지 이더넷 주소를 비교합니다.

| | opcode | 목적지 MAC |
|---|---|---|
| 요청 | 1 (request) | `ff:ff:ff:ff:ff:ff` - **브로드캐스트** |
| 응답 | 2 (reply) | 물어본 쪽의 MAC - **유니캐스트** |

**모두에게 묻고 하나에게 답을 받는** 이 비대칭이 ARP 의 전부입니다.
모르는 상대의 MAC 을 물어야 하니 요청은 모두에게 갈 수밖에 없고,
답하는 쪽은 물어본 상대를 이미 알고 있으니 유니캐스트로 충분합니다.

---

## 태스크 3 · 스위치 학습 표 (6주차 토폴로지 재사용)

6주차에서 만든 FRR 토폴로지를 다시 올립니다.

```bash
cd ..                    # repository root
docker compose --profile routing up -d
```

컨테이너 사이로 ping 을 주고받으면서 **네이버 표(ARP 표)** 가 채워지는 것을 봅니다.

```bash
docker compose exec r1 vtysh -c "show ip route"
docker compose exec r1 ip neigh
```

**볼 것** - 통신하기 전에는 비어 있고, 통신한 상대만 채워집니다.
스위치의 자가 학습도 같은 원리입니다. 트래픽을 보고 배웁니다.

```bash
docker compose --profile routing down
```

---

## 경로 (B) · 캡처가 막힐 때

공식 **Ethernet and ARP Lab** trace 를 받아 같은 `tshark` 명령을 `-r` 로 돌리세요.
태스크 2 는 그대로 할 수 있습니다.

---

## 제출물

| 파일 | 내용 |
|---|---|
| `arp-before.txt` | 비우기 전 표 |
| `arp-after.txt` | 되살아난 순서 |
| `arp.pcapng` | 캡처 (경로 B 면 없어도 됨) |
| `arp.txt` | 요청 · 응답의 주소 판독 |
| `observation.md` | 관찰 2 ~ 3줄 |

```bash
python3 check.py w07
```

## observation.md 에 쓸 것

- 무엇이 가장 먼저 되살아났는가. 그것이 내 트래픽에 대해 말해 주는 것
- 요청과 응답의 목적지 주소가 다른 이유를 자기 말로
- ARP 에 인증이 없다는 것이 어떤 문제를 만들 수 있는가 (11주차 예고)
