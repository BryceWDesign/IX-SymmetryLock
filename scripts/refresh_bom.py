"""Refresh default-model inventory and local optional-figures dependency metadata.

Requires packaging (installed with the figures extra). Fixed model quantities
refer to the shipped default configuration, not arbitrary user scenarios.
"""

import csv
import importlib.metadata as md
import json
import math
import platform
from pathlib import Path

from packaging.requirements import Requirement

p = Path(__file__).resolve().parents[1]
d = p / "BOM"
rows = []


def add(id, scope, subsystem, item, qty, unit, basis, status, closure):
    rows.append(
        dict(
            id=id,
            scope=scope,
            subsystem=subsystem,
            item=item,
            quantity=qty,
            unit=unit,
            quantity_basis=basis,
            status=status,
            closure_needed=closure,
            unit_price_USD=None,
            total_price_USD=None,
        )
    )


add(
    "M01",
    "numerical",
    "geometry",
    "Local circular trim centerlines",
    24,
    "loops",
    "8 toroidal by 3 poloidal stations",
    "IMPLEMENTED",
    "finite winding pack not modeled",
)
add(
    "M02",
    "numerical",
    "geometry",
    "Straight segments per trim loop",
    96,
    "segments/loop",
    "configured polygon approximation",
    "IMPLEMENTED",
    "refine for each new geometry",
)
add(
    "M03",
    "numerical",
    "geometry",
    "Training evaluation points",
    288,
    "points",
    "24 by 12 geometric-angle grid",
    "IMPLEMENTED",
    "not a physical sensor inventory",
)
add(
    "M04",
    "numerical",
    "geometry",
    "Held-out evaluation points",
    703,
    "points",
    "37 by 19 grid with half-cell offset",
    "IMPLEMENTED",
    "not continuous-volume validation",
)
add(
    "M05",
    "numerical",
    "field",
    "Ideal analytic toroidal backbone",
    1,
    "field model",
    "B_phi=B0 R0/R at B0=0.03 T",
    "IDEALIZED",
    "no primary conductor hardware provided",
)
add(
    "M06",
    "numerical",
    "fault",
    "Independent shifted fault paths",
    2,
    "paths",
    "55 and -35 ampere-turns; [4,-3,2] mm shift",
    "IMPLEMENTED",
    "fault truth is injected, not measured",
)
add(
    "M07",
    "numerical",
    "surface refinement",
    "Additional independent surface grids",
    3,
    "grids",
    "49x25, 97x49 and 145x73; up to 10585 independent sample points",
    "IMPLEMENTED",
    "grid convergence remains specific to this fault and fixed geometry",
)
add(
    "S01",
    "software",
    "runtime",
    "Python interpreter",
    1,
    "installation",
    "Python 3.11-3.13 supported; 3.12.14 executed",
    "IMPLEMENTED",
    "other interpreter/OS combinations require CI evidence",
)
add(
    "S02",
    "software",
    "runtime",
    "NumPy",
    1,
    "package",
    "2.3.5 executed",
    "IMPLEMENTED",
    "see resolved software BOM",
)
add(
    "S03",
    "software",
    "runtime",
    "SciPy",
    1,
    "package",
    "1.17.0 executed",
    "IMPLEMENTED",
    "see resolved software BOM",
)
add(
    "S04",
    "software",
    "optional figures",
    "Matplotlib and transitive dependencies",
    1,
    "dependency graph",
    "3.10.8 executed",
    "IMPLEMENTED",
    "only needed for plot generation",
)
add(
    "S05",
    "software",
    "quality",
    "Ruff",
    1,
    "tool",
    "0.12.12 executed",
    "IMPLEMENTED",
    "not a runtime dependency",
)
add(
    "S06",
    "software",
    "build",
    "setuptools",
    1,
    "build backend",
    "84.0.0 used for wheel packaging",
    "IMPLEMENTED",
    "build isolation can resolve a different compatible backend",
)
bench = [
    (
        "magnetics",
        "Air-core copper trim winding",
        24,
        "windings",
        "20 turns per modeled local loop; proposed, not winding-pack CAD",
        "turn packing, leads, thermal and insulation qualification",
    ),
    (
        "magnetics",
        "Nonmagnetic coil former",
        24,
        "formers",
        "one per trim winding",
        "material, tolerance and fastener drawing",
    ),
    (
        "magnetics",
        "Insulated copper winding conductor",
        None,
        "m",
        "20 times 24 polygon centerline length, plus unknown leads",
        "wire gauge, packing, lead lengths and insulation specification",
    ),
    (
        "support",
        "Toroidal station fixtures",
        8,
        "fixtures",
        "one per toroidal station",
        "alignment, stiffness and survey design",
    ),
    (
        "support",
        "Poloidal adjustment mounts",
        24,
        "mounts",
        "one per winding",
        "motion range, locking and load path",
    ),
    (
        "power",
        "Bipolar current-regulated driver channels",
        24,
        "channels",
        "one per trim; ±4 A would give ±80 AT at 20 turns",
        "compliance voltage, inductance, stability and fault review",
    ),
    (
        "power",
        "Shared isolated DC supply",
        None,
        "units",
        "sized from driver topology and duty",
        "losses, voltage and protection study",
    ),
    (
        "power",
        "Current shunts or isolated transducers",
        24,
        "channels",
        "one per driven coil",
        "gain, bandwidth and calibration uncertainty",
    ),
    (
        "power",
        "Driver enable isolation channels",
        24,
        "channels",
        "one per driver",
        "electrical architecture and fault analysis",
    ),
    (
        "power",
        "Independent overcurrent protection channels",
        24,
        "channels",
        "one per driver",
        "trip limits and ratings",
    ),
    (
        "power",
        "Inductive energy clamp networks",
        24,
        "channels",
        "one per driver",
        "inductance, mutual coupling and release-energy design",
    ),
    (
        "power",
        "Winding temperature sensors",
        24,
        "sensors",
        "one per winding as an initial monitoring allocation",
        "placement and acceptance limits",
    ),
    (
        "wiring",
        "Coil lead pair assemblies",
        24,
        "pairs",
        "one per winding",
        "length, gauge, twist and connector qualification",
    ),
    (
        "wiring",
        "Driver-side coil connectors",
        24,
        "connectors",
        "one per winding",
        "ratings and pinout",
    ),
    (
        "wiring",
        "Interlock harness",
        1,
        "assembly",
        "one independent enable loop",
        "fail-safe circuit review",
    ),
    (
        "measurement",
        "Three-axis magnetic probe",
        1,
        "probe",
        "scanned probe proposal, not 703 simultaneous sensors",
        "range, noise, offset and calibration selection",
    ),
    (
        "measurement",
        "Nonmagnetic positioning stage",
        1,
        "stage",
        "scan the training and independent grids",
        "spatial repeatability and coordinate survey",
    ),
    (
        "measurement",
        "Probe calibration reference",
        1,
        "reference",
        "traceable probe calibration",
        "calibration method and reference uncertainty",
    ),
    (
        "measurement",
        "Current calibration reference",
        1,
        "reference",
        "traceable current calibration",
        "reference accuracy and schedule",
    ),
    (
        "measurement",
        "Coordinate survey targets",
        8,
        "targets",
        "one per station initial allocation",
        "metrology method and placement",
    ),
    (
        "measurement",
        "DAQ acquisition system",
        1,
        "system",
        "scan magnetic, temperature and current data",
        "channel count, simultaneity, isolation and timestamps",
    ),
    (
        "control",
        "Research workstation",
        1,
        "workstation",
        "local numerical evaluation and data logging",
        "RAM/CPU choice follows measured workload",
    ),
    (
        "control",
        "Driver command DAC channels",
        24,
        "channels",
        "one per current driver",
        "command resolution and independent inhibits",
    ),
    (
        "control",
        "Hardwired emergency-off assembly",
        1,
        "assembly",
        "independent of research software",
        "qualified hardware review",
    ),
    (
        "control",
        "Independent safety/enable controller",
        1,
        "controller",
        "research code has no device authority",
        "qualified requirements and implementation",
    ),
    (
        "facility",
        "Nonmagnetic mapping platform",
        1,
        "platform",
        "fixture and probe support",
        "load, clearances and measurement contamination",
    ),
    (
        "facility",
        "Instrument enclosure and access guard",
        1,
        "assembly",
        "guarded mapping rig concept",
        "access and thermal review",
    ),
    (
        "facility",
        "Grounding and bonding assembly",
        1,
        "assembly",
        "facility dependent",
        "electrical review",
    ),
    (
        "facility",
        "Test instruments",
        None,
        "instruments",
        "DMM, oscilloscope and thermal inspection functions",
        "equipment selection and calibration",
    ),
    (
        "backbone",
        "Physical reference-field source",
        None,
        "system",
        "ideal toroidal backbone has no construction design",
        "primary coils, leads, power, ripple and hardware qualification",
    ),
]
for i, (sub, item, qty, unit, basis, closure) in enumerate(bench, 1):
    add(
        f"B{i:02}",
        "proposed_mapping_bench",
        sub,
        item,
        qty,
        unit,
        basis,
        "PROPOSED_NOT_BUILT",
        closure,
    )
