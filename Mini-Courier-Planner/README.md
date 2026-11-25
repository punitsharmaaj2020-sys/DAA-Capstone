# Mini-Courier Planner

DAA Capstone Assignment (ETCCDA302) - an integrated Python application that plans one courier trip:
it prioritises parcels, chooses what fits in the vehicle, finds shortest roads and builds a delivery route.

## How to run
```
pip install -r requirements.txt        # only needed for the charts (matplotlib)
python main.py                          # run the planner on the sample data
python main.py --capacity 15            # change vehicle capacity (kg)
python main.py --parcels my_parcels.json --locations my_map.json    # unseen data
python performance/benchmark.py         # performance tests + charts (takes ~5 seconds)
```
Python 3.8 or newer. `main.py` uses only the standard library.

## Project structure
```
main.py                  integrated application (steps 1-7)
algorithms/sorting.py    Merge Sort (+ Bubble Sort for comparison)
algorithms/knapsack.py   0/1 Knapsack with Dynamic Programming
algorithms/dijkstra.py   graph building + Dijkstra + path rebuilding
algorithms/tsp.py        Nearest Neighbor TSP (+ brute force to check it)
data/parcels.json        12 sample parcels
data/locations.json      warehouse + 10 places + 15 two-way roads
performance/benchmark.py correctness checks, timings, charts
report/REPORT.md         final report
report/charts/           runtime charts (PNG)
report/benchmark_results.txt   benchmark output
screenshots/             output traces of sample runs
```

## Data formats
Parcel: `{"id", "name", "weight" (kg, whole number), "value" (Rs, delivery charge), "priority" (1 = most urgent), "deadline_hours", "location"}`
Map: `{"warehouse": name, "locations": [...], "roads": [[placeA, placeB, km], ...]}` - roads are two-way.

## How data moves through the program
1. `load_json` reads both files; `check_parcels` removes bad parcels (missing field, weight <= 0, unknown or unreachable location).
2. `sort_parcels` (Merge Sort) orders parcels by `(priority, deadline_hours)`.
3. `knapsack` receives the sorted list and the capacity, and returns best value, selected parcels, and the DP table.
4. Selected parcels are grouped by location -> the list of **stops**.
5. `dijkstra` is run from the warehouse and from every stop -> a **distance matrix** (`matrix[a][b]` = shortest road km).
6. `nearest_neighbor` reads only that matrix and returns the stop order and total km.
7. `full_road_path` uses Dijkstra's `previous` dictionaries to expand each leg into real roads.

## Assumptions
- Vehicle capacity is 25 kg (constant `VEHICLE_CAPACITY` in `main.py`, or `--capacity`).
- Parcel value = delivery charge in rupees; weights are whole kg (needed for the DP table).
- The vehicle starts and ends at the warehouse, and makes one trip.
- Nearest Neighbor only looks at distance, not deadlines (see limitations in the report).

## Assignment phases -> where they are covered
| Phase | Covered in |
|---|---|
| 1. Design and planning | `report/REPORT.md` sections 1-4, data files, "How data moves" above |
| 2. Sorting + Knapsack | `algorithms/sorting.py`, `algorithms/knapsack.py`, Steps 2-3 of `main.py` (DP table is printed) |
| 3. Dijkstra + Nearest Neighbor | `algorithms/dijkstra.py`, `algorithms/tsp.py`, Steps 4-7 of `main.py` |
| 4. Performance testing | `performance/benchmark.py`, `report/charts/`, `report/benchmark_results.txt`, report sections 9-12 |
| 5. Report + demo | `report/REPORT.md`, `screenshots/`, this README |

## Viva guide - things you may be asked
**Merge Sort** (`merge_sort`, `merge`): split in half, sort each half recursively, merge by repeatedly taking the smaller front element. O(n log n) always; O(n) extra space. Stable (`<=` in `merge`).
*Change it:* edit `parcel_key` to sort by deadline only -> `return parcel["deadline_hours"]`; for highest value first use `-parcel["value"]`.

**Knapsack** (`knapsack`): `table[i][w]` = best value using the first `i` parcels with limit `w`. Either skip parcel `i` (`table[i-1][w]`) or take it (`table[i-1][w-weight] + value`) and keep the larger. The traceback goes from the last row: if `table[i][w] != table[i-1][w]`, parcel `i` was taken, so subtract its weight. O(nW) time and space.
*Trace by hand:* use 3 parcels and capacity 5 and fill the table row by row.
*Edge cases handled:* capacity 0, parcel heavier than capacity (never taken), negative capacity (error).

**Dijkstra** (`dijkstra`): keep the best known distance to every node; repeatedly pop the closest unvisited node from the heap and *relax* its edges (`new_dist < dist[v]`). `previous` remembers the path. O((V+E) log V). Needs non-negative weights (checked in `build_graph`).
*Change it:* change the warehouse in `locations.json`; add a road to the `roads` list.

**Nearest Neighbor** (`nearest_neighbor`): from the current place always move to the closest unvisited stop, then return to the warehouse. O(n^2). It is a *greedy approximation*: it can be worse than the best route (the sample data shows 47 km vs 37 km), which is why `brute_force_tsp` exists for comparison (O(n!), only for few stops).

**Why DP and not greedy for packing?** Greedy by value/weight can miss the best combination, and we cannot split a parcel (0/1), so DP is needed.

**Why Dijkstra before TSP?** The map is not complete - not every place has a direct road to every other place. Dijkstra gives the real shortest distance between any two stops, and Nearest Neighbor needs those distances.

## Checklist (assignment requirement -> implementation)
| Requirement | Done in |
|---|---|
| Parcel attributes defined | `data/parcels.json`, report section 4 |
| Delivery points / graph format | `data/locations.json`, `build_graph` |
| Design showing how algorithms work together | report section 4 & 6, "How data moves" |
| Sort by deadline/priority (best sorting algorithm) | `merge_sort` / `sort_parcels`, report explains the choice |
| DP for the optimal parcel set | `knapsack` |
| DP table / output evidence, selected list | printed in Step 3 of `main.py`, `screenshots/` |
| Customer graph | `build_graph` |
| Dijkstra individual shortest paths | Step 5 of `main.py`, `dijkstra`, `get_path` |
| Nearest-neighbour TSP route and length | Step 6-7 of `main.py`, `nearest_neighbor` |
| Small and larger datasets | `performance/benchmark.py` (small/medium/large) |
| Runtime of major steps, runtime chart | `report/charts/`, `benchmark_results.txt` |
| Correctness evidence | "Correctness checks" in `benchmark.py` |
| Optimization comments | report section 12 |
| Screenshots / output traces | `screenshots/` (take your own screenshots too, see below) |
| Documentation + execution steps | this README + `report/REPORT.md` |
