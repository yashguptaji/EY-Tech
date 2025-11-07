# loan_agent_demo.py
# Author: yggy (Techathon 6.0 BFSI Challenge)
# Description: Agentic AI chatbot for Tata Capital - Personal Loan Orchestration

import gradio as gr
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
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

# Underwriting Agent
def underwrite_loan(name, amount):
    data = customers.get(name)
    if not data:
        return "❌ Customer not found."

    score, limit, salary = data["credit_score"], data["limit"], data["salary"]

    if score < 700:
        return f"❌ Loan rejected for {name} — Credit Score {score} (Below threshold)."
    elif amount <= limit:
        return f"✅ Instant Approval! Amount ₹{amount:,} is within pre-approved limit of ₹{limit:,}."
    elif amount <= 2 * limit and (amount / 12) <= 0.5 * salary:
        return f"📝 Conditional Approval for ₹{amount:,}. Please upload salary slip for verification."
    else:
        return f"❌ Request exceeds permissible limits or salary criteria. Rejected."

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

    # 1. Loan interest inquiry
    if "loan" in msg and "apply" in msg:
        return "Sure! Please share your *name* and *loan amount* (e.g., 'Rahul 250000')."

    # 2. Parse name + amount
    parts = msg.split()
    if len(parts) == 2 and parts[0].capitalize() in customers:
        name, amount = parts[0].capitalize(), int(parts[1])
        context["name"], context["amount"] = name, amount
        verify_text = verify_customer(name)
        decision_text = underwrite_loan(name, amount)
        return f"{verify_text}\n\n{decision_text}"

    # 3. Generate sanction letter
    if "generate" in msg or "sanction" in msg:
        if "name" not in context or "amount" not in context:
            return "Please provide your name and approved amount first."
        name, amount = context["name"], context["amount"]
        return generate_sanction_letter(name, amount)

    # 4. Help or fallback
    return (
        "👋 I’m your Tata Capital Loan Assistant.\n"
        "- Type: *Apply for loan*\n"
        "- Or share: *Name Amount* (e.g., Meera 400000)\n"
        "- Then type: *Generate sanction letter*"
    )

# ------------------------------
# 4️⃣ Gradio Chat Interface
# ------------------------------
chat = gr.ChatInterface(
    fn=master_agent,
    title="💬 Tata Capital AI Loan Assistant",
    description="Demo: Agentic AI orchestrating Sales, KYC, Underwriting, and Sanction Letter Generation.",
    theme="soft"
)

if __name__ == "__main__":
    chat.launch()
