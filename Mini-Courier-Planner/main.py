
import argparse
import json
import sys
import os

from algorithms.sorting import sort_parcels
from algorithms.knapsack import knapsack, print_dp_table
from algorithms.dijkstra import build_graph, dijkstra, get_path, INF
from algorithms.tsp import nearest_neighbor, brute_force_tsp

VEHICLE_CAPACITY = 25
BRUTE_FORCE_LIMIT = 8

# Get the folder where main.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_json(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)

    except FileNotFoundError:
        print(f"Error: file '{filename}' not found")
        print("Please check whether the data folder and JSON files exist.")
        sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"Error: '{filename}' is not valid JSON ({e})")
        sys.exit(1)


def check_parcels(parcels, graph, warehouse):
    dist_from_warehouse, _ = dijkstra(graph, warehouse)

    required = [
        "id", "weight", "value", "priority",
        "deadline_hours", "location"
    ]

    valid = []

    for p in parcels:
        missing = [field for field in required if field not in p]

        if missing:
            print(f"  Skipping a parcel: missing fields {missing}")

        elif p["weight"] <= 0 or p["value"] < 0:
            print(f"  Skipping {p['id']}: weight must be > 0 and value >= 0")

        elif p["location"] not in graph:
            print(f"  Skipping {p['id']}: location '{p['location']}' is not on the map")

        elif dist_from_warehouse[p["location"]] == INF:
            print(f"  Skipping {p['id']}: '{p['location']}' cannot be reached from the warehouse")

        else:
            valid.append(p)

    return valid


def print_parcel_table(parcels):
    print(
        f"  {'ID':<5}{'Name':<16}{'Wt(kg)':>7}"
        f"{'Value':>7}{'Prio':>6}{'Deadline(h)':>12}  Location"
    )

    for p in parcels:
        print(
            f"  {p['id']:<5}{p['name']:<16}{p['weight']:>7}"
            f"{p['value']:>7}{p['priority']:>6}"
            f"{p['deadline_hours']:>12}  {p['location']}"
        )


def build_distance_matrix(graph, places):
    matrix = {}
    previous = {}

    for a in places:
        dist, prev = dijkstra(graph, a)
        matrix[a] = {b: dist[b] for b in places}
        previous[a] = prev

    return matrix, previous


def full_road_path(route, previous):
    path = [route[0]]

    for i in range(len(route) - 1):
        leg = get_path(
            previous[route[i]],
            route[i],
            route[i + 1]
        )

        path.extend(leg[1:])

    return path


