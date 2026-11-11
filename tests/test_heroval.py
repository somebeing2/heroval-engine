import pytest
import os
import sys
import json
import time

# Add paths
sys.path.insert(0, "/home/user/heroval-engine/app")
sys.path.insert(0, "/home/user/heroval-engine")

from engine import HeroValEngine
from fastapi.testclient import TestClient
from main import app

@pytest.fixture(scope="module")
def engine():
    return HeroValEngine(
        model_path="/home/user/heroval-engine/models/heroval_lightgbm.pkl",
        calib_path="/home/user/heroval-engine/models/conformal_calib.json"
    )

@pytest.fixture(scope="module")
def api_client():
    return TestClient(app)

# TEST 1: Data Pipeline & Feature Schema
def test_01_data_pipeline_and_feature_schema(engine):
    """Test 1: Verify data pipeline ingestion, H3 spatial indexing, and schema validity."""
    assert len(engine.micro_markets) >= 8, "Expected at least 8 micro-markets across India"
    assert "Bengaluru_Whitefield" in engine.micro_markets
    assert "Mumbai_BandraWest" in engine.micro_markets
    assert "NCR_DwarkaExpressway" in engine.micro_markets
    assert "Jaipur_VaishaliNagar" in engine.micro_markets
    
    # Feature columns check
    assert "carpet_sqft" in engine.feature_cols
    assert "road_width_ft" in engine.feature_cols
    assert "dist_metro_km" in engine.feature_cols
    assert "rera_approved" in engine.feature_cols
    assert "circle_rate_sqft" in engine.feature_cols

# TEST 2: Model Inference & Sub-Second Latency
def test_02_model_inference_and_latency(engine):
    """Test 2: Verify model generates accurate predictions with sub-second inference latency."""
    prop = {
        "city": "Bengaluru",
        "micro_market": "Bengaluru_Whitefield",
        "property_type": "Apartment",
        "carpet_sqft": 1420,
        "bhk": 3,
        "floor": 7,
        "total_floors": 16,
        "age_years": 2.5,
        "road_width_ft": 50,
        "dist_metro_km": 0.8,
        "amenities_score": 9,
        "rera_approved": 1
    }
    
    t0 = time.time()
    res = engine.valuate(prop)
    elapsed_ms = (time.time() - t0) * 1000
    
    assert elapsed_ms < 100.0, f"Inference took {elapsed_ms:.2f}ms, expected < 100ms"
    fmv = res["valuation_output"]["fair_market_value_lakhs"]
    assert 120.0 <= fmv <= 170.0, f"Predicted FMV ₹{fmv}L out of expected range for Whitefield 1420 sqft"
    assert res["valuation_output"]["rate_per_sqft_inr"] > 8000

# TEST 3: Conformal Prediction Bounds & Statistical Coverage Guarantee
def test_03_conformal_prediction_bounds(engine):
    """Test 3: Verify Inductive Conformal Prediction produces valid 90% confidence bounds."""
    prop = {
        "city": "Mumbai",
        "micro_market": "Mumbai_BandraWest",
        "property_type": "Commercial_Retail",
        "carpet_sqft": 550,
        "bhk": 0,
        "floor": 0,
        "total_floors": 4,
        "age_years": 8.0,
        "road_width_ft": 60,
        "dist_metro_km": 1.5,
        "amenities_score": 6,
        "rera_approved": 1
    }
    res = engine.valuate(prop)
    conf = res["conformal_confidence"]
    val = res["valuation_output"]
    
    lower = conf["lower_bound_lakhs"]
    upper = conf["upper_bound_lakhs"]
    fmv = val["fair_market_value_lakhs"]
    
    assert lower > 0, "Lower bound must be strictly positive"
    assert lower < fmv < upper, f"Conformal bounds violation: {lower} < {fmv} < {upper}"
    assert conf["margin_error_pct"] > 0
    assert "90%" in conf["coverage_guarantee"]

# TEST 4: Statutory Mortgage Metrics (NHB/RBI Requirements)
def test_04_statutory_mortgage_metrics(engine):
    """Test 4: Verify NHB/RBI statutory collateral metrics (RV, FSV, Circle Floor)."""
    prop = {
        "city": "Delhi-NCR",
        "micro_market": "NCR_DwarkaExpressway",
        "property_type": "Apartment",
        "carpet_sqft": 1850,
        "bhk": 3,
        "floor": 14,
        "total_floors": 28,
        "age_years": 1.0,
        "road_width_ft": 80,
        "dist_metro_km": 2.1,
        "amenities_score": 9,
        "rera_approved": 1
    }
    res = engine.valuate(prop)
    v = res["valuation_output"]
    
    fmv = v["fair_market_value_lakhs"]
    rv = v["realizable_value_lakhs"]
    fsv = v["forced_sale_value_lakhs"]
    circle = v["government_circle_value_lakhs"]
    
    # Statutory relationships
    assert rv < fmv, "Realizable value must be discounted relative to FMV for 90-day liquidation"
    assert fsv < rv, "Forced Sale Value must be more conservative than Realizable Value"
    assert round(rv / fmv, 2) == 0.88, "RV should be calibrated at 88% of FMV"
    assert round(fsv / fmv, 2) == 0.72, "FSV should be calibrated at 72% of FMV"
    assert v["market_to_circle_ratio"] > 1.0, "Market price should exceed circle rate baseline"

