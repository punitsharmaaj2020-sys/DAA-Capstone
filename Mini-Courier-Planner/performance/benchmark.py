import itertools
import os
import random
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_FOLDER)

from algorithms.sorting import merge_sort, bubble_sort, parcel_key
from algorithms.knapsack import knapsack
from algorithms.dijkstra import build_graph, dijkstra
from algorithms.tsp import nearest_neighbor, brute_force_tsp

CHART_FOLDER = os.path.join(PROJECT_FOLDER, "report", "charts")
REPORT_FILE = os.path.join(PROJECT_FOLDER, "report", "benchmark_results.txt")
SIZE_NAMES = ["small", "medium", "large"]

SORT_SIZES = [100, 1000, 3000]
KNAPSACK_SIZES = [(10, 50), (100, 500), (400, 2000)]
DIJKSTRA_SIZES = [10, 500, 5000]
TSP_SIZES = [10, 200, 1000]
TSP_EXACT_SIZES = [5, 6, 7, 8, 9]

output_lines = []


def say(text=""):
    print(text)
    output_lines.append(text)


def make_parcels(n, seed=42):
    rnd = random.Random(seed)
    return [{"id": f"P{i}", "weight": rnd.randint(1, 20), "value": rnd.randint(10, 500),
             "priority": rnd.randint(1, 3), "deadline_hours": rnd.randint(1, 72)}
            for i in range(n)]


def make_roads(v, seed=42):
    rnd = random.Random(seed)
    roads = []
    for i in range(1, v):
        roads.append([f"N{i}", f"N{rnd.randint(0, i - 1)}", rnd.randint(1, 20)])
    for _ in range(3 * v):
        a, b = rnd.randint(0, v - 1), rnd.randint(0, v - 1)
        if a != b:
            roads.append([f"N{a}", f"N{b}", rnd.randint(1, 20)])
    return roads


def make_distance_matrix(n, seed=42):
    rnd = random.Random(seed)
    points = [(rnd.uniform(0, 100), rnd.uniform(0, 100)) for _ in range(n)]
    names = [f"S{i}" for i in range(n)]
    matrix = {}
    for i in range(n):
        matrix[names[i]] = {}
        for j in range(n):
            matrix[names[i]][names[j]] = ((points[i][0] - points[j][0]) ** 2 +
                                          (points[i][1] - points[j][1]) ** 2) ** 0.5
    return matrix, names


def time_it(func, repeats):
    total = 0
    for _ in range(repeats):
        start = time.perf_counter()
        func()
        total += time.perf_counter() - start
    return total / repeats


def run_correctness_checks():
    say("CORRECTNESS CHECKS")
    say("-" * 60)

    parcels = make_parcels(200)
    ok = merge_sort(parcels, parcel_key) == sorted(parcels, key=parcel_key)
    say(f"1. Merge Sort matches Python's sorted() on 200 parcels : {'PASS' if ok else 'FAIL'}")

    items = make_parcels(12)
    capacity = 30
    best_dp, _, _ = knapsack(items, capacity)
    best_brute = 0
    for mask in range(1 << len(items)):
        w = sum(items[i]["weight"] for i in range(len(items)) if mask >> i & 1)
        v = sum(items[i]["value"] for i in range(len(items)) if mask >> i & 1)
        if w <= capacity and v > best_brute:
            best_brute = v
    ok = best_dp == best_brute
    say(f"2. Knapsack DP equals brute force (12 parcels, cap 30)  : {'PASS' if ok else 'FAIL'}"
        f"  ({best_dp} vs {best_brute})")

    graph = build_graph([["A", "B", 4], ["A", "C", 1], ["C", "B", 2], ["B", "D", 5], ["C", "D", 8]])
    dist, _ = dijkstra(graph, "A")
    ok = dist == {"A": 0, "B": 3, "C": 1, "D": 8}
    say(f"3. Dijkstra on a hand-checked 4-node graph              : {'PASS' if ok else 'FAIL'}  {dist}")

    matrix, names = make_distance_matrix(8)
    route, total = nearest_neighbor(matrix, names[0], names)
    best_route, best_total = brute_force_tsp(matrix, names[0], names)
    ok = sorted(route[:-1]) == sorted(names) and route[0] == route[-1] and total >= best_total - 1e-9
    say(f"4. Nearest Neighbor: all stops visited, >= exact answer : {'PASS' if ok else 'FAIL'}"
        f"  (NN {total:.1f} vs exact {best_total:.1f})")
    say()


def benchmark_sorting():
    results = {"Merge Sort": [], "Bubble Sort": []}
    for n in SORT_SIZES:
        data = make_parcels(n)
        results["Merge Sort"].append(time_it(lambda: merge_sort(data, parcel_key), 5))
        results["Bubble Sort"].append(time_it(lambda: bubble_sort(data, parcel_key), 1))
    return results


def benchmark_knapsack():
    times = []
    for n, capacity in KNAPSACK_SIZES:
        data = make_parcels(n)
        times.append(time_it(lambda: knapsack(data, capacity), 3))
    return times


def benchmark_dijkstra():
    times = []
    for v in DIJKSTRA_SIZES:
        graph = build_graph(make_roads(v))
        times.append(time_it(lambda: dijkstra(graph, "N0"), 5))
    return times


def benchmark_tsp():
    times = []
    for n in TSP_SIZES:
        matrix, names = make_distance_matrix(n)
        times.append(time_it(lambda: nearest_neighbor(matrix, names[0], names), 5))
    return times


