import warnings

import numpy as np

from zirkel.generic_file import RawGenericFile
from zirkel.generic_file import read_json


class RawHatchet(RawGenericFile):
    def __init__(self, name):
        self._load_profile(name)

    def _load_profile(self, name):
        raw = read_json(name)
        data = [row for row in raw["data"] if row[2] != None]

        self._mpi_ranks = np.array([row[0] for row in data])
        self._raw_excl_time = np.array([row[1] for row in data])
        self._region_ids = np.array([row[2] for row in data])

        self._region_names = np.array([row["label"] for row in raw["nodes"]])
        self._parents = np.array(
            [row["parent"] if "parent" in row else None for row in raw["nodes"]]
        )

    def data(self, id):
        return {"excl_time": self.excl_time(id)}

    def excl_time(self, id):
        n_mpi_ranks = self.n_mpi_ranks

        I = np.argwhere(self._region_ids == id)

        assert I.size > 0, "Missing data."

        time = self._raw_excl_time[I[:, 0]]
        ranks = self._mpi_ranks[I[:, 0]]

        excl_time = np.ma.masked_all(n_mpi_ranks)
        for p, t in zip(ranks, time):
            excl_time[p] = t

        return excl_time

    @property
    def parents(self):
        return self._parents

    def region_name(self, id):
        return self._region_names[id]

    @property
    def region_ids(self):
        return list(range(len(self._region_names)))

    def count_mpi_ranks(self):
        mpi_ranks = self._mpi_ranks
        max_rank = mpi_ranks.max()
        n_ranks = len(list(set(mpi_ranks)))

        if max_rank + 1 != n_ranks:
            warnings.warn("There seems to be a gap in the MPI ranks.", RuntimeWarning)

        return max_rank + 1
