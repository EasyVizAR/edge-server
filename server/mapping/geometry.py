# All point/line/square functions go here

import math

# Line-line intersection


# Lerp between points
def lerp(p0, p1, u):
    return (p0[0] * (1-u) + p1[0] * u, p0[1] * (1-u) + p1[1] * u)

if __name__ == "__main__":
    p0 = (0, 0)
    p1 = (5, 0)
    points = 5
    segments = 4
    for j in range(segments):
        # lerp between p0 and p1 by j / segments
        pj = lerp(p0, p1, j/segments)
        print(pj)