reactor = {
    "confinement": [
        "Primary nonplanar modular coil set",
        "Trim/current-group architecture",
        "Plasma boundary and winding surface",
        "Magnet support and preload system",
        "Coil alignment metrology",
        "Magnetic diagnostics and reconstruction",
    ],
    "magnet engineering": [
        "Superconductor/conductor winding packs",
        "Conductor stabilizer and insulation",
        "Coil joints and current leads",
        "Cryostat and thermal shield",
        "Cryogenic refrigeration plant",
        "Quench detection and energy extraction",
        "Power converters and current protection",
        "Feedthroughs and service routing",
    ],
    "plasma vessel": [
        "Vacuum vessel and ports",
        "Pumping and vacuum distribution",
        "Leak detection and interspace monitoring",
        "Plasma-facing armor and attachment",
        "First-wall cooling circuits",
        "Remote handling and inspection access",
    ],
    "heating and fueling": [
        "Auxiliary heating source",
        "Heating launchers and transmission",
        "Fuel delivery and density control",
        "Tritium inventory and processing",
        "Helium ash and impurity exhaust",
        "Plasma temperature/density diagnostics",
    ],
    "exhaust": [
        "Divertor target modules",
        "Divertor cooling and manifolds",
        "Divertor pumping and neutral baffling",
        "Strike-point and heat-flux monitoring",
    ],
    "neutronics": [
        "Blanket and lithium breeder inventory",
        "Blanket structure and coolant",
        "Neutron shielding and streaming-path control",
        "Tritium extraction and permeation barriers",
        "Neutron/dose instrumentation",
        "Irradiation and materials qualification specimens",
    ],
    "plant": [
        "Primary heat-exchange loops",
        "Secondary heat conversion system",
        "Generator and grid interface",
        "Electrical recirculating loads",
        "Heat rejection and water services",
        "Fuel-cycle confinement and ventilation",
        "Plant protection and independent control",
        "Maintenance tooling and replacement logistics",
        "Waste and activated-component handling",
    ],
    "qualification": [
        "Finite-beta equilibrium and Boozer analysis",
        "Alpha orbit and transport modeling",
        "MHD and gyrokinetic stability/transport evaluation",
        "Structural and thermal finite-element models",
        "Three-dimensional neutron transport calculation",
        "Quench and cryogenic transient models",
        "Cost and reliability/availability models",
        "Independent experiment and code validation",
    ],
}
k = 0
for sub, items in reactor.items():
    for item in items:
        k += 1
        add(
            f"R{k:02}",
            "reactor_functional_inventory",
            sub,
            item,
            None,
            "design-dependent",
            "no accepted reactor geometry or operating point",
            "UNRESOLVED",
            "solver, engineering or facility design must determine quantity/specification",
        )
