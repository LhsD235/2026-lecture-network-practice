#!/usr/bin/env bash
# 6주차 - OSPF 재수렴 관찰
#
#   bash w06-routing/scenario.sh up        토폴로지 올리기
#   bash w06-routing/scenario.sh routes    라우팅 표 보기
#   bash w06-routing/scenario.sh cut       링크 끊고 재수렴 시간 재기
#   bash w06-routing/scenario.sh restore   링크 복구
#   bash w06-routing/scenario.sh cost      링크 비용 바꾸기
#   bash w06-routing/scenario.sh down      정리
set -euo pipefail
SELF="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
cd "$(dirname "$0")/.." || exit 1
OUT="w06-routing/out"; mkdir -p "$OUT"
DC="docker compose --profile routing"

show_routes() {
  for r in r1 r2 r3; do
    echo "===== $r ====="
    $DC exec -T "$r" vtysh -c "show ip route ospf"
  done
}

wait_for_r1_change() {
  BEFORE="$1"
  for i in $(seq 1 60); do
    sleep 1
    NOW=$($DC exec -T r1 vtysh -c "show ip route ospf" 2>/dev/null)
    if [ "$NOW" != "$BEFORE" ]; then
      echo "$i"
      return 0
    fi
  done
  return 1
}

case "${1:-}" in
  up)
    $DC up -d
    echo "라우터 3대를 올렸습니다. OSPF 인접 수립까지 30초쯤 기다리세요."
    sleep 30
    $DC exec -T r1 vtysh -c "show ip ospf neighbor"
    ;;

  routes)
    show_routes
    ;;

  cut)
    echo "== 끊기 전 =="
    show_routes | tee "$OUT/route-before.txt"
    BEFORE=$($DC exec -T r1 vtysh -c "show ip route ospf" 2>/dev/null)

    echo
    echo "r2 의 eth0 (net_b, r1-r2 링크) 을 내립니다."
    # r1 쪽 인터페이스는 살아 있으므로 r1은 hello/dead timer로 장애를 발견한다.
    $DC exec -T r2 ip link set eth0 down

    if ELAPSED=$(wait_for_r1_change "$BEFORE"); then
      echo "link down reconvergence: ${ELAPSED} seconds" | tee "$OUT/reconverge.txt"
      show_routes | tee "$OUT/route-after.txt"
    else
      echo "link down: no route change within 60 seconds" | tee "$OUT/reconverge.txt"
      exit 1
    fi
    ;;

  restore)
    BEFORE=$($DC exec -T r1 vtysh -c "show ip route ospf" 2>/dev/null)
    $DC exec -T r2 ip link set eth0 up
    if ELAPSED=$(wait_for_r1_change "$BEFORE"); then
      echo "link restore reconvergence: ${ELAPSED} seconds" | tee -a "$OUT/reconverge.txt"
    else
      echo "link restore: no route change within 60 seconds" | tee -a "$OUT/reconverge.txt"
      exit 1
    fi
    ;;

  cost)
    show_routes | tee "$OUT/cost-before.txt"
    BEFORE=$($DC exec -T r1 vtysh -c "show ip route ospf" 2>/dev/null)
    echo "r1 의 eth0 (net_a) 비용을 10 에서 100 으로 올립니다."
    $DC exec -T r1 vtysh -c "configure terminal" \
                    -c "interface eth0" -c "ip ospf cost 100"
    if ELAPSED=$(wait_for_r1_change "$BEFORE"); then
      echo "cost change reconvergence: ${ELAPSED} seconds" | tee "$OUT/cost-reconverge.txt"
      show_routes | tee "$OUT/cost-after.txt"
    else
      echo "cost change: no route change within 60 seconds" | tee "$OUT/cost-reconverge.txt"
      exit 1
    fi
    ;;

  down)
    $DC down
    ;;

  *)
    sed -n '2,10p' "$SELF"
    ;;
esac
