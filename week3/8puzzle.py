def dfs(s, g, d, path, seen):
    if s == g:
        return path

    if d == 0:
        return None

    z = s.index(0)
    r = z // 3
    c = z % 3

    a = []

    if r > 0:
        a.append(z - 3)
    if r < 2:
        a.append(z + 3)
    if c > 0:
        a.append(z - 1)
    if c < 2:
        a.append(z + 1)

    for x in a:
        t = list(s)
        t[z], t[x] = t[x], t[z]
        t = tuple(t)

        if t not in seen:
            q = dfs(t, g, d - 1, path + [t], seen | {t})
            if q:
                return q

    return None


def iddfs(s, g):
    for d in range(1, 50):
        p = dfs(s, g, d, [s], {s})
        if p:
            return p


s = (5, 4, 0, 6, 1, 8, 7, 3, 2)
g = (0,1, 2, 3, 4, 5, 6, 7, 8)

p = iddfs(s, g)

if p:
    print("Solution:")
    z = 1
    for x in p:
        print("step: ",z)
        z+=1
        print(x[0:3])
        print(x[3:6])
        print(x[6:9])
        print()
else:
    print("No solution")
