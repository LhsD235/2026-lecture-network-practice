# 4주차 실습 · TCP handshake와 처리량

이론 연결 - **4-1 · TCP** (§3.5 handshake · 순서 번호) · **4-2 · TCP 혼잡 제어** (§3.7)

제출 위치 - `w04-tcp/out/`

```bash
mkdir -p w04-tcp/out
```

---

## 태스크 1 · handshake 의 순서 번호 읽기

### 캡처는 호스트에서

컨테이너는 여러분 노트북의 랜카드를 볼 수 없습니다. **호스트 Wireshark** 로 뜹니다.

1. Wireshark 실행 → 쓰고 있는 인터페이스 선택 → 캡처 시작
2. 필터에 `tcp.flags.syn == 1` 입력
3. 브라우저나 터미널로 아무 사이트에 접속
4. 캡처 중지 → `w04-tcp/out/handshake.pcapng` 로 저장

### 분석은 컨테이너에서

```bash
tshark -r out/handshake.pcapng -Y tcp.flags.syn==1 \
  -T fields -e frame.number -e ip.src -e ip.dst \
  -e tcp.flags -e tcp.seq_raw -e tcp.ack_raw | tee out/handshake.txt
```

**중요** - `tcp.seq_raw` 를 씁니다. Wireshark 는 기본으로 **상대 순서 번호**(0 부터)를 보여 주는데,
그것은 실제로 오가는 값이 아닙니다. 장표 `w04-tcp-3way` 에서 "초기 순서 번호는 무작위"라고
한 것을 확인하려면 **절대값**을 봐야 합니다.

**볼 것**

- SYN 의 seq 가 **0 이 아니라 큰 무작위 수**인가
- SYN-ACK 의 ack 가 **SYN 의 seq + 1** 인가
- 왜 +1 인가 (데이터를 하나도 안 보냈는데)

---

## 태스크 2 · 같은 구간을 세 번 재기

```bash
for i in 1 2 3; do
  echo "=== 측정 $i ===" >> out/iperf3.txt
  iperf3 -c iperf.he.net -t 10 >> out/iperf3.txt 2>&1
  sleep 5
done
```

공개 서버가 붐비면 `ping` · `curl` 로 대체해도 됩니다. **세 번 재는 것**이 핵심입니다.

**볼 것** - 세 값이 **같지 않습니다.** 평균과 편차를 적고, 왜 다른지 쓰세요.
네트워크를 한 번 재서 얻은 값은 거의 아무것도 말해 주지 않습니다.
14주차에서 이것을 어떻게 보고하는지 다시 다룹니다.

---

## 태스크 3 · 지연을 넣고 처리량 보기 (컨테이너)

13주차에서 clumsy · Network Link Conditioner 로 할 것을 미리 해 봅니다.

```bash
# 컨테이너 안에서 (privileged 필요)
tc qdisc add dev eth0 root netem delay 100ms
iperf3 -c iperf.he.net -t 10 | tee -a out/iperf3.txt
tc qdisc del dev eth0 root
```

**볼 것** - 대역폭은 그대로인데 **처리량이 떨어집니다.**
RTT 가 커지면 같은 윈도로 보낼 수 있는 양이 줄기 때문입니다.
장표 `w04-cc-cwnd` 의 "전송률은 대략 cwnd 나누기 RTT" 가 이것입니다.

> `tc` 가 권한 오류를 내면 `docker compose run --rm --privileged lab` 으로 여세요.
> 안 되면 이 태스크는 건너뛰고 `observation.md` 에 그렇게 적으면 됩니다.

---

## 경로 (B) · 캡처가 막힐 때

공식 **TCP Lab** trace 를 받아 같은 `tshark` 명령을 `-r` 로 돌리면 됩니다.
handshake 와 재전송이 모두 들어 있습니다.

---

## 제출물

| 파일 | 내용 |
|---|---|
| `handshake.pcapng` | 캡처 (경로 B 면 없어도 됨) |
| `handshake.txt` | 순서 번호 판독 결과 |
| `iperf3.txt` | 3회 측정 (+ 지연 주입) |
| `observation.md` | 관찰 2 ~ 3줄 |

```bash
python3 check.py w04
```

## observation.md 에 쓸 것

- 초기 순서 번호가 무작위인 것을 확인했는가. **왜 무작위여야 하는가**
- 세 번의 측정이 얼마나 달랐는가. 한 번만 쟀다면 무엇을 잘못 말했겠는가
- 지연 100ms 를 넣었을 때 처리량이 변한 이유
