#!/usr/bin/env python3
"""Week 6 · Task 3 — Reconverge without recomputing the world.

Textbook §5.2.1, §5.3.

A link flaps. Every router in the area has to decide what changed. `FullRecompute`
does the honest thing: throw the table away and run Dijkstra again, from scratch,
for every event. It is correct and it is what the first implementations did.

It is also why a single flapping link in a large area used to melt the CPU of
every router that could see it.

Beat it:

    python3 bench.py
    python3 bench.py --yours

Correctness first. `bench.py` compares your table against a full recompute after
**every single event**. A router that is fast and wrong black-holes traffic.
"""
import heapq

# The harness counts how many times you run a full SPF. This is the score:
# wall-clock time in Python says more about dictionary overhead than about
# routing, but "how many times did the CPU have to recompute the world" is
# exactly what melted real routers.
SPF_RUNS = 0
LAST_SPF_DISTANCES = {}
LAST_SPF_PARENTS = {}


def dijkstra_table(graph, source):
    """Reference shortest-path-first. Returns {destination: first_hop}.

    Use THIS function whenever you need a full recompute. Rolling your own to
    dodge the counter is not an optimisation, it is cheating the meter.
    """
    global SPF_RUNS, LAST_SPF_DISTANCES, LAST_SPF_PARENTS
    SPF_RUNS += 1
    best = {source: (0, None)}
    parents = {source: None}
    pq, done = [(0, source, None)], set()
    while pq:
        cost, node, first_hop = heapq.heappop(pq)
        if node in done:
            continue
        done.add(node)
        best[node] = (cost, first_hop)
        for nbr, w in sorted(graph[node].items()):
            if nbr in done:
                continue
            hop = nbr if node == source else first_hop
            if cost + w < best.get(nbr, (float("inf"), None))[0]:
                best[nbr] = (cost + w, hop)
                parents[nbr] = node
                heapq.heappush(pq, (cost + w, nbr, hop))
    LAST_SPF_DISTANCES = {node: cost for node, (cost, _) in best.items()}
    LAST_SPF_PARENTS = parents
    return {d: h for d, (_, h) in best.items() if d != source and h}


class FullRecompute:
    """On every event, forget everything and run SPF again."""

    def __init__(self, graph, source):
        self.graph = {n: dict(e) for n, e in graph.items()}
        self.source = source
        self.table = dijkstra_table(self.graph, source)

    def link_change(self, a, b, cost):
        """cost=None means the link went down."""
        if cost is None:
            self.graph[a].pop(b, None)
            self.graph[b].pop(a, None)
        else:
            self.graph[a][b] = cost
            self.graph[b][a] = cost
        self.table = dijkstra_table(self.graph, self.source)


class YourRouter:
    """Your router. Same two methods, same table, less work per event.

    What is actually true after one link changes:

      * most destinations are not affected at all
      * a link that is not on any of your shortest paths, going *up*, can only
        matter if it creates something shorter
      * a link going *down* only matters if you were using it

    Deciding which of those applies, cheaply, without getting it wrong, is the
    task. Getting it wrong is worse than being slow - the harness will catch it
    on the event where it happens.
    """

    def __init__(self, graph, source):
        self.graph = {node: dict(edges) for node, edges in graph.items()}
        self.source = source
        self._recompute()

    def link_change(self, a, b, cost):
        old_cost = self.graph[a].get(b)

        # Repeating the current state is not a topology change.
        if old_cost == cost or (old_cost is None and cost is None):
            return

        edge = frozenset((a, b))
        was_tree_edge = edge in self.tree_edges

        if cost is None:
            self.graph[a].pop(b, None)
            self.graph[b].pop(a, None)
        else:
            self.graph[a][b] = cost
            self.graph[b][a] = cost

        if old_cost is not None and (cost is None or cost > old_cost):
            # Raising/removing an edge cannot improve a route.  It matters only
            # when the previous shortest-path tree actually used that edge.
            if was_tree_edge:
                self._recompute()
            return

        # A new/cheaper edge can matter only if crossing it can make the known
        # distance to either endpoint no worse.  Equality needs a full SPF so
        # the result follows exactly the reference algorithm's tie ordering.
        distance_a = self.distances.get(a, float("inf"))
        distance_b = self.distances.get(b, float("inf"))
        candidate_b = distance_a + cost
        candidate_a = distance_b + cost
        if candidate_b == distance_b or candidate_a == distance_a:
            self._recompute()
        elif candidate_b < distance_b or candidate_a < distance_a:
            self._incremental_decrease(a, b, cost)

    def _incremental_decrease(self, a, b, cost):
        """Propagate only improvements caused by one new or cheaper edge.

        If the propagation encounters an equal-cost alternative, fall back to
        full SPF: reproducing the reference implementation's discovery-order
        tie choice is more important than saving one run.
        """
        distances = dict(self.distances)
        parents = dict(self.parents)
        hops = dict(self.table)
        queue = []

        def offer(node, new_cost, parent, first_hop):
            old_cost = distances.get(node, float("inf"))
            if new_cost < old_cost:
                distances[node] = new_cost
                parents[node] = parent
                hops[node] = first_hop
                heapq.heappush(queue, (new_cost, node, first_hop))
                return True
            if new_cost == old_cost and parents.get(node) != parent:
                return False
            return True

        hop_to_b = b if a == self.source else hops.get(a)
        hop_to_a = a if b == self.source else hops.get(b)
        if (hop_to_b is not None and
                not offer(b, distances.get(a, float("inf")) + cost,
                          a, hop_to_b)):
            self._recompute()
            return
        if (hop_to_a is not None and
                not offer(a, distances.get(b, float("inf")) + cost,
                          b, hop_to_a)):
            self._recompute()
            return

        while queue:
            path_cost, node, first_hop = heapq.heappop(queue)
            if path_cost != distances.get(node):
                continue
            for neighbour, weight in sorted(self.graph[node].items()):
                if neighbour == self.source:
                    continue
                if not offer(neighbour, path_cost + weight, node, first_hop):
                    self._recompute()
                    return

        self.distances = distances
        self.parents = parents
        self.table = {
            node: hop for node, hop in hops.items()
            if node != self.source and node in distances and hop is not None
        }
        self.tree_edges = {
            frozenset((node, parent))
            for node, parent in parents.items()
            if parent is not None
        }

    def _recompute(self):
        """Run one full SPF and retain the facts needed to skip later runs."""
        self.table = dijkstra_table(self.graph, self.source)
        self.distances = dict(LAST_SPF_DISTANCES)
        self.parents = dict(LAST_SPF_PARENTS)
        self.tree_edges = {
            frozenset((node, parent))
            for node, parent in self.parents.items()
            if parent is not None
        }
