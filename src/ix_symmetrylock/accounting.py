"""Causal D-T source and conditional electricity accounting, not burn prediction."""

import math

EV_J = 1.602176634e-19  # exact SI electronvolt
ALPHA_MEV = 3.5
NEUTRON_MEV = 14.1


def dt_source(reactions_per_second, alpha_deposition_fraction):
    values = [reactions_per_second, alpha_deposition_fraction]
    if not all(math.isfinite(x) for x in values):
        raise ValueError("nonfinite D-T source")
    if reactions_per_second < 0 or not 0 <= alpha_deposition_fraction <= 1:
        raise ValueError("invalid rate or alpha deposition fraction")
    alpha = reactions_per_second * ALPHA_MEV * 1e6 * EV_J
    neutron = reactions_per_second * NEUTRON_MEV * 1e6 * EV_J
    return {
        "reactions_per_second": reactions_per_second,
        "deuterons_consumed_per_second": reactions_per_second,
        "tritons_consumed_per_second": reactions_per_second,
        "helium_nuclei_created_per_second": reactions_per_second,
        "neutrons_per_second": reactions_per_second,
        "alpha_birth_W": alpha,
        "neutron_birth_W": neutron,
        "fusion_W": alpha + neutron,
        "alpha_deposited_W": alpha * alpha_deposition_fraction,
        "alpha_escape_W": alpha * (1 - alpha_deposition_fraction),
        "authority": "ACCOUNTING_FROM_EXTERNALLY_SUPPLIED_RATE",
    }


PLANT_LOADS = (
    "heating_wallplug_W",
    "magnets_W",
    "cryogenics_W",
    "cooling_and_pumps_W",
    "fuel_cycle_W",
    "balance_of_plant_W",
)


def plant_balance(thermal_recovered_W, conversion_efficiency, loads):
    if not math.isfinite(thermal_recovered_W) or thermal_recovered_W < 0:
        raise ValueError("invalid recovered heat")
    if not math.isfinite(conversion_efficiency) or not 0 <= conversion_efficiency <= 1:
        raise ValueError("invalid conversion efficiency")
    if not isinstance(loads, dict) or set(loads) - set(PLANT_LOADS):
        raise ValueError("unknown or invalid plant loads")
    missing = [key for key in PLANT_LOADS if key not in loads or loads[key] is None]
    for value in loads.values():
        if value is not None and (not math.isfinite(value) or value < 0):
            raise ValueError("invalid recirculating load")
    if missing:
        return {
            "closed": False,
            "missing": missing,
            "net_electric_W": None,
            "authority": "CONDITIONAL_ACCOUNTING",
        }
    gross = thermal_recovered_W * conversion_efficiency
    return {
        "closed": True,
        "gross_electric_W": gross,
        "recirculating_W": sum(loads.values()),
        "net_electric_W": gross - sum(loads.values()),
        "authority": "CONDITIONAL_ACCOUNTING",
    }
