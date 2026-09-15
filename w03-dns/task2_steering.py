#!/usr/bin/env python3
"""Week 3 · Task 2 — Does DNS actually steer you? Measure it.

Textbook §2.4.3 (records) and §2.5 (CDNs).

The lecture claims two things:

    (a) most large sites are served by a CDN, reached through a CNAME chain
    (b) DNS steers each user to a *nearby* replica

Both are testable from your laptop, and one of them is harder to prove than
the slide makes it look. Your job is to produce the evidence and a number.

    python3 task2_steering.py --collect        # gather the raw data
    python3 task2_steering.py --report         # your analysis

What you have to build
----------------------
1.  For each hostname in SITES, follow the CNAME chain to its end and record
    every hop. `--collect` should leave the raw data in out/chains.json.

2.  Decide, for each site, whether it is served by a **third party**.
    This is the hard part and there is no single right answer:

      - `www.microsoft.com` ends at `akamaiedge.net`     - clearly third party
      - `www.netflix.com`   stops inside `netflix.com`   - own CDN, not third party
      - some sites have no CNAME at all and still sit behind a CDN (anycast)
      - `foo.cloudfront.net` and `foo.s3.amazonaws.com` are both Amazon,
        but they are not the same service

    Write down the rule you used and **defend it in observation.md**. A rule
    that just compares the last two labels will be wrong on at least one of
    the sites below; find which, and say so.

3.  Ask **two different resolvers** for the same name and compare the
    addresses you get back. If DNS really steers by location, a CDN-hosted
    name should answer differently to resolvers sitting in different places.

        RESOLVERS below has your system resolver and two public ones.

    Report: of N CDN-hosted sites, how many returned a different address set
    from a different resolver? Claim (b) predicts most of them. Check it.

Pass condition
--------------
There is no fixed answer. You pass by producing, in out/report.md:

  - the table: site | chain length | final zone | third party? | your rule's verdict
  - the steering number: "X of N sites answered differently to a different resolver"
  - at least one site where your classification rule was wrong, and why
"""
import argparse, json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

SITES = [
    "www.microsoft.com",     # Akamai, multi-hop
    "www.netflix.com",       # own CDN
    "www.adobe.com",
    "www.cnn.com",
    "www.apple.com",
    "www.korea.ac.kr",       # no CDN at all
    "www.stanford.edu",
    "www.bbc.co.uk",
    "www.spotify.com",
    "www.github.com",
    "www.wikipedia.org",
    "www.nytimes.com",
]

RESOLVERS = {
    "system": None,          # whatever is in your resolv.conf
    "google": "8.8.8.8",
    "quad9":  "9.9.9.9",
}


def dig(name, rtype="A", server=None):
    """Raw lookup. Transport only - the thinking is yours."""
    args = ["dig", "+short", name, rtype]
    if server:
        args.insert(1, f"@{server}")
    out = subprocess.run(args, capture_output=True, text=True).stdout
    return [l.strip() for l in out.splitlines() if l.strip()]


def collect():
    data = {}

    for site in SITES:
        print(f"Collecting {site}...")

        # 1. CNAME chain 따라가기
        chain = [site]
        current = site

        for _ in range(10):
            cnames = dig(current, "CNAME")

            if not cnames:
                break

            next_name = cnames[0].rstrip(".")
            chain.append(next_name)
            current = next_name

        # 2. resolver별 A record 수집
        answers = {}

        for resolver_name, server in RESOLVERS.items():
            records = dig(site, "A", server)

            # dig +short A는 CNAME도 같이 출력할 수 있으므로
            # IPv4처럼 보이는 값만 저장
            addresses = []

            for value in records:
                parts = value.split(".")

                if len(parts) == 4 and all(
                    part.isdigit() for part in parts
                ):
                    addresses.append(value)

            answers[resolver_name] = sorted(set(addresses))

        data[site] = {
            "chain": chain,
            "answers": answers
        }

    path = os.path.join(OUT, "chains.json")

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Saved to {path}")


