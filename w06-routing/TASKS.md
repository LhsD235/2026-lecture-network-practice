# 6주차 실습 · OSPF와 재수렴

이론 연결 - **6-1 · 링크 상태와 거리 벡터** (§5.2) · **6-2 · OSPF** (§5.3)

제출 위치 - `w06-routing/out/`

```bash
mkdir -p w06-routing/out
```

> **이 주차만 다릅니다.** 라우팅은 내 노트북에서 캡처해서 볼 수 있는 것이 아닙니다.
> 망을 직접 세워야 관찰됩니다. 그래서 라우터 3대를 컨테이너로 올립니다.

---

## 태스크 1 · 남의 경로 보기 · traceroute

내가 통제하지 않는 경로를 바깥에서 봅니다.

```bash
traceroute www.korea.ac.kr      | tee    out/traceroute.txt
traceroute www.mit.edu          | tee -a out/traceroute.txt
# Windows 는 tracert
```

**볼 것** - 왕복 시간이 **크게 뛰는 홉**을 찾으세요. 그리고 그것이 무엇인지 판단하세요.

| 가능한 원인 | 어떻게 구분하는가 |
|---|---|
| 거리 | 해외 구간에서 한 번 뛰고 그 뒤로는 계속 높음 |
| 혼잡 | 특정 홉에서 뛰었다가 다음 홉에서 다시 내려감 |
| 응답 비우선순위 | 그 홉만 높고 **뒤 홉은 낮음** - 라우터가 자기 응답을 미룬 것 |

세 번째가 가장 자주 오해받습니다. 중간 홉의 RTT 가 높다고 그 구간이 느린 것이 아닙니다.
그 라우터가 ICMP 응답을 뒤로 미뤘을 뿐, **통과하는 트래픽은 빠를 수 있습니다.**

---

## 태스크 2 · OSPF 라우터 3대 세우기

### 토폴로지

삼각형입니다. 어느 두 라우터 사이에도 경로가 둘 있습니다.

```
        net_a
    r1 ------- r3
     |         |
net_b|         |net_c
     |         |
     +--- r2 --+
```

설정은 `topology/r1/frr.conf` · `r2` · `r3` 에 있습니다. **텍스트 파일입니다.**
열어서 읽어 보세요. `ip ospf cost 10` 이 링크 비용이고, `router ospf` 아래가 OSPF 설정입니다.

### 올리기

```bash
bash w06-routing/scenario.sh up
```

30초쯤 지나면 인접(neighbor)이 맺힙니다. 라우팅 표를 봅니다.

```bash
bash w06-routing/scenario.sh routes
```

**볼 것** - 각 라우터가 **직접 연결되지 않은 망**으로 가는 경로를 알고 있습니다.
아무도 알려 주지 않았는데 알아냈습니다. 그것이 링크 상태 라우팅입니다.

---

## 태스크 3 · 링크를 끊고 재수렴 시간 재기

```bash
bash w06-routing/scenario.sh cut
```

r1 과 r2 사이 링크를 내리고, 경로가 바뀔 때까지 1초 간격으로 확인합니다.
`out/route-before.txt` · `out/route-after.txt` · `out/reconverge.txt` 가 자동으로 남습니다.

**볼 것**

- r2 로 가는 경로가 **r3 를 거치는 것으로 바뀌었는가**
- **몇 초** 걸렸는가. 즉시가 아닙니다
- 왜 즉시가 아닌가 - OSPF 는 이웃이 죽었다고 판단하기까지 **dead interval**(기본 40초)을 기다립니다.
  hello 를 몇 번 놓쳐야 죽었다고 봅니다. 너무 빨리 판단하면 잠깐 끊긴 것에도 경로가 요동칩니다.

복구합니다.

```bash
bash w06-routing/scenario.sh restore
```

---

## 태스크 4 · 비용을 바꿔 경로 옮기기

```bash
bash w06-routing/scenario.sh cost
```

r1 의 한쪽 링크 비용을 10 에서 100 으로 올립니다.

**볼 것** - **홉 수는 그대로인데 경로가 바뀝니다.**
OSPF 는 홉 수가 아니라 **관리자가 정한 비용**으로 고릅니다.
장표 `w06-ospf-cost` 에서 "링크 가중치는 관리자가 설정한다"고 한 것이 이것입니다.

끝나면 정리합니다.

```bash
bash w06-routing/scenario.sh down
```

---

## Docker 를 못 쓴다면

이 주차는 경로 (B)가 없습니다. 라우팅은 trace 로 볼 수 없기 때문입니다.
대신 **Cisco Packet Tracer**(무료 · Windows · macOS)로 같은 삼각 토폴로지를 만들고
같은 네 가지를 관찰하면 됩니다. 제출물은 스크린샷으로 대체합니다.

---

## 제출물

| 파일 | 내용 |
|---|---|
| `traceroute.txt` | 국내 · 해외 추적 + 뛰는 홉 판단 |
| `route-before.txt` | 링크 끊기 전 라우팅 표 |
| `route-after.txt` | 끊은 뒤 라우팅 표 |
| `reconverge.txt` | 재수렴 시간 |
| `observation.md` | 관찰 2 ~ 3줄 |

```bash
python3 check.py w06
```

## observation.md 에 쓸 것

- traceroute 에서 지연이 뛴 홉은 무엇 때문이라고 판단했는가. 근거는
- 재수렴에 몇 초 걸렸는가. **왜 즉시가 아닌가**
- 비용을 바꿨을 때 경로가 바뀐 것이 OSPF 에 대해 말해 주는 것