for row in rows:
    if row["id"] == "B03":
        # Circular polygon length is exactly known; a turn-pack wire estimate is not.
        loop_length = 96 * 2 * 0.035 * math.sin(math.pi / 96)
        row["quantity"] = 20 * 24 * loop_length
        row["quantity_basis"] = (
            "105.54 m approximate centerline-only wire estimate; "
            "excludes leads, packing and allowance"
        )
(d / "FULL_BOM.json").write_text(
    json.dumps(
        {
            "schema": "ix-symmetrylock.bom.v1",
            "currency": "USD",
            "prices": "UNQUOTED, no vendor quotes or invented costs",
            "scope": (
                "Numerical/software inventory, proposed mapping bench and comprehensive "
                "unresolved reactor functional inventory; not a procurement-ready fusion bill"
            ),
            "items": rows,
        },
        indent=2,
    )
    + "\n"
)
with (d / "FULL_BOM.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
# Resolved package graph, including optional plotting dependencies.
roles = {}
edges = []


def visit(name, role):
    key = name.lower().replace("_", "-")
    if key in roles:
        roles[key]["roles"] = sorted(set(roles[key]["roles"] + [role]))
        return
    dist = md.distribution(name)
    roles[key] = {
        "name": dist.metadata["Name"],
        "version": dist.version,
        "roles": [role],
        "requires_python": dist.metadata.get("Requires-Python"),
        "license_expression": dist.metadata.get("License-Expression"),
        "license_metadata": dist.metadata.get("License"),
    }
    for raw in dist.requires or []:
        req = Requirement(raw)
        if req.marker is not None and not req.marker.evaluate({"extra": ""}):
            continue
        target = req.name.lower().replace("_", "-")
        edges.append({"from": key, "to": target, "requirement": raw})
        visit(req.name, role)


for name, role in [("numpy", "runtime"), ("scipy", "runtime"), ("matplotlib", "optional figures")]:
    visit(name, role)
notices = d / "third_party_notices"
notices.mkdir(exist_ok=True)
for key, item in roles.items():
    dist = md.distribution(item["name"])
    lics = []
    for file in dist.files or []:
        fs = str(file)
        if (
            ".dist-info/" in fs
            and ("license" in fs.lower() or "copying" in fs.lower())
            and dist.locate_file(file).is_file()
        ):
            target = notices / (key + "-" + fs.split(".dist-info/", 1)[1].replace("/", "_"))
            target.write_bytes(dist.locate_file(file).read_bytes())
            lics.append(target.relative_to(d).as_posix())
    item["license_notice_files"] = lics
    item["package_origin"] = (
        "validation environment distribution metadata; dependency installed separately, not bundled"
    )
(d / "SOFTWARE_BOM.json").write_text(
    json.dumps(
        {
            "schema": "ix-symmetrylock.software-bom.v1",
            "python": platform.python_version(),
            "packages": list(roles.values()),
            "dependency_edges": edges,
            "quality_tools": [{"name": "ruff", "version": "0.12.12"}],
            "build_tools": [{"name": "setuptools", "version": md.version("setuptools")}],
            "native_library_boundary": (
                "NumPy/SciPy wheel-contained native components have their "
                "bundled notices preserved; this is a Python package graph, "
                "not a binary SBOM for every native shared library"
            ),
        },
        indent=2,
    )
    + "\n"
)
with (d / "SOFTWARE_BOM.csv").open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["name", "version", "roles", "requires_python", "license_expression"])
    for item in roles.values():
        w.writerow(
            [
                item["name"],
                item["version"],
                "; ".join(item["roles"]),
                item["requires_python"],
                item["license_expression"] or "see upstream notice",
            ]
        )
print(
    len(rows),
    "full BOM rows;",
    len(roles),
    "resolved Python packages; approx winding conductor",
    20 * 24 * 96 * 2 * 0.035 * math.sin(math.pi / 96),
)
