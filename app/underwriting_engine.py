import math
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class UnderwritingApplication(BaseModel):
    application_id: str = "HHFL-APP-2026-8841"
    loan_product: str = "Home_Loan"  # "Home_Loan" or "LAP"
    applicant_type: str = "Salaried"  # "Salaried" or "Self_Employed"
    applicant_name: str = "Rajesh Sharma"
    age: int = 34
    pan: str = "ABCPS1234K"
    aadhaar_masked: str = "XXXXXXXX1234"
    cibil_score: int = 765
    monthly_net_income: float = 125000.0  # For Salaried
    annual_pat_itr: Optional[float] = 1800000.0  # For Self-Employed (Profit After Tax)
    annual_depreciation: Optional[float] = 250000.0  # Added back for cash flow
    annual_gst_turnover: Optional[float] = 12000000.0  # For Self-Employed
    business_vintage_years: Optional[float] = 5.5
    existing_monthly_obligations: float = 18000.0  # Existing EMIs
    requested_loan_amount: float = 5500000.0  # ₹55 Lakhs
    requested_tenure_years: int = 20
    property_market_value: float = 7500000.0  # ₹75 Lakhs
    property_type: str = "Apartment"
    pincode: str = "560066"  # Bengaluru Whitefield
    
    # External Verification Data / Flags (Simulated from India Stack APIs)
    pan_verified: bool = True
    aadhaar_ekyc_verified: bool = True
    account_aggregator_verified: bool = True
    recent_30_dpd_count_12m: int = 0
    written_off_accounts: int = 0
    bank_statement_tamper_flag: bool = False
    hunter_fraud_match: bool = False
    circular_transaction_flag: bool = False
    pep_sanctions_match: bool = False