def main():

    parser = argparse.ArgumentParser(
        description="Mini-Courier Planner"
    )

    # Absolute paths prevent working-directory errors
    parser.add_argument(
        "--parcels",
        default=os.path.join(BASE_DIR, "data", "parcels.json")
    )

    parser.add_argument(
        "--locations",
        default=os.path.join(BASE_DIR, "data", "locations.json")
    )

    parser.add_argument(
        "--capacity",
        type=int,
        default=VEHICLE_CAPACITY
    )

    args = parser.parse_args()

    print("=" * 70)
    print("STEP 1: Load data")
    print("=" * 70)

    print(f"Loading parcels from: {args.parcels}")
    print(f"Loading locations from: {args.locations}")

    parcels = load_json(args.parcels)
    map_data = load_json(args.locations)

    warehouse = map_data["warehouse"]
    graph = build_graph(map_data["roads"])

    if warehouse not in graph:
        print("Error: warehouse is not connected to any road")
        sys.exit(1)

    if args.capacity < 0:
        print("Error: capacity cannot be negative")
        sys.exit(1)

    print(f"Vehicle capacity : {args.capacity} kg")
    print(f"Warehouse        : {warehouse}")
    print(f"Locations on map : {len(graph)}   Roads: {len(map_data['roads'])}")
    print(f"Parcels loaded   : {len(parcels)}")

    parcels = check_parcels(parcels, graph, warehouse)

    if not parcels:
        print("No valid parcels to deliver.")
        return

    print_parcel_table(parcels)

    # STEP 2: SORTING
    print("\n" + "=" * 70)
    print("STEP 2: Sort parcels with Merge Sort (priority first, then deadline)")
    print("=" * 70)

    sorted_parcels = sort_parcels(parcels)
    print_parcel_table(sorted_parcels)

    # STEP 3: KNAPSACK
    print("\n" + "=" * 70)
    print("STEP 3: 0/1 Knapsack (Dynamic Programming)")
    print("=" * 70)

    best_value, selected, table = knapsack(
        sorted_parcels,
        args.capacity
    )

    print("DP table (rows = parcels considered so far, columns = capacity in kg):")

    print_dp_table(sorted_parcels, table)

    total_weight = sum(p["weight"] for p in selected)

    print(f"\nSelected parcels ({len(selected)}):")
    print_parcel_table(selected)

    print(f"Total weight : {total_weight} / {args.capacity} kg")
    print(f"Total value  : {best_value}")

    left_behind = [
        p for p in sorted_parcels if p not in selected
    ]

    print(
        "Left for the next trip: "
        + (", ".join(p["id"] for p in left_behind) or "none")
    )

    if not selected:
        print("No parcel fits in the vehicle, nothing to deliver.")
        return

    # STEP 4: DELIVERY LOCATIONS
    print("\n" + "=" * 70)
    print("STEP 4: Delivery locations of the selected parcels")
    print("=" * 70)

    parcels_at = {}

    for p in selected:
        parcels_at.setdefault(p["location"], []).append(p["id"])

    stops = sorted(parcels_at)

    for place in stops:
        print(f"  {place:<18} -> {', '.join(parcels_at[place])}")

    # STEP 5: DIJKSTRA
    print("\n" + "=" * 70)
    print("STEP 5: Dijkstra - shortest paths from the warehouse")
    print("=" * 70)

    dist, prev = dijkstra(graph, warehouse)

    for place in stops:
        path = get_path(prev, warehouse, place)

        print(
            f"  {warehouse} -> {place:<18} "
            f"{dist[place]:>4} km   via {' -> '.join(path)}"
        )

    places = [warehouse] + stops

    matrix, previous = build_distance_matrix(graph, places)

    print("\nShortest distance matrix between stops (km):")

    short = lambda name: name[:9]

    print(
        f"  {'':<10}"
        + "".join(f"{short(b):>10}" for b in places)
    )

    for a in places:
        print(
            f"  {short(a):<10}"
            + "".join(f"{matrix[a][b]:>10}" for b in places)
        )

    # STEP 6: TSP
    print("\n" + "=" * 70)
    print("STEP 6: Nearest Neighbor TSP (approximation)")
    print("=" * 70)

    route, total_distance = nearest_neighbor(
        matrix,
        warehouse,
        stops
    )

    print("Stop order: " + " -> ".join(route))

    # STEP 7: FINAL DELIVERY PLAN
    print("\n" + "=" * 70)
    print("STEP 7: FINAL DELIVERY PLAN")
    print("=" * 70)

    print("Road-by-road route:")

    print("  " + " -> ".join(
        full_road_path(route, previous)
    ))

    print(
        f"\nTotal route distance : {total_distance} km "
        "(returning to the warehouse)"
    )

    print(f"Parcels delivered    : {', '.join(p['id'] for p in selected)}")
    print(f"Packed weight        : {total_weight} kg of {args.capacity} kg")
    print(f"Total parcel value   : {best_value}")

    print("\nDelivery order and deadlines:")

    for place in route[1:-1]:
        for p in selected:
            if p["location"] == place:
                print(
                    f"  {place:<18} {p['id']} "
                    f"{p['name']:<15} priority {p['priority']}, "
                    f"deadline {p['deadline_hours']} h"
                )

    print("\nNote: Nearest Neighbor is an approximation, not always the shortest route.")

    # BRUTE FORCE COMPARISON
    if len(stops) <= BRUTE_FORCE_LIMIT:

        best_route, best_total = brute_force_tsp(
            matrix,
            warehouse,
            stops
        )

        print(
            f"Exact best route (brute force, {len(stops)} stops): "
            f"{best_total} km"
        )

        print(
            f"Nearest Neighbor gave: {total_distance} km "
            f"({total_distance - best_total} km more than the best)"
        )

    else:
        print(
            f"(More than {BRUTE_FORCE_LIMIT} stops, "
            "so the exact comparison was skipped.)"
        )


if __name__ == "__main__":
    main()
