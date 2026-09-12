#!/usr/bin/env python3
"""제출 형식 점검

답을 채점하지 않습니다. 빠진 것만 알려 줍니다.
    python3 check.py w03
"""
import sys, os, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))

# 주차별로 out/ 아래에 있어야 하는 것
# (파일 glob, 설명, 필수 여부)
SPEC = {
    "w02": ("w02-agent", [
        ("source-list.md", "수집한 문서 목록", True),
        ("analysis.md",    "분석 표", True),
        ("report.md",      "보고서 초안", True),
        ("review.md",      "리뷰어 검증 결과 - 두 경로가 어긋난 항목", True),
        ("observation.md", "관찰 2~3줄", True),
    ]),
    "w03": ("w03-dns", [
        ("trace.txt",      "dig +trace 출력", True),
        ("cname.txt",      "CNAME 사슬 조회 출력", True),
        ("ttl.txt",        "TTL 3회 관찰", True),
        ("observation.md", "관찰 2~3줄", True),
    ]),
    "w04": ("w04-tcp", [
        ("handshake.pcapng", "handshake 캡처", False),
        ("handshake.txt",    "순서 번호 판독 결과", True),
        ("iperf3.txt",       "iperf3 3회 측정", True),
        ("observation.md",   "관찰 2~3줄", True),
    ]),
    "w05": ("w05-ip-nat", [
        ("ifconfig.txt",   "주소 · 마스크 · 게이트웨이", True),
        ("subnet.md",      "서브넷 범위 계산과 대조", True),
        ("public.txt",     "외부에서 보이는 공인 주소", True),
        ("dhcp.md",        "DORA 4단계 확인", True),
        ("observation.md", "관찰 2~3줄", True),
    ]),
    "w06": ("w06-routing", [
        ("traceroute.txt", "국내 · 해외 traceroute", True),
        ("route-before.txt", "링크 down 전 라우팅 표", True),
        ("route-after.txt",  "링크 down 후 라우팅 표", True),
        ("reconverge.txt",   "재수렴 시간 측정", True),
        ("observation.md",   "관찰 2~3줄", True),
    ]),
    "w07": ("w07-ethernet-arp", [
        ("arp-before.txt", "비우기 전 ARP 표", True),
        ("arp-after.txt",  "비운 뒤 되살아난 순서", True),
        ("arp.pcapng",     "ARP 요청 · 응답 캡처", False),
        ("arp.txt",        "요청 · 응답의 목적지 주소 판독", True),
        ("observation.md", "관찰 2~3줄", True),
    ]),
}


def check(week):
    if week not in SPEC:
        print(f"모르는 주차: {week}")
        print("가능한 값: " + " ".join(sorted(SPEC)))
        return 2

    folder, items = SPEC[week]
    out = os.path.join(HERE, folder, "out")
    print(f"== {folder}/out/ 점검 ==\n")

    if not os.path.isdir(out):
        print(f"  out/ 폴더가 없습니다. 만들고 결과를 넣으세요:")
        print(f"      mkdir -p {folder}/out")
        return 1

    missing, weak = [], []
    for name, desc, required in items:
        path = os.path.join(out, name)
        if os.path.exists(path):
            size = os.path.getsize(path)
            if size == 0:
                print(f"  [비었음] {name:20s} {desc}")
                missing.append(name)
            else:
                print(f"  [있음]   {name:20s} {desc}  ({size:,} bytes)")
        elif required:
            print(f"  [없음]   {name:20s} {desc}")
            missing.append(name)
        else:
            # 선택 항목 - 공식 trace 경로를 쓰면 없을 수 있음
            print(f"  [선택]   {name:20s} {desc}  (공식 trace 경로면 없어도 됨)")

    # 관찰 서술은 길이만 봅니다
    obs = os.path.join(out, "observation.md")
    if os.path.exists(obs):
        text = open(obs, encoding="utf-8").read().strip()
        lines = [l for l in text.splitlines() if l.strip()]
        if len(text) < 60:
            weak.append("observation.md 가 너무 짧습니다. 무엇을 봤는지 2~3줄로 쓰세요")
        elif len(lines) < 2:
            weak.append("observation.md 가 한 줄입니다. 2~3줄을 권합니다")

    print()
    for w in weak:
        print(f"  ! {w}")
    if missing:
        print(f"\n  빠진 것 {len(missing)}개: {', '.join(missing)}")
        return 1
    if weak:
        print("\n  형식은 갖췄습니다. 위 안내를 보고 보완하면 좋습니다.")
        return 0
    print("  형식 점검 통과. 내용은 스스로 확인하세요.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    arg = sys.argv[1].lower()
    if not arg.startswith("w"):
        arg = "w" + arg.zfill(2)
    sys.exit(check(arg))
