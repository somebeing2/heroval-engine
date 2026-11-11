import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error, r2_score
import joblib
import json
import os
import h3

print("Starting HeroVal-AI Model Training Pipeline...")

# Set random seed
np.random.seed(42)

# Define micro-market characteristics in India
MICRO_MARKETS = {
    # Bengaluru
    "Bengaluru_Indiranagar": {"city": "Bengaluru", "base_sqft": 14500, "circle_rate": 9200, "lat": 12.9784, "lon": 77.6408, "infra_growth": 0.08},
    "Bengaluru_Whitefield": {"city": "Bengaluru", "base_sqft": 8200, "circle_rate": 5800, "lat": 12.9698, "lon": 77.7500, "infra_growth": 0.12},
    "Bengaluru_Koramangala": {"city": "Bengaluru", "base_sqft": 15500, "circle_rate": 10500, "lat": 12.9352, "lon": 77.6245, "infra_growth": 0.07},
    "Bengaluru_ElectronicCity": {"city": "Bengaluru", "base_sqft": 5800, "circle_rate": 4200, "lat": 12.8452, "lon": 77.6602, "infra_growth": 0.10},
    "Bengaluru_Hebbal": {"city": "Bengaluru", "base_sqft": 9800, "circle_rate": 6800, "lat": 13.0358, "lon": 77.5970, "infra_growth": 0.11},
    
    # Mumbai MMR
    "Mumbai_BandraWest": {"city": "Mumbai", "base_sqft": 52000, "circle_rate": 34000, "lat": 19.0596, "lon": 72.8295, "infra_growth": 0.06},
    "Mumbai_AndheriEast": {"city": "Mumbai", "base_sqft": 22000, "circle_rate": 15500, "lat": 19.1136, "lon": 72.8697, "infra_growth": 0.09},
    "Mumbai_ThaneWest": {"city": "Mumbai", "base_sqft": 13500, "circle_rate": 9800, "lat": 19.2183, "lon": 72.9781, "infra_growth": 0.11},
    "Mumbai_NaviMumbaiVashi": {"city": "Mumbai", "base_sqft": 14800, "circle_rate": 10800, "lat": 19.0771, "lon": 72.9986, "infra_growth": 0.13},
    
    # Delhi NCR
    "NCR_GurugramDLF5": {"city": "Delhi-NCR", "base_sqft": 21000, "circle_rate": 12500, "lat": 28.4595, "lon": 77.0944, "infra_growth": 0.09},
    "NCR_DwarkaExpressway": {"city": "Delhi-NCR", "base_sqft": 11500, "circle_rate": 6800, "lat": 28.5110, "lon": 76.9930, "infra_growth": 0.16},
    "NCR_NoidaSector150": {"city": "Delhi-NCR", "base_sqft": 8900, "circle_rate": 5400, "lat": 28.4350, "lon": 77.4820, "infra_growth": 0.14},
    
    # Pune
    "Pune_Hinjawadi": {"city": "Pune", "base_sqft": 7400, "circle_rate": 5200, "lat": 18.5913, "lon": 73.7389, "infra_growth": 0.11},
    "Pune_Kothrud": {"city": "Pune", "base_sqft": 12800, "circle_rate": 8900, "lat": 18.5074, "lon": 73.8077, "infra_growth": 0.08},
    "Pune_VimanNagar": {"city": "Pune", "base_sqft": 11200, "circle_rate": 7800, "lat": 18.5679, "lon": 73.9143, "infra_growth": 0.09},

    # Hyderabad
    "Hyderabad_Gachibowli": {"city": "Hyderabad", "base_sqft": 9600, "circle_rate": 6400, "lat": 17.4401, "lon": 78.3489, "infra_growth": 0.14},
    "Hyderabad_Madhapur": {"city": "Hyderabad", "base_sqft": 10800, "circle_rate": 7200, "lat": 17.4483, "lon": 78.3915, "infra_growth": 0.12},
    "Hyderabad_Kukatpally": {"city": "Hyderabad", "base_sqft": 7100, "circle_rate": 4800, "lat": 17.4849, "lon": 78.4138, "infra_growth": 0.09},

    # Tier-2 High Growth Hubs (Hero Housing Finance sweet-spot)
    "Jaipur_VaishaliNagar": {"city": "Jaipur", "base_sqft": 5600, "circle_rate": 3800, "lat": 26.9124, "lon": 75.7423, "infra_growth": 0.11},
    "Jaipur_Mansarovar": {"city": "Jaipur", "base_sqft": 4800, "circle_rate": 3200, "lat": 26.8528, "lon": 75.7681, "infra_growth": 0.10},
    "Coimbatore_RS_Puram": {"city": "Coimbatore", "base_sqft": 6900, "circle_rate": 4900, "lat": 11.0125, "lon": 76.9472, "infra_growth": 0.09},
    "Lucknow_GomtiNagar": {"city": "Lucknow", "base_sqft": 5900, "circle_rate": 4100, "lat": 26.8532, "lon": 80.9984, "infra_growth": 0.12}
}

