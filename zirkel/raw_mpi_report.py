import numpy as np

from zirkel.generic_file import RawGenericFile
from zirkel.generic_file import read_json


class RawMPIReport(RawGenericFile):
    def __init__(self, filename):
        self._load_profile(filename)

    def _load_profile(self, filename):
        raw_data = read_json(filename)
        assert "path" not in raw_data[0], "Heuristic for finding the catch all region"
        raw_data = raw_data[1:]

        self._parents = len(raw_data) * [None]
        for k, d1 in enumerate(raw_data):
            path_early = d1["path"]
            parent_path_early, region_name_early = self._split_path(path_early)

            for l in range(k + 1, len(raw_data)):
                d2 = raw_data[l]
                path_late = d2["path"]
                parent_path_late, region_name_late = self._split_path(path_late)

                if path_early == parent_path_late:
                    self._parents[l] = k

                if path_late == parent_path_early:
                    self._parents[k] = l

        self._parents = np.array(self._parents)
        self._region_name = [self._split_path(d["path"])[1] for d in raw_data]
        self._data = [{k: v for k, v in d.items() if k != "path"} for d in raw_data]

    def _split_path(self, path):
        if not "/" in path:
            parent_path = ""
            region_name = path

        else:
            parent_path, region_name = path.rsplit("/", 1)

        return parent_path, region_name

    def data(self, id):
        return self._data[id]

    def region_name(self, id):
        return self._region_name[id]

    @property
    def parents(self):
        return self._parents

    @property
    def region_ids(self):
        return list(range(len(self._region_name)))

    def count_mpi_ranks(self):
        # Currently "the" MPI report only contains aggregated data,
        # such as min/max/avg over all ranks.
        #
        # Therefore, this is '1', until we can load aggregated and
        # non-aggregated data in a more expressive manner.
        return 1
