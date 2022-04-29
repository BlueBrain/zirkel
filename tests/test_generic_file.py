import pytest

import zirkel
import zirkel.generic_file


class IncompleteRawFile(zirkel.generic_file.RawGenericFile):
    pass


def test_incomplete_raw_file():
    with pytest.raises(TypeError):
        raw_file = IncompleteRawFile()
