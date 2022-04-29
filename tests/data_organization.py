import os


data_dir = os.path.join(os.path.dirname(__file__), "data")

filenames = {
    "hatchet": {
        "profile": os.path.join(data_dir, "hatchet.json"),
        "expected_hierarchy": os.path.join(data_dir, "hatchet.expected_hierarchy.json"),
    },
    "mpi_report": {
        "profile": os.path.join(data_dir, "mpi_report.json"),
        "expected_hierarchy": os.path.join(
            data_dir, "mpi_report.expected_hierarchy.json"
        ),
    },
}