def report():
    network1_path = os.path.join(OUT, "chains_network1.json")
    hotspot_path = os.path.join(OUT, "chains_hotspot.json")

    with open(network1_path, encoding="utf-8") as f:
        network1 = json.load(f)

    with open(hotspot_path, encoding="utf-8") as f:
        hotspot = json.load(f)

    # 사람이 판단한 final zone
    final_zones = {
        "www.microsoft.com": "akamaiedge.net",
        "www.netflix.com": "netflix.com",
        "www.adobe.com": "akamai.net",
        "www.cnn.com": "fastly.net",
        "www.apple.com": "akamaiedge.net",
        "www.korea.ac.kr": "korea.ac.kr",
        "www.stanford.edu": "netlifyglobalcdn.com",
        "www.bbc.co.uk": "fastly.net",
        "www.spotify.com": "fastly.net",
        "www.github.com": "github.com",
        "www.wikipedia.org": "wikimedia.org",
        "www.nytimes.com": "fastly.net",
    }

    # 실제 의미를 고려한 third-party 판단
    actual_third_party = {
        "www.microsoft.com": True,
        "www.netflix.com": False,
        "www.adobe.com": True,
        "www.cnn.com": True,
        "www.apple.com": True,
        "www.korea.ac.kr": False,
        "www.stanford.edu": True,
        "www.bbc.co.uk": True,
        "www.spotify.com": True,
        "www.github.com": False,
        "www.wikipedia.org": False,
        "www.nytimes.com": True,
    }

    def simple_zone(name):
        name = name.rstrip(".")
        parts = name.split(".")
        return ".".join(parts[-2:]) if len(parts) >= 2 else name

    lines = []

    lines.append("# Task 2 Report")
    lines.append("")
    lines.append("## Part A - Wireshark")
    lines.append("")
    lines.append("- Delegation response: packet 2")
    lines.append(
        "- Packet 1 query and packet 2 response had the same "
        "transaction ID: 0x12ab."
    )
    lines.append("- Final A-record answer: packet 6")
    lines.append("- Largest DNS response: packet 2, 394 bytes")
    lines.append(
        "- Packet 2 was largest because the root response contained "
        "multiple NS records and glue addresses."
    )
    lines.append("")

    lines.append("## Part B - CDN / DNS steering")
    lines.append("")
    lines.append(
        "Rule: if the final CNAME zone differs from the original site's "
        "zone, classify it as third-party."
    )
    lines.append("")
    lines.append(
        "| Site | Chain length | Final zone | Third party? | Rule verdict |"
    )
    lines.append(
        "|---|---:|---|---|---|"
    )

    for site in SITES:
        chain = network1[site]["chain"]

        # number of CNAME transitions
        chain_length = len(chain) - 1

        final_zone = final_zones[site]

        original_zone = simple_zone(site)
        rule_zone = simple_zone(chain[-1])

        rule_third = original_zone != rule_zone

        actual = actual_third_party[site]

        if rule_third == actual:
            verdict = "correct"
        else:
            verdict = "wrong"

        lines.append(
            f"| {site} | {chain_length} | {final_zone} | "
            f"{'yes' if actual else 'no'} | "
            f"{'third-party' if rule_third else 'first-party'} "
            f"({verdict}) |"
        )

    lines.append("")

    # 이 과제에서 CDN-hosted라고 분류할 사이트
    cdn_sites = [
        "www.microsoft.com",
        "www.netflix.com",
        "www.adobe.com",
        "www.cnn.com",
        "www.apple.com",
        "www.stanford.edu",
        "www.bbc.co.uk",
        "www.spotify.com",
        "www.wikipedia.org",
        "www.nytimes.com",
    ]

    steered = 0

    for site in cdn_sites:
        all_sets = []

        for result in (network1, hotspot):
            for resolver in RESOLVERS:
                addresses = tuple(sorted(
                    result[site]["answers"].get(resolver, [])
                ))
                all_sets.append(addresses)

        if len(set(all_sets)) > 1:
            steered += 1

    lines.append("## Steering result")
    lines.append("")
    lines.append(
        f"{steered} of {len(cdn_sites)} CDN-hosted sites answered "
        "with a different address set for a different resolver or network."
    )
    lines.append("")
    lines.append(
        "The two measurement networks were home Wi-Fi and a phone hotspot."
    )
    lines.append("")

    lines.append("## Rule failure")
    lines.append("")
    lines.append(
        "The simple zone-comparison rule misclassified www.wikipedia.org. "
        "Its CNAME ends at dyna.wikimedia.org, so the names differ, but "
        "Wikipedia and Wikimedia are part of the same organization rather "
        "than an unrelated third-party CDN."
    )

    report_path = os.path.join(OUT, "report.md")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Saved to {report_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--collect", action="store_true")
    p.add_argument("--report", action="store_true")
    a = p.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.collect:
        collect()
    elif a.report:
        report()
    else:
        p.print_help()
