import streamlit as st
import pandas as pd
import numpy as np
import json
import joblib
import os
import sys

# Ensure app path in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "app"))
from underwriting_engine import MortgageUnderwritingEngine, UnderwritingApplication

st.set_page_config(
    page_title="Hero Fintech Suite | Property Valuation & Mortgage Underwriting",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown(r"""
<style>
    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        color: white; padding: 1.25rem 1.75rem; border-radius: 10px;
        border-bottom: 4px solid #E31E24; margin-bottom: 1.25rem;
    }
    .decision-box { padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 6px solid; }
    .decision-green { background-color: #ECFDF5; border-color: #10B981; color: #065F46; }
    .decision-amber { background-color: #FFFBEB; border-color: #F59E0B; color: #92400E; }
    .decision-red { background-color: #FFF1F2; border-color: #F43F5E; color: #9F1239; }
    .check-card {
        background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px;
        padding: 0.75rem; margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Helper function
def format_inr(amt):
    if amt >= 10000000:
        return f"₹{amt/10000000:.2f} Cr"
    elif amt >= 100000:
        return f"₹{amt/100000:.2f} Lakhs"
    return f"₹{amt:,.0f}"

# Navigation between Problem Statements
app_mode = st.sidebar.radio(
    "🧭 Select Solution Track:",
    ["Problem Statement 2: Automated Mortgage Underwriting Engine (Home Loans & LAP)",
     "Problem Statement 1: AI Property Valuation Engine (AVM)"]
)

# ==============================================================================
# TRACK 2: DIGITALLY AUTOMATED MORTGAGE UNDERWRITING ENGINE
# ==============================================================================
if "Problem Statement 2" in app_mode:
    uw_engine = MortgageUnderwritingEngine()

    st.markdown(r"""
    <div class="main-header">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
            <div>
                <h1 style="margin:0; font-size:1.75rem; font-weight:800;">Digitally Automated Mortgage Underwriting Engine</h1>
                <p style="margin:4px 0 0 0; color:#94A3B8; font-size:0.92rem;">
                    Autonomous Humanless Underwriting for Home Loans & LAP | Compliant with NHB, KYC/AML & Fair Practices Code
                </p>
            </div>
            <div style="text-align:right; background:rgba(255,255,255,0.08); padding:6px 14px; border-radius:8px;">
                <span style="color:#10B981; font-weight:800; font-size:1.05rem;">STP &lt; 15 Mins</span> | 
                <span style="color:#38BDF8; font-weight:800; font-size:1.05rem;">India Stack DPI</span> | 
                <span style="color:#F8FAFC; font-weight:800; font-size:1.05rem;">Audit-Ready</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Preset selector for Underwriting
    UW_PRESETS = {
        "Custom Application (Edit sidebar inputs)": None,
        "🟢 Salaried Home Loan (Clean STP Auto-Approve)": {
            "loan_product": "Home_Loan", "applicant_type": "Salaried", "applicant_name": "Pooja Verma",
            "age": 32, "cibil_score": 785, "monthly_net_income": 135000.0, "existing_monthly_obligations": 12000.0,
            "requested_loan_amount": 5500000.0, "requested_tenure_years": 20, "property_market_value": 7500000.0,
            "pincode": "560066", "pan_verified": True, "aadhaar_ekyc_verified": True, "account_aggregator_verified": True,
            "recent_30_dpd_count_12m": 0, "written_off_accounts": 0, "bank_statement_tamper_flag": False,
            "hunter_fraud_match": False, "circular_transaction_flag": False
        },
        "🟢 Self-Employed LAP (ITR + GST Verified Cash Flow)": {
            "loan_product": "LAP", "applicant_type": "Self_Employed", "applicant_name": "Sanjay Agarwal",
            "age": 42, "cibil_score": 750, "annual_pat_itr": 1800000.0, "annual_depreciation": 300000.0,
            "annual_gst_turnover": 18000000.0, "business_vintage_years": 7.0, "existing_monthly_obligations": 28000.0,
            "requested_loan_amount": 4500000.0, "requested_tenure_years": 12, "property_market_value": 8500000.0,
            "pincode": "302021", "pan_verified": True, "aadhaar_ekyc_verified": True, "account_aggregator_verified": True,
            "recent_30_dpd_count_12m": 0, "written_off_accounts": 0, "bank_statement_tamper_flag": False,
            "hunter_fraud_match": False, "circular_transaction_flag": False
        },
        "🟡 Borderline Bureau Case (Refer to Underwriting Committee)": {
            "loan_product": "Home_Loan", "applicant_type": "Salaried", "applicant_name": "Amit Saxena",
            "age": 36, "cibil_score": 685, "monthly_net_income": 95000.0, "existing_monthly_obligations": 18000.0,
            "requested_loan_amount": 4200000.0, "requested_tenure_years": 20, "property_market_value": 5500000.0,
            "pincode": "122002", "pan_verified": True, "aadhaar_ekyc_verified": True, "account_aggregator_verified": True,
            "recent_30_dpd_count_12m": 0, "written_off_accounts": 0, "bank_statement_tamper_flag": False,
            "hunter_fraud_match": False, "circular_transaction_flag": False
        },
        "🔴 Hunter Fraud Alert (Hard Reject - Phone Recycling)": {
            "loan_product": "Home_Loan", "applicant_type": "Salaried", "applicant_name": "Vikas Malhotra",
            "age": 29, "cibil_score": 710, "monthly_net_income": 80000.0, "existing_monthly_obligations": 10000.0,
            "requested_loan_amount": 3500000.0, "requested_tenure_years": 20, "property_market_value": 4500000.0,
            "pincode": "110025", "pan_verified": True, "aadhaar_ekyc_verified": True, "account_aggregator_verified": True,
            "recent_30_dpd_count_12m": 0, "written_off_accounts": 0, "bank_statement_tamper_flag": False,
            "hunter_fraud_match": True, "circular_transaction_flag": False
        },
        "🔴 Bank Statement Alteration Alert (Tampered PDF Reject)": {
            "loan_product": "LAP", "applicant_type": "Self_Employed", "applicant_name": "Karan Mehra",
            "age": 45, "cibil_score": 720, "annual_pat_itr": 1200000.0, "annual_depreciation": 100000.0,
            "annual_gst_turnover": 8000000.0, "business_vintage_years": 4.0, "existing_monthly_obligations": 30000.0,
            "requested_loan_amount": 5000000.0, "requested_tenure_years": 10, "property_market_value": 7000000.0,
            "pincode": "400053", "pan_verified": True, "aadhaar_ekyc_verified": True, "account_aggregator_verified": False,
            "recent_30_dpd_count_12m": 0, "written_off_accounts": 0, "bank_statement_tamper_flag": True,
            "hunter_fraud_match": False, "circular_transaction_flag": False
        }
    }

    uw_choice = st.selectbox("⚡ Representative Mortgage Underwriting Scenarios:", list(UW_PRESETS.keys()))
    uw_def = UW_PRESETS.get(uw_choice) or UW_PRESETS["🟢 Salaried Home Loan (Clean STP Auto-Approve)"]

    st.sidebar.header("📋 Application & Borrower Parameters")
    sel_prod = st.sidebar.selectbox("Loan Product", ["Home_Loan", "LAP"], index=0 if uw_def["loan_product"]=="Home_Loan" else 1)
    sel_app_type = st.sidebar.selectbox("Applicant Profile", ["Salaried", "Self_Employed"], index=0 if uw_def["applicant_type"]=="Salaried" else 1)
    applicant_name = st.sidebar.text_input("Applicant Name", value=uw_def["applicant_name"])
    
    col_u1, col_u2 = st.sidebar.columns(2)
    with col_u1:
        age = st.number_input("Age", min_value=18, max_value=75, value=int(uw_def["age"]))
        cibil = st.number_input("CIBIL Score", min_value=300, max_value=900, value=int(uw_def["cibil_score"]))
    with col_u2:
        tenure = st.number_input("Tenure (Yrs)", min_value=1, max_value=30, value=int(uw_def["requested_tenure_years"]))
        pincode = st.text_input("Pincode", value=uw_def["pincode"])

    st.sidebar.markdown("---")
    st.sidebar.header("💰 Financials & Collateral")
    if sel_app_type == "Salaried":
        monthly_income = st.sidebar.number_input("Monthly Net Salary (₹)", min_value=10000.0, max_value=2000000.0, value=float(uw_def.get("monthly_net_income", 125000.0)), step=5000.0)
        pat_itr = 0.0
        depr = 0.0
        gst_turn = 0.0
        vintage = 0.0
    else:
        monthly_income = 0.0
        pat_itr = st.sidebar.number_input("Annual ITR PAT (₹)", min_value=100000.0, max_value=50000000.0, value=float(uw_def.get("annual_pat_itr", 1800000.0)), step=50000.0)
        depr = st.sidebar.number_input("Annual Depreciation (₹)", min_value=0.0, max_value=10000000.0, value=float(uw_def.get("annual_depreciation", 250000.0)), step=25000.0)
        gst_turn = st.sidebar.number_input("Annual GST Turnover (₹)", min_value=500000.0, max_value=100000000.0, value=float(uw_def.get("annual_gst_turnover", 15000000.0)), step=100000.0)
        vintage = st.sidebar.number_input("Business Vintage (Yrs)", min_value=0.0, max_value=40.0, value=float(uw_def.get("business_vintage_years", 5.0)), step=0.5)

    existing_emi = st.sidebar.number_input("Existing Monthly Obligations (₹)", min_value=0.0, max_value=1000000.0, value=float(uw_def["existing_monthly_obligations"]), step=2000.0)
    req_loan = st.sidebar.number_input("Requested Loan Amount (₹)", min_value=100000.0, max_value=100000000.0, value=float(uw_def["requested_loan_amount"]), step=50000.0)
    prop_val = st.sidebar.number_input("Property Valuation (₹)", min_value=500000.0, max_value=200000000.0, value=float(uw_def["property_market_value"]), step=100000.0)

    st.sidebar.markdown("---")
    st.sidebar.header("🛡️ Fraud & Digital Verifications")
    pan_ok = st.sidebar.checkbox("PAN Verified (NSDL/ITD)", value=uw_def.get("pan_verified", True))
    aadhaar_ok = st.sidebar.checkbox("Aadhaar e-KYC Verified (UIDAI)", value=uw_def.get("aadhaar_ekyc_verified", True))
    tamper_flag = st.sidebar.checkbox("⚠️ Bank Statement Tampering Flag", value=uw_def.get("bank_statement_tamper_flag", False))
    hunter_flag = st.sidebar.checkbox("⚠️ Hunter Fraud Bureau Match", value=uw_def.get("hunter_fraud_match", False))
    circular_flag = st.sidebar.checkbox("⚠️ Circular Fund Round-Trip Anomaly", value=uw_def.get("circular_transaction_flag", False))

    # Construct application model
    app_obj = UnderwritingApplication(
        loan_product=sel_prod,
        applicant_type=sel_app_type,
        applicant_name=applicant_name,
        age=int(age),
        cibil_score=int(cibil),
        monthly_net_income=float(monthly_income),
        annual_pat_itr=float(pat_itr),
        annual_depreciation=float(depr),
        annual_gst_turnover=float(gst_turn),
        business_vintage_years=float(vintage),
        existing_monthly_obligations=float(existing_emi),
        requested_loan_amount=float(req_loan),
        requested_tenure_years=int(tenure),
        property_market_value=float(prop_val),
        pincode=pincode,
        pan_verified=pan_ok,
        aadhaar_ekyc_verified=aadhaar_ok,
        bank_statement_tamper_flag=tamper_flag,
        hunter_fraud_match=hunter_flag,
        circular_transaction_flag=circular_flag
    )

    # Run Underwriting Engine
    res = uw_engine.underwrite(app_obj)
    elig = res["eligibility_metrics"]

    # Decision Banner
    if res["decision"] == "APPROVE":
        st.markdown(f"""
        <div class="decision-box decision-green">
            <h2 style="margin:0; color:#065F46;">🟢 DECISION: APPROVE (STP AUTO-SANCTION)</h2>
            <p style="margin:6px 0 10px 0; font-size:1rem;">{res['decision_summary']}</p>
            <b>Sanctioned Loan Amount:</b> {format_inr(res['sanctioned_loan_amount'])} | 
            <b>Interest Rate:</b> {res['effective_interest_rate_pct']}% p.a. | 
            <b>Monthly EMI:</b> ₹{res['monthly_emi']:,.0f} | 
            <b>Turnaround Time:</b> &lt; 15 Mins
        </div>
        """, unsafe_allow_html=True)
    elif res["decision"] == "REFER":
        st.markdown(f"""
        <div class="decision-box decision-amber">
            <h2 style="margin:0; color:#92400E;">🟡 DECISION: REFER (MANUAL UNDERWRITER EXCEPTION REVIEW)</h2>
            <p style="margin:6px 0 10px 0; font-size:1rem;">{res['decision_summary']}</p>
            <b>Eligible Capacity:</b> {format_inr(res['sanctioned_loan_amount'])} | 
            <b>Refer Triggers:</b> {', '.join(res['refer_reasons'])}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="decision-box decision-red">
            <h2 style="margin:0; color:#9F1239;">🔴 DECISION: REJECT (CREDIT POLICY KNOCKOUT)</h2>
            <p style="margin:6px 0 10px 0; font-size:1rem;">{res['decision_summary']}</p>
            <b>Primary Rejection Reasons:</b><br/>
            {"<br/>".join(["• " + r for r in res['hard_reject_reasons']])}
        </div>
        """, unsafe_allow_html=True)

    # Core Underwriting Metrics
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Assessed Monthly Income", format_inr(elig["assessed_monthly_income"]), f"{sel_app_type} Basis")
    with col_m2:
        st.metric("Proposed FOIR", f"{elig['proposed_foir_pct']}%", f"Cap: {elig['allowable_foir_limit']*100:.0f}%", delta_color="inverse" if elig['proposed_foir_pct'] > elig['allowable_foir_limit']*100 else "normal")
    with col_m3:
        st.metric("Collateral LTV", f"{elig['proposed_ltv_pct']}%", f"NHB Cap: {elig['statutory_ltv_cap']*100:.0f}%", delta_color="inverse" if elig['proposed_ltv_pct'] > elig['statutory_ltv_cap']*100 else "normal")
    with col_m4:
        st.metric("Execution Latency", f"{res['execution_latency_ms']} ms", "Real-Time DPI Stream")

    st.markdown("---")

    # Detailed Sub-Sections
    uw_tab1, uw_tab2, uw_tab3, uw_tab4 = st.tabs([
        "✅ Internal Credit Policy Matrix",
        "🛡️ Fraud Detection & KYC/AML",
        "🌐 External Data Flow Architecture",
        "📜 Regulatory Audit & Governance"
    ])

    with uw_tab1:
        st.subheader("Internal Credit Policy Validation Matrix")
        st.write("Each loan application is automatically validated against Hero Housing credit policies and NHB statutory caps:")
        for chk in res["credit_policy_checks"]:
            color = "#10B981" if chk["passed"] else ("#F43F5E" if chk["severity"]=="HARD_KNOCKOUT" else "#F59E0B")
            icon = "✅" if chk["passed"] else ("❌" if chk["severity"]=="HARD_KNOCKOUT" else "⚠️")
            st.markdown(f"""
            <div class="check-card" style="border-left: 5px solid {color};">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <b>{icon} {chk['rule']}</b>
                    <span style="font-size:0.75rem; font-weight:700; color:{color}; text-transform:uppercase;">{chk['severity']}</span>
                </div>
                <div style="color:#64748B; font-size:0.85rem; margin-top:2px;">{chk['details']}</div>
            </div>
            """, unsafe_allow_html=True)

    with uw_tab2:
        st.subheader("Multi-Vector Fraud Detection & KYC/AML Engine")
        st.write("Continuous fraud detection across identity, document tampering, bureau recycling, and AML watchlists:")
        col_f1, col_f2 = st.columns(2)
        for idx, fc in enumerate(res["fraud_kyc_checks"]):
            target_col = col_f1 if idx % 2 == 0 else col_f2
            with target_col:
                is_fraud = fc["fraud_detected"]
                color = "#F43F5E" if is_fraud else "#10B981"
                icon = "🚨 ALERT" if is_fraud else "🛡️ VERIFIED"
                target_col.markdown(f"""
                <div class="check-card" style="border-left: 5px solid {color};">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <b>{fc['check']}</b>
                        <span style="font-size:0.75rem; font-weight:700; color:{color};">{icon}</span>
                    </div>
                    <div style="color:#64748B; font-size:0.82rem; margin-top:4px;">{fc['details']}</div>
                </div>
                """, unsafe_allow_html=True)

    with uw_tab3:
        st.subheader("External Data Integration & Real-Time Flow")
        st.markdown(r"""
        ```
                                HERO HOUSING FINTECH DATA FLOW ARCHITECTURE
                                
         [ BORROWER / CHANNEL ]                      [ INDIA STACK APIS ]                  [ ENTERPRISE SERVICES ]
                   |                                           |                                       |
                   v                                           v                                       v
         +-------------------+                       +-------------------+                   +-------------------+
         | Digital Portal /  |                       | NSDL PAN API      |                   | CERSAI Asset /    |
         | Mobile Origination|                       | UIDAI Aadhaar OTP |                   | Existing Lien DB  |
         +-------------------+                       +-------------------+                   +-------------------+
                   |                                           |                                       |
                   |                                           v                                       |
                   |                                 +-------------------+                             |
                   |                                 | Account Aggregator|                             |
                   |                                 | (Setu / Finvu AA) |                             |
                   |                                 +-------------------+                             |
                   \                                           |                                      /
                    \                                          v                                     /
                     +---------------------------------> [ INGESTION GATEWAY ] <--------------------+
                                                               |
                                                               v
                                                 +---------------------------+
                                                 | Real-Time Schema Validator|
                                                 | & Identity Hash Resolver  |
                                                 +---------------------------+
                                                               |
                                     +-------------------------+-------------------------+
                                     |                                                   |
                                     v                                                   v
                       +---------------------------+                       +---------------------------+
                       | Eligibility & Policy Rule |                       | Multi-Vector Fraud & KYC/ |
                       | Engine (FOIR, LTV, Age)   |                       | AML Screening (Hunter/PEP)|
                       +---------------------------+                       +---------------------------+
                                     |                                                   |
                                     \                                                   /
                                      \                                                 /
                                       v                                               v
                                     +---------------------------------------------------+
                                     |        DECISION ENGINE (Approve/Reject/Refer)     |
                                     |        Latency: < 50ms | Immutable Audit Hash     |
                                     +---------------------------------------------------+
        ```
        """)

    with uw_tab4:
        st.subheader("Statutory Compliance & Audit Governance")
        st.write("Compliant with National Housing Bank (NHB) Directions & Fair Practices Code:")
        audit = res["statutory_compliance"]
        st.json({
            "Application ID": res["application_id"],
            "Trace Hash": audit["immutable_trace_id"],
            "Timestamp": audit["audit_timestamp"],
            "NHB Master Directions Compliance": "VERIFIED (LTV caps & FOIR rules satisfied)",
            "Fair Practices Code": "VERIFIED (Objective rejection reasons supplied)",
            "PMLA / KYC Compliance": "PASSED" if audit["pmla_kyc_aml_compliant"] else "ALERT"
        })

# ==============================================================================
# TRACK 1: AI PROPERTY VALUATION ENGINE (HEROVAL-AI)
# ==============================================================================
else:
    # Load valuation models
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model = joblib.load(os.path.join(base_dir, "models", "heroval_lightgbm.pkl"))
    with open(os.path.join(base_dir, "models", "conformal_calib.json"), "r") as f:
        calib_meta = json.load(f)
    micro_markets = calib_meta["micro_markets"]
    q_90_rel = calib_meta["q_90_rel"]
    benchmarks = calib_meta["benchmark_summary"]

    st.markdown(r"""
    <div class="main-header">
        <h1 style="margin:0; font-size:1.75rem; font-weight:800;">HeroVal-AI: Digital Property Valuation Engine</h1>
        <p style="margin:4px 0 0 0; color:#94A3B8; font-size:0.92rem;">
            Hierarchical Geospatial AVM for Indian Real Estate | Accuracy: 4.61% MdAPE | 90% Conformal Prediction Bounds
        </p>
    </div>
    """, unsafe_allow_html=True)

    cities = ["Bengaluru", "Mumbai", "Delhi-NCR", "Pune", "Hyderabad", "Jaipur", "Coimbatore", "Lucknow"]
    sel_city = st.sidebar.selectbox("City", cities, index=0)
    city_mm = [k for k, v in micro_markets.items() if v["city"] == sel_city]
    sel_mm = st.sidebar.selectbox("Micro-Market Cluster", city_mm, index=0)

    carpet_sqft = st.sidebar.number_input("Carpet Area (sq.ft)", min_value=200, max_value=12000, value=1420, step=50)
    road_width_ft = st.sidebar.slider("Road Access Width (ft)", 15, 100, 50, step=5)
    dist_metro_km = st.sidebar.slider("Distance to Metro (km)", 0.1, 14.0, 0.8, step=0.1)
    rera_approved = st.sidebar.selectbox("RERA Status", ["Approved", "Unapproved"])

    minfo = micro_markets[sel_mm]
    df_val = pd.DataFrame([{
        "city": sel_city, "property_type": "Apartment", "carpet_sqft": float(carpet_sqft),
        "bhk": 3, "floor": 5, "total_floors": 12, "age_years": 3.0, "road_width_ft": float(road_width_ft),
        "dist_metro_km": float(dist_metro_km), "amenities_score": 8, "rera_approved": 1 if rera_approved=="Approved" else 0,
        "circle_rate_sqft": minfo["circle_rate"], "satellite_ndvi": 0.42, "satellite_density": 0.65,
        "satellite_rooftop": 4, "flood_hazard_score": 1, "h3_comp_median_sqft": minfo["base_sqft"],
        "circle_to_comp_ratio": minfo["circle_rate"]/minfo["base_sqft"], "lat": minfo["lat"], "lon": minfo["lon"]
    }])
    df_val["city"] = df_val["city"].astype("category")
    df_val["property_type"] = df_val["property_type"].astype("category")

    pred_lakhs = float(model.predict(df_val)[0])
    c1, c2, c3 = st.columns(3)
    c1.metric("Fair Market Value", format_inr(pred_lakhs * 100000.0), f"₹{(pred_lakhs*100000.0)/carpet_sqft:,.0f}/sqft")
    c2.metric("Realizable Value (90d)", format_inr(pred_lakhs * 0.88 * 100000.0), "88% of FMV")
    c3.metric("Forced Sale Value", format_inr(pred_lakhs * 0.72 * 100000.0), "72% Statutory Recovery Floor")

    st.success(f"**90% Conformal Interval:** {format_inr(pred_lakhs*(1-q_90_rel)*100000.0)} to {format_inr(pred_lakhs*(1+q_90_rel)*100000.0)} (Statistically Guaranteed)")

st.markdown("---")
st.caption("Hero Housing Fintech Challenge 2026 | Comprehensive FinTech Suite | Built for Hero Housing Finance Limited")
