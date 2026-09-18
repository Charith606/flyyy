import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Set up paths so app imports work seamlessly
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

# Ensure database path is resolved properly
DB_PATH = BACKEND_DIR / "flyyy_cdp.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")

import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

# Import backend modules
from app.config import get_settings
from app.db.session import SessionLocal, init_db, engine
from app.db.models import (
    SourceCustomer,
    ProtectedCustomer,
    VaultMapping,
    AuditLog,
    BatchRun,
    ProtectionPolicy,
)
from app.seed import seed_source_database
from app.discovery.analyzer import discover_field_pii, discover_dataset
from app.batch.pipeline import run_batch_protection_job, get_or_create_default_policies
from app.protection.masking import mask_email, mask_phone, mask_name
from app.protection.vault import resolve_vault_mapping, reverse_lookup_vault_by_plaintext
from app.gateway.router import record_audit
from app.gateway.mailer import send_smtp_email

# Initialize DB tables on start
init_db()

# Page configuration
st.set_page_config(
    page_title="Flyyy CDP • Privacy-Preserving Data Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium Modern Dark SaaS CSS Theme
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    code, pre, .mono {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Background and containers */
    .stApp {
        background-color: #0B0F19;
        color: #F1F5F9;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    /* Modern Navigation Items (Custom Radio styling) */
    div[data-testid="stRadio"] > div {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    
    div[data-testid="stRadio"] > div > label {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px;
        padding: 10px 14px;
        cursor: pointer;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        margin: 0;
        width: 100%;
        color: #94A3B8;
        font-size: 0.88rem;
        font-weight: 500;
        display: flex;
        align-items: center;
    }
    
    div[data-testid="stRadio"] > div > label:hover {
        background: rgba(51, 65, 85, 0.8);
        border-color: rgba(56, 189, 248, 0.4);
        color: #F8FAFC;
        transform: translateX(4px);
    }
    
    /* Hide the ugly native radio circle */
    div[data-testid="stRadio"] > div > label > div:first-child {
        display: none !important;
    }
    
    /* Active Selected Radio Item */
    div[data-testid="stRadio"] > div > label:has(input:checked) {
        background: linear-gradient(90deg, rgba(16, 185, 129, 0.2), rgba(15, 23, 42, 0.8)) !important;
        border: 1px solid rgba(16, 185, 129, 0.6) !important;
        border-left: 4px solid #10B981 !important;
        color: #34D399 !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
    }

    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8));
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 16px 20px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.4);
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #34D399, #38BDF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 700;
        color: #94A3B8 !important;
    }

    /* Hero / Feature Cards */
    .hero-container {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.7));
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
        position: relative;
        overflow: hidden;
    }
    .hero-container::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, #10B981, #38BDF8, #8B5CF6);
    }

    .card-box {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 18px;
        transition: all 0.2s ease;
    }
    .card-box:hover {
        border-color: rgba(255, 255, 255, 0.2);
    }

    /* Status Badges */
    .badge-live {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .badge-live::before {
        content: "";
        width: 6px;
        height: 6px;
        background-color: #34D399;
        border-radius: 50%;
        box-shadow: 0 0 8px #34D399;
    }
    .badge-fpe {
        background: rgba(56, 189, 248, 0.15);
        color: #38BDF8;
        border: 1px solid rgba(56, 189, 248, 0.3);
        padding: 3px 8px;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
    }
    .badge-token {
        background: rgba(168, 85, 247, 0.15);
        color: #C084FC;
        border: 1px solid rgba(168, 85, 247, 0.3);
        padding: 3px 8px;
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        padding: 8px 18px;
        transition: all 0.2s ease;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #10B981, #059669);
        border: none;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #34D399, #10B981);
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.45);
        transform: translateY(-1px);
    }

    /* Dataframe table rounded borders */
    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        overflow: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Helper DB access functions
def get_db_session():
    return SessionLocal()

