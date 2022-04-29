# Zirkel
Zirkel parses Caliper output and represents the measurements as a tree.

## Getting started
Currently only cloning and installing via pip is supported. This could look something like:

```
git clone git@bbpgitlab.epfl.ch:hpc/zirkel.git
cd zirkel
```
There's two options:
```
# If you don't intend to edit the package:
pip install .

# As an editable package:
pip install -e .
```

## Instrumentation Conventions
For code which marks regions inside multi-threaded regions, there must be a
specific region marking the entire multi-threaded region called:

```
multi_threaded(id=${ID} tid=${TID})
```
where `ID` is a unique identifier for this region, consisting entirely of
low-case letters `[a-z]`; and `TID` is the thread index, an integer taking
values `0, ..., n_threads-1`.

## Examples
```
import zirkel

# Loading a Hatchet file
tree = zirkel.load_tree("hatchet.json", format="hatchet")

# To compute inclusive time:
tree.scan(zirkel.InclusiveTimeScan(excl_key="excl_time", incl_key="incl_time"))

# print the computed inclusive time.
zirkel.print_data("incl_time")
```
