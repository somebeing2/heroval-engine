import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../app")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from underwriting_engine import MortgageUnderwritingEngine, UnderwritingApplication

@pytest.fixture(scope="module")
def uw_engine():
    return MortgageUnderwritingEngine()

# TEST 1: External Data Sources & Integration Ingestion
def test_01_external_data_sources_and_flow(uw_engine):
    """Test 1: Verify multi-source external data flow (PAN, Aadhaar, AA, CIBIL, Hunter)."""
    app = UnderwritingApplication(
        pan="ABCDE1234F",
        aadhaar_masked="XXXXXXXX9876",
        pan_verified=True,
        aadhaar_ekyc_verified=True,
        account_aggregator_verified=True
    )
    res = uw_engine.underwrite(app)
    assert res["statutory_compliance"]["pmla_kyc_aml_compliant"] is True
    assert "immutable_trace_id" in res["statutory_compliance"]
    assert res["execution_latency_ms"] < 100.0

# TEST 2: Real-Time Eligibility for Home Loans (Salaried)
def test_02_real_time_eligibility_home_loan(uw_engine):
    """Test 2: Real-time Home Loan eligibility, FOIR caps, and NHB statutory LTV."""
    app = UnderwritingApplication(
        loan_product="Home_Loan",
        applicant_type="Salaried",
        monthly_net_income=120000.0,
        existing_monthly_obligations=15000.0,
        requested_loan_amount=5000000.0, # 50L
        requested_tenure_years=20,
        property_market_value=7000000.0  # 70L
    )
    elig = uw_engine.assess_eligibility(app)
    assert elig["assessed_monthly_income"] == 120000.0
    assert elig["allowable_foir_limit"] == 0.65 # High income salaried limit
    assert elig["statutory_ltv_cap"] == 0.80   # 30L-75L Home Loan tier = 80%
    assert elig["max_loan_collateral_capacity"] == 5600000.0 # 70L * 0.80
    assert elig["eligible_loan_amount"] == 5000000.0 # Full requested amount eligible
    assert elig["eligible_emi"] > 0

# TEST 3: Real-Time Eligibility for LAP (Self-Employed)
def test_03_real_time_eligibility_lap(uw_engine):
    """Test 3: Real-time LAP eligibility using ITR + GST cash flow and conservative 65% LTV."""
    app = UnderwritingApplication(
        loan_product="LAP",
        applicant_type="Self_Employed",
        annual_pat_itr=1500000.0,
        annual_depreciation=300000.0,
        annual_gst_turnover=15000000.0,
        business_vintage_years=6.0,
        existing_monthly_obligations=25000.0,
        requested_loan_amount=4000000.0,
        requested_tenure_years=15,
        property_market_value=8000000.0  # 80L
    )
    elig = uw_engine.assess_eligibility(app)
    assert elig["statutory_ltv_cap"] == 0.65  # LAP strict cap = 65%
    assert elig["max_loan_collateral_capacity"] == 5200000.0 # 80L * 0.65
    assert elig["eligible_loan_amount"] == 4000000.0

# TEST 4: Credit Policy Validation Matrix (Age, CIBIL, Delinquency, Pincode)
def test_04_credit_policy_validation_matrix(uw_engine):
    """Test 4: Verify internal credit policy rules (hard knockouts vs approvals)."""
    # Low CIBIL (<650) -> Must Hard Reject
    app_low_cibil = UnderwritingApplication(cibil_score=610)
    res_cibil = uw_engine.underwrite(app_low_cibil)
    assert res_cibil["decision"] == "REJECT"
    assert any("CIBIL" in r for r in res_cibil["hard_reject_reasons"])

    # High Delinquency -> Must Hard Reject
    app_delinq = UnderwritingApplication(recent_30_dpd_count_12m=2)
    res_delinq = uw_engine.underwrite(app_delinq)
    assert res_delinq["decision"] == "REJECT"
    assert any("Delinquency" in r for r in res_delinq["hard_reject_reasons"])

    # Blacklisted Pincode -> Must Hard Reject
    app_pin = UnderwritingApplication(pincode="110099")
    res_pin = uw_engine.underwrite(app_pin)
    assert res_pin["decision"] == "REJECT"
    assert any("Pincode" in r for r in res_pin["hard_reject_reasons"])