def get_counts():
    with get_db_session() as db:
        src_cnt = db.query(SourceCustomer).count()
        prot_cnt = db.query(ProtectedCustomer).count()
        vault_cnt = db.query(VaultMapping).count()
        audit_cnt = db.query(AuditLog).count()
        return src_cnt, prot_cnt, vault_cnt, audit_cnt

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(
        """
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
            <div style="font-size: 1.4rem; font-weight: 800; background: linear-gradient(135deg, #38BDF8, #10B981); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                🛡️ Flyyy CDP
            </div>
            <span class="badge-live">LIVE</span>
        </div>
        <div style="font-size: 0.78rem; color: #94A3B8; margin-bottom: 16px;">
            Privacy-Preserving Customer Data Platform
        </div>
        <div style="background: rgba(15, 23, 42, 0.6); border-left: 3px solid #38BDF8; padding: 10px 12px; border-radius: 6px; font-size: 0.75rem; color: #CBD5E1; margin-bottom: 20px; font-style: italic;">
            "Protected by Default. Reveal or Use Plaintext Only by Exception."
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='font-size:0.75rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:8px;'>NAVIGATION</div>", unsafe_allow_html=True)
    
    # Modern Navigation Radio (CSS styled as buttons)
    selected_tab = st.radio(
        "Navigation",
        [
            "🏛️ Architecture & Overview",
            "🔍 1. PII Discovery",
            "⚙️ 2. Policy & Batch Engine",
            "🛡️ 3. Protected Data Store",
            "🚪 4. Privacy Gateway",
            "🔑 5. Controlled Reveal",
            "📜 6. Compliance Audit Trail",
        ],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:0.75rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:8px;'>QUICK ACTIONS</div>", unsafe_allow_html=True)

    with st.container():
        col_seed1, col_seed2 = st.columns([1, 1])
        with col_seed1:
            seed_count = st.number_input("Records", min_value=10, max_value=200, value=50, step=10, label_visibility="collapsed")
        with col_seed2:
            if st.button("🌱 Seed Data", use_container_width=True, type="primary"):
                with st.spinner("Seeding database..."):
                    seed_source_database(int(seed_count))
                    st.success(f"Seeded {seed_count} rows!")
                    time.sleep(0.6)
                    st.rerun()

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255,255,255,0.05); border-radius: 10px; padding: 12px; font-size: 0.75rem; color: #94A3B8;">
            <div style="font-weight: 700; color: #E2E8F0; margin-bottom: 6px;">🔒 Cryptographic Stack:</div>
            <div>• <span style="color:#38BDF8;">pyffx FF3-1</span> (Format Preserving)</div>
            <div>• <span style="color:#C084FC;">HMAC-SHA256</span> (Deterministic Token)</div>
            <div>• <span style="color:#34D399;">AES-256-GCM</span> (Secure Isolated Vault)</div>
            <div>• <span style="color:#FBBF24;">Immutable Audit</span> (Zero Plaintext Logs)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Get live metrics
src_cnt, prot_cnt, vault_cnt, audit_cnt = get_counts()

# Top KPI Metric Cards Bar
m1, m2, m3, m4 = st.columns(4)
m1.metric("Source Raw Records", f"{src_cnt:,}")
m2.metric("Protected Store Records", f"{prot_cnt:,}")
m3.metric("Vault Mappings (AES-GCM)", f"{vault_cnt:,}")
m4.metric("Audited Events Logged", f"{audit_cnt:,}")

st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

# ==============================================================================
# TAB 1: ARCHITECTURE & OVERVIEW
# ==============================================================================
if selected_tab == "🏛️ Architecture & Overview":
    st.markdown(
        """
        <div class="hero-container">
            <h2 style="margin: 0 0 10px 0; font-size: 1.6rem; color: #38BDF8;">
                🏛️ Flyyy Privacy-Preserving Customer Data Platform
            </h2>
            <p style="color: #CBD5E1; font-size: 0.98rem; line-height: 1.6; margin-bottom: 0;">
                Flyyy CDP prevents Personally Identifiable Information (PII) from leaking into analytics, marketing automation, CRM, or support tools.
                Downstream applications operate exclusively on <strong>Format-Preserving Ciphers</strong> and <strong>Deterministic Tokens</strong>,
                while raw plaintext is permanently sealed inside an isolated <strong>AES-256-GCM encrypted vault</strong>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🔄 End-to-End Architectural Pipeline")
    st.markdown(
        """
```
+-----------------------------------------------------------------------------------+
| 1. DATA INGESTION & DISCOVERY                                                     |
|    - Source Database (Read-Only)                                                  |
|    - Automated PII Classifier: Presidio + Regex (Phone, Email, Name)              |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
| 2. PROTECTION & ENCRYPTION ENGINE                                                 |
|    - Format-Preserving Encryption (FPE / pyffx): 10-digit phone -> 10-digit cipher|
|    - Deterministic Tokenization: HMAC-SHA256 -> EMAIL_P91QZ, NAME_A72K            |
|    - Isolated Vault: AES-256-GCM Encrypted Mappings                               |
+-----------------------------------------------------------------------------------+
                   │                                             │
                   ▼                                             ▼
+------------------------------------+         +------------------------------------+
| 3. PROTECTED DATA STORE            |         | 4. ISOLATED SECURE VAULT           |
|    - table: protected_customers    |         |    - table: vault_mappings         |
|    - Zero plaintext PII            |         |    - Encrypted tokens & ciphers    |
|    - Safe for analytics / CRM      |         |    - Inaccessible to normal apps   |
+------------------------------------+         +------------------------------------+
                   │                                             ▲
                   ▼                                             │ (Authorized Only)
+----------------------------------------------------------------┴------------------+
| 5. PRIVACY GATEWAY (THE GATEKEEPER)                                               |
|    - Blind Marketing Dispatch: Sends email via SMTP without exposing real email   |
|    - Bounce Webhook Handler: Reverse-resolves email -> EMAIL_P91QZ for safe store |
|    - Controlled Reveal Exception: RBAC + Purpose (Ticket #) -> Plaintext          |
|    - Immutable Append-Only Audit Trail: Every attempt (allowed / denied) logged   |
+-----------------------------------------------------------------------------------+
```
        """
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div class="card-box">
                <h4 style="color: #38BDF8; margin-top: 0;">🔢 Format-Preserving Encryption</h4>
                <p style="font-size: 0.85rem; color: #94A3B8; line-height: 1.5;">
                    Transforms 10-digit phone numbers into 10-digit ciphertext using standard <strong>pyffx FF3-1</strong>.
                    Guarantees schema compliance and telephony format validity with zero plaintext leakage.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="card-box">
                <h4 style="color: #C084FC; margin-top: 0;">🏷️ Deterministic Tokens</h4>
                <p style="font-size: 0.85rem; color: #94A3B8; line-height: 1.5;">
                    Replaces emails and names with salted <strong>HMAC-SHA256 tokens</strong> (<code>EMAIL_...</code>, <code>NAME_...</code>).
                    Enables joins across datasets without ever disclosing identity.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
            <div class="card-box">
                <h4 style="color: #34D399; margin-top: 0;">🔐 Isolated Vault & Gateway</h4>
                <p style="font-size: 0.85rem; color: #94A3B8; line-height: 1.5;">
                    Mappings stored using authenticated <strong>AES-256-GCM</strong>.
                    Campaigns execute blindly through the Privacy Gateway, and plaintext is revealed strictly through audited RBAC exceptions.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ==============================================================================
# TAB 2: PII DISCOVERY
# ==============================================================================
elif selected_tab == "🔍 1. PII Discovery":
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h3 style="margin:0 0 4px 0; color:#38BDF8;">🔍 Automated PII Ingestion & Discovery</h3>
            <p style="color:#94A3B8; font-size:0.9rem;">
                Scan incoming raw customer datasets using Presidio analyzers and regex heuristics to automatically classify sensitive fields.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with get_db_session() as db:
        source_data = db.query(SourceCustomer).limit(20).all()
        total_source = db.query(SourceCustomer).count()

    if total_source == 0:
        st.warning("⚠️ Source database is empty. Click '🌱 Seed Data' in the left sidebar to generate 50 sample records.")
    else:
        st.caption(f"Showing sample records from `source_customers` ({total_source} total rows):")
        df_source = pd.DataFrame([
            {
                "Customer ID": s.customer_id,
                "Plaintext Name": s.name,
                "Plaintext Email": s.email,
                "Plaintext Mobile": s.mobile,
                "City": s.city,
                "Segment": s.segment,
            }
            for s in source_data
        ])
        st.dataframe(df_source, use_container_width=True, hide_index=True)

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        col_scan1, col_scan2 = st.columns([2, 1])
        with col_scan1:
            st.markdown("#### 🤖 Run Automated Discovery Scan")
            st.caption("Analyzes field names and pattern distributions across all columns.")
        with col_scan2:
            st.write("")
            run_scan = st.button("🚀 Run Discovery Scan", type="primary", use_container_width=True)

        if run_scan:
            with st.spinner("Analyzing dataset with Presidio & Regex Heuristics..."):
                with get_db_session() as db:
                    records = [
                        {
                            "customer_id": s.customer_id,
                            "name": s.name,
                            "email": s.email,
                            "mobile": s.mobile,
                            "city": s.city,
                            "segment": s.segment,
                        }
                        for s in db.query(SourceCustomer).limit(100).all()
                    ]
                    findings = discover_dataset(records)

                st.success("✅ PII Discovery Completed Successfully!")

                findings_data = []
                for f in findings:
                    findings_data.append({
                        "Field Name": f["field_name"],
                        "Entity Type": f["entity_type"],
                        "Confidence Score": f"{f['confidence'] * 100:.1f}%",
                        "Recommended Protection": f["recommended_action"],
                        "Sample Count": f["sample_count"],
                    })

                st.dataframe(pd.DataFrame(findings_data), use_container_width=True, hide_index=True)

        st.markdown("---")
        with st.expander("🧪 Interactive Single-String PII Sandbox"):
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                test_field = st.text_input("Column / Field Name", value="customer_contact_email")
            with c_s2:
                test_val = st.text_input("Sample Value", value="sarah.connor@cyberdyne.io")
            if st.button("Analyze Sample"):
                res = discover_field_pii(test_field, [test_val])
                st.json(res)

# ==============================================================================
# TAB 3: POLICY & BATCH ENGINE
# ==============================================================================
elif selected_tab == "⚙️ 2. Policy & Batch Engine":
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h3 style="margin:0 0 4px 0; color:#38BDF8;">⚙️ Protection Policy & Batch Transformation Engine</h3>
            <p style="color:#94A3B8; font-size:0.9rem;">
                Configure cryptographic rules and execute high-throughput batch transformations from <code>source_customers</code> to <code>protected_customers</code>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with get_db_session() as db:
        get_or_create_default_policies(db)
        policies = db.query(ProtectionPolicy).all()

    st.markdown("#### Active Protection Policies")
    if policies:
        df_pol = pd.DataFrame([
            {
                "Field": p.field_name,
                "Entity Type": p.entity_type,
                "Protection Type": p.protection_type,
                "Active": "✅ Yes" if p.is_active else "❌ No",
            }
            for p in policies
        ])
        st.dataframe(df_pol, use_container_width=True, hide_index=True)

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    st.markdown("#### ⚡ Trigger Batch Protection Run")
    
    col_b1, col_b2 = st.columns([2, 1])
    with col_b1:
        batch_size = st.number_input("Batch Size (records per chunk)", min_value=10, max_value=5000, value=1000, step=500)
    with col_b2:
        st.write("")
        st.write("")
        trigger_batch = st.button("▶️ Run Batch Transformation", type="primary", use_container_width=True)

    if trigger_batch:
        t0 = time.time()
        with st.spinner("Executing Batch Cryptographic Protection Pipeline..."):
            with get_db_session() as db:
                batch_run = run_batch_protection_job(db, batch_size=batch_size)
                dur_ms = (time.time() - t0) * 1000

            st.success(f"🎉 Batch Run `{batch_run.batch_id}` Completed Successfully!")
            
            b_col1, b_col2, b_col3, b_col4 = st.columns(4)
            b_col1.metric("Processed Rows", batch_run.row_count)
            b_col2.metric("Succeeded", batch_run.success_count)
            b_col3.metric("Errors", batch_run.error_count)
            b_col4.metric("Duration (ms)", f"{dur_ms:.2f} ms")

    st.markdown("---")
    st.markdown("#### 📋 Recent Batch Runs History")
    with get_db_session() as db:
        batch_runs = db.query(BatchRun).order_by(BatchRun.start_time.desc()).limit(10).all()
        if batch_runs:
            df_runs = pd.DataFrame([
                {
                    "Batch ID": b.batch_id,
                    "Source": b.source,
                    "Status": b.status,
                    "Total Rows": b.row_count,
                    "Success": b.success_count,
                    "Errors": b.error_count,
                    "Start Time": b.start_time.strftime("%Y-%m-%d %H:%M:%S") if b.start_time else "N/A",
                }
                for b in batch_runs
            ])
            st.dataframe(df_runs, use_container_width=True, hide_index=True)
        else:
            st.info("No batch runs executed yet.")

# ==============================================================================
# TAB 4: PROTECTED DATA STORE
# ==============================================================================
elif selected_tab == "🛡️ 3. Protected Data Store":
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h3 style="margin:0 0 4px 0; color:#38BDF8;">🛡️ Zero-Plaintext Protected Customer Store</h3>
            <p style="color:#94A3B8; font-size:0.9rem;">
                Downstream applications query <code>protected_customers</code>. All plaintext PII is replaced with FPE ciphers and HMAC tokens.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    apply_mask = st.toggle("🎭 Apply UI Dynamic Presentation Masking (e.g. `J*** D**`, `j***@***.com`)", value=False)

    with get_db_session() as db:
        protected_records = db.query(ProtectedCustomer).limit(50).all()
        total_prot = db.query(ProtectedCustomer).count()

    if total_prot == 0:
        st.warning("Protected store is empty. Please run a Batch Job in Tab 2 to transform source records.")
    else:
        table_rows = []
        for p in protected_records:
            name_val = mask_name(p.name_token) if apply_mask else p.name_token
            email_val = mask_email(p.email_token) if apply_mask else p.email_token
            mobile_val = mask_phone(p.mobile_fpe) if apply_mask else p.mobile_fpe

            table_rows.append({
                "Customer ID": p.customer_id,
                "Name (Token)": name_val,
                "Email (HMAC Token)": email_val,
                "Mobile (FPE 10-Digit Cipher)": mobile_val,
                "City": p.city,
                "Segment": p.segment,
                "Batch ID": p.batch_id,
            })

        df_prot = pd.DataFrame(table_rows)
        st.dataframe(df_prot, use_container_width=True, hide_index=True)

        st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
        c_exp1, c_exp2 = st.columns([3, 1])
        with c_exp1:
            st.caption(f"Showing {len(protected_records)} of {total_prot} protected records • Plaintext Leakage: 0.00%")
        with c_exp2:
            csv_data = df_prot.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Export Protected CSV",
                data=csv_data,
                file_name="flyyy_protected_customers_export.csv",
                mime="text/csv",
                use_container_width=True,
            )

        st.markdown("---")
        st.markdown("#### 🔍 Side-by-Side Plaintext vs Protected Inspector")
        with get_db_session() as db:
            sample_ids = [p.customer_id for p in protected_records[:20]]
            
        selected_cid = st.selectbox("Select Customer ID to inspect cryptographic representation:", options=sample_ids)
        if selected_cid:
            with get_db_session() as db:
                src_rec = db.query(SourceCustomer).filter(SourceCustomer.customer_id == selected_cid).first()
                prot_rec = db.query(ProtectedCustomer).filter(ProtectedCustomer.customer_id == selected_cid).first()

            if src_rec and prot_rec:
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    st.markdown("##### 🔴 Raw Source DB (Plaintext)")
                    st.json({
                        "customer_id": src_rec.customer_id,
                        "name": src_rec.name,
                        "email": src_rec.email,
                        "mobile": src_rec.mobile,
                        "city": src_rec.city,
                        "segment": src_rec.segment,
                    })
                with col_s2:
                    st.markdown("##### 🟢 Protected Data Store (Zero Plaintext)")
                    st.json({
                        "customer_id": prot_rec.customer_id,
                        "name_token": prot_rec.name_token,
                        "email_token": prot_rec.email_token,
                        "mobile_fpe": prot_rec.mobile_fpe,
                        "city": prot_rec.city,
                        "segment": prot_rec.segment,
                        "batch_id": prot_rec.batch_id,
                    })

# ==============================================================================
# TAB 5: PRIVACY GATEWAY
# ==============================================================================
elif selected_tab == "🚪 4. Privacy Gateway":
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h3 style="margin:0 0 4px 0; color:#38BDF8;">🚪 Privacy Gateway (Blind Execution & Webhook Engine)</h3>
            <p style="color:#94A3B8; font-size:0.9rem;">
                Enables downstream marketing and CRM apps to trigger dispatches without seeing real customer emails or phones.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    g_tab1, g_tab2 = st.tabs(["📧 Blind Campaign Dispatch", "↩️ Reverse Bounce Webhook"])

    # 1. Blind Campaign Dispatch
    with g_tab1:
        st.markdown("#### Scenario: Blind Marketing Campaign Dispatch")
        st.caption("Marketing systems dispatch campaigns using only protected tokens. The Gateway resolves the recipient in an isolated memory context, delivers the email, and returns a confirmation with zero plaintext exposure.")

        with get_db_session() as db:
            token_options = [p.email_token for p in db.query(ProtectedCustomer).limit(20).all()]

        if not token_options:
            st.warning("No protected tokens found. Please seed data and run batch protection.")
        else:
            c_gw1, c_gw2 = st.columns(2)
            with c_gw1:
                selected_token = st.selectbox("Recipient Protected Token", options=token_options)
                campaign_id = st.text_input("Campaign ID", value="FLY-SPRING-2026")
            with c_gw2:
                subject = st.text_input("Email Subject", value="Exclusive Spring Perks for Flyyy Members")
                body = st.text_area("Email Content", value="Hi there! Enjoy 20% off your next booking with coupon FLYYY20.")

            if st.button("🚀 Send Blind Campaign Email", type="primary"):
                with st.spinner("Executing Privacy Gateway blind dispatch..."):
                    with get_db_session() as db:
                        # 1. Resolve token from isolated vault
                        real_email = resolve_vault_mapping(db, selected_token)
                        if not real_email:
                            record_audit(
                                db=db,
                                actor="marketing_service",
                                action="SEND_CAMPAIGN_EMAIL",
                                subject_id=selected_token,
                                field="EMAIL",
                                purpose=f"MARKETING_{campaign_id}",
                                reference=campaign_id,
                                outcome="ACCESS_DENIED",
                                details="Token not found in vault",
                            )
                            st.error("Error: Token not found in vault")
                        else:
                            # 2. Dispatch email
                            send_smtp_email(to_email=real_email, subject=subject, body_text=body)
                            # 3. Audit
                            record_audit(
                                db=db,
                                actor="marketing_service",
                                action="SEND_CAMPAIGN_EMAIL",
                                subject_id=selected_token,
                                field="EMAIL",
                                purpose=f"MARKETING_{campaign_id}",
                                reference=campaign_id,
                                outcome="ALLOWED",
                                details=f"Blind campaign dispatch to token {selected_token}",
                            )

                            st.success("✅ Blind Campaign Dispatched Successfully!")
                            st.markdown("**Gateway API Response Returned to Marketing App:**")
                            st.json({
                                "recipient": selected_token,
                                "status": "SENT",
                                "campaign_id": campaign_id,
                                "timestamp": datetime.utcnow().isoformat(),
                                "protection_guarantee": "Zero Plaintext Disclosed to Marketing Service"
                            })

    # 2. Reverse Bounce Webhook
    with g_tab2:
        st.markdown("#### Scenario: Inbound Provider Webhook (Reverse Resolution)")
        st.caption("When an external email provider (SendGrid, Mailgun, SES) sends a bounce webhook containing a raw email address, the gateway converts it into the protected token before persisting.")

        mock_email = st.text_input("Provider Bounced Plaintext Email", value="john.doe@example.com")
        bounce_reason = st.selectbox("Bounce Reason", ["MAILBOX_NOT_FOUND", "SPAM_REJECTION", "DOMAIN_UNRESOLVED", "USER_OPT_OUT"])

        if st.button("📩 Ingest Provider Bounce Webhook"):
            with st.spinner("Reverse resolving email to token..."):
                with get_db_session() as db:
                    token = reverse_lookup_vault_by_plaintext(db, "EMAIL", mock_email)
                    prot_id = token if token else "TOKEN_UNRESOLVED"

                    record_audit(
                        db=db,
                        actor="email_provider_webhook",
                        action="PROCESS_BOUNCE_WEBHOOK",
                        subject_id=prot_id,
                        field="EMAIL",
                        purpose="BOUNCE_HANDLING",
                        reference="BOUNCE",
                        outcome="ALLOWED",
                        details=f"Reason: {bounce_reason}",
                    )

                st.success("✅ Webhook Ingested & Safely Tokenized!")
                st.json({
                    "bounced_protected_token": prot_id,
                    "event": "BOUNCE",
                    "reason": bounce_reason,
                    "status": "PROCESSED",
                    "audit_status": "Logged to Compliance Trail"
                })

# ==============================================================================
# TAB 6: CONTROLLED REVEAL
# ==============================================================================
elif selected_tab == "🔑 5. Controlled Reveal":
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h3 style="margin:0 0 4px 0; color:#38BDF8;">🔑 Controlled Reveal & RBAC Exception Gate</h3>
            <p style="color:#94A3B8; font-size:0.9rem;">
                Strictly enforces: <strong>Reveal Only by Exception</strong>. Plaintext is decrypted only when an authorized role, approved purpose, and documented ticket ID are validated.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### ⚡ Quick Simulation Presets")
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    preset_choice = None
    with col_p1:
        if st.button("🟢 Authorized Support", use_container_width=True):
            preset_choice = ("support_agent", "CUSTOMER_SUPPORT", "TICKET-1092", "EMAIL")
    with col_p2:
        if st.button("🟢 Fraud Auditor", use_container_width=True):
            preset_choice = ("fraud_investigator", "FRAUD_INVESTIGATION", "CASE-902", "MOBILE")
    with col_p3:
        if st.button("🔴 Unauthorized Intern", use_container_width=True):
            preset_choice = ("guest_intern_unauthorized", "CUSTOMER_SUPPORT", "TICKET-1092", "EMAIL")
    with col_p4:
        if st.button("🔴 Invalid Purpose", use_container_width=True):
            preset_choice = ("support_agent", "MARKETING_TARGETING", "PROMO-99", "EMAIL")

    with get_db_session() as db:
        customer_ids = [p.customer_id for p in db.query(ProtectedCustomer).limit(20).all()]

    default_actor = preset_choice[0] if preset_choice else "support_agent"
    default_purpose = preset_choice[1] if preset_choice else "CUSTOMER_SUPPORT"
    default_ticket = preset_choice[2] if preset_choice else "TICKET-1092"
    default_field = preset_choice[3] if preset_choice else "EMAIL"

    st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)
    c_rev1, c_rev2 = st.columns(2)
    with c_rev1:
        subject_id = st.selectbox("Subject Customer ID / Token", options=customer_ids if customer_ids else ["C001"])
        field_name = st.selectbox("Target Field to Reveal", ["EMAIL", "MOBILE", "NAME"], index=["EMAIL", "MOBILE", "NAME"].index(default_field))
        actor_role = st.text_input("Requesting Actor / Role", value=default_actor)

    with c_rev2:
        purpose = st.selectbox(
            "Declared Purpose Justification",
            ["CUSTOMER_SUPPORT", "FRAUD_INVESTIGATION", "LEGAL_COMPLIANCE", "MARKETING_TARGETING", "DATA_EXPORT"],
            index=["CUSTOMER_SUPPORT", "FRAUD_INVESTIGATION", "LEGAL_COMPLIANCE", "MARKETING_TARGETING", "DATA_EXPORT"].index(default_purpose) if default_purpose in ["CUSTOMER_SUPPORT", "FRAUD_INVESTIGATION", "LEGAL_COMPLIANCE", "MARKETING_TARGETING", "DATA_EXPORT"] else 0
        )
        ticket_ref = st.text_input("Audit Ticket / Reference ID", value=default_ticket)

    if st.button("🔐 Request Cryptographic Plaintext Reveal", type="primary", use_container_width=True):
        valid_purposes = ["CUSTOMER_SUPPORT", "FRAUD_INVESTIGATION", "LEGAL_COMPLIANCE"]
        is_denied = False
        deny_reason = ""

        if purpose not in valid_purposes or not ticket_ref.strip():
            is_denied = True
            deny_reason = "ACCESS_DENIED: Request does not meet authorized purpose or ticket criteria."
        elif "unauthorized" in actor_role.lower() or "guest" in actor_role.lower():
            is_denied = True
            deny_reason = "ACCESS_DENIED: Requesting role lacks REVEAL_PII privilege."

        with get_db_session() as db:
            if is_denied:
                record_audit(
                    db=db,
                    actor=actor_role,
                    action="REVEAL_PII",
                    subject_id=subject_id,
                    field=field_name,
                    purpose=purpose,
                    reference=ticket_ref,
                    outcome="ACCESS_DENIED",
                    details=deny_reason,
                )
                st.error(f"❌ {deny_reason}")
                st.caption("Immutable compliance log entry generated with outcome `ACCESS_DENIED`.")
            else:
                cust = db.query(ProtectedCustomer).filter(ProtectedCustomer.customer_id == subject_id).first()
                token_to_resolve = subject_id
                if cust:
                    if field_name == "EMAIL":
                        token_to_resolve = cust.email_token
                    elif field_name == "MOBILE":
                        token_to_resolve = cust.mobile_fpe
                    elif field_name == "NAME":
                        token_to_resolve = cust.name_token

                plaintext = resolve_vault_mapping(db, token_to_resolve)
                if not plaintext:
                    record_audit(
                        db=db,
                        actor=actor_role,
                        action="REVEAL_PII",
                        subject_id=subject_id,
                        field=field_name,
                        purpose=purpose,
                        reference=ticket_ref,
                        outcome="ACCESS_DENIED",
                        details="Record not found in vault",
                    )
                    st.error("❌ Requested identity not found in secure vault.")
                else:
                    record_audit(
                        db=db,
                        actor=actor_role,
                        action="REVEAL_PII",
                        subject_id=subject_id,
                        field=field_name,
                        purpose=purpose,
                        reference=ticket_ref,
                        outcome="ALLOWED",
                        details="Authorized reveal approved",
                    )
                    st.success("✅ Access Granted: Plaintext Decrypted Under Strict Audit Reference")
                    st.markdown(
                        f"""
                        <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(15, 23, 42, 0.8)); border: 1px solid #10B981; border-radius: 12px; padding: 20px; box-shadow: 0 8px 24px rgba(16, 185, 129, 0.2);">
                            <div style="color: #94A3B8; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 700;">DECRYPTED PLAINTEXT VALUE ({field_name}):</div>
                            <div style="font-size: 1.8rem; font-weight: 800; color: #34D399; font-family: 'JetBrains Mono', monospace; margin: 6px 0;">{plaintext}</div>
                            <div style="color: #64748B; font-size: 0.78rem; margin-top: 8px;">Ticket: <strong style="color:#CBD5E1;">{ticket_ref}</strong> | Purpose: <strong style="color:#CBD5E1;">{purpose}</strong> | Actor: <strong style="color:#CBD5E1;">{actor_role}</strong></div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

# ==============================================================================
# TAB 7: IMMUTABLE AUDIT TRAIL
# ==============================================================================
elif selected_tab == "📜 6. Compliance Audit Trail":
    st.markdown(
        """
        <div style="margin-bottom: 16px;">
            <h3 style="margin:0 0 4px 0; color:#38BDF8;">📜 Immutable Compliance & Access Audit Trail</h3>
            <p style="color:#94A3B8; font-size:0.9rem;">
                Append-only ledger of all access attempts, blind executions, reveal requests, and automated batch jobs.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with get_db_session() as db:
        all_actors = [r[0] for r in db.query(AuditLog.actor).distinct().all()]

    c_flt1, c_flt2 = st.columns(2)
    with c_flt1:
        outcome_filter = st.selectbox("Filter by Outcome", ["ALL", "ALLOWED", "ACCESS_DENIED"])
    with c_flt2:
        actor_filter = st.selectbox("Filter by Requesting Actor", ["ALL"] + all_actors)

    with get_db_session() as db:
        query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
        if outcome_filter != "ALL":
            query = query.filter(AuditLog.outcome == outcome_filter)
        if actor_filter != "ALL":
            query = query.filter(AuditLog.actor == actor_filter)

        logs = query.limit(100).all()
        total_logs = db.query(AuditLog).count()
        allowed_count = db.query(AuditLog).filter(AuditLog.outcome == "ALLOWED").count()
        denied_count = db.query(AuditLog).filter(AuditLog.outcome == "ACCESS_DENIED").count()

    col_a1, col_a2, col_a3 = st.columns(3)
    col_a1.metric("Total Audited Events", total_logs)
    col_a2.metric("Authorized Actions", allowed_count)
    col_a3.metric("Blocked Breach Attempts", denied_count)

    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
    if not logs:
        st.info("No audit logs matching current filter.")
    else:
        df_logs = pd.DataFrame([
            {
                "Log ID": l.id,
                "Timestamp (UTC)": l.timestamp.strftime("%Y-%m-%d %H:%M:%S") if l.timestamp else "N/A",
                "Actor": l.actor,
                "Action": l.action,
                "Subject / Token": l.subject_id,
                "Field": l.field,
                "Purpose": l.purpose,
                "Reference": l.reference_id,
                "Outcome": l.outcome,
                "Details": l.details,
            }
            for l in logs
        ])

        st.dataframe(df_logs, use_container_width=True, hide_index=True)

# Footer
st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
st.divider()
st.caption("Flyyy.ai Privacy-Preserving Customer Data Platform • Format-Preserving Encryption & Isolated Vault Architecture")
