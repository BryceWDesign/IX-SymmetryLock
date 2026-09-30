"""Scientific plots from executed campaign data only."""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def plot(bundle):
    bundle = Path(bundle)
    result = json.loads((bundle / "campaign.json").read_text())
    cases = result["cases"][1:]
    labels = [c["name"].replace("_", " ") for c in cases]
    before = [c["validation_before"]["normal_rms_over_B0"] for c in cases]
    after = [c["validation_after"]["normal_rms_over_B0"] for c in cases]
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), gridspec_kw={"width_ratios": [1.6, 1]})
    fig.patch.set_facecolor("#f5f7fa")
    positions = np.arange(len(cases))
    colors = ["#19856d" if c["local_field_screen_pass"] else "#b34b45" for c in cases]
    for index, initial, final in zip(positions, before, after, strict=True):
        axes[0].plot([initial, final], [index, index], color="#bac4d0", linewidth=2)
    axes[0].scatter(before, positions, color="#8796a8", s=45, label="Before", zorder=3)
    axes[0].scatter(after, positions, color=colors, s=45, label="After", zorder=3)
    axes[0].set_yticks(positions, labels, fontsize=9)
    axes[0].invert_yaxis()
    axes[0].set_xscale("log")
    axes[0].set_xlabel("Held-out RMS normal field / fixed B0, lower is better")
    axes[0].set_title("Explicit-coil correction and negative controls")
    axes[0].legend(frameon=False)
    conv = result["polygon_convergence"]
    axes[1].loglog(
        [c["segments"] for c in conv],
        [c["relative_field_l2_error_to_384_segments"] for c in conv],
        "o-",
        color="#345995",
    )
    axes[1].set_xlabel("Segments per loop")
    axes[1].set_ylabel("Relative field error to 384-segment reference")
    axes[1].set_title("Independent polygon convergence")
    for ax in axes:
        ax.grid(axis="x", alpha=0.2)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("IX-SymmetryLock v0.1.0 | Vacuum magnetic-error correction", fontsize=15)
    fig.text(
        0.02,
        0.01,
        "Green: model gates pass. Red: rejected. Geometric angles, not Boozer QA. "
        "Ideal toroidal backbone has zero transform. No fusion credit.",
        fontsize=9,
    )
    fig.tight_layout(rect=[0, 0.04, 1, 0.94])
    fig.savefig(bundle / "field_correction.png", dpi=160)
    plt.close(fig)
    data = np.load(bundle / "geometry.npz", allow_pickle=False)
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(projection="3d")
    for vertices in data["vertices_m"]:
        closed = np.vstack([vertices, vertices[0]])
        ax.plot(*closed.T, color="#19856d", linewidth=1)
    points = data["training_points_m"]
    ax.scatter(*points.T, color="#345995", alpha=0.2, s=5)
    ax.set(
        xlabel="x (m)",
        ylabel="y (m)",
        zlabel="z (m)",
        title="24 explicit local trim loops and evaluation torus\n"
        "Primary backbone is analytic, not shown as hardware",
    )
    ax.set_box_aspect([1, 1, 0.5])
    fig.tight_layout()
    fig.savefig(bundle / "coil_geometry.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    plot(sys.argv[1] if len(sys.argv) > 1 else "results/poc")
