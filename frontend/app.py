"""
Streamlit Multi-Page Main Application.
Features top navigation bar with Home & Upload, Overview, and Profile & History tabs.
"""
import streamlit as st
import pandas as pd
import json
from api_client import FinanceAPIClient

# Page Configuration
st.set_page_config(
    page_title="Personal Finance Agent - AI Budget Assistant",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Tokens & Modern Top Navigation Styling
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
        padding: 10px 16px;
        border-radius: 8px;
        margin-bottom: 16px;
        font-size: 0.88em;
        color: #94A3B8;
    }
    .upload-hero-card {
        background: linear-gradient(145deg, #182030 0%, #111726 100%);
        border: 2px dashed #3B82F6;
        border-radius: 16px;
        padding: 28px 24px;
        margin: 10px 0 20px 0;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
        text-align: center;
    }
    .upload-hero-icon {
        font-size: 2.8rem;
        margin-bottom: 8px;
    }
    .upload-hero-title {
        color: #F8FAFC;
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .upload-hero-desc {
        color: #94A3B8;
        font-size: 0.95rem;
        max-width: 650px;
        margin: 0 auto 16px auto;
        line-height: 1.5;
    }
    .profile-card {
        background: #182030;
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 18px;
    }
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        border-bottom: 2px solid #334155;
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: #1E293B;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 24px;
        font-size: 1.05rem;
        font-weight: 600;
        color: #94A3B8;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
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
if "upload_history" not in st.session_state:
    st.session_state.upload_history = []

api = FinanceAPIClient()
if st.session_state.token:
    api.set_token(st.session_state.token)

# Sidebar & Global Branding
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
        - 💡 **Weekly AI Recommendations**: Actionable savings guidance with strict guardrails.
        - 🔒 **DPDP Act 2023 Ready**: Granular consent, export data, and AES-256 field encryption.
        """)

        st.markdown("---")
        if st.button("🚀 Try Instant Demo Mode (No Signup Required)", type="primary", use_container_width=True):
            try:
                res = api.seed_demo()
                st.session_state.token = res["access_token"]
                st.session_state.user_email = res["email"]
                st.session_state.upload_history.append({
                    "filename": "demo_seed_transactions.csv",
                    "rows_parsed": 141,
                    "anomalies": 1,
                    "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                })
                st.success("Demo loaded! Explore Home, Overview, and Profile tabs above.")
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
    # Authenticated User View
    st.sidebar.success(f"Signed in as:\n**{st.session_state.user_email}**")
    if st.sidebar.button("Log Out", use_container_width=True):
        st.session_state.token = None
        st.session_state.user_email = None
        st.session_state.execution_id = None
        st.session_state.last_upload_res = None
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧭 Deep Dive Pages")
    st.sidebar.page_link("pages/1_Overview.py", label="Detailed Overview", icon="📊")
    st.sidebar.page_link("pages/2_Transactions.py", label="Transactions Ledger", icon="💳")
    st.sidebar.page_link("pages/3_Alerts.py", label="Anomaly Alerts", icon="🚨")
    st.sidebar.page_link("pages/4_Budget.py", label="Weekly Budgets", icon="🎯")
    st.sidebar.page_link("pages/5_Weekly_Advice.py", label="Weekly AI Advice", icon="💡")
    st.sidebar.page_link("pages/6_Agent_Trace.py", label="Agent Pipeline Trace", icon="🔍")
    st.sidebar.page_link("pages/7_Settings.py", label="Settings & DPDP Privacy", icon="⚙️")

    # =========================================================================
    # TOP NAVIGATION TABS: HOME, OVERVIEW, PROFILE & HISTORY
    # =========================================================================
    tab_home, tab_overview, tab_profile = st.tabs([
        "🏠 Home & Upload",
        "📊 Overview",
        "👤 Profile & History"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: HOME & CENTERED UPLOAD
    # -------------------------------------------------------------------------
    with tab_home:
        col_l, col_center, col_r = st.columns([1, 8, 1])
        with col_center:
            st.markdown("""
            <div class="upload-hero-card">
                <div class="upload-hero-icon">📥</div>
                <div class="upload-hero-title">Upload Bank Statement</div>
                <div class="upload-hero-desc">
                    Drop your <strong>CSV</strong> or <strong>Excel</strong> statement to execute the LangGraph multi-agent AI pipeline.
                    Normalizes rows, assigns categories, compares IQR anomaly baselines, and flags overspending in INR (Rs.).
                </div>
            </div>
            """, unsafe_allow_html=True)

            uploaded_file = st.file_uploader(
                "Choose statement file (CSV or Excel)",
                type=["csv", "xlsx", "xls"],
                key="home_file_uploader",
                help="Accepts HDFC, SBI, ICICI, Axis, or custom CSV/Excel statement sheets."
            )

            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn1:
                run_btn = st.button(
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
                        help="Download realistic synthetic 12-week INR bank statement for testing."
                    )

            if run_btn and uploaded_file is not None:
                with st.spinner("🤖 Executing LangGraph Multi-Agent Pipeline (Ingestion ➔ Category ➔ Anomaly ➔ Budget)..."):
                    try:
                        bytes_data = uploaded_file.getvalue()
                        res = api.upload_statement(bytes_data, uploaded_file.name)
                        st.session_state.execution_id = res["execution_id"]
                        st.session_state.last_upload_res = res
                        st.session_state.upload_history.append({
                            "filename": uploaded_file.name,
                            "rows_parsed": res.get("total_rows_parsed", 0),
                            "anomalies": res.get("anomalies_flagged", 0),
                            "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                        })
                        st.success(f"Processed statement! Parsed {res['total_rows_parsed']} rows with {res['anomalies_flagged']} anomalies.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Pipeline processing failed: {e}")

            if st.session_state.get("last_upload_res"):
                res = st.session_state.last_upload_res
                st.markdown("### ⚡ Latest Pipeline Results")
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Rows Processed", res.get("total_rows_parsed", 0))
                k2.metric("Deduplicated", res.get("deduplicated_count", 0))
                k3.metric("Categories Assigned", len(res.get("categories_assigned", {})))
                k4.metric("Anomalies Flagged", res.get("anomalies_flagged", 0), delta_color="inverse")

            st.markdown("---")
            st.markdown("### 🕒 Recent Activity & Transactions")
            try:
                txns = api.get_transactions()
                if txns:
                    recent_df = pd.DataFrame(txns[:5])
                    cols = [c for c in ["transaction_date", "normalized_merchant", "category", "amount", "transaction_type"] if c in recent_df.columns]
                    st.dataframe(recent_df[cols], use_container_width=True)
                else:
                    st.info("No transactions recorded yet. Drop a statement file above to begin!")
            except Exception:
                st.info("Upload a statement above to start analyzing your finances.")

    # -------------------------------------------------------------------------
    # TAB 2: OVERVIEW
    # -------------------------------------------------------------------------
    with tab_overview:
        st.subheader("📊 Financial Overview")
        st.caption("Real-time spending metrics, category breakdown, and budget targets in INR (Rs.)")

        try:
            txns = api.get_transactions()
            budgets = api.get_budgets()
            alerts = api.get_alerts()

            total_spend = sum(t["amount"] for t in txns if t.get("transaction_type") == "debit")
            pending_alerts = len([a for a in alerts if a.get("user_feedback") == "pending"])
            overbudget_count = len([b for b in budgets if b.get("is_overbudget")])

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Spending", f"Rs. {total_spend:,.2f}")
            c2.metric("Total Transactions", len(txns))
            c3.metric("Pending Anomaly Alerts", pending_alerts, delta_color="inverse")
            c4.metric("Overbudget Categories", overbudget_count, delta_color="inverse")

            st.markdown("---")

            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.markdown("#### Category Allocation (INR)")
                if txns:
                    df = pd.DataFrame(txns)
                    debits = df[df["transaction_type"] == "debit"]
                    if not debits.empty:
                        cat_totals = debits.groupby("category")["amount"].sum().reset_index()
                        cat_totals.columns = ["Category", "Amount (Rs.)"]
                        cat_totals["Category"] = cat_totals["Category"].str.title()
                        st.bar_chart(cat_totals.set_index("Category"))
                    else:
                        st.info("No debit transactions found.")
                else:
                    st.info("No transactions recorded yet.")

            with col_chart2:
                st.markdown("#### Weekly Budget vs Actual Spend")
                if budgets:
                    b_df = pd.DataFrame(budgets)
                    disp_cols = [c for c in ["category", "weekly_target_amount", "current_week_actual", "is_overbudget"] if c in b_df.columns]
                    st.dataframe(b_df[disp_cols], use_container_width=True)
                else:
                    st.info("No active budget targets set.")

        except Exception as e:
            st.error(f"Error loading overview: {e}")

    # -------------------------------------------------------------------------
    # TAB 3: PROFILE & HISTORY
    # -------------------------------------------------------------------------
    with tab_profile:
        st.subheader("👤 User Profile & Activity History")
        st.caption("Manage your profile, income & savings targets, statement upload records, and audit history.")

        col_prof_left, col_prof_right = st.columns([1, 1])

        # Left Column: Profile Details & Target Settings
        with col_prof_left:
            st.markdown('<div class="profile-card">', unsafe_allow_html=True)
            st.markdown("#### 📋 Account Information")
            try:
                prof = api.get_profile()
                st.write(f"**Email:** `{prof.get('email', st.session_state.user_email)}`")
                st.write(f"**Account Role:** `{prof.get('role', 'user')}`")
                st.write(f"**Currency Symbol:** `{prof.get('currency_symbol', 'Rs.')}`")
                st.write(f"**Age Gate:** Verified 18+")

                st.markdown("---")
                st.markdown("#### 🎯 Financial Targets")
                curr_income = float(prof.get("monthly_income") or 50000.0)
                curr_goal = float(prof.get("savings_goal") or 10000.0)

                new_income = st.number_input("Monthly Income (Rs.)", value=curr_income, step=5000.0)
                new_goal = st.number_input("Monthly Savings Goal (Rs.)", value=curr_goal, step=1000.0)

                if st.button("💾 Save Profile Targets", type="primary", use_container_width=True):
                    try:
                        api.update_profile({
                            "monthly_income": new_income,
                            "savings_goal": new_goal,
                            "currency_symbol": "Rs."
                        })
                        st.success("Financial goals updated successfully!")
                    except Exception as e:
                        st.error(f"Failed to update profile: {e}")
            except Exception as e:
                st.error(f"Unable to load profile: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

            # Data Portability & Privacy Card
            st.markdown('<div class="profile-card">', unsafe_allow_html=True)
            st.markdown("#### 🔒 DPDP Data Portability")
            st.write("Export your complete personal financial ledger in standardized JSON format.")
            if st.button("📦 Export Full Personal Data (JSON)", use_container_width=True):
                try:
                    export_data = api.export_data()
                    st.download_button(
                        label="⬇️ Download Data Package (.json)",
                        data=json.dumps(export_data, indent=2),
                        file_name=f"finance_data_export_{st.session_state.user_email}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Export failed: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

        # Right Column: History (Upload History & Audit Log)
        with col_prof_right:
            st.markdown('<div class="profile-card">', unsafe_allow_html=True)
            st.markdown("#### 📥 Statement Ingestion History")
            if st.session_state.upload_history:
                hist_df = pd.DataFrame(st.session_state.upload_history)
                st.dataframe(hist_df, use_container_width=True)
            else:
                st.info("No files uploaded in this session yet.")
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="profile-card">', unsafe_allow_html=True)
            st.markdown("#### 📜 Audit & Activity Log")
            try:
                activity_logs = api.get_activity_history()
                if activity_logs:
                    act_df = pd.DataFrame(activity_logs)
                    act_df = act_df[["timestamp", "action", "resource"]]
                    st.dataframe(act_df, use_container_width=True)
                else:
                    st.info("No audit logs recorded.")
            except Exception:
                # Fallback to display current session info
                st.write(f"- **Current Session:** Active")
                st.write(f"- **Signed In As:** `{st.session_state.user_email}`")
                st.write(f"- **Encryption:** AES-256 enabled at rest")
            st.markdown('</div>', unsafe_allow_html=True)
