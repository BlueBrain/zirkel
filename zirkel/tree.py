from zirkel.nodes import build_tree
from zirkel.nodes import stack_multi_threaded_regions
from zirkel.raw_hatchet import RawHatchet
from zirkel.raw_mpi_report import RawMPIReport


def load_tree(filename, format):
    if format == "hatchet":
        parsed_data = RawHatchet(filename)
    elif format == "mpi_report":
        parsed_data = RawMPIReport(filename)
    else:
        raise NotImplementedError(f"Format `{format}` has not been implemented.")

    root_id = parsed_data.guess_root()
    tree = build_tree(parsed_data, root_id=root_id)
    tree = stack_multi_threaded_regions(tree)

    return tree
