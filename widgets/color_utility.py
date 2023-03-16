import random


def random_color() -> str:
    # forces soft colors (not dark & not too white)
    color = "#" + ''.join([random.choice('ABCD') for j in range(6)])
    return color


def opposite_color(rgb: str) -> str:
    rgb_int = int(rgb[1:], 16)
    while_int = int("FFFFFF", 16)
    opposite = while_int - rgb_int
    return "#" + str(hex(opposite))[2:]