# TEST 5: TreeSHAP Rupee-Value Explainability Waterfall
def test_05_treeshap_explainability_waterfall(engine):
    """Test 5: Verify explainability waterfall decomposes valuation into auditable Rupee impacts."""
    prop = {
        "city": "Jaipur",
        "micro_market": "Jaipur_VaishaliNagar",
        "property_type": "Independent_House",
        "carpet_sqft": 2400,
        "bhk": 4,
        "floor": 1,
        "total_floors": 2,
        "age_years": 5.0,
        "road_width_ft": 40,
        "dist_metro_km": 3.8,
        "amenities_score": 6,
        "rera_approved": 1
    }
    res = engine.valuate(prop)
    waterfall = res["explainability_waterfall"]
    
    assert len(waterfall) >= 7, "Expected at least 7 explainability factors"
    factors = {item["factor"]: item["impact_lakhs"] for item in waterfall}
    
    assert "Base Micro-Market Benchmark" in factors
    assert "Road Width & Right of Way" in factors
    assert "Building Age & Depreciation" in factors
    assert "RERA Title & Regulatory Clearances" in factors
    
    # Building age must be negative or zero impact
    assert factors["Building Age & Depreciation"] <= 0

# TEST 6: Hero Housing Credit Decision Engine (Green STP vs Red Trigger)
def test_06_hero_housing_credit_decision_engine(engine):
    """Test 6: Verify automated credit decisioning triggers (Green STP vs Red Channel)."""
    # Case A: Prime property -> Must trigger GREEN CHANNEL STP
    prime_prop = {
        "city": "Bengaluru",
        "micro_market": "Bengaluru_Whitefield",
        "property_type": "Apartment",
        "carpet_sqft": 1420,
        "bhk": 3,
        "floor": 7,
        "total_floors": 16,
        "age_years": 2.5,
        "road_width_ft": 50,
        "dist_metro_km": 0.8,
        "amenities_score": 9,
        "rera_approved": 1,
        "flood_hazard_score": 1
    }
    res_prime = engine.valuate(prime_prop)
    dec_prime = res_prime["lender_underwriting_decision"]
    assert dec_prime["decision_code"] == "APPROVE_STP"
    assert dec_prime["recommended_ltv_pct"] == 85
    assert dec_prime["inspection_cost_saved_inr"] == 2500
    assert len(dec_prime["risk_flags"]) == 0
    
    # Case B: High-Risk Unapproved Layout -> Must trigger RED CHANNEL
    risk_prop = {
        "city": "Bengaluru",
        "micro_market": "Bengaluru_ElectronicCity",
        "property_type": "Independent_House",
        "carpet_sqft": 1600,
        "bhk": 3,
        "floor": 1,
        "total_floors": 2,
        "age_years": 14.0,
        "road_width_ft": 16,  # Narrow road < 20ft
        "dist_metro_km": 7.5,
        "amenities_score": 3,
        "rera_approved": 0,   # Unapproved
        "flood_hazard_score": 4  # High flood risk
    }
    res_risk = engine.valuate(risk_prop)
    dec_risk = res_risk["lender_underwriting_decision"]
    assert dec_risk["decision_code"] == "PHYSICAL_INSPECT"
    assert dec_risk["recommended_ltv_pct"] <= 65
    assert len(dec_risk["risk_flags"]) >= 2

# TEST 7: Full REST API Endpoints & Serialization
def test_07_api_endpoints_and_serialization(api_client):
    """Test 7: Verify FastAPI REST endpoints return HTTP 200 and serialize properly."""
    # Health check
    r_health = api_client.get("/api/v1/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "healthy"
    
    # Presets
    r_presets = api_client.get("/api/v1/presets")
    assert r_presets.status_code == 200
    assert len(r_presets.json()) >= 4
    
    # Benchmarks
    r_bench = api_client.get("/api/v1/benchmarks")
    assert r_bench.status_code == 200
    assert "HeroVal_AI" in r_bench.json()
    
    # Valuate POST
    payload = {
        "city": "Pune",
        "micro_market": "Pune_Hinjawadi",
        "property_type": "Apartment",
        "carpet_sqft": 980,
        "bhk": 2,
        "floor": 5,
        "total_floors": 12,
        "age_years": 4.0,
        "road_width_ft": 35,
        "dist_metro_km": 1.2,
        "amenities_score": 8,
        "rera_approved": 1
    }
    r_val = api_client.post("/api/v1/valuate", json=payload)
    assert r_val.status_code == 200
    data = r_val.json()
    assert "valuation_output" in data
    assert "conformal_confidence" in data
    assert "lender_underwriting_decision" in data
