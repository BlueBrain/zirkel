import os
import zirkel
import anytree
import pytest

from data_organization import filenames


def format_hierarchy(tree):
    paths = [node.path for _, _, node in anytree.RenderTree(tree)]
    return sorted(paths)


def load_expected_hierarchy(format):
    return zirkel.read_json(filenames[format]["expected_hierarchy"])


@pytest.mark.parametrize("format", ["hatchet", "mpi_report"])
def test_hierarchy(format):
    tree = zirkel.load_tree(filenames[format]["profile"], format=format)

    expected = load_expected_hierarchy(format=format)
    actual = format_hierarchy(tree)

    assert expected == actual
