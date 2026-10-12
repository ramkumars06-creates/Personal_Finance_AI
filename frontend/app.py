"""
Streamlit Multi-Page Main Application.
Manages session state, authentication, sidebar navigation, modern UI/UX styling,
and centered bank statement upload experience.
"""
import streamlit as st
import pandas as pd
from api_client import FinanceAPIClient

# Page Configuration
st.set_page_config(
    page_title="Personal Finance Agent - AI Budget Assistant",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Tokens & Modern Styling
st.markdown("""
<style>
    .main {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .stMetric {
        background: linear-gradient(135deg, #1E2640 0%, #0F172A 100%);
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .disclaimer-banner {
        background-color: #1E293B;
        border-left: 4px solid #3B82F6;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 24px;
        font-size: 0.9em;
        color: #94A3B8;
    }
    .upload-hero-card {
        background: linear-gradient(145deg, #182030 0%, #111726 100%);
        border: 2px dashed #3B82F6;
        border-radius: 16px;
        padding: 32px 28px;
        margin: 12px 0 24px 0;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        text-align: center;
    }
    .upload-hero-icon {
        font-size: 3rem;
        margin-bottom: 12px;
    }
    .upload-hero-title {
        color: #F8FAFC;
        font-size: 1.6rem;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .upload-hero-desc {
        color: #94A3B8;
        font-size: 0.95rem;
        max-width: 650px;
        margin: 0 auto 18px auto;
        line-height: 1.5;
    }
    .quick-stat-card {
        background: #1E2640;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if "token" not in st.session_state:
    st.session_state.token = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "execution_id" not in st.session_state:
    st.session_state.execution_id = None
if "last_upload_res" not in st.session_state:
    st.session_state.last_upload_res = None

api = FinanceAPIClient()
if st.session_state.token:
    api.set_token(st.session_state.token)

# Sidebar & Global Header
st.sidebar.title("💰 Finance Agent")
st.sidebar.caption("Agentic AI Budget & Spending Assistant")

# Always show disclaimer
st.markdown("""
<div class="disclaimer-banner">
    ℹ️ <strong>Financial Awareness Disclaimer:</strong> This tool supports financial awareness and planning; it is not a replacement for a financial adviser. No recommendation is executed automatically.
</div>
""", unsafe_allow_html=True)

if not st.session_state.token:
    # Public Landing Page & Auth Tabs
    st.title("Personal Finance Agent: Agentic AI Assistant")
    st.subheader("Observe ➔ Understand ➔ Detect ➔ Recommend ➔ Improve")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("""
        ### Features Built For Public Users in India:
        - 📊 **Automatic Transaction Categorization**: Hybrid keyword rules & LLM fallback.
        - 🚨 **Explainable Anomaly Alerts**: Z-Score & statistical signal triggers.
        - 🎯 **Budget-vs-Actual Tracking**: Weekly target tracking in INR (Rs.).
        - 💡 **Weekly AI Recommendations**: Deterministic Python recommendations with plain-language explanations.
        - 🔒 **DPDP Act 2023 Ready**: Granular consent, export data, and AES-256 encrypted storage.
        """)

        st.markdown("---")
        if st.button("🚀 Try Instant Demo Mode (No Signup Required)", type="primary", use_container_width=True):
            try:
                res = api.seed_demo()
                st.session_state.token = res["access_token"]
                st.session_state.user_email = res["email"]
                st.success("Demo environment loaded! Select any page from the sidebar to explore.")
                st.rerun()
            except Exception as e:
                st.error(f"Error loading demo: {e}")

    with col2:
        tab_login, tab_signup = st.tabs(["Log In", "Sign Up"])

        with tab_login:
            st.write("### Access Account")
            login_email = st.text_input("Email Address", key="login_email")
            login_pass = st.text_input("Password", type="password", key="login_pass")
            if st.button("Log In", use_container_width=True):
                try:
                    res = api.login(login_email, login_pass)
                    st.session_state.token = res["access_token"]
                    st.session_state.user_email = res["email"]
                    st.success("Logged in successfully!")
                    st.rerun()
                except Exception as e:
                    st.error("Login failed. Check your email or password.")

        with tab_signup:
            st.write("### Create Public Account")
            signup_email = st.text_input("Email Address", key="signup_email")
            signup_pass = st.text_input("Password (min 8 chars)", type="password", key="signup_pass")
            age_check = st.checkbox("I confirm I am 18 years of age or older (Mandatory Age Gate)", value=True)
            consent_store = st.checkbox("Consent to store transactions for budget analysis", value=True)
            consent_llm = st.checkbox("Consent to AI processing for categorization & advice", value=True)

            if st.button("Create Account & Sign In", use_container_width=True):
                if not age_check:
                    st.error("You must confirm you are 18+ to register.")
                else:
                    try:
                        res = api.signup({
                            "email": signup_email,
                            "password": signup_pass,
                            "age_confirmed": age_check,
                            "transaction_storage_consent": consent_store,
                            "llm_processing_consent": consent_llm
                        })
                        st.session_state.token = res["access_token"]
                        st.session_state.user_email = res["email"]
                        st.success("Account created successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Signup failed: {e}")
else:
    # User is Authenticated -> Modern Centered Upload & Dashboard Experience
    st.sidebar.success(f"Signed in as:\n**{st.session_state.user_email}**")
    if st.sidebar.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.session_state.user_email = None
        st.session_state.execution_id = None
        st.session_state.last_upload_res = None
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧭 Quick Navigation")
    st.sidebar.page_link("pages/1_Overview.py", label="Financial Overview", icon="📊")
    st.sidebar.page_link("pages/2_Transactions.py", label="Transactions Ledger", icon="💳")
    st.sidebar.page_link("pages/3_Alerts.py", label="Anomaly Alerts", icon="🚨")
    st.sidebar.page_link("pages/4_Budget.py", label="Weekly Budgets", icon="🎯")
    st.sidebar.page_link("pages/5_Weekly_Advice.py", label="Weekly AI Advice", icon="💡")
    st.sidebar.page_link("pages/6_Agent_Trace.py", label="Agent Pipeline Trace", icon="🔍")
    st.sidebar.page_link("pages/7_Settings.py", label="Account & Privacy Settings", icon="⚙️")

    # =========================================================================
    # CENTERED FRONT HERO SECTION: FILE UPLOADER
    # =========================================================================
    col_spacer_l, col_center_hero, col_spacer_r = st.columns([1, 8, 1])

    with col_center_hero:
        st.markdown("""
        <div class="upload-hero-card">
            <div class="upload-hero-icon">📥</div>
            <div class="upload-hero-title">Upload Bank Statement</div>
            <div class="upload-hero-desc">
                Drag and drop your <strong>CSV</strong> or <strong>Excel</strong> statement below to run the autonomous
                multi-agent AI pipeline. Handles normalization, automated categorization, IQR anomaly detection,
                and weekly budget analysis in INR (Rs.).
            </div>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Select bank statement file (CSV, XLSX, XLS)",
            type=["csv", "xlsx", "xls"],
            key="center_file_uploader",
            help="Upload statement exports from HDFC, SBI, ICICI, Axis, or custom CSV/Excel sheets."
        )

        # Centered Action Buttons
        col_btn1, col_btn2 = st.columns([3, 1])

        with col_btn1:
            run_pipeline_clicked = st.button(
                "🚀 Run AI Agent Pipeline",
                type="primary",
                use_container_width=True,
                disabled=(uploaded_file is None)
            )

        with col_btn2:
            sample_csv_data = b""
            try:
                with open("data/sample_transactions.csv", "rb") as f:
                    sample_csv_data = f.read()
            except Exception:
                pass

            if sample_csv_data:
                st.download_button(
                    label="📄 Sample CSV",
                    data=sample_csv_data,
                    file_name="sample_statement.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Download a synthetic 12-week INR bank statement to test immediately."
                )

        # Handle Pipeline Execution
        if run_pipeline_clicked and uploaded_file is not None:
            with st.spinner("🤖 Executing LangGraph Multi-Agent Pipeline (Ingestion ➔ Category ➔ Anomaly ➔ Budget ➔ Advisor)..."):
                try:
                    bytes_data = uploaded_file.getvalue()
                    res = api.upload_statement(bytes_data, uploaded_file.name)
                    st.session_state.execution_id = res["execution_id"]
                    st.session_state.last_upload_res = res
                    st.success(f"Statement processed successfully! Parsed {res['total_rows_parsed']} rows with {res['anomalies_flagged']} anomalies flagged.")
                    st.balloons()
                except Exception as e:
                    st.error(f"Pipeline processing failed: {e}")

        # Show Real-time Execution Summary when upload succeeds
        if st.session_state.get("last_upload_res"):
            res = st.session_state.last_upload_res
            st.markdown("### ⚡ Multi-Agent Pipeline Results")

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Rows Processed", res.get("total_rows_parsed", 0))
            k2.metric("Deduplicated", res.get("deduplicated_count", 0))
            k3.metric("Categories Assigned", len(res.get("categories_assigned", {})))
            k4.metric("Anomalies Flagged", res.get("anomalies_flagged", 0), delta_color="inverse")

            st.markdown("#### 🎯 Explore Results")
            nav1, nav2, nav3, nav4 = st.columns(4)
            with nav1:
                st.page_link("pages/1_Overview.py", label="View Overview Chart", icon="📊")
            with nav2:
                st.page_link("pages/2_Transactions.py", label="View Transactions", icon="💳")
            with nav3:
                st.page_link("pages/3_Alerts.py", label="Review Anomaly Alerts", icon="🚨")
            with nav4:
                st.page_link("pages/5_Weekly_Advice.py", label="View AI Advice", icon="💡")

        st.markdown("---")

        # Live Quick Financial Snapshot
        st.markdown("### 📈 Current Account Snapshot")
        try:
            txns = api.get_transactions()
            alerts = api.get_alerts()
            budgets = api.get_budgets()

            total_spend = sum(t["amount"] for t in txns if t.get("transaction_type") == "debit")
            pending_alerts = len([a for a in alerts if a.get("user_feedback") == "pending"])
            overbudget = len([b for b in budgets if b.get("is_overbudget")])

            stat1, stat2, stat3 = st.columns(3)
            stat1.metric("Total Recorded Spend", f"Rs. {total_spend:,.2f}")
            stat2.metric("Total Transactions", len(txns))
            stat3.metric("Pending Anomaly Alerts", pending_alerts, delta_color="inverse")

            if txns:
                st.markdown("#### 🕒 Recent Transactions")
                recent_df = pd.DataFrame(txns[:5])
                if not recent_df.empty and "transaction_date" in recent_df.columns:
                    display_cols = [c for c in ["transaction_date", "normalized_merchant", "category", "amount", "transaction_type"] if c in recent_df.columns]
                    st.dataframe(recent_df[display_cols], use_container_width=True)
        except Exception:
            st.info("No transactions on file yet. Upload a statement above to get started!")
