from zirkel.scan import InclusiveTimeScan
from data_organization import filenames
import anytree
import zirkel


def test_inclusive_time_scan():
    tree = zirkel.load_tree(filenames["hatchet"]["profile"], format="hatchet")
    tree.scan(InclusiveTimeScan(incl_key="incl_time", excl_key="excl_time"))

    for node in anytree.PreOrderIter(tree):
        assert node.data_point("incl_time") is not None
