from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import os

from engine import HeroValEngine

app = FastAPI(
    title="HeroVal-AI: Digital Property Valuation & Underwriting Engine",
    description="Production-grade AI/ML Automated Valuation Model (AVM) for Hero Housing Finance Limited",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engine
engine = HeroValEngine()

# Load sample properties and benchmark info
with open("/home/user/heroval-engine/models/sample_properties.json", "r") as f:
    sample_properties = json.load(f)

with open("/home/user/heroval-engine/models/conformal_calib.json", "r") as f:
    conformal_meta = json.load(f)

class ValuationRequest(BaseModel):
    city: str = "Bengaluru"
    micro_market: str = "Bengaluru_Whitefield"
    property_type: str = "Apartment"
    carpet_sqft: float = 1250.0
    bhk: int = 3
    floor: int = 4
    total_floors: int = 12
    age_years: float = 3.0
    road_width_ft: float = 40.0
    dist_metro_km: float = 1.2
    amenities_score: int = 8
    rera_approved: int = 1
    satellite_ndvi: Optional[float] = 0.38
    satellite_density: Optional[float] = 0.65
    satellite_rooftop: Optional[int] = 4
    flood_hazard_score: Optional[int] = 1
    lat: Optional[float] = None
    lon: Optional[float] = None
    circle_rate_sqft: Optional[float] = None

@app.get("/api/v1/health")
def health():
    return {
        "status": "healthy",
        "service": "HeroVal-AI Digital Property Valuation Engine",
        "target_organization": "Hero Housing Finance Limited (HFC)",
        "model_architecture": "Hierarchical Spatial Gradient Boosted Tree + Conformal Predictor + Satellite CV Extractor",
        "accuracy_mdape": f"{conformal_meta['benchmark_summary']['HeroVal_AI']['MdAPE']}%",
        "p10_accuracy": f"{conformal_meta['benchmark_summary']['HeroVal_AI']['P10']}%",
        "conformal_confidence_guarantee": "90% Statistically Calibrated"
    }

@app.get("/api/v1/presets")
def get_presets():
    curated = [
        {
            "id": "blr_whitefield_apt",
            "name": "Bengaluru - Whitefield IT Corridor (3 BHK)",
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
            "satellite_ndvi": 0.42,
            "satellite_density": 0.68,
            "satellite_rooftop": 5,
            "flood_hazard_score": 1,
            "notes": "Prime tech cluster, high comp density, direct purple line metro access."
        },
        {
            "id": "mum_bandra_comm",
            "name": "Mumbai - Bandra West Commercial Boutique",
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
            "rera_approved": 1,
            "satellite_ndvi": 0.18,
            "satellite_density": 0.92,
            "satellite_rooftop": 4,
            "flood_hazard_score": 1,
            "notes": "Ultra-prime retail corridor, high street frontage, substantial rental yield."
        },
        {
            "id": "ncr_dwarka_exp",
            "name": "Delhi NCR - Dwarka Expressway High-Rise",
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
            "rera_approved": 1,
            "satellite_ndvi": 0.35,
            "satellite_density": 0.55,
            "satellite_rooftop": 5,
            "flood_hazard_score": 1,
            "notes": "Fastest growing expressway corridor in NCR with high capital appreciation."
        },
        {
            "id": "jpr_vaishali_house",
            "name": "Jaipur - Vaishali Nagar Independent Villa",
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
            "rera_approved": 1,
            "satellite_ndvi": 0.28,
            "satellite_density": 0.62,
            "satellite_rooftop": 4,
            "flood_hazard_score": 1,
            "notes": "Tier-2 Sweet Spot for Hero Housing Finance LAP and Self-Employed lending."
        },
        {
            "id": "high_risk_unapproved",
            "name": "Risk Case: Peripheral Unapproved Layout (Red Flag)",
            "city": "Bengaluru",
            "micro_market": "Bengaluru_ElectronicCity",
            "property_type": "Independent_House",
            "carpet_sqft": 1600,
            "bhk": 3,
            "floor": 1,
            "total_floors": 2,
            "age_years": 14.0,
            "road_width_ft": 16,
            "dist_metro_km": 7.5,
            "amenities_score": 3,
            "rera_approved": 0,
            "satellite_ndvi": 0.20,
            "satellite_density": 0.78,
            "satellite_rooftop": 2,
            "flood_hazard_score": 4,
            "notes": "Narrow 16ft road, unapproved Gram Panchayat layout, flood zone risk - triggers Red Channel."
        }
    ]
    return curated

@app.get("/api/v1/benchmarks")
def get_benchmarks():
    return conformal_meta["benchmark_summary"]

@app.get("/api/v1/micromarkets")
def get_micromarkets():
    return conformal_meta["micro_markets"]

@app.post("/api/v1/valuate")
def valuate_property(req: ValuationRequest):
    try:
        data = req.model_dump() if hasattr(req, "model_dump") else req.dict()
        result = engine.valuate(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    with open("/home/user/heroval-engine/app/templates/index.html", "r") as f:
        return f.read()

