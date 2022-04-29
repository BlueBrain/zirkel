import numpy as np


class ElementaryTransform:
    def __call__(self, data_point, node):
        raise NotImplementedError(f"{self.__class__.__name__}.__call__")


class MasterOnlyTransform(ElementaryTransform):
    def __init__(self, master_tid):
        self.master_tid = master_tid

    def __call__(self, data_point, node):
        return data_point[self.master_tid, ...]


class AxisTransform(ElementaryTransform):
    def __init__(self, axis, reduction):
        self.axis = axis
        self.reduction = reduction

    def __call__(self, data_point, node):
        return self.reduction(data_point, axis=self.axis)


class AverageTransform(AxisTransform):
    def __init__(self, axis):
        super().__init__(axis, np.mean)


class MaximumTransform(AxisTransform):
    def __init__(self, axis):
        super().__init__(axis, np.max)


class MinimumTransform(AxisTransform):
    def __init__(self, axis):
        super().__init__(axis, np.min)


class RenamingTransform:
    def __init__(self, old_key, new_key, elementary_transform):
        self.elementary_transform = elementary_transform
        self.old_key = old_key
        self.new_key = new_key

    def __call__(self, node):
        node._data[self.new_key] = self.elementary_transform(
            node.data_point(self.old_key, master_only=False),
            node=node,
        )


class MultiThreadedTransform:
    def __init__(self, transform):
        self.transform = transform

    def __call__(self, data_point, node):
        if node.is_multi_threaded:
            return self.transform(data_point, node)
        else:
            return data_point
