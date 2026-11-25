
import matplotlib.pyplot as plt

def make(d, i):
    if d == 3:
        return {"d": d, "i": i, "val": v[i], "kids": [], "cut": False}

    return {
        "d": d,
        "i": i,
        "val": None,
        "kids": [make(d+1, i*2), make(d+1, i*2+1)],
        "cut": False
    }


def prune(node):
    node["cut"] = True
    for ch in node["kids"]:
        prune(ch)


def ab(node, mx, a, b):
    if node["d"] == 3:
        return node["val"]

    best = -9999 if mx else 9999

    for j, ch in enumerate(node["kids"]):
        if a >= b:
            prune(ch)
            continue

        val = ab(ch, not mx, a, b)

        if mx:
            best = max(best, val)
            a = max(a, best)
        else:
            best = min(best, val)
            b = min(b, best)

    node["val"] = best
    return best


def positions(node, x, y, gap):
    node["x"] = x
    node["y"] = y

    if node["d"] < 3:
        positions(node["kids"][0], x-gap, y-1, gap/2)
        positions(node["kids"][1], x+gap, y-1, gap/2)


def draw(node, ax):
    x, y = node["x"], node["y"]

    for ch in node["kids"]:
        ax.plot([x, ch["x"]], [y, ch["y"]], color="black",
                linestyle="--" if ch["cut"] else "-",
                linewidth=1.5)
        draw(ch, ax)

    if node["cut"]:
        name = "X"
        color = "red"
    elif node["d"] == 3:
        name = str(node["val"])
        color = "black"
    else:
        name = ("MAX" if node["d"] % 2 == 0 else "MIN")
        name += "\n" + str(node["val"])
        color = "black"

    ax.scatter(x, y, s=1500, facecolors="white",
               edgecolors=color, linewidths=1.8, zorder=3)

    ax.text(x, y, name, ha="center", va="center",
            fontsize=9, color=color, zorder=4)


v = list(map(int, input("Enter 8 leaf values: ").split()))

if len(v) != 8:
    print("Enter exactly 8 values")
else:
    root = make(0, 0)

    ans = ab(root, True, -9999, 9999)

    positions(root, 0, 3, 3.5)

    fig, ax = plt.subplots(figsize=(15, 8))

    draw(root, ax)

    ax.set_title("MINIMAX TREE WITH ALPHA-BETA PRUNING",
                 fontsize=15, pad=20)

    ax.text(0, -1.5, "Optimal Value: " + str(ans),
            ha="center", fontsize=13)

    ax.text(-7, -1, "Solid line = Explored",
            fontsize=10)
    ax.text(2, -1, "Dashed line = Pruned",
            fontsize=10, color="red")

    ax.set_xlim(-9, 9)
    ax.set_ylim(-2, 4)
    ax.axis("off")

    plt.tight_layout()
    plt.show()

    print("Optimal Value:", ans)
