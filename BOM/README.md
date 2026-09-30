# Full bill of materials and scope

`FULL_BOM.csv` and `FULL_BOM.json` contain 96 rows spanning the executable numerical/software system, a proposed magnetic mapping bench and the complete reactor functional inventory. `SOFTWARE_BOM.csv/json` contain the resolved 12-package runtime/optional-figures dependency graph from the validation environment, with upstream distribution license notices retained.

This is a full research inventory, not a procurement-ready reactor BOM. A complete purchase/build specification is impossible before an accepted equilibrium, physical primary magnet design and engineering qualification exist. Unknown quantities and prices are explicit nulls/blanks, not concealed placeholders or invented quotes. The reactor section identifies exactly which design functions remain unclosed.

## Implemented numerical inventory

24 local loop centerlines, 96 segments each, 288 training and 703 held-out sample points. The geometric primary backbone is an ideal analytic field. Its physical source has no supplied BOM and is explicitly unresolved in the proposed-bench list.

## Proposed mapping bench

The software needs no bench hardware. A possible future bench uses 24 local air-core copper windings with 20 turns per loop, 24 current drivers, 24 current measurements, 24 winding temperatures, 8 station fixtures, a calibrated scanned three-axis probe and independent hardwired enables. These counts are design allocations, not as-built quantities, vendor specifications or a construction approval.

For the default 96-segment polygon, one loop centerline is approximately 0.21987 m. 20 turns across 24 loops would use approximately 105.54 m of conductor before leads, packing and allowance. At 20 turns the modeled 80 AT cap corresponds to 4 A. These are arithmetic conversions only. The winding pack, inductance, mutual coupling, compliance voltage, conductor gauge, copper loss, temperature rise and support load are not engineered, so no electrical or thermal qualification is implied.

The 703 validation points are spatial samples. They do not mean 703 physical probes. A scanning probe is one concept; simultaneous sensors would require a different BOM and measurement-noise model.

## Reactor inventory

Includes confinement and trim magnets, structure, conductor/insulation/joints, cryogenics, quench protection, vessel/vacuum, plasma-facing materials/cooling, heating/fueling, tritium/ash, divertor, blanket/shielding, conversion/grid, plant protection, maintenance and every required physics/engineering validation function. Each is unresolved until a real accepted design determines its quantity and specification.

No price total is published. There are no supplier quotes. No net-electric, safety, tritium breeding, neutron shielding or service-lifetime performance is assigned to these rows.

The Python dependency graph is complete for the resolved runtime and figure packages. Wheel-bundled native libraries are covered by their upstream notices, not asserted to be a complete per-binary SBOM. Build/quality tools are identified separately. Dependencies are installed separately, never relicensed as the author's evaluation-only code.

`python scripts/refresh_bom.py` refreshes the default-model and local software inventory after installing the figures extra. It deliberately reports your installed dependency versions; it does not reproduce an old environment by fiat.
