# 4주차 관찰 기록

## 과제 1

Stop-and-Wait를 직접 구현해 보니 신뢰성은 단순히 패킷을 다시 보내는 것만으로 만들어지지 않았다. 8 bytes씩 2,000 bytes를 보내려면 최소 250개 패킷이면 되지만, 손실과 재전송 때문에 기본 seed에서는 323회, seed 999에서는 299회 전송했다. 그래도 sequence number로 중복 패킷을 구분하고 ACK를 확인했기 때문에 두 번 모두 결과가 `IDENTICAL`이었다.

## 과제 2

Wireshark에서 첫 TCP 연결을 확인했을 때 1·2·3번 frame이 SYN, SYN-ACK, ACK 순서로 나타났다. Client와 server의 ISN도 서로 달랐다. Receive window는 2,704,896 bytes인데 최대 Bytes in Flight는 203,086 bytes였기 때문에 이 실험에서는 수신 창이 병목이 아니라고 판단했다. Wi-Fi는 처리량 125.89 Mbps, handshake 9.2 ms였고 핫스팟은 51.47 Mbps와 54.7 ms여서 접속 환경에 따라 속도와 지연 시간이 크게 달라지는 것도 확인했다.

## 과제 3

처음에는 goodput이 가장 높으면 좋은 controller라고 생각했다. 하지만 FixedWindow는 goodput이 986.8로 가장 높으면서도 손실률이 37.4%였고 재전송도 2,340회 발생했다. 반면 내가 만든 controller는 goodput이 972.8로 조금 낮지만 손실률은 0.5%이고 평균 queue도 4.9였다. 이 결과를 보고 goodput 하나만 비교할 것이 아니라 손실률, 재전송 횟수, queue 크기까지 함께 봐야 한다는 것을 알게 되었다.
