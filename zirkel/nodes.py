import hashlib
import anytree

import numpy as np

from zirkel.generic_file import is_multi_threaded_region
from zirkel.generic_file import parse_multi_threaded_region_name


class SingleThreadedDataMixin:
    def data_point(self, key, master_only=False):
        return self._data[key]

    def data(self, master_only=False):
        return {k: self.data_point(k, master_only=master_only) for k in self._data}


class PathSHAMixin:
    @property
    def path(self):
        if not hasattr(self, "_str_path"):
            if self.parent:
                self._str_path = self.parent.path + "/" + self.region_name
            else:
                self._str_path = self.region_name

        return self._str_path

    @property
    def sha(self):
        if not hasattr(self, "_sha"):
            self._sha = hashlib.sha256(self.path.encode("utf-8")).hexdigest()

        return self._sha


class ScanMixin:
    def scan(self, transform):
        for child in self.children:
            child.scan(transform)

        transform(self)


class TransformMixin:
    def transform(self, transform):
        transform(self)
        for child in self.children:
            child.transform(transform)


class BasicNode(ScanMixin, TransformMixin, PathSHAMixin, SingleThreadedDataMixin):
    @property
    def is_multi_threaded(self):
        return not self.is_single_threaded

    def __getitem__(self, path):
        r = anytree.Resolver("region_name")
        return r.get(self, path)


class MPINode(BasicNode, anytree.NodeMixin):
    def __init__(self, region_name, data, parent=None, children=None):
        self.region_name = region_name
        self._data = data

        # anytree requirements
        self.parent = parent
        if children:
            self.children = children

    @property
    def is_single_threaded(self):
        return True


class MultiThreadNode(BasicNode, anytree.NodeMixin):
    def __init__(self, region_name, data, parent=None, children=None):
        self.region_name = region_name
        self._data = data

        # anytree requirements
        self.parent = parent
        if children:
            self.children = children

    @property
    def is_single_threaded(self):
        return False

    def data_point(self, key, master_only=False):
        if master_only:
            return self._data[key][self.master_tid, ...]
        else:
            return self._data[key]

    @property
    def master_tid(self):
        if not hasattr(self, "_master_tid"):
            self._master_tid = self.parent.master_tid

        return self._master_tid

    @master_tid.setter
    def master_tid(self, master_tid):
        self._master_tid = master_tid
        return self._master_tid


class IndividualThreadsNode(anytree.NodeMixin):
    def __init__(self, master_region_name, parent=None, children=None):
        self.region_name = "multi_threaded"
        self.id, self.master_tid = self.parse_region_name(master_region_name)

        # anytree requirements
        self.parent = parent
        if children:
            self.children = children

    def parse_region_name(self, region_name):
        return parse_multi_threaded_region_name(region_name)


class SingleThreadNode(SingleThreadedDataMixin, anytree.NodeMixin):
    def __init__(self, region_name, data, tid=None, parent=None, children=None):
        self.region_name = region_name
        self._data = data
        self.tid = tid

        # anytree requirements
        self.parent = parent
        if children:
            self.children = children


class StackingAggregator:
    def __init__(self, n_threads):
        self.n_threads = n_threads

    def __call__(self, threadwise_data):
        keys = set().union(*[d.keys() for d in threadwise_data.values()])
        data = dict()

        for tid, thread_data in threadwise_data.items():
            for key in keys:
                if key in thread_data:
                    self.maybe_initialize(data, key, thread_data[key])
                    data[key][tid, ...] = thread_data[key]

        return data

    def maybe_initialize(self, data, key, data_point):
        if key not in data:
            shape = (self.n_threads,) + np.shape(data_point)
            data[key] = np.ma.masked_all(shape, dtype=np.float64)


def build_tree(parsed_data, root_id):
    if is_multi_threaded_region(parsed_data.region_name(root_id)):
        return build_multi_threaded_tree(parsed_data, root_id)
    else:
        return build_mpi_tree(parsed_data, root_id)


def _build_tree(parsed_data, root_id, build_tree, Node):
    children_id = parsed_data.children(root_id)
    children = [build_tree(parsed_data, i) for i in children_id]

    region_name = parsed_data.region_name(root_id)
    data = parsed_data.data(root_id)
    return Node(region_name, data, children=children)


def build_mpi_tree(parsed_data, root_id):
    return _build_tree(parsed_data, root_id, build_tree, MPINode)


def build_multi_threaded_tree(parsed_data, root_id):
    region_name = parsed_data.region_name(root_id)
    mtr_id, _ = parse_multi_threaded_region_name(region_name)
    children_id = parsed_data.multi_threaded_region_ids(mtr_id)
    child_trees = [build_single_thread_tree(parsed_data, i) for i in children_id]

    region_name = parsed_data.region_name(root_id)
    return IndividualThreadsNode(region_name, children=child_trees)


def build_single_thread_tree(parsed_data, root_id, tid=None):
    region_name = parsed_data.region_name(root_id)
    if tid is None:
        assert is_multi_threaded_region(region_name)
        _, tid = parse_multi_threaded_region_name(region_name)

    return _build_tree(
        parsed_data,
        root_id,
        lambda md, rid: build_single_thread_tree(md, rid, tid=tid),
        lambda *a, **kw: SingleThreadNode(*a, tid=tid, **kw),
    )


def stack_multi_threaded_regions(root):
    if type(root) == MPINode:
        children = [stack_multi_threaded_regions(child) for child in root.children]
        return MPINode(root.region_name, root._data, children=children)

    if type(root) == IndividualThreadsNode:
        new_self = merge_nodes(
            root.region_name, root.children, n_threads=len(root.children)
        )

        new_self.master_tid = root.master_tid
        return new_self


def compute_mergeable_nodes(nodes):
    to_merge = dict()
    for n in nodes:
        region_name = n.region_name
        to_merge.setdefault(region_name, []).append(n)

    return to_merge


def merge_nodes(region_name, nodes, n_threads, aggregator=None):
    if aggregator is None:
        aggregator = StackingAggregator(n_threads=n_threads)

    single_threaded_children = []
    for n in nodes:
        if hasattr(n, "children"):
            single_threaded_children += n.children

    to_merge = compute_mergeable_nodes(single_threaded_children)
    children = [
        merge_nodes(
            *item,
            n_threads=n_threads,
            aggregator=aggregator,
        )
        for item in to_merge.items()
    ]

    aggregated_data = aggregator({n.tid: n.data(master_only=False) for n in nodes})
    return MultiThreadNode(region_name, aggregated_data, children=children)
