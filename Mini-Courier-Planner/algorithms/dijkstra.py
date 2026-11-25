import heapq

INF = float("inf")


def build_graph(roads):
    graph = {}
    for a, b, distance in roads:
        if distance < 0:
            raise ValueError(f"Negative distance on road {a}-{b}; Dijkstra needs non-negative weights")
        graph.setdefault(a, []).append((b, distance))
        graph.setdefault(b, []).append((a, distance))
    return graph


def dijkstra(graph, source):
    if source not in graph:
        raise ValueError(f"'{source}' is not in the graph")

    dist = {node: INF for node in graph}
    previous = {}
    dist[source] = 0
    heap = [(0, source)]

    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, weight in graph[u]:
            new_dist = d + weight
            if new_dist < dist[v]:
                dist[v] = new_dist
                previous[v] = u
                heapq.heappush(heap, (new_dist, v))

    return dist, previous


def get_path(previous, source, target):
    if target != source and target not in previous:
        return None
    path = [target]
    while path[-1] != source:
        path.append(previous[path[-1]])
    path.reverse()
    return path
