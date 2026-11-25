def knapsack(parcels, capacity):
    if capacity < 0:
        raise ValueError("Capacity cannot be negative")

    n = len(parcels)
    table = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        weight = parcels[i - 1]["weight"]
        value = parcels[i - 1]["value"]
        for w in range(capacity + 1):
            table[i][w] = table[i - 1][w]
            if weight <= w:
                take = table[i - 1][w - weight] + value
                if take > table[i][w]:
                    table[i][w] = take

    selected = []
    w = capacity
    for i in range(n, 0, -1):
        if table[i][w] != table[i - 1][w]:
            selected.append(parcels[i - 1])
            w -= parcels[i - 1]["weight"]
    selected.reverse()

    return table[n][capacity], selected, table


def print_dp_table(parcels, table):
    capacity = len(table[0]) - 1
    print("        " + "".join(f"{w:>5}" for w in range(capacity + 1)))
    for i in range(len(table)):
        label = "none" if i == 0 else parcels[i - 1]["id"]
        print(f"{label:<8}" + "".join(f"{v:>5}" for v in table[i]))