N_SAMPLES = 12000
records = []

market_keys = list(MICRO_MARKETS.keys())

for i in range(N_SAMPLES):
    mkey = np.random.choice(market_keys)
    minfo = MICRO_MARKETS[mkey]
    
    # Property category
    prop_type = np.random.choice(
        ["Apartment", "Independent_House", "Commercial_Retail", "Commercial_Office"],
        p=[0.60, 0.25, 0.08, 0.07]
    )
    
    # Area
    if prop_type == "Apartment":
        carpet_sqft = np.random.normal(1150, 350)
        carpet_sqft = np.clip(carpet_sqft, 450, 3200)
        bhk = int(np.clip(np.round(carpet_sqft / 420), 1, 4))
        floor = np.random.randint(1, 28)
        total_floors = max(floor + np.random.randint(1, 8), 4)
    elif prop_type == "Independent_House":
        carpet_sqft = np.random.normal(2100, 600)
        carpet_sqft = np.clip(carpet_sqft, 900, 4800)
        bhk = int(np.clip(np.round(carpet_sqft / 500), 2, 6))
        floor = 1
        total_floors = np.random.randint(1, 4)
    elif prop_type == "Commercial_Retail":
        carpet_sqft = np.random.normal(650, 300)
        carpet_sqft = np.clip(carpet_sqft, 180, 2200)
        bhk = 0
        floor = np.random.choice([0, 1, 2], p=[0.65, 0.25, 0.10]) # Ground floor premium
        total_floors = np.random.randint(2, 6)
    else: # Commercial_Office
        carpet_sqft = np.random.normal(1800, 800)
        carpet_sqft = np.clip(carpet_sqft, 500, 6000)
        bhk = 0
        floor = np.random.randint(1, 15)
        total_floors = max(floor + np.random.randint(1, 6), 5)

    age_years = np.clip(np.random.exponential(4.5), 0, 30)
    road_width_ft = np.random.choice([15, 20, 30, 40, 60, 80, 100], p=[0.08, 0.15, 0.35, 0.22, 0.12, 0.05, 0.03])
    dist_metro_km = np.clip(np.random.exponential(2.8), 0.1, 14.0)
    amenities_score = np.random.randint(2, 10)
    rera_approved = np.random.choice([1, 0], p=[0.88, 0.12])
    
    # Unstructured / Satellite extracted synthetic features
    satellite_ndvi = np.clip(np.random.normal(0.32, 0.14), 0.05, 0.75) # Greenery
    satellite_density = np.clip(np.random.normal(0.68, 0.16), 0.20, 0.95) # Built-up density
    satellite_rooftop = np.random.choice([1, 2, 3, 4, 5], p=[0.05, 0.12, 0.38, 0.32, 0.13])
    flood_hazard_score = np.random.choice([1, 2, 3, 4, 5], p=[0.60, 0.22, 0.12, 0.04, 0.02])

    # Spatial coordinates with jitter around micro-market center
    lat = minfo["lat"] + np.random.normal(0, 0.012)
    lon = minfo["lon"] + np.random.normal(0, 0.012)
    h3_res8 = h3.geo_to_h3(lat, lon, 8) if hasattr(h3, 'geo_to_h3') else h3.latlng_to_cell(lat, lon, 8)

    # Base price calculation
    base_sqft = minfo["base_sqft"]
    circle_sqft = minfo["circle_rate"] * (1.0 + np.random.normal(0, 0.04))

    # Multipliers
    type_mult = 1.0
    if prop_type == "Commercial_Retail":
        type_mult = 1.85 if floor == 0 else 1.25
    elif prop_type == "Commercial_Office":
        type_mult = 1.20
    elif prop_type == "Independent_House":
        type_mult = 1.15 # land component premium

    # Road width multiplier
    road_mult = 1.0 + (road_width_ft - 30) * 0.0035

    # Metro distance multiplier (exponential decay)
    metro_mult = 1.0 + 0.18 * np.exp(-0.45 * dist_metro_km)

    # Age depreciation (approx 1.2% per year up to 25%)
    age_mult = max(0.72, 1.0 - (age_years * 0.012))

    # Amenities multiplier
    amenities_mult = 1.0 + (amenities_score - 5) * 0.025

    # Floor rise premium (higher floors get better light/view in apartments)
    floor_mult = 1.0
    if prop_type == "Apartment" and total_floors > 8:
        floor_mult = 1.0 + (floor / total_floors) * 0.06

    # RERA & Legal discount
    rera_mult = 1.0 if rera_approved == 1 else 0.82

    # Satellite environmental & structural premium
    sat_mult = 1.0 + (satellite_ndvi - 0.3) * 0.08 + (satellite_rooftop - 3) * 0.025 - (flood_hazard_score - 1) * 0.035

    # True market rate per sqft
    true_rate_sqft = base_sqft * type_mult * road_mult * metro_mult * age_mult * amenities_mult * floor_mult * rera_mult * sat_mult
    
    # Market noise (real estate idiosyncratic variability ~ 4.5%)
    noise = np.random.normal(1.0, 0.045)
    final_rate_sqft = max(circle_sqft * 0.95, true_rate_sqft * noise)
    
    total_market_value = final_rate_sqft * carpet_sqft

    # Portal asking price (inflated by 10-18%, typical legacy AVM trap)
    portal_ask_sqft = final_rate_sqft * np.random.uniform(1.10, 1.18)

    records.append({
        "city": minfo["city"],
        "micro_market": mkey,
        "property_type": prop_type,
        "carpet_sqft": round(carpet_sqft, 1),
        "bhk": bhk,
        "floor": floor,
        "total_floors": total_floors,
        "age_years": round(age_years, 1),
        "road_width_ft": road_width_ft,
        "dist_metro_km": round(dist_metro_km, 2),
        "amenities_score": amenities_score,
        "rera_approved": rera_approved,
        "circle_rate_sqft": round(circle_sqft, 1),
        "satellite_ndvi": round(satellite_ndvi, 3),
        "satellite_density": round(satellite_density, 3),
        "satellite_rooftop": satellite_rooftop,
        "flood_hazard_score": flood_hazard_score,
        "lat": round(lat, 5),
        "lon": round(lon, 5),
        "h3_index": str(h3_res8),
        "portal_ask_sqft": round(portal_ask_sqft, 1),
        "actual_rate_sqft": round(final_rate_sqft, 1),
        "market_val_inr": round(total_market_value, 0),
        "market_val_lakhs": round(total_market_value / 100000.0, 2)
    })

