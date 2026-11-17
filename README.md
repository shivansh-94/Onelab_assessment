# ReconAI – Payment Reconciliation

A Streamlit assessment prototype that compares payment-platform transactions with bank settlements.

## Features
- Synthetic data generation with assessment scenarios
- CSV upload and validation
- Transaction-level reconciliation
- Delayed settlement, rounding, duplicate, and orphan-refund detection
- Interactive dashboard and charts
- CSV and PDF exports
- Deterministic financial explanations without requiring an API key

## Setup

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Install packages:
```bash
pip install -r requirements.txt
```

Run:
```bash
streamlit run app.py
```

## Tests

```bash
pytest -q
```

## CSV schemas

Payment CSV columns:
`transaction_id, customer_id, transaction_date, transaction_amount, transaction_status, transaction_type, original_transaction_id`

Settlement CSV columns:
`settlement_id, transaction_id, settlement_date, settlement_amount, settlement_status, bank_reference`

## Important assumptions and limitations
- INR is used as the currency.
- Transaction ID is the primary matching key.
- The sample data is synthetic.
- This is an assessment prototype, not a production accounting ledger.
- Production deployment would require robust bank file ingestion, authentication, audit logs, timezone/currency handling, settlement fee models, chargeback handling, and human review workflows.