# TEST 5: Multi-Vector Fraud Detection Engine
def test_05_fraud_detection_engine(uw_engine):
    """Test 5: Verify fraud detection triggers (Hunter, Tampering, Circular, AML/PEP)."""
    # Hunter Fraud Bureau Hit -> Hard Reject
    app_hunter = UnderwritingApplication(hunter_fraud_match=True)
    res_hunter = uw_engine.underwrite(app_hunter)
    assert res_hunter["decision"] == "REJECT"
    assert any("Hunter" in r for r in res_hunter["hard_reject_reasons"])

    # Bank statement tampering -> Hard Reject
    app_tamper = UnderwritingApplication(bank_statement_tamper_flag=True)
    res_tamper = uw_engine.underwrite(app_tamper)
    assert res_tamper["decision"] == "REJECT"
    assert any("Bank Statement" in r for r in res_tamper["hard_reject_reasons"])

    # Circular transactions anomaly -> Hard Reject
    app_circular = UnderwritingApplication(circular_transaction_flag=True)
    res_circular = uw_engine.underwrite(app_circular)
    assert res_circular["decision"] == "REJECT"

# TEST 6: Instant Decisioning Engine (Approve, Reject, Refer)
def test_06_instant_decisioning_engine(uw_engine):
    """Test 6: Verify tri-state decisioning outcomes (APPROVE, REJECT, REFER)."""
    # 1. Clean Profile -> APPROVE (STP)
    app_clean = UnderwritingApplication(
        cibil_score=780,
        monthly_net_income=150000.0,
        existing_monthly_obligations=10000.0,
        requested_loan_amount=4000000.0,
        property_market_value=6000000.0
    )
    res_approve = uw_engine.underwrite(app_clean)
    assert res_approve["decision"] == "APPROVE"
    assert res_approve["decision_code"] == "STP_AUTO_APPROVE"
    assert res_approve["disbursal_tat_hours"] <= 0.25

    # 2. Borderline Bureau (680) -> REFER (Underwriter Review)
    app_refer = UnderwritingApplication(
        cibil_score=680, # 650-724 triggers refer
        monthly_net_income=150000.0,
        requested_loan_amount=4000000.0,
        property_market_value=6000000.0
    )
    res_refer = uw_engine.underwrite(app_refer)
    assert res_refer["decision"] == "REFER"
    assert res_refer["decision_code"] == "MANUAL_UNDERWRITER_REVIEW"
    assert len(res_refer["refer_reasons"]) > 0

    # 3. Non-negotiable Knockout -> REJECT
    app_reject = UnderwritingApplication(written_off_accounts=1)
    res_reject = uw_engine.underwrite(app_reject)
    assert res_reject["decision"] == "REJECT"

# TEST 7: Explainability, Governance & Statutory Audit Compliance
def test_07_explainability_governance_and_audit(uw_engine):
    """Test 7: Verify decision explainability, transparent rejection reasons, and audit trail."""
    app_bad = UnderwritingApplication(cibil_score=620, age=58, requested_tenure_years=15)
    res = uw_engine.underwrite(app_bad)
    
    assert res["decision"] == "REJECT"
    # Fair Practices Code compliance: Must provide transparent human-readable rejection reasons
    assert len(res["hard_reject_reasons"]) >= 1
    for r in res["hard_reject_reasons"]:
        assert isinstance(r, str) and len(r) > 10
        
    # Statutory NHB audit record check
    audit = res["statutory_compliance"]
    assert "audit_timestamp" in audit
    assert audit["immutable_trace_id"].startswith("TRACE-")
    assert audit["nhb_master_directions_compliant"] is True
    assert audit["fair_practices_code_compliant"] is True
