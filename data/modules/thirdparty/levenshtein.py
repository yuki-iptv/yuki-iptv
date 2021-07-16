def levenshtein_distance(str1, str2):
    """
    This function returns the Levenshtein distance between two strings.
    The Levenshtain distance is defined as the minimum number of
    insertions, deletions, and/or substitutions that must be made to
    make two strings equal.
    """
    x, y = len(str1), len(str2)

    search = [[0 for _ in range(x)] for _ in range(y)]
    search[0][0] = int(str1[0] != str2[0])

    for i in range(1, x):
        search[0][i] = max(i, search[0][i-1] + int(str1[i] != str2[0]))

    for j in range(1, y):
        search[j][0] = max(j, search[j-1][0] + int(str1[0] != str2[j]))

    for j in range(1, y):
        for i in range(1, x):

            search[j][i] = min(search[j-1][i], search[j][i-1], search[j-1][i-1]) + int(str1[i] != str2[j])

    if __name__ == '__main__':
        print('   ' + ', '.join([s for s in str1]))
        print('\n'.join([str2[j] + ': ' + ', '.join([str(s) for s in r]) for j, r in enumerate(search)]))

    return search[-1][-1]

def damerau_levenshtein(a, b):
    x, y = len(a), len(b)

    a_lookup = {k: -1 for k in set(a).union(set(b))}
    dist = [[0 for _ in range(x)] for _ in range(y)]
    max_dist = x + y
    dist[0][0] = int(a[0] != b[0])
    for i in range(1, x):
        dist[0][i] = max(i, dist[0][i-1] + int(a[i] != b[0]))

    a_lookup[a[0]] = 0

    for j in range(1, y):
        dist[j][0] = max(j, dist[j-1][0] + int(a[0] != b[j]))

    for i in range(1, x):
        _b = 0
        for j in range(1, y):
            da = a_lookup[b[j]]
            db = _b
            if a[i] == b[j]:
                cost = 0
                _b = j
            else:
                cost = 1
            sub = dist[j-1][i-1] + cost
            ins = dist[j][i-1] + 1
            del_ = dist[j-1][i] + 1
            if da < 0 or db < 0:
                trans = max_dist
            elif da == 0 and db == 0:
                trans = i + j - 1
            elif da == 0:
                trans = 2 * i + j - db - 1
            elif db == 0:
                trans = 2 * j + i - da - 1
            else:
                trans = dist[db-1][da-1] + (i - da - 1) + (j - db - 1) + 1
            dist[j][i] = min(
                sub,
                ins,
                del_,
                trans
            )

        a_lookup[a[i]] = i

    return dist[-1][-1]