df = pd.DataFrame(records)
print(f"Generated {len(df)} property records across {df['city'].nunique()} cities.")

# Feature Engineering
# Target: log of market value or market_val_lakhs
# Spatial Lag / H3 comps: calculate historical median rate per H3 cell
h3_median_rate = df.groupby("h3_index")["actual_rate_sqft"].median().to_dict()
df["h3_comp_median_sqft"] = df["h3_index"].map(h3_median_rate)

# Ratio of circle rate to comp rate (indicates local cash component / undervaluation spread)
df["circle_to_comp_ratio"] = df["circle_rate_sqft"] / df["h3_comp_median_sqft"]

# Feature columns for LightGBM
cat_cols = ["city", "property_type"]
for c in cat_cols:
    df[c] = df[c].astype("category")

feature_cols = [
    "city", "property_type", "carpet_sqft", "bhk", "floor", "total_floors",
    "age_years", "road_width_ft", "dist_metro_km", "amenities_score", "rera_approved",
    "circle_rate_sqft", "satellite_ndvi", "satellite_density", "satellite_rooftop",
    "flood_hazard_score", "h3_comp_median_sqft", "circle_to_comp_ratio", "lat", "lon"
]

X = df[feature_cols]
y = df["market_val_lakhs"]

# Split: 70% Train, 15% Calibration (for Conformal Prediction), 15% Test
X_temp, X_test, y_temp, y_test, df_temp, df_test = train_test_split(X, y, df, test_size=0.15, random_state=42)
X_train, X_calib, y_train, y_calib, df_train, df_calib = train_test_split(X_temp, y_temp, df_temp, test_size=0.1765, random_state=42)

print(f"Dataset split: Train={len(X_train)}, Calib={len(X_calib)}, Test={len(X_test)}")

# Train LightGBM Regressor
model = lgb.LGBMRegressor(
    n_estimators=350,
    learning_rate=0.05,
    num_leaves=31,
    subsample=0.85,
    colsample_bytree=0.85,
    random_state=42,
    verbose=-1
)
model.fit(X_train, y_train)

# Inductive Conformal Prediction (ICP) for distribution-free calibrated confidence intervals
# Calibration predictions
calib_preds = model.predict(X_calib)
# Non-conformity score: absolute relative percentage error or absolute rupee error
calib_rel_errors = np.abs(calib_preds - y_calib) / calib_preds
calib_abs_errors = np.abs(calib_preds - y_calib)

# 90% Conformal quantile
q_90_rel = np.quantile(calib_rel_errors, 0.90)
q_90_abs = np.quantile(calib_abs_errors, 0.90)
print(f"Conformal Calibration 90% quantile relative error: {q_90_rel*100:.2f}% (Absolute: ₹{q_90_abs:.2f} Lakhs)")

