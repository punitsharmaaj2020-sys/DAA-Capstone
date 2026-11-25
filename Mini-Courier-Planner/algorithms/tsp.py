from itertools import permutations


def nearest_neighbor(dist, start, stops):
    unvisited = [s for s in stops if s != start]
    route = [start]
    total = 0
    current = start

    while unvisited:
        nearest = min(unvisited, key=lambda place: dist[current][place])
        total += dist[current][nearest]
        route.append(nearest)
        unvisited.remove(nearest)
        current = nearest

    total += dist[current][start]
    route.append(start)
    return route, total


def route_length(dist, route):
    return sum(dist[route[i]][route[i + 1]] for i in range(len(route) - 1))


def brute_force_tsp(dist, start, stops):
    stops = [s for s in stops if s != start]
    best_route = None
    best_total = float("inf")
    for order in permutations(stops):
        route = [start] + list(order) + [start]
        total = route_length(dist, route)
        if total < best_total:
            best_total = total
            best_route = route
    return best_route, best_total
