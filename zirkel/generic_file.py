import os
import json
import re
import abc

import numpy as np


def read_something(filename, command, mode="r", **kwargs):
    filename = os.path.expandvars(os.path.expanduser(filename))
    with open(filename, mode, **kwargs) as f:
        return command(f)


def read_json(filename):
    """Reads the JSON file into memory.

    Arguments:
        filename  The name of the JSON file. Environment variables will be
                  expanded automatically, incl. "~/".
    """
    return read_something(filename, lambda f: json.load(f))


class RawGenericFile(abc.ABC):
    @abc.abstractproperty
    def parents(self):
        """For each region this list contains the ID of the parent."""
        pass

    @abc.abstractmethod
    def region_name(self, id):
        """The region with id `id` without the full path."""
        pass

    @abc.abstractproperty
    def region_ids(self):
        """An ID of the region.

        This ID is not propagated to the final tree. It is mearly an ID of a
        region which will be passed back to this function to retrieve
        information.
        """
        pass

    @abc.abstractmethod
    def count_mpi_ranks(self):
        """Counts the number of MPI ranks we have data for."""
        pass

    @abc.abstractmethod
    def data(self, id):
        """A dictionary with the data to be stored in the node for region `id`."""
        pass

    @property
    def n_mpi_ranks(self):
        if not hasattr(self, "_n_mpi_ranks"):
            self._n_mpi_ranks = self.count_mpi_ranks()

        return self._n_mpi_ranks

    def guess_root(self):
        root = [
            k
            for k in self.find_tree_roots_id()
            if not is_multi_threaded_region(self.region_name(k))
        ]

        root = [k for k in root if not self.region_name(k).startswith("MPI_")]

        if len(root) != 1:
            print(root)
            raise RuntimeError("Failed determine the root of the tree.")

        return root[0]

    def multi_threaded_region_ids(self, mtr_id):
        mt_region_ids = [
            k for k in self.region_ids if is_multi_threaded_region(self.region_name(k))
        ]
        id_tids = [
            (k, *parse_multi_threaded_region_name(self.region_name(k)))
            for k in mt_region_ids
        ]
        id_tids = sorted(id_tids, key=lambda x: x[2])

        return [k for k, id, _ in id_tids if id == mtr_id]

    def children(self, parent_id):
        all_children = np.argwhere(self.parents == parent_id)

        if len(all_children) == 0:
            return np.array([])
        else:
            return all_children[:, 0]

    def find_tree_roots_id(self):
        return [k for k, p in enumerate(self.parents) if p is None]

    def parent(self, child_id):
        return self.parent[child_id]


def is_multi_threaded_region(region):
    return region.startswith("multi_threaded")


def parse_multi_threaded_region_name(region_name):
    id_match = re.search("id=([a-z]*)", region_name)
    assert id_match

    tid_match = re.search("tid=([0-9]*)", region_name)
    assert tid_match

    return id_match.group(1), int(tid_match.group(1))
