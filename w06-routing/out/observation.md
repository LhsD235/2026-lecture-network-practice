# 6주차 관찰 기록

## 과제 1

비용이 같은 경로가 여러 개면 첫 next hop의 알파벳 순서가 빠른 것을 선택해 항상 같은 forwarding table이 나오도록 했다. 실제 router라면 같은 비용의 경로를 여러 개 설치하는 ECMP를 사용할 수도 있다. `u`에서 `w`로 갈 때 direct link의 비용은 5지만 `u-x-y-w`는 3이므로 next hop은 `x`가 된다. `u-x`가 끊기면 `w`, `x`, `y`, `z`의 next hop은 모두 `v`로 바뀐다.

## 과제 2

Traceroute에서 첫 hop은 사설 gateway `192.168.35.1`, 두 번째 hop은 공인 ISP 주소 `123.212.146.1`이었다. 국내 목적지는 7 hop 이후 응답하지 않아 목적지 쪽 인계 지점을 정확히 정할 수 없었다. Stanford 경로는 9 hop에서 Hong Kong, 12 hop에서 Tokyo, 14 hop에서 Seattle이 나타났고, Tokyo와 Seattle 사이에서 지연 시간이 약 100 ms 증가해 태평양 해저 구간을 지난 것으로 추정했다. 다만 traceroute만으로 실제 해저 cable의 이름까지 확정할 수는 없다.

`1.1.1.1` anycast 경로는 13 hop이었고 최종 지연 시간이 약 5–8 ms라서 멀리 있는 원본 server가 아니라 국내와 가까운 replica가 선택된 것으로 보였다. 중간의 `* * *`는 router가 TTL-expired ICMP 응답을 제한했기 때문일 수도 있고 실제 손실이나 filtering 때문일 수도 있다. 뒤쪽 hop이 다시 응답하면 경로 전체가 끊어진 것보다는 해당 router만 traceroute에 답하지 않은 경우로 보는 것이 맞다.

OSPF 실험 전에는 `r1`이 직접 연결되지 않은 `172.22.0.0/16`을 `r2`와 `r3` 양쪽을 통해 비용 20으로 학습했다. `r1-r2` link를 끊은 뒤에는 `172.19.0.3` 방향 경로가 사라지고 `172.20.0.3` 방향 경로만 남았다. Docker Hub의 기존 FRR image가 없어 처음에 router가 실행되지 않았고, image 주소를 `quay.io/frrouting/frr:9.1.0`으로 바꾼 뒤 실험할 수 있었다.

Link down, 복구, cost 변경은 모두 1초로 기록됐다. Interface를 관리 명령으로 내렸기 때문에 FRR이 상태 변화를 바로 받았고, 측정 script도 1초마다 확인했기 때문에 실제 sub-second 차이는 구분할 수 없었다. 따라서 이 결과로 세 경우의 실제 수렴 시간이 같다고 결론 내리거나 OSPF dead timer 만료 시간을 측정했다고 말할 수는 없다.

## 과제 3

매번 전체 SPF를 다시 실행하지 않기 위해 각 node까지의 거리, parent, shortest-path tree edge를 저장했다. 사용하지 않는 edge의 삭제나 비용 증가는 건너뛰고, 새 edge 또는 비용이 낮아진 edge가 거리를 실제로 줄일 때만 해당 지점부터 갱신했다. 사용 중인 tree edge나 equal-cost처럼 판단이 애매한 변화는 정확성을 위해 전체 SPF로 돌아갔다.

1,000개 event 뒤에도 모든 forwarding 결과가 맞았고 전체 SPF 실행은 1,001회에서 290회로 줄어 71%를 피했다. 하지만 Python benchmark의 실행 시간은 dictionary 복사와 metadata 관리 비용 때문에 오히려 더 느렸다. 실제 router에서는 link flap 때 큰 SPF 계산이 반복되는 것을 줄여 control plane을 안정시키는 장점이 있으므로, 단순 wall time만으로 이 최적화의 가치를 판단하면 안 된다고 생각했다.
