class InclusiveTimeScan:
    def __init__(self, excl_key, incl_key):
        self.excl_key = excl_key
        self.incl_key = incl_key

    def __call__(self, node):
        excl_key, incl_key = self.excl_key, self.incl_key

        # The issue arises for single threaded nodes with
        # multi-threaded children. Here it's important that
        # the values from the master thread of the children
        # are used.
        master_only = node.is_single_threaded

        node._data[incl_key] = node.data_point(excl_key, master_only=master_only) + sum(
            child.data_point(incl_key, master_only=master_only)
            for child in node.children
        )
