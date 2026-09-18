# Flyyy Privacy-Preserving Customer Data Platform (CDP)

> **Core Principle:** *Protected by Default. Reveal or Use Plaintext Only by Exception.*

An end-to-end prototype of a Privacy-Preserving Customer Data Platform engineered to protect Personally Identifiable Information (PII) before it reaches downstream analytics, marketing, CRM, or support environments.

---

## 🏛️ Architecture Overview

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

---

## 🚀 Quickstart Guide

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- *(Optional)* **Docker & Docker Compose** for MySQL 8.0 & Mailpit

---

### Step 1: Start Backend (FastAPI)
```powershell
cd d:\P_1\flyyy-cdp\backend
python -m pip install -r requirements.txt
python -m app.main
```
The FastAPI backend server will run at `http://127.0.0.1:8000` with interactive Swagger docs at `http://127.0.0.1:8000/docs`.

---

### Step 2: Start Streamlit App (All-in-One Dashboard)
```powershell
cd d:\P_1\flyyy-cdp
python -m streamlit run streamlit_app.py
```
The full interactive Streamlit dashboard will be live at `http://localhost:8501`.

---

### Step 3 (Alternative): Start React Dashboard
In a new terminal:
```powershell
cd d:\P_1\flyyy-cdp\frontend
npm install
npm run dev
```
The React dashboard will be live at `http://localhost:5173`.

---

### Step 4 (Optional): Start Mailpit SMTP & MySQL via Docker
```powershell
cd d:\P_1\flyyy-cdp
docker compose up -d
```
- **Mailpit Web UI:** `http://localhost:8025` (View dispatched test emails)
- **MySQL 8.0:** `localhost:3306` (Database: `flyyy_cdp`, User: `cdp_admin`)

---

## 🧪 Running Automated Tests

Run the complete test suite (Unit tests for FPE, AES-GCM Vault security, Deterministic Tokenization, and Full E2E Demonstration flow):

```powershell
cd d:\P_1\flyyy-cdp\backend
python -m pytest -v
```

---

## 📋 Step-by-Step Demonstration Walkthrough

1. **Seed & Inspect Source Data:** Open `http://localhost:5173`, click **"Reset & Seed Data"** to load 50 customer records into `source_customers`.
2. **Run PII Discovery:** On the **1. PII Discovery** tab, click **"Run PII Discovery"** to view detected entity types and confidence scores.
3. **Configure Policy & Run Batch:** Go to **2. Policy & Batch**, review the FPE / Tokenization rules, and click **"Trigger Batch Run"**.
4. **Inspect Protected Data Store:** Switch to **3. Protected Data**. Observe that:
   - 10-digit phone numbers are encrypted to 10-digit numbers using FPE.
   - Emails and names are replaced with deterministic tokens (`EMAIL_...`, `NAME_...`).
   - Export CSV button proves 0% plaintext leakage in database exports.
5. **Test Blind Campaign Dispatch:** Go to **4. Privacy Gateway**, pick a recipient token, and click **"Send Campaign"**. The marketing app receives `{"status": "SENT"}` without ever seeing the real email address.
6. **Simulate Provider Bounce:** On the same tab, simulate a provider bounce for `john@example.com`. The gateway safely converts it to the protected token.
7. **Test Controlled Reveal:** Go to **5. Controlled Reveal**:
   - Try the **Unauthorized Role** preset $\to$ returns `403 ACCESS_DENIED`.
   - Try the **Authorized Support** preset $\to$ returns plaintext value with ticket reference.
8. **Inspect Audit Trail:** Go to **6. Audit Trail** to view the real-time compliance log showing every access, reveal, and batch operation with its timestamp and outcome.

---

## 🔒 Security Specifications

- **Format-Preserving Encryption (FPE):** Implemented using standard `pyffx` FF3-1/FF1 algorithms. Preserves numeric domain and exact digit length.
- **Tokenization:** Deterministic HMAC-SHA256 tokens with configurable salt for cross-batch referential integrity.
- **Vault Protection:** AES-256-GCM authenticated encryption for mapping storage.
- **Log Hygiene:** Plaintext PII is strictly excluded from application, batch, and error logs.
