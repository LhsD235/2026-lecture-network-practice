# 5주차 실습 · 주소 · 서브넷 · NAT · DHCP

이론 연결 - **5-2 · IPv4 주소와 서브넷** (§4.3.2) · **5-2 · DHCP** (§4.3.2) · **5-2 · NAT** (§4.3.3)

제출 위치 - `w05-ip-nat/out/`

```bash
mkdir -p w05-ip-nat/out
```

---

## 태스크 1 · 내 주소와 서브넷 범위

### 주소 확인 (호스트에서)

```bash
# macOS
ifconfig | grep -A3 -E '^(en|wl)' | tee out/ifconfig.txt
netstat -rn | grep default        >> out/ifconfig.txt

# Windows (PowerShell)
ipconfig /all | Tee-Object out/ifconfig.txt
```

### 범위를 손으로 계산한 뒤 대조

마스크를 보고 **먼저 직접 계산**하세요. 장표 `w05-subnet-calc` 방식 그대로입니다.

- 네트워크 주소 · 브로드캐스트 주소 · 쓸 수 있는 호스트 범위 · 호스트 개수

그다음 컨테이너에서 대조합니다.

```bash
ipcalc 192.168.0.37/24     # 자기 주소와 마스크로 바꿔서
```

`out/subnet.md` 에 **손 계산과 `ipcalc` 결과를 나란히** 적으세요.
틀렸다면 어디서 틀렸는지도 함께 적으면 좋습니다.

**볼 것** - 같은 서브넷의 다른 기기(휴대폰 등)의 주소가 그 범위 **안에** 들어오는가

---

## 태스크 2 · NAT 은 무엇을 고쳐 썼는가

```bash
# 내 기기의 주소
ip addr show 2>/dev/null || ifconfig

# 외부 서버가 보는 내 주소
curl -s https://ifconfig.me | tee out/public.txt
```

**볼 것** - 두 주소가 **다릅니다.**

`out/public.txt` 아래에, 장표 `w05-nat-table` 의 4-튜플로 **무엇이 바뀌었는지** 적으세요.

```
나갈 때   출발지 (사설 IP, 사설 포트)  →  (공인 IP, 새 포트)
돌아올 때 목적지 (공인 IP, 새 포트)    →  (사설 IP, 사설 포트)
```

> **컨테이너를 쓰면 NAT 이 두 단**입니다. 컨테이너 주소 → 호스트 주소 → 공인 주소.
> 세 개를 다 적어 보면 NAT 이 겹칠 수 있다는 것이 눈에 보입니다.

---

## 태스크 3 · DHCP 의 DORA 4단계

**공식 DHCP Lab trace 를 씁니다.** 직접 캡처하려면 임대를 갱신해야 하는데
학교망에서 하기 곤란합니다.

1. `traces/` 에 공식 DHCP Lab trace 를 둡니다
2. Wireshark 로 열고 필터 `dhcp` (또는 `bootp`)
3. 네 메시지를 찾습니다

| 순서 | 메시지 | 보낸 쪽 | 목적지 주소가 무엇인가 |
|---|---|---|---|
| D | Discover | 클라이언트 | ? |
| O | Offer | 서버 | ? |
| R | Request | 클라이언트 | ? |
| A | ACK | 서버 | ? |

`out/dhcp.md` 에 표를 채우세요.

**볼 것** - Request 가 **왜 다시 브로드캐스트인가.** 이미 서버를 알았는데도 그렇습니다.
(힌트 - Offer 를 보낸 서버가 하나가 아닐 수 있습니다)

---

## 제출물

| 파일 | 내용 |
|---|---|
| `ifconfig.txt` | 주소 · 마스크 · 게이트웨이 |
| `subnet.md` | 손 계산과 `ipcalc` 대조 |
| `public.txt` | 공인 주소 + 4-튜플 변화 |
| `dhcp.md` | DORA 4단계 표 |
| `observation.md` | 관찰 2 ~ 3줄 |

```bash
python3 check.py w05
```

## observation.md 에 쓸 것

- 손 계산이 `ipcalc` 와 맞았는가. 틀렸다면 어디서
- NAT 이 고쳐 쓴 필드를 자기 말로. 이것이 왜 종단 간 원칙을 약하게 하는가
- DHCP Request 가 브로드캐스트인 이유
