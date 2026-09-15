#!/usr/bin/env python3
"""Week 3 · Task 1 — Build your own iterative resolver.

Textbook §2.4.2 - §2.4.3.

`dig +trace` walks root -> TLD -> authoritative for you. In this task you do
that walk yourself: start at a root server, read the delegation it returns,
ask the next server, and keep going until somebody answers authoritatively.

You may shell out to `dig` for the transport, or use a DNS library
(`dnspython` is in the container). Either is fine - what matters is that
*you* follow the delegations rather than letting a tool do it.

    python3 task1_resolve.py www.korea.ac.kr
    python3 task1_resolve.py --verify        # check yourself against dig

Pass condition
--------------
`--verify` resolves five names with your resolver and with `dig`, and the
addresses must agree. A name behind a CDN may legitimately return a different
address each time; the harness compares the *set of authoritative nameservers*
you ended at for those, not the address.
"""
import argparse, subprocess, sys

# Root servers. Everything starts here; there is no earlier step.
ROOT_SERVERS = [
    "198.41.0.4",       # a.root-servers.net
    "199.9.14.201",     # b.root-servers.net
    "192.33.4.12",      # c.root-servers.net
]

# (name, kind).  "stable" names must match dig exactly.  "cdn" names are served
# from many replicas and may legitimately give you a different address than dig
# got a second earlier - for those we only require that you reached an answer.
VERIFY_NAMES = [
    ("www.korea.ac.kr", "stable"),
    ("dns.google", "stable"),
    ("en.wikipedia.org", "stable"),
    ("www.stanford.edu", "stable"),
    ("www.microsoft.com", "cdn"),
]


class Resolver:

    def parse_sections(self, output):
        sections = {
            "ANSWER": [],
            "AUTHORITY": [],
            "ADDITIONAL": []
        }

        current = None

        for line in output.splitlines():
            line = line.strip()

            if line == ";; ANSWER SECTION:":
                current = "ANSWER"
                continue

            if line == ";; AUTHORITY SECTION:":
                current = "AUTHORITY"
                continue

            if line == ";; ADDITIONAL SECTION:":
                current = "ADDITIONAL"
                continue

            if line.startswith(";; ") and line.endswith("SECTION:"):
                current = None
                continue

            if not line or line.startswith(";"):
                continue

            if current is not None:
                parts = line.split()

                if len(parts) >= 5:
                    record = {
                        "name": parts[0],
                        "ttl": parts[1],
                        "class": parts[2],
                        "type": parts[3],
                        "value": parts[4]
                    }

                    sections[current].append(record)

        return sections

    def query(self, server, name):
        result = subprocess.run(
            ["dig", f"@{server}", name, "A", "+norecurse"],
            capture_output=True,
            text=True,
            timeout=3
        )
        return result.stdout

    def get_glue_servers(self, sections):
        ns_names = set()

        for record in sections["AUTHORITY"]:
            if record["type"] == "NS":
                ns_names.add(record["value"])

        servers = []

        for record in sections["ADDITIONAL"]:
            if record["type"] == "A" and record["name"] in ns_names:
                servers.append(record["value"])

        return servers

    def resolve(self, name, depth = 0):
        if depth > 8:
            raise RuntimeError("Too many recursive NS lookups")
        servers = ROOT_SERVERS[:]
        path = []

        for _ in range(20):
            next_servers = []
            cname_found = None

            for server in servers:
                path.append(server)

                try:
                    output = self.query(server,name)
                    sections = self.parse_sections(output)

                except subprocess.TimeoutExpired:
                    continue

                for record in sections["ANSWER"]:
                    if record["type"] == "A":
                        return record["value"], path

                for record in sections["ANSWER"]:
                    if record["type"] == "CNAME":
                        cname_found = record["value"]
                        break

                if cname_found:
                    break

                next_servers = self.get_glue_servers(sections)

                if not next_servers:
                    ns_names = []

                    for record in sections["AUTHORITY"]:
                        if record["type"] == "NS":
                            ns_names.append(record["value"])

                    for ns_name in ns_names:
                        try:
                            ns_addr, ns_path = self.resolve(ns_name, depth + 1)

                            path.extend(ns_path)
                            next_servers.append(ns_addr)

                        except Exception:
                            continue

                if next_servers:
                    break

            if cname_found:
                name = cname_found
                servers = ROOT_SERVERS[:]
                continue

            if not next_servers:
                raise RuntimeError("Could not find the next DNS server")

            servers = next_servers

        raise RuntimeError("Too many DNS delegation steps")

# ------------------------------------------------------------------- harness
def dig_answer(name):
    """What the system resolver says, for comparison."""
    out = subprocess.run(["dig", "+short", name, "A"],
                         capture_output=True, text=True).stdout
    return [l for l in out.split() if l and l[0].isdigit()]


def verify():
    r, failures = Resolver(), 0
    for name, kind in VERIFY_NAMES:
        try:
            addr, path = r.resolve(name)
        except NotImplementedError:
            print("Nothing implemented yet - write Resolver.resolve first.")
            return 1
        except Exception as e:
            print(f"  FAIL  {name:<22} your resolver raised {e!r}")
            failures += 1
            continue
        expected = dig_answer(name)
        if addr in expected:
            note = ""
        elif kind == "cdn":
            note = "  <- differs, but this name is CDN-hosted. Explain it."
        else:
            note = "  <- should have matched"
            failures += 1
        print(f"  {'FAIL' if note.endswith('matched') else 'ok  '}  {name:<22} "
              f"you={addr:<16} dig={','.join(expected) or '-'}   "
              f"hops={len(path)}{note}")
    print(f"\n  {len(VERIFY_NAMES) - failures}/{len(VERIFY_NAMES)} ok")
    return 1 if failures else 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("name", nargs="?", default="www.korea.ac.kr")
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()

    if a.verify:
        sys.exit(verify())

    addr, path = Resolver().resolve(a.name)
    for i, server in enumerate(path, 1):
        print(f"  {i}. asked {server}")
    print(f"\n  {a.name} -> {addr}")


if __name__ == "__main__":
    main()
