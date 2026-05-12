# Agents

## Cursor Cloud specific instructions

This repository contains an **ns-3 Wi-Fi network simulation** comparing Chain (sequential) vs Cluster (grouped by frequency) topologies with 12 nodes.

### Key components
- `wifi-simulation.cc` — ns-3 C++ simulation source (both topologies)
- `plot_results.py` — Python script to generate comparison charts from CSV output
- CSV/XML result files produced by simulation runs

### ns-3 setup
- ns-3.41 is installed at `/opt/ns3/ns-allinone-3.41/ns-3.41`
- The simulation source must be copied to `scratch/` before building
- Build: `cd /opt/ns3/ns-allinone-3.41/ns-3.41 && cp /workspace/wifi-simulation.cc scratch/ && ./ns3 build scratch/wifi-simulation`
- ns-3 outputs files (CSV, XML) to its own working directory — copy them to `/workspace` afterwards

### Running simulations
```bash
cd /opt/ns3/ns-allinone-3.41/ns-3.41
./ns3 run "scratch/wifi-simulation --mode=chain"
./ns3 run "scratch/wifi-simulation --mode=cluster"
./ns3 run "scratch/wifi-simulation --mode=both"
cp chain-results.csv cluster-results.csv /workspace/
```

### Generating graphs
```bash
cd /workspace && python3 plot_results.py
```
Requires `matplotlib` and `numpy`.

### Gotchas
- The default `c++` compiler is clang-18, which requires `libstdc++-14-dev` (or `g++-14`) to link properly. If ns-3 configure fails with "cannot find -lstdc++", install `g++-14`.
- ns-3 build with `-j3` takes ~5 minutes; individual scratch programs rebuild in seconds.
- Simulation outputs go to the ns-3 root directory, not the current shell directory.
