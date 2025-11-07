# loan_agent_dashboard.py
# Author: yggy (Techathon 6.0 BFSI Challenge)
# Description: Agentic AI chatbot with confidence levels + live dashboard (Gradio)

import gradio as gr
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd
import random
import os

# ------------------------------
# 1️⃣ Synthetic Customer Dataset
# ------------------------------
customers = {
    "Rahul": {"kyc": True, "credit_score": 780, "limit": 300000, "salary": 60000},
    "Meera": {"kyc": True, "credit_score": 710, "limit": 400000, "salary": 80000},
    "Arjun": {"kyc": False, "credit_score": 620, "limit": 200000, "salary": 45000},
    "Simran": {"kyc": True, "credit_score": 745, "limit": 350000, "salary": 72000},
    "Ravi": {"kyc": True, "credit_score": 680, "limit": 250000, "salary": 50000}
}

# Dashboard data storage
results = []  # list of dicts

# ------------------------------
# 2️⃣ Worker Agents
# ------------------------------

# Verification Agent
def verify_customer(name):
    data = customers.get(name)
    if not data:
        return f"❌ No records found for {name}. Please recheck spelling."
    if data["kyc"]:
        return f"✅ KYC verified for {name}. Proceeding to credit evaluation."
    return f"⚠️ KYC pending or invalid for {name}. Please update details before proceeding."


# Underwriting Agent with Confidence Level
def underwrite_loan(name, amount):
    data = customers.get(name)
    if not data:
        return "❌ Customer not found."

    score, limit, salary = data["credit_score"], data["limit"], data["salary"]
    confidence = random.randint(85, 99)  # simulate AI confidence %

    # Determine decision
    if score < 700:
        decision = f"❌ Loan rejected for {name} — Credit Score {score} (Below threshold)."
        status = "Rejected"
    elif amount <= limit:
        decision = f"✅ Instant Approval! ₹{amount:,} within pre-approved limit of ₹{limit:,}."
        status = "Approved"
    elif amount <= 2 * limit and (amount / 12) <= 0.5 * salary:
        decision = f"📝 Conditional Approval for ₹{amount:,}. Please upload salary slip."
        status = "Conditional"
    else:
        decision = f"❌ Request exceeds permissible limits or salary criteria."
        status = "Rejected"

    # Save result for dashboard
    results.append({
        "Customer": name,
        "Amount": amount,
        "Credit Score": score,
        "Confidence (%)": confidence,
        "Decision": status
    })

    return f"{decision}\n🤖 *AI Confidence Level:* {confidence}%"


# Sanction Letter Agent
def generate_sanction_letter(name, amount, tenure=24, rate=11.5):
    file_path = f"{name}_sanction_letter.pdf"
    c = canvas.Canvas(file_path, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(180, 750, "Tata Capital Sanction Letter")
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, f"Name: {name}")
    c.drawString(100, 680, f"Approved Loan Amount: ₹{amount:,}")
    c.drawString(100, 660, f"Tenure: {tenure} months | Interest Rate: {rate}% p.a.")
    c.drawString(100, 640, "Congratulations on your loan approval!")
    c.drawString(100, 620, "Please visit the nearest Tata Capital branch for final signing.")
    c.save()
    return f"📄 Sanction letter generated successfully for {name}.\nDownload: {os.path.abspath(file_path)}"


# ------------------------------
# 3️⃣ Master Agent Logic
# ------------------------------
context = {}

def master_agent(message, history):
    msg = message.strip().lower()

    # Step 1: Apply for loan
    if "loan" in msg and "apply" in msg:
        return "Sure! Please share your *name* and *loan amount* (e.g., 'Rahul 250000')."

    # Step 2: Parse name + amount
    parts = msg.split()
    if len(parts) == 2 and parts[0].capitalize() in customers:
        name, amount = parts[0].capitalize(), int(parts[1])
        context["name"], context["amount"] = name, amount
        verify_text = verify_customer(name)
        decision_text = underwrite_loan(name, amount)
        return f"{verify_text}\n\n{decision_text}"

    # Step 3: Generate sanction letter
    if "generate" in msg or "sanction" in msg:
        if "name" not in context or "amount" not in context:
            return "Please provide your name and approved amount first."
        name, amount = context["name"], context["amount"]
        return generate_sanction_letter(name, amount)

    # Step 4: Dashboard request
    if "dashboard" in msg:
        return "📊 Switch to the *Dashboard* tab to see current approval statistics."

    # Fallback
    return (
        "👋 I’m your Tata Capital Loan Assistant.\n"
        "- Type: *Apply for loan*\n"
        "- Or share: *Name Amount* (e.g., Meera 400000)\n"
        "- Then type: *Generate sanction letter*\n"
        "- Or say: *Show dashboard*"
    )


# ------------------------------
# 4️⃣ Dashboard Logic
# ------------------------------
def dashboard_view():
    if not results:
        return pd.DataFrame([{"Message": "No applications processed yet."}])
    df = pd.DataFrame(results)
    return df


# ------------------------------
# 5️⃣ Build Gradio Multi-Tab Interface
# ------------------------------
with gr.Blocks(theme="soft") as demo:
    gr.Markdown("## 💬 Tata Capital AI Loan Assistant\nSimulating Agentic AI orchestration: Sales, Verification, Underwriting & Sanction Letter Generation")

    with gr.Tab("🧠 Chat Assistant"):
        chat = gr.ChatInterface(fn=master_agent)

    with gr.Tab("📊 Dashboard"):
        gr.Markdown("### Loan Decision Summary")
        dashboard = gr.DataFrame(
            value=dashboard_view(),
            interactive=False,
            wrap=True,
            label="Processed Applications"
        )
        refresh_btn = gr.Button("🔄 Refresh Dashboard")

        # Refresh updates dashboard view
        refresh_btn.click(fn=dashboard_view, outputs=dashboard)

demo.launch()