def benchmark_tsp_exact():
    nn_times, brute_times, gaps = [], [], []
    for n in TSP_EXACT_SIZES:
        matrix, names = make_distance_matrix(n)
        nn_times.append(time_it(lambda: nearest_neighbor(matrix, names[0], names), 5))
        brute_times.append(time_it(lambda: brute_force_tsp(matrix, names[0], names), 1))
        _, nn_total = nearest_neighbor(matrix, names[0], names)
        _, best_total = brute_force_tsp(matrix, names[0], names)
        gaps.append(max(0.0, (nn_total - best_total) / best_total * 100))
    return nn_times, brute_times, gaps


def ms(seconds):
    return f"{seconds * 1000:.3f}"


def bar_chart(filename, title, xlabels, series, ylabel="Time (ms)", log=False):
    plt.figure(figsize=(7, 4.5))
    width = 0.8 / len(series)
    for k, (label, values) in enumerate(series.items()):
        positions = [i + k * width for i in range(len(xlabels))]
        plt.bar(positions, [v * 1000 for v in values], width=width, label=label)
    plt.xticks([i + width * (len(series) - 1) / 2 for i in range(len(xlabels))], xlabels)
    plt.title(title)
    plt.ylabel(ylabel)
    if log:
        plt.yscale("log")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(CHART_FOLDER, filename), dpi=120)
    plt.close()


def main():
    os.makedirs(CHART_FOLDER, exist_ok=True)

    say("MINI-COURIER PLANNER - PERFORMANCE TESTING")
    say("=" * 60)
    say("Fixed random seed = 42, time.perf_counter(), averaged over several runs\n")

    run_correctness_checks()

    sort_res = benchmark_sorting()
    knap_res = benchmark_knapsack()
    dij_res = benchmark_dijkstra()
    tsp_res = benchmark_tsp()

    say("RUNTIME RESULTS (milliseconds)")
    say("-" * 60)
    say(f"{'Algorithm':<22}{'Input size':<24}{'Time (ms)':>12}")
    for i, name in enumerate(SIZE_NAMES):
        say(f"{'Merge Sort':<22}{name + ' (n=' + str(SORT_SIZES[i]) + ')':<24}{ms(sort_res['Merge Sort'][i]):>12}")
    for i, name in enumerate(SIZE_NAMES):
        say(f"{'Bubble Sort':<22}{name + ' (n=' + str(SORT_SIZES[i]) + ')':<24}{ms(sort_res['Bubble Sort'][i]):>12}")
    for i, name in enumerate(SIZE_NAMES):
        n, cap = KNAPSACK_SIZES[i]
        say(f"{'Knapsack DP':<22}{name + ' (n=' + str(n) + ', W=' + str(cap) + ')':<24}{ms(knap_res[i]):>12}")
    for i, name in enumerate(SIZE_NAMES):
        say(f"{'Dijkstra':<22}{name + ' (V=' + str(DIJKSTRA_SIZES[i]) + ')':<24}{ms(dij_res[i]):>12}")
    for i, name in enumerate(SIZE_NAMES):
        say(f"{'Nearest Neighbor':<22}{name + ' (n=' + str(TSP_SIZES[i]) + ')':<24}{ms(tsp_res[i]):>12}")

    nn_t, brute_t, gaps = benchmark_tsp_exact()
    say()
    say("NEAREST NEIGHBOR vs BRUTE FORCE (exact) - same random maps")
    say("-" * 60)
    say(f"{'Stops':<8}{'NN time (ms)':>15}{'Brute force (ms)':>20}{'NN longer by (%)':>20}")
    for i, n in enumerate(TSP_EXACT_SIZES):
        say(f"{n:<8}{ms(nn_t[i]):>15}{ms(brute_t[i]):>20}{gaps[i]:>20.1f}")

    bar_chart("sorting.png", "Sorting: Merge Sort vs Bubble Sort",
              [f"{s}\n(n={n})" for s, n in zip(SIZE_NAMES, SORT_SIZES)], sort_res)
    bar_chart("knapsack.png", "0/1 Knapsack (Dynamic Programming)",
              [f"{s}\n(n={n}, W={w})" for s, (n, w) in zip(SIZE_NAMES, KNAPSACK_SIZES)],
              {"Knapsack DP": knap_res})
    bar_chart("dijkstra.png", "Dijkstra's Algorithm",
              [f"{s}\n(V={v})" for s, v in zip(SIZE_NAMES, DIJKSTRA_SIZES)], {"Dijkstra": dij_res})
    bar_chart("tsp.png", "Nearest Neighbor TSP",
              [f"{s}\n(n={n})" for s, n in zip(SIZE_NAMES, TSP_SIZES)], {"Nearest Neighbor": tsp_res})
    bar_chart("all_algorithms.png", "All algorithms (log scale)", SIZE_NAMES,
              {"Merge Sort": sort_res["Merge Sort"], "Knapsack DP": knap_res,
               "Dijkstra": dij_res, "Nearest Neighbor": tsp_res}, log=True)
    bar_chart("tsp_exact_vs_nn.png", "TSP: Nearest Neighbor vs Brute Force (log scale)",
              [f"{n} stops" for n in TSP_EXACT_SIZES],
              {"Nearest Neighbor": nn_t, "Brute force": brute_t}, log=True)

    say()
    say(f"Charts saved in: {CHART_FOLDER}")
    with open(REPORT_FILE, "w") as f:
        f.write("\n".join(output_lines) + "\n")
    say(f"Results saved in: {REPORT_FILE}")


if __name__ == "__main__":
    main()