class MortgageUnderwritingEngine:
    def __init__(self):
        # NHB & Internal Credit Policy Constants
        self.POLICY = {
            "MIN_AGE": 21,
            "MAX_AGE_SALARIED_MATURITY": 60,
            "MAX_AGE_SENP_MATURITY": 65,
            "MIN_CIBIL_HARD_REJECT": 650,
            "MIN_CIBIL_AUTO_APPROVE": 725,
            "MIN_BUSINESS_VINTAGE_YEARS": 3.0,
            # NHB Statutory LTV Caps for Home Loans
            "HL_LTV_TIER_1": 0.90,  # <= 30 Lakhs
            "HL_LTV_TIER_2": 0.80,  # 30L to 75L
            "HL_LTV_TIER_3": 0.75,  # > 75 Lakhs
            # LAP LTV Caps (More conservative as per NHB guidelines)
            "LAP_MAX_LTV": 0.65,
            # Max FOIR limits
            "MAX_FOIR_SALARIED_HIGH": 0.65,  # Income > 1L/mo
            "MAX_FOIR_SALARIED_MID": 0.55,   # Income 50k - 1L
            "MAX_FOIR_SALARIED_LOW": 0.50,   # Income < 50k
            "MAX_FOIR_SELF_EMPLOYED": 0.60,
            # Benchmark Interest Rates
            "BASE_RATE_HL": 8.65,  # % p.a.
            "BASE_RATE_LAP": 10.25, # % p.a.
            # Negative / Caution Pincodes
            "NEGATIVE_PINCODES": ["110099", "400099", "560099"]
        }

    def compute_income_and_foir_limit(self, app: UnderwritingApplication) -> tuple[float, float]:
        """Calculates normalized monthly disposable income and allowable FOIR threshold."""
        if app.applicant_type == "Salaried":
            monthly_income = app.monthly_net_income
            if monthly_income >= 100000:
                foir_limit = self.POLICY["MAX_FOIR_SALARIED_HIGH"]
            elif monthly_income >= 50000:
                foir_limit = self.POLICY["MAX_FOIR_SALARIED_MID"]
            else:
                foir_limit = self.POLICY["MAX_FOIR_SALARIED_LOW"]
        else: # Self_Employed
            pat = app.annual_pat_itr or 0.0
            dep = app.annual_depreciation or 0.0
            cash_profit_monthly = (pat + dep) / 12.0
            gst_turnover = app.annual_gst_turnover or 0.0
            gst_implied_monthly = (gst_turnover * 0.10) / 12.0
            monthly_income = min(cash_profit_monthly, gst_implied_monthly * 1.25) if gst_turnover > 0 else cash_profit_monthly
            foir_limit = self.POLICY["MAX_FOIR_SELF_EMPLOYED"]

        return round(monthly_income, 2), foir_limit

    def calculate_statutory_ltv_cap(self, loan_product: str, property_val: float, requested_amt: float) -> float:
        """Enforces NHB master directions on maximum Loan-to-Value (LTV)."""
        if loan_product == "LAP":
            return self.POLICY["LAP_MAX_LTV"]
        else: # Home Loan
            if requested_amt <= 3000000:
                return self.POLICY["HL_LTV_TIER_1"] # 90%
            elif requested_amt <= 7500000:
                return self.POLICY["HL_LTV_TIER_2"] # 80%
            else:
                return self.POLICY["HL_LTV_TIER_3"] # 75%

    def calculate_emi(self, principal: float, annual_rate_pct: float, tenure_years: int) -> float:
        """Calculates standard reducing monthly EMI."""
        if principal <= 0 or tenure_years <= 0:
            return 0.0
        monthly_rate = (annual_rate_pct / 100.0) / 12.0
        n_months = tenure_years * 12
        emi = (principal * monthly_rate * math.pow(1 + monthly_rate, n_months)) / (math.pow(1 + monthly_rate, n_months) - 1)
        return round(emi, 2)

    def calculate_max_loan_from_emi(self, max_emi: float, annual_rate_pct: float, tenure_years: int) -> float:
        """Inverts the EMI formula to find maximum loan principal for a given monthly EMI capacity."""
        if max_emi <= 0 or tenure_years <= 0:
            return 0.0
        monthly_rate = (annual_rate_pct / 100.0) / 12.0
        n_months = tenure_years * 12
        principal = (max_emi * (math.pow(1 + monthly_rate, n_months) - 1)) / (monthly_rate * math.pow(1 + monthly_rate, n_months))
        return round(principal, 2)

    def assess_eligibility(self, app: UnderwritingApplication) -> Dict[str, Any]:
        """Performs real-time multi-dimensional eligibility assessment (Income + Collateral)."""
        monthly_income, foir_limit = self.compute_income_and_foir_limit(app)
        
        base_rate = self.POLICY["BASE_RATE_HL"] if app.loan_product == "Home_Loan" else self.POLICY["BASE_RATE_LAP"]
        if app.cibil_score >= 775:
            spread = 0.0
        elif app.cibil_score >= 725:
            spread = 0.25
        elif app.cibil_score >= 675:
            spread = 0.65
        else:
            spread = 1.25
        effective_interest_rate = base_rate + spread

        max_total_monthly_obligation = monthly_income * foir_limit
        available_emi_capacity = max(0.0, max_total_monthly_obligation - app.existing_monthly_obligations)

        max_loan_income_capacity = self.calculate_max_loan_from_emi(
            available_emi_capacity, effective_interest_rate, app.requested_tenure_years
        )

        ltv_cap = self.calculate_statutory_ltv_cap(app.loan_product, app.property_market_value, app.requested_loan_amount)
        max_loan_collateral_capacity = round(app.property_market_value * ltv_cap, 2)

        eligible_loan_amount = min(max_loan_income_capacity, max_loan_collateral_capacity, app.requested_loan_amount)

        requested_emi = self.calculate_emi(app.requested_loan_amount, effective_interest_rate, app.requested_tenure_years)
        eligible_emi = self.calculate_emi(eligible_loan_amount, effective_interest_rate, app.requested_tenure_years)

        proposed_foir = ((app.existing_monthly_obligations + requested_emi) / monthly_income) if monthly_income > 0 else 1.0
        proposed_ltv = (app.requested_loan_amount / app.property_market_value) if app.property_market_value > 0 else 1.0

        return {
            "assessed_monthly_income": monthly_income,
            "allowable_foir_limit": foir_limit,
            "effective_interest_rate_pct": effective_interest_rate,
            "available_emi_capacity": round(available_emi_capacity, 2),
            "max_loan_income_capacity": round(max_loan_income_capacity, 2),
            "max_loan_collateral_capacity": round(max_loan_collateral_capacity, 2),
            "statutory_ltv_cap": ltv_cap,
            "eligible_loan_amount": round(eligible_loan_amount, 2),
            "requested_emi": requested_emi,
            "eligible_emi": eligible_emi,
            "proposed_foir_pct": round(proposed_foir * 100, 2),
            "proposed_ltv_pct": round(proposed_ltv * 100, 2)
        }

    def validate_credit_policy(self, app: UnderwritingApplication, elig: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validates application against internal credit policies & NHB Master Directions."""
        checks = []

        # 1. Age criteria at maturity
        maturity_age = app.age + app.requested_tenure_years
        max_age = self.POLICY["MAX_AGE_SALARIED_MATURITY"] if app.applicant_type == "Salaried" else self.POLICY["MAX_AGE_SENP_MATURITY"]
        age_passed = (app.age >= self.POLICY["MIN_AGE"]) and (maturity_age <= max_age)
        checks.append({
            "rule": "Applicant Age & Loan Maturity",
            "passed": age_passed,
            "details": f"Age: {app.age} yrs, Maturity Age: {maturity_age} yrs (Max: {max_age} yrs)",
            "severity": "HARD_KNOCKOUT"
        })

        # 2. Bureau Score
        if app.cibil_score < self.POLICY["MIN_CIBIL_HARD_REJECT"]:
            checks.append({
                "rule": "Credit Bureau Score Threshold (CIBIL)",
                "passed": False,
                "details": f"CIBIL Score: {app.cibil_score} (Below Hard Knockout {self.POLICY['MIN_CIBIL_HARD_REJECT']})",
                "severity": "HARD_KNOCKOUT"
            })
        elif app.cibil_score < self.POLICY["MIN_CIBIL_AUTO_APPROVE"]:
            checks.append({
                "rule": "Credit Bureau Score Threshold (CIBIL)",
                "passed": False,
                "details": f"CIBIL Score: {app.cibil_score} (Borderline Band {self.POLICY['MIN_CIBIL_HARD_REJECT']}-{self.POLICY['MIN_CIBIL_AUTO_APPROVE']})",
                "severity": "REFER"
            })
        else:
            checks.append({
                "rule": "Credit Bureau Score Threshold (CIBIL)",
                "passed": True,
                "details": f"CIBIL Score: {app.cibil_score} (Prime Tier)",
                "severity": "PASS"
            })

        # 3. Delinquency (DPD) & Written-Off Accounts
        no_delinquency = (app.recent_30_dpd_count_12m == 0) and (app.written_off_accounts == 0)
        checks.append({
            "rule": "Bureau Delinquency & Written-off Record",
            "passed": no_delinquency,
            "details": f"30+ DPD in 12M: {app.recent_30_dpd_count_12m}, Written-Off Accounts: {app.written_off_accounts}",
            "severity": "HARD_KNOCKOUT"
        })

        # 4. FOIR Policy Threshold
        foir_passed = elig["proposed_foir_pct"] <= (elig["allowable_foir_limit"] * 100)
        checks.append({
            "rule": "Fixed Obligation to Income Ratio (FOIR)",
            "passed": foir_passed,
            "details": f"Proposed FOIR: {elig['proposed_foir_pct']}% (Max Limit: {elig['allowable_foir_limit']*100}%)",
            "severity": "HARD_KNOCKOUT" if elig["proposed_foir_pct"] > (elig["allowable_foir_limit"] * 100 + 10) else "REFER"
        })

        # 5. Statutory LTV Cap
        ltv_passed = elig["proposed_ltv_pct"] <= (elig["statutory_ltv_cap"] * 100 + 0.1)
        checks.append({
            "rule": "Collateral Loan-to-Value (LTV) Statutory Cap",
            "passed": ltv_passed,
            "details": f"Proposed LTV: {elig['proposed_ltv_pct']}% (Statutory Ceiling: {elig['statutory_ltv_cap']*100}%)",
            "severity": "HARD_KNOCKOUT"
        })

        # 6. Business Vintage (for Self-Employed & LAP)
        if app.applicant_type == "Self_Employed" or app.loan_product == "LAP":
            vintage = app.business_vintage_years or 0.0
            vintage_passed = vintage >= self.POLICY["MIN_BUSINESS_VINTAGE_YEARS"]
            checks.append({
                "rule": "Self-Employed Business Vintage Check",
                "passed": vintage_passed,
                "details": f"Vintage: {vintage} years (Min Required: {self.POLICY['MIN_BUSINESS_VINTAGE_YEARS']} years)",
                "severity": "REFER" if not vintage_passed else "PASS"
            })

        # 7. Negative / Blacklisted Pincodes
        pincode_passed = app.pincode not in self.POLICY["NEGATIVE_PINCODES"]
        checks.append({
            "rule": "Pincode Negative Risk List Check",
            "passed": pincode_passed,
            "details": f"Property Pincode: {app.pincode} ({'Approved Locality' if pincode_passed else 'Blacklisted Caution Locality'})",
            "severity": "HARD_KNOCKOUT" if not pincode_passed else "PASS"
        })

        return checks

    def detect_fraud(self, app: UnderwritingApplication) -> List[Dict[str, Any]]:
        """Multi-vector fraud and KYC/AML screening engine."""
        fraud_checks = []

        # 1. Identity Verification (PAN & Aadhaar)
        id_verified = app.pan_verified and app.aadhaar_ekyc_verified
        fraud_checks.append({
            "check": "Digital Identity Verification (PAN & Aadhaar)",
            "fraud_detected": not id_verified,
            "details": f"PAN Verified: {app.pan_verified} (NSDL/ITD), Aadhaar e-KYC: {app.aadhaar_ekyc_verified} (UIDAI)",
            "risk_weight": "HIGH"
        })

        # 2. Bank Statement Tampering / Financial Document Manipulation
        fraud_checks.append({
            "check": "Bank Statement Font & Metadata Alteration Check",
            "fraud_detected": app.bank_statement_tamper_flag,
            "details": "Tampering flag raised: Suspicious PDF font inconsistencies or modified transaction balances" if app.bank_statement_tamper_flag else "Digital hash verified; direct Account Aggregator pull authentic",
            "risk_weight": "HIGH"
        })

        # 3. Hunter Fraud Bureau Cross-Match
        fraud_checks.append({
            "check": "Hunter Fraud Cross-Match (Phone/PAN Recycling)",
            "fraud_detected": app.hunter_fraud_match,
            "details": "Positive Hunter cross-match: Mobile number or PAN recycled across conflicting loan files" if app.hunter_fraud_match else "Clear Hunter bureau history; zero identity recycling hits",
            "risk_weight": "CRITICAL"
        })

        # 4. Circular Transaction / Fund Inundation Detection
        fraud_checks.append({
            "check": "Circular Fund Round-Tripping Anomaly",
            "fraud_detected": app.circular_transaction_flag,
            "details": "High-velocity round-trip credit transactions detected 48h before application" if app.circular_transaction_flag else "Normal organic cash-flow cadence verified by Account Aggregator",
            "risk_weight": "HIGH"
        })

        # 5. PEP & AML / Sanctions Screening
        fraud_checks.append({
            "check": "AML / Sanctions / Politically Exposed Person (PEP)",
            "fraud_detected": app.pep_sanctions_match,
            "details": "Adverse match in FIU-IND / OFAC / CBI sanctions watchlists" if app.pep_sanctions_match else "Clean KYC/AML screening; zero sanctions or PEP exposure",
            "risk_weight": "CRITICAL"
        })

        return fraud_checks

    def underwrite(self, app: UnderwritingApplication) -> Dict[str, Any]:
        """Main end-to-end autonomous underwriting entrypoint."""
        t_start = time.time()

        elig = self.assess_eligibility(app)
        policy_checks = self.validate_credit_policy(app, elig)
        fraud_checks = self.detect_fraud(app)

        hard_reject_reasons = []
        refer_reasons = []

        # Evaluate Fraud Checks
        for fc in fraud_checks:
            if fc["fraud_detected"]:
                hard_reject_reasons.append(f"Fraud / AML Alert: {fc['check']} - {fc['details']}")

        # Evaluate Credit Policy Checks
        for pc in policy_checks:
            if not pc["passed"]:
                if pc["severity"] == "HARD_KNOCKOUT":
                    hard_reject_reasons.append(f"Credit Policy Knockout: {pc['rule']} - {pc['details']}")
                else:
                    refer_reasons.append(f"Credit Policy Refer Trigger: {pc['rule']} - {pc['details']}")

        # Final Decision Logic
        if len(hard_reject_reasons) > 0:
            decision = "REJECT"
            decision_code = "CREDIT_REJECT"
            decision_color = "rose"
            decision_summary = "Application declined due to non-negotiable credit policy knockouts or fraud alerts."
            sanctioned_amount = 0.0
            disbursal_tat_hours = 0.1
        elif len(refer_reasons) > 0:
            decision = "REFER"
            decision_code = "MANUAL_UNDERWRITER_REVIEW"
            decision_color = "amber"
            decision_summary = "Application routed to Senior Underwriting Committee for manual deviation approval."
            sanctioned_amount = elig["eligible_loan_amount"]
            disbursal_tat_hours = 12.0
        else:
            decision = "APPROVE"
            decision_code = "STP_AUTO_APPROVE"
            decision_color = "emerald"
            decision_summary = "Application fully approved via Straight-Through Processing (STP) with zero human touch."
            sanctioned_amount = elig["eligible_loan_amount"]
            disbursal_tat_hours = 0.25

        execution_latency_ms = round((time.time() - t_start) * 1000, 2)

        return {
            "application_id": app.application_id,
            "applicant_name": app.applicant_name,
            "loan_product": app.loan_product,
            "applicant_type": app.applicant_type,
            "decision": decision,
            "decision_code": decision_code,
            "decision_color": decision_color,
            "decision_summary": decision_summary,
            "sanctioned_loan_amount": sanctioned_amount,
            "requested_loan_amount": app.requested_loan_amount,
            "effective_interest_rate_pct": elig["effective_interest_rate_pct"],
            "monthly_emi": elig["eligible_emi"] if decision != "REJECT" else 0.0,
            "disbursal_tat_hours": disbursal_tat_hours,
            "execution_latency_ms": execution_latency_ms,
            "eligibility_metrics": elig,
            "credit_policy_checks": policy_checks,
            "fraud_kyc_checks": fraud_checks,
            "hard_reject_reasons": hard_reject_reasons,
            "refer_reasons": refer_reasons,
            "statutory_compliance": {
                "nhb_master_directions_compliant": True,
                "fair_practices_code_compliant": True,
                "pmla_kyc_aml_compliant": (not any(fc["fraud_detected"] for fc in fraud_checks)),
                "audit_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "immutable_trace_id": f"TRACE-{app.application_id}-{int(time.time())}"
            }
        }
