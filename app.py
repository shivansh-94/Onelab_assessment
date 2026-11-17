import streamlit as st
import pandas as pd
import plotly.express as px

from modules.data_generator import generate_sample_data
from modules.reconciliation import reconcile, validate_data
from modules.ai_insights import generate_insights
from modules.report_generator import build_pdf_report

st.set_page_config(
    page_title="ReconAI | Payment Reconciliation",
    page_icon="💳",
    layout="wide"
)

st.markdown("""
<style>
    .main {background-color: #f5f7fb;}
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    div[data-testid="stMetric"] {
        background: white; padding: 16px; border-radius: 12px;
        border: 1px solid #e7ebf2;
    }
    .hero {
        background: linear-gradient(110deg, #10213d, #1e4d78);
        padding: 25px; border-radius: 16px; color: white; margin-bottom: 18px;
    }
    .hero h1 {color: white; margin: 0;}
    .hero p {color: #d8e7f5; margin-bottom: 0;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>💳 ReconAI</h1>
  <p>Find the gaps. Understand the differences. Balance the books.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("ReconAI")
    page = st.radio("Navigation", ["Overview", "Upload & Reconcile", "AI Insights", "About"])
    st.divider()
    st.caption("Assessment demo • Synthetic data supported")

if "payments" not in st.session_state:
    p, s = generate_sample_data()
    st.session_state.payments = p
    st.session_state.settlements = s
    st.session_state.results = None
    st.session_state.summary = None

if page == "Overview":
    st.subheader("Month-end reconciliation overview")
    st.write("Start with the generated assessment dataset or upload your own payment and bank files.")
    if st.session_state.results is None:
        st.info("No reconciliation has been run yet. Open **Upload & Reconcile** and click Run Reconciliation.")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Payment rows loaded", len(st.session_state.payments))
        with c2:
            st.metric("Bank rows loaded", len(st.session_state.settlements))
    else:
        summary = st.session_state.summary
        cols = st.columns(4)
        cols[0].metric("Payment rows", summary["platform_rows"])
        cols[1].metric("Bank rows", summary["bank_rows"])
        cols[2].metric("Matched", summary["matched"])
        exception_count = len(st.session_state.results[st.session_state.results.status != "MATCHED"])
        cols[3].metric("Exceptions", exception_count)

        st.markdown("### Discrepancy breakdown")
        labels = {
            "Delayed settlement": summary["delayed"],
            "Rounding difference": summary["rounding"],
            "Duplicate transaction": summary["duplicate_transactions"],
            "Duplicate settlement": summary["duplicate_settlements"],
            "Unmatched refund": summary["unmatched_refunds"],
            "Missing settlement": summary["missing_settlements"],
            "Unmatched bank": summary["unmatched_bank"],
        }
        chart_df = pd.DataFrame({"Category": list(labels.keys()), "Count": list(labels.values())})
        chart_df = chart_df[chart_df["Count"] > 0]
        if not chart_df.empty:
            st.plotly_chart(px.bar(chart_df, x="Category", y="Count", color="Category",
                                   title="Detected discrepancy categories"), use_container_width=True)
        else:
            st.success("No discrepancies were detected.")

        st.markdown("### Reconciliation results")
        st.dataframe(st.session_state.results, use_container_width=True, hide_index=True)

elif page == "Upload & Reconcile":
    st.subheader("Load datasets")
    st.caption("Upload CSV files or use the built-in synthetic assessment dataset.")
    col1, col2 = st.columns(2)
    with col1:
        payment_file = st.file_uploader("Payment transactions CSV", type=["csv"], key="payments_upload")
    with col2:
        settlement_file = st.file_uploader("Bank settlements CSV", type=["csv"], key="settlements_upload")

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("Load synthetic assessment data", use_container_width=True):
            p, s = generate_sample_data()
            st.session_state.payments, st.session_state.settlements = p, s
            st.session_state.results = None
            st.session_state.summary = None
            st.success("Synthetic datasets loaded.")
    with b2:
        st.download_button("Download sample payments CSV",
                           st.session_state.payments.to_csv(index=False).encode("utf-8"),
                           "sample_transactions.csv", "text/csv", use_container_width=True)
    with b3:
        st.download_button("Download sample settlements CSV",
                           st.session_state.settlements.to_csv(index=False).encode("utf-8"),
                           "sample_settlements.csv", "text/csv", use_container_width=True)

    if payment_file is not None:
        try:
            st.session_state.payments = pd.read_csv(payment_file, dtype=str).fillna("")
        except Exception as exc:
            st.error(f"Could not read payment CSV: {exc}")
    if settlement_file is not None:
        try:
            st.session_state.settlements = pd.read_csv(settlement_file, dtype=str).fillna("")
        except Exception as exc:
            st.error(f"Could not read settlement CSV: {exc}")

    st.markdown("### Dataset preview")
    pcol, scol = st.columns(2)
    with pcol:
        st.write("**Payment transactions**")
        st.dataframe(st.session_state.payments.head(8), use_container_width=True, hide_index=True)
    with scol:
        st.write("**Bank settlements**")
        st.dataframe(st.session_state.settlements.head(8), use_container_width=True, hide_index=True)

    tolerance = st.number_input("Per-transaction rounding tolerance (₹)", min_value=0.0,
                                max_value=1.0, value=0.02, step=0.01, format="%.2f")
    aggregate_threshold = st.number_input("Aggregate rounding threshold (₹)", min_value=0.01,
                                          max_value=10.0, value=0.03, step=0.01, format="%.2f")

    if st.button("▶ Run Reconciliation", type="primary", use_container_width=True):
        errors = validate_data(st.session_state.payments, st.session_state.settlements)
        if errors:
            for error in errors:
                st.error(error)
        else:
            results, summary = reconcile(
                st.session_state.payments,
                st.session_state.settlements,
                rounding_tolerance=f"{tolerance:.2f}",
                aggregate_rounding_threshold=f"{aggregate_threshold:.2f}"
            )
            st.session_state.results = results
            st.session_state.summary = summary
            st.success("Reconciliation completed.")
            st.rerun()

    if st.session_state.results is not None:
        st.markdown("### Results")
        results = st.session_state.results
        statuses = ["All"] + sorted(results["status"].dropna().unique().tolist())
        selected = st.selectbox("Filter by status", statuses)
        filtered = results if selected == "All" else results[results["status"] == selected]
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        st.download_button("Download reconciliation CSV",
                           results.to_csv(index=False).encode("utf-8"),
                           "reconciliation_results.csv", "text/csv")
        pdf = build_pdf_report(st.session_state.summary, results)
        st.download_button("Download PDF report", pdf, "reconai_report.pdf", "application/pdf")

elif page == "AI Insights":
    st.subheader("AI Financial Insights")
    if st.session_state.results is None:
        st.info("Run reconciliation first to generate verified insights.")
    else:
        st.markdown(generate_insights(st.session_state.results, st.session_state.summary))
        st.caption("These explanations are generated from deterministic reconciliation results. No LLM API is required in this starter version.")

elif page == "About":
    st.subheader("About ReconAI")
    st.write("""
    ReconAI is an AI-assisted payment reconciliation prototype built for the Onelab AI Fitness Assessment.

    It compares payment-platform records with bank settlement records and highlights:
    - Settlements crossing the month boundary.
    - Cumulative rounding differences.
    - Duplicate transaction and settlement entries.
    - Refunds without a valid original transaction.

    **Important:** This is an assessment prototype using synthetic/demo data. It is not a production banking ledger or an accounting system.
    """)
    st.markdown("### Assumptions")
    st.write("""
    - Currency is INR.
    - Dates are interpreted in the same local timezone.
    - Transaction IDs are the primary matching key.
    - Small rounding differences are evaluated with configurable tolerances.
    - A delayed settlement is a timing difference, not automatically a loss.
    - Refunds are separate records and must reference an existing original transaction.
    """)
