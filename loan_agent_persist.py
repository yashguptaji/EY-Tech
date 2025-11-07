# loan_agent_persistent.py
# Author: yggy (Techathon 6.0 BFSI Challenge)
# Description: Agentic AI chatbot + dashboard + external data persistence

import gradio as gr
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd
import random
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key=os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file!")

# Configure Gemini
genai.configure(api_key=api_key)

def ask_gemini(prompt):
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text
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

DATA_FILE = "loan_applications.csv"

# Initialize persistent file if missing
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=[
        "Customer", "Amount", "Credit Score", "Confidence (%)", "Decision"
    ]).to_csv(DATA_FILE, index=False)

# ------------------------------
# 2️⃣ Worker Agents
# ------------------------------

# Verification Agent
def verify_customer(name):
    data = customers.get(name)
    if not data:
        return f"❌ No records found for {name}."
    if data["kyc"]:
        return f"✅ KYC verified for {name}. Proceeding to credit evaluation."
    return f"⚠️ KYC pending or invalid for {name}. Please update details before proceeding."


# Underwriting Agent (writes to CSV)
def underwrite_loan(name, amount):
    data = customers.get(name)
    if not data:
        return "❌ Customer not found."

    score, limit, salary = data["credit_score"], data["limit"], data["salary"]
    confidence = random.randint(85, 99)

    if score < 700:
        decision = f"❌ Loan rejected for {name} — Credit Score {score}."
        status = "Rejected"
    elif amount <= limit:
        decision = f"✅ Instant Approval! ₹{amount:,} within limit ₹{limit:,}."
        status = "Approved"
    elif amount <= 2 * limit and (amount / 12) <= 0.5 * salary:
        decision = f"📝 Conditional Approval for ₹{amount:,}. Upload salary slip."
        status = "Conditional"
    else:
        decision = f"❌ Request exceeds permissible limits or salary criteria."
        status = "Rejected"

    # Append record to CSV
    new_row = pd.DataFrame([{
        "Customer": name,
        "Amount": amount,
        "Credit Score": score,
        "Confidence (%)": confidence,
        "Decision": status
    }])
    df = pd.read_csv(DATA_FILE)
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

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

# def master_agent(message, history):
#     msg = message.strip().lower()

#     if "loan" in msg and "apply" in msg:
#         return "Sure! Please share your *name* and *loan amount* (e.g., 'Rahul 250000')."

#     parts = msg.split()
#     if len(parts) == 2 and parts[0].capitalize() in customers:
#         name, amount = parts[0].capitalize(), int(parts[1])
#         context["name"], context["amount"] = name, amount
#         verify_text = verify_customer(name)
#         decision_text = underwrite_loan(name, amount)
#         return f"{verify_text}\n\n{decision_text}"

#     if "generate" in msg or "sanction" in msg:
#         if "name" not in context or "amount" not in context:
#             return "Please provide your name and approved amount first."
#         name, amount = context["name"], context["amount"]
#         return generate_sanction_letter(name, amount)

#     if "dashboard" in msg:
#         return "📊 Switch to the *Dashboard* tab to view current analytics."

#     return (
#         "👋 I’m your Tata Capital Loan Assistant.\n"
#         "- Type: *Apply for loan*\n"
#         "- Or share: *Name Amount* (e.g., Meera 400000)\n"
#         "- Then type: *Generate sanction letter*\n"
#         "- Or say: *Show dashboard*"
#     )
def master_agent(message, history):
    msg = message.strip().lower()

    # Handle structured loan flows
    if "apply" in msg and "loan" in msg:
        return "Sure! Please share your name and loan amount (e.g., 'Rahul 250000')."
    elif "kyc" in msg or "verify" in msg:
        return "Our system automatically verifies KYC once you share your name."
    elif "generate" in msg or "sanction" in msg:
        if "name" not in context or "amount" not in context:
            return "Please provide your name and amount first."
        name, amount = context["name"], context["amount"]
        return generate_sanction_letter(name, amount)

    # Everything else → Gemini handles tone / free Q&A
    try:
        response = ask_gemini(
            f"You are Tata Capital’s friendly loan advisor. "
            f"User said: {message}. Respond conversationally and helpfully "
            f"without committing to any financial decision."
        )
        return response
    except Exception as e:
        return f"(Gemini error: {e})"


# ------------------------------
# 4️⃣ Dashboard Logic
# ------------------------------
def dashboard_view():
    if not os.path.exists(DATA_FILE) or os.stat(DATA_FILE).st_size == 0:
        return pd.DataFrame([{"Message": "No applications processed yet."}])
    df = pd.read_csv(DATA_FILE)
    return df


# ------------------------------
# 5️⃣ Build Gradio Interface
# ------------------------------
with gr.Blocks(theme="soft") as demo:
    gr.Markdown("## 💬 Tata Capital AI Loan Assistant (with Persistent Data Storage)")

    with gr.Tab("🤖 Chat Assistant"):
        chat = gr.ChatInterface(fn=master_agent)

    with gr.Tab("📊 Dashboard"):
        gr.Markdown("### Loan Decision Summary (from stored CSV)")
        dashboard = gr.DataFrame(value=dashboard_view(), interactive=False, label="Processed Applications")
        refresh_btn = gr.Button("🔄 Refresh Dashboard")
        refresh_btn.click(fn=dashboard_view, outputs=dashboard)

demo.launch()
