import pandas as pd

# =========================
# Load assumption tables
# =========================

config = pd.read_csv(
    "data/assumptions/simulation_config.csv"
)

city_assumptions = pd.read_csv(
    "data/assumptions/city_assumptions.csv"
)

scenarios = pd.read_csv(
    "data/assumptions/scenario_table.csv"
)

# =========================
# Preview data
# =========================

print("\n=== Simulation Config ===")
print(config)

print("\n=== City Assumptions ===")
print(city_assumptions)

print("\n=== Scenario Table ===")
print(scenarios)

config_dict = dict(zip(config["variable"], config["value"]))

print("\n=== Config Dictionary ===")
print(config_dict)

# =========================
# Convert config values to correct types
# =========================

numeric_keys = [
    "amortization_years",
    "renewal_frequency_years",
    "maintenance_rate_of_rent",
    "structure_depreciation_rate",
    "purchase_cost_rate",
    "sale_cost_rate",
    "renter_discipline",
    "investment_fee",
    "tax_drag",
]

for key in numeric_keys:
    config_dict[key] = float(config_dict[key])

config_dict["end_date"] = pd.to_datetime(config_dict["end_date"])

print("\n=== Typed Config Dictionary ===")
print(config_dict)

print(type(config_dict["investment_fee"]))
print(type(config_dict["end_date"]))

# =========================
# Merge scenarios with city assumptions
# =========================

scenario_inputs = scenarios.merge(
    city_assumptions,
    on="city",
    how="left"
)

print("\n=== Scenario Inputs ===")
print(scenario_inputs)

# =========================
# Export scenario inputs
# =========================

scenario_inputs.to_csv(
    "data/assumptions/scenario_inputs.csv",
    index=False
)

print("\nSaved: data/assumptions/scenario_inputs.csv")