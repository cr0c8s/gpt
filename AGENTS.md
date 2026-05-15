# AGENTS.md

## Cursor Cloud specific instructions

This repository contains an ns-3 network simulation research project with:
- `simulation/wifi-research.cc` — ns-3 C++ simulation source (chain vs cluster Wi-Fi topologies)
- `simulation/plot_results.py` — Python visualization script (reads `sweep-results.csv`, generates 8 PNG graphs)
- `simulation/sweep-results.csv` — simulation results data
- `report/report.md` — detailed practice report in Russian (formatted per БГУИР СТП 01-2024)

### Running the visualization script

```bash
cd simulation
python3 plot_results.py
```

This generates 8 PNG graphs in the `simulation/` directory and copies them to `report/images/`.

### Dependencies

- Python 3.12+ with `matplotlib` and `numpy` (installed via `pip3 install matplotlib numpy`)
- ns-3 is NOT installed in the cloud VM — the C++ source is provided for reference only; simulation data is pre-generated in `sweep-results.csv`

### Notes

- The plot script uses `matplotlib.use("Agg")` backend (no display needed)
- All text in graphs and the report is in Russian
- Graph images are referenced from the report via relative paths in `report/images/`
