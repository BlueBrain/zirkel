import anytree
import numpy as np


def print_data(tree, key):
    prefix_width = 40
    for pre, _, node in anytree.RenderTree(tree):
        prefix = f"{pre}{node.region_name}"

        time = node.data_point(key, master_only=False)
        formatted_data = format_array("{:7.3f}", time, indent=prefix_width)

        print(prefix.ljust(prefix_width), formatted_data)


def format_array(pattern, array, indent=0):
    return np.array2string(
        np.array(array),
        prefix=(indent + 1) * " ",
        formatter={"float": lambda x: pattern.format(x)},
        max_line_width=1000,
    )
