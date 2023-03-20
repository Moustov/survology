import random
from datetime import datetime


def random_color() -> str:
    # forces soft colors (not dark & not too white)
    random.seed(datetime.now().timestamp())
    color = "#" + ''.join([random.choice('ABCD') for j in range(6)])
    print("color", color)
    return color


def opposite_color(rgb: str) -> str:
    rgb_int = int(rgb[1:], 16)
    while_int = int("FFFFFF", 16)
    opposite = while_int - rgb_int
    return "#" + str(hex(opposite))[2:]