# Test Predictions
test_preds = model.predict(X_test)
test_mape = mean_absolute_percentage_error(y_test, test_preds) * 100
test_mdape = np.median(np.abs(y_test - test_preds) / y_test) * 100
p10 = np.mean(np.abs(y_test - test_preds) / y_test <= 0.10) * 100
p20 = np.mean(np.abs(y_test - test_preds) / y_test <= 0.20) * 100
rmse = np.sqrt(mean_squared_error(y_test, test_preds))
r2 = r2_score(y_test, test_preds)

# Conformal coverage on test set
test_lower = test_preds * (1 - q_90_rel)
test_upper = test_preds * (1 + q_90_rel)
empirical_coverage = np.mean((y_test >= test_lower) & (y_test <= test_upper)) * 100

print("\n================ HEROVAL-AI TEST SET PERFORMANCE ================")
print(f"R² Score:                           {r2:.4f}")
print(f"Median Absolute % Error (MdAPE):    {test_mdape:.2f}%")
print(f"Mean Absolute % Error (MAPE):       {test_mape:.2f}%")
print(f"P10 (Within 10% of Actual Value):   {p10:.2f}%")
print(f"P20 (Within 20% of Actual Value):   {p20:.2f}%")
print(f"Root Mean Squared Error (RMSE):     ₹{rmse:.2f} Lakhs")
print(f"Empirical 90% Conformal Coverage:   {empirical_coverage:.2f}% (Statistically Guaranteed)")

# Compare with Legacy Baselines on Test Set
# Baseline 1: Pure Circle Rate
circle_preds = (df_test["circle_rate_sqft"] * df_test["carpet_sqft"]) / 100000.0
circle_mdape = np.median(np.abs(y_test - circle_preds) / y_test) * 100
circle_p10 = np.mean(np.abs(y_test - circle_preds) / y_test <= 0.10) * 100

# Baseline 2: Portal Asking Price (Legacy Portal AVM)
portal_preds = (df_test["portal_ask_sqft"] * df_test["carpet_sqft"]) / 100000.0
portal_mdape = np.median(np.abs(y_test - portal_preds) / y_test) * 100
portal_p10 = np.mean(np.abs(y_test - portal_preds) / y_test <= 0.10) * 100

benchmark_summary = {
    "HeroVal_AI": {
        "MdAPE": round(test_mdape, 2),
        "P10": round(p10, 2),
        "P20": round(p20, 2),
        "RMSE_Lakhs": round(rmse, 2),
        "R2": round(r2, 4),
        "Conformal_90_Coverage": round(empirical_coverage, 2)
    },
    "Legacy_Portal_AVM": {
        "MdAPE": round(portal_mdape, 2),
        "P10": round(portal_p10, 2),
        "P20": round(np.mean(np.abs(y_test - portal_preds) / y_test <= 0.20) * 100, 2),
        "RMSE_Lakhs": round(np.sqrt(mean_squared_error(y_test, portal_preds)), 2),
        "R2": round(r2_score(y_test, portal_preds), 4)
    },
    "Govt_Circle_Rate": {
        "MdAPE": round(circle_mdape, 2),
        "P10": round(circle_p10, 2),
        "P20": round(np.mean(np.abs(y_test - circle_preds) / y_test <= 0.20) * 100, 2),
        "RMSE_Lakhs": round(np.sqrt(mean_squared_error(y_test, circle_preds)), 2),
        "R2": round(r2_score(y_test, circle_preds), 4)
    }
}

print("\nBenchmark Summary vs Existing Approaches:")
print(json.dumps(benchmark_summary, indent=2))

# Save artifacts
os.makedirs("/home/user/heroval-engine/models", exist_ok=True)
joblib.dump(model, "/home/user/heroval-engine/models/heroval_lightgbm.pkl")

with open("/home/user/heroval-engine/models/conformal_calib.json", "w") as f:
    json.dump({
        "q_90_rel": float(q_90_rel),
        "q_90_abs": float(q_90_abs),
        "benchmark_summary": benchmark_summary,
        "feature_cols": feature_cols,
        "micro_markets": MICRO_MARKETS
    }, f, indent=2)

# Save sample test properties for interactive demo
sample_properties = df_test.head(15).to_dict(orient="records")
# Convert categorical / complex types to json serializable
for item in sample_properties:
    for k, v in item.items():
        if isinstance(v, (np.integer, int)):
            item[k] = int(v)
        elif isinstance(v, (np.floating, float)):
            item[k] = float(v)
        elif isinstance(v, (np.ndarray, list)):
            item[k] = list(v)

with open("/home/user/heroval-engine/models/sample_properties.json", "w") as f:
    json.dump(sample_properties, f, indent=2)

print("\nModel artifacts and benchmarks successfully saved to /home/user/heroval-engine/models/")
