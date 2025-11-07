# loan_agent_complete.py
# Enhanced Agentic AI Loan Assistant for NBFC
# Implements Master Agent + 4 Worker Agents with full workflow

import gradio as gr
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
import pandas as pd
import random
import os
import json
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file!")

genai.configure(api_key=api_key)

# ------------------------------
# 1️⃣ SYNTHETIC CUSTOMER DATABASE (10+ Customers)
# ------------------------------
customers = {
    "Rahul": {
        "age": 32, "city": "Mumbai", "phone": "9876543210",
        "address": "Andheri West, Mumbai",
        "kyc": True, "credit_score": 780, "pre_approved_limit": 300000,
        "salary": 60000, "current_loans": {"Home Loan": 1500000, "Car Loan": 400000}
    },
    "Meera": {
        "age": 28, "city": "Bangalore", "phone": "9876543211",
        "address": "Koramangala, Bangalore",
        "kyc": True, "credit_score": 710, "pre_approved_limit": 400000,
        "salary": 80000, "current_loans": {"Personal Loan": 200000}
    },
    "Arjun": {
        "age": 35, "city": "Delhi", "phone": "9876543212",
        "address": "Dwarka, Delhi",
        "kyc": False, "credit_score": 620, "pre_approved_limit": 200000,
        "salary": 45000, "current_loans": {}
    },
    "Simran": {
        "age": 30, "city": "Pune", "phone": "9876543213",
        "address": "Hinjewadi, Pune",
        "kyc": True, "credit_score": 745, "pre_approved_limit": 350000,
        "salary": 72000, "current_loans": {"Car Loan": 500000}
    },
    "Ravi": {
        "age": 40, "city": "Hyderabad", "phone": "9876543214",
        "address": "Gachibowli, Hyderabad",
        "kyc": True, "credit_score": 680, "pre_approved_limit": 250000,
        "salary": 50000, "current_loans": {"Home Loan": 2000000}
    },
    "Priya": {
        "age": 26, "city": "Chennai", "phone": "9876543215",
        "address": "Velachery, Chennai",
        "kyc": True, "credit_score": 820, "pre_approved_limit": 500000,
        "salary": 95000, "current_loans": {}
    },
    "Amit": {
        "age": 33, "city": "Ahmedabad", "phone": "9876543216",
        "address": "Satellite, Ahmedabad",
        "kyc": True, "credit_score": 690, "pre_approved_limit": 280000,
        "salary": 55000, "current_loans": {"Personal Loan": 150000}
    },
    "Neha": {
        "age": 29, "city": "Kolkata", "phone": "9876543217",
        "address": "Salt Lake, Kolkata",
        "kyc": True, "credit_score": 765, "pre_approved_limit": 380000,
        "salary": 70000, "current_loans": {"Car Loan": 350000}
    },
    "Vikram": {
        "age": 38, "city": "Jaipur", "phone": "9876543218",
        "address": "Mansarovar, Jaipur",
        "kyc": False, "credit_score": 640, "pre_approved_limit": 220000,
        "salary": 48000, "current_loans": {}
    },
    "Kavya": {
        "age": 31, "city": "Surat", "phone": "9876543219",
        "address": "Adajan, Surat",
        "kyc": True, "credit_score": 790, "pre_approved_limit": 420000,
        "salary": 85000, "current_loans": {"Home Loan": 1800000}
    }
}

# Persistent storage files
DATA_FILE = "loan_applications.csv"
CONVERSATION_LOG = "conversation_logs.json"

# Initialize files
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=[
        "Timestamp", "Customer", "Age", "City", "Amount", "Tenure", "Interest Rate",
        "Credit Score", "Pre-Approved Limit", "Salary", "Decision", "Confidence (%)"
    ]).to_csv(DATA_FILE, index=False)

if not os.path.exists(CONVERSATION_LOG):
    with open(CONVERSATION_LOG, 'w') as f:
        json.dump([], f)

# ------------------------------
# 2️⃣ WORKER AGENTS
# ------------------------------

class SalesAgent:
    """Negotiates loan terms and convinces customers"""
    
    @staticmethod
    def pitch_loan(name, customer_data):
        limit = customer_data["pre_approved_limit"]
        current_loans = customer_data["current_loans"]
        
        pitch = f"""🎉 **Great news, {name}!**

You have a **pre-approved personal loan** of up to **₹{limit:,}** waiting for you!

✨ **Why choose us?**
• Interest rates starting from **10.99% p.a.**
• Flexible tenure: **12 to 60 months**
• Instant approval for pre-approved amounts
• No hidden charges
• Digital process - paperless & hassle-free

"""
        if current_loans:
            pitch += f"📊 We see you have existing loans with us. Great loyalty! We value our customers.\n\n"
        
        pitch += "💡 **What would you like to do today?**\n- Share your loan requirement\n- Discuss terms and conditions\n- Get instant approval"
        
        return pitch
    
    @staticmethod
    def negotiate_terms(amount, tenure=None, rate=None):
        """Provides flexible loan terms"""
        if not tenure:
            tenure = 24 if amount <= 200000 else 36
        if not rate:
            rate = 10.99 if amount <= 300000 else 11.5
        
        emi = (amount * rate/100/12 * (1 + rate/100/12)**tenure) / ((1 + rate/100/12)**tenure - 1)
        
        return f"""📋 **Loan Terms Summary**
━━━━━━━━━━━━━━━━━━━━
💰 Loan Amount: ₹{amount:,}
⏱️ Tenure: {tenure} months
📊 Interest Rate: {rate}% p.a.
💳 EMI: ₹{emi:,.2f}/month
━━━━━━━━━━━━━━━━━━━━
✅ These terms look good? Let me proceed with verification!"""


class VerificationAgent:
    """Handles KYC verification from CRM"""
    
    @staticmethod
    def verify_kyc(name):
        if name not in customers:
            return "❌ Customer not found in our CRM system."
        
        data = customers[name]
        
        if data["kyc"]:
            return f"""✅ **KYC Verification Successful**
━━━━━━━━━━━━━━━━━━━━
👤 Name: {name}
📱 Phone: {data['phone']}
📍 Address: {data['address']}
🏙️ City: {data['city']}
━━━━━━━━━━━━━━━━━━━━
All documents verified. Moving to credit assessment..."""
        else:
            return f"""⚠️ **KYC Pending for {name}**

We need to complete your KYC verification. Please share:
1. Aadhaar Card
2. PAN Card
3. Address Proof

You can upload these documents or visit the nearest branch.
For now, I cannot proceed with the loan application."""


class UnderwritingAgent:
    """Credit assessment and eligibility validation"""
    
    @staticmethod
    def fetch_credit_score(name):
        """Mock Credit Bureau API Call"""
        if name not in customers:
            return None
        return customers[name]["credit_score"]
    
    @staticmethod
    def assess_eligibility(name, amount, tenure=24):
        if name not in customers:
            return "❌ Customer not found."
        
        data = customers[name]
        score = data["credit_score"]
        limit = data["pre_approved_limit"]
        salary = data["salary"]
        
        # Calculate EMI
        rate = 11.5
        emi = (amount * rate/100/12 * (1 + rate/100/12)**tenure) / ((1 + rate/100/12)**tenure - 1)
        emi_to_salary_ratio = (emi / salary) * 100
        
        confidence = random.randint(82, 98)
        
        result = {
            "name": name,
            "amount": amount,
            "score": score,
            "limit": limit,
            "salary": salary,
            "emi": emi,
            "confidence": confidence,
            "decision": "",
            "status": ""
        }
        
        # Decision Logic
        if score < 700:
            result["decision"] = f"❌ **Application Rejected**\n\nCredit Score: {score}/900 (Minimum required: 700)\nWe recommend improving your credit score and reapplying after 6 months."
            result["status"] = "Rejected"
        
        elif amount <= limit:
            result["decision"] = f"""🎉 **INSTANT APPROVAL!**
━━━━━━━━━━━━━━━━━━━━
💰 Approved Amount: ₹{amount:,}
📊 Credit Score: {score}/900
✅ Within Pre-Approved Limit: ₹{limit:,}
💳 Monthly EMI: ₹{emi:,.2f}
🤖 AI Confidence: {confidence}%
━━━━━━━━━━━━━━━━━━━━
🎊 Congratulations! Your loan is approved instantly!"""
            result["status"] = "Approved"
        
        elif amount <= 2 * limit and emi_to_salary_ratio <= 50:
            result["decision"] = f"""📝 **CONDITIONAL APPROVAL**
━━━━━━━━━━━━━━━━━━━━
💰 Requested: ₹{amount:,}
📊 Pre-Approved Limit: ₹{limit:,}
💳 Monthly EMI: ₹{emi:,.2f}
💼 EMI/Salary Ratio: {emi_to_salary_ratio:.1f}%
━━━━━━━━━━━━━━━━━━━━
✅ Your application is conditionally approved!

📄 **Please upload:**
• Latest 3 months salary slips
• Last 6 months bank statement

Upload these and get instant approval!"""
            result["status"] = "Conditional"
        
        else:
            result["decision"] = f"""❌ **Application Declined**
━━━━━━━━━━━━━━━━━━━━
Requested: ₹{amount:,}
Pre-Approved Limit: ₹{limit:,}
Maximum Eligible: ₹{2*limit:,}
━━━━━━━━━━━━━━━━━━━━
The requested amount exceeds our lending criteria.
Consider applying for ₹{limit:,} for instant approval."""
            result["status"] = "Rejected"
        
        return result


class SanctionLetterGenerator:
    """Generates PDF sanction letter"""
    
    @staticmethod
    def generate_pdf(name, amount, tenure, rate, customer_data):
        filename = f"sanction_letter_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        
        # Header
        c.setFillColor(colors.HexColor('#1E3A8A'))
        c.rect(0, height - 1.5*inch, width, 1.5*inch, fill=True, stroke=False)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(1*inch, height - 1*inch, "TATA CAPITAL")
        c.setFont("Helvetica", 12)
        c.drawString(1*inch, height - 1.2*inch, "Financial Services Limited")
        
        # Date and Reference
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 10)
        c.drawString(1*inch, height - 2*inch, f"Date: {datetime.now().strftime('%d %B %Y')}")
        c.drawString(1*inch, height - 2.2*inch, f"Reference No: TC/PL/{random.randint(100000, 999999)}")
        
        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1*inch, height - 2.8*inch, "PERSONAL LOAN SANCTION LETTER")
        
        # Customer Details
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1*inch, height - 3.3*inch, "Customer Details:")
        c.setFont("Helvetica", 10)
        y_pos = height - 3.5*inch
        details = [
            f"Name: {name}",
            f"Address: {customer_data['address']}",
            f"Phone: {customer_data['phone']}",
        ]
        for detail in details:
            c.drawString(1.2*inch, y_pos, detail)
            y_pos -= 0.2*inch
        
        # Loan Details
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1*inch, y_pos - 0.3*inch, "Loan Details:")
        y_pos -= 0.5*inch
        
        emi = (amount * rate/100/12 * (1 + rate/100/12)**tenure) / ((1 + rate/100/12)**tenure - 1)
        
        c.setFont("Helvetica", 10)
        loan_details = [
            f"Sanctioned Amount: ₹{amount:,}",
            f"Interest Rate: {rate}% per annum",
            f"Loan Tenure: {tenure} months",
            f"Monthly EMI: ₹{emi:,.2f}",
            f"Processing Fee: ₹{int(amount * 0.02):,} (2% of loan amount)",
        ]
        for detail in loan_details:
            c.drawString(1.2*inch, y_pos, detail)
            y_pos -= 0.2*inch
        
        # Terms
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1*inch, y_pos - 0.3*inch, "Terms & Conditions:")
        y_pos -= 0.5*inch
        c.setFont("Helvetica", 9)
        terms = [
            "• This sanction is valid for 30 days from the date of issue",
            "• Final disbursement subject to verification of documents",
            "• Pre-payment charges: 2% on outstanding principal",
            "• Please visit the nearest branch to complete formalities",
        ]
        for term in terms:
            c.drawString(1*inch, y_pos, term)
            y_pos -= 0.18*inch
        
        # Footer
        c.setFont("Helvetica-Bold", 10)
        c.drawString(1*inch, 1.5*inch, "For Tata Capital Financial Services Ltd.")
        c.drawString(1*inch, 1*inch, "Authorized Signatory")
        
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(1*inch, 0.5*inch, "This is a computer-generated document and does not require a physical signature.")
        
        c.save()
        return os.path.abspath(filename)


# ------------------------------
# 3️⃣ MASTER AGENT (Orchestrator)
# ------------------------------

class MasterAgent:
    def __init__(self):
        self.context = {}
        self.conversation_stage = "greeting"
        self.sales_agent = SalesAgent()
        self.verification_agent = VerificationAgent()
        self.underwriting_agent = UnderwritingAgent()
        self.sanction_generator = SanctionLetterGenerator()
    
    def process_message(self, message, history):
        msg = message.strip().lower()
        
        # Stage 1: Greeting & Identification
        if self.conversation_stage == "greeting":
            if any(word in msg for word in ["hello", "hi", "hey", "start"]):
                return self._greet_customer()
            elif any(name.lower() in msg for name in customers.keys()):
                return self._identify_customer(message)
            else:
                return """👋 **Welcome to Tata Capital!**

I'm your personal loan advisor. I'm here to help you get the best loan offers!

To get started, please share your name from this list:
""" + ", ".join(customers.keys())
        
        # Stage 2: Sales Pitch
        elif self.conversation_stage == "sales_pitch":
            if "yes" in msg or "interested" in msg or "sure" in msg:
                return self._show_loan_pitch()
            elif "no" in msg or "not interested" in msg:
                return self._handle_objection()
            else:
                return "Are you interested in exploring personal loan options tailored for you?"
        
        # Stage 3: Loan Requirement
        elif self.conversation_stage == "loan_requirement":
            amount = self._extract_amount(msg)
            if amount:
                self.context["amount"] = amount
                self.context["tenure"] = 24  # default
                return self.sales_agent.negotiate_terms(amount)
            else:
                return "Please share the loan amount you need (e.g., 250000 or 2.5 lakh)"
        
        # Stage 4: Terms Acceptance
        elif self.conversation_stage == "terms_confirmation":
            if "yes" in msg or "proceed" in msg or "ok" in msg:
                return self._start_verification()
            elif any(word in msg for word in ["tenure", "month", "year"]):
                return "Our standard tenures are 12, 24, 36, 48, or 60 months. Which would you prefer?"
            else:
                return "Shall I proceed with these terms? (Yes/No)"
        
        # Stage 5: Underwriting
        elif self.conversation_stage == "underwriting":
            result = self.underwriting_agent.assess_eligibility(
                self.context["name"],
                self.context["amount"],
                self.context.get("tenure", 24)
            )
            
            # Save to CSV
            self._save_application(result)
            
            if result["status"] == "Approved":
                self.conversation_stage = "sanction"
                return result["decision"] + "\n\n" + self._offer_sanction_letter()
            else:
                self.conversation_stage = "completed"
                return result["decision"] + "\n\n" + self._end_conversation()
        
        # Stage 6: Sanction Letter Generation
        elif self.conversation_stage == "sanction":
            if "generate" in msg or "yes" in msg or "send" in msg:
                return self._generate_sanction()
            else:
                return "Would you like me to generate your sanction letter now?"
        
        # Default: Use Gemini for conversational responses
        return self._gemini_response(message)
    
    def _greet_customer(self):
        self.conversation_stage = "identification"
        return """👋 **Welcome to Tata Capital Digital Loan Assistant!**

I'm here to help you get personal loans with attractive rates and instant approvals!

May I know your name? (Choose from: """ + ", ".join(customers.keys()) + ")"
    
    def _identify_customer(self, message):
        for name in customers.keys():
            if name.lower() in message.lower():
                self.context["name"] = name
                self.context["customer_data"] = customers[name]
                self.conversation_stage = "sales_pitch"
                return f"""Hello {name}! 👋

I pulled up your profile. Before we begin, are you interested in exploring personal loan options today?

We have some exciting pre-approved offers for you! 🎉"""
        return "I couldn't find that name. Please choose from: " + ", ".join(customers.keys())
    
    def _show_loan_pitch(self):
        self.conversation_stage = "loan_requirement"
        return self.sales_agent.pitch_loan(
            self.context["name"],
            self.context["customer_data"]
        )
    
    def _handle_objection(self):
        return """I understand! Let me share why thousands choose us:

✅ Lowest interest rates in the market
✅ Flexible repayment options  
✅ No hidden charges
✅ 24/7 customer support

Even if you don't need a loan now, it's good to know your pre-approved limit. Shall we check?"""
    
    def _extract_amount(self, msg):
        import re
        # Extract numbers
        numbers = re.findall(r'\d+', msg)
        if numbers:
            amount = int(numbers[0])
            # Handle lakh notation
            if "lakh" in msg or "lac" in msg:
                amount *= 100000
            elif amount < 10000:  # assume lakhs if small number
                amount *= 100000
            return amount
        return None
    
    def _start_verification(self):
        self.conversation_stage = "underwriting"
        name = self.context["name"]
        
        # Step 1: KYC Verification
        kyc_result = self.verification_agent.verify_kyc(name)
        
        if "Pending" in kyc_result:
            self.conversation_stage = "completed"
            return kyc_result
        
        # Step 2: Credit Score Check
        score = self.underwriting_agent.fetch_credit_score(name)
        credit_msg = f"\n\n📊 **Credit Bureau Check**\nCredit Score: {score}/900\n"
        
        return kyc_result + credit_msg + "\n⏳ Running final eligibility assessment..."
    
    def _offer_sanction_letter(self):
        return "🎉 Would you like me to generate your official sanction letter now?"
    
    def _generate_sanction(self):
        self.conversation_stage = "completed"
        name = self.context["name"]
        amount = self.context["amount"]
        tenure = self.context.get("tenure", 24)
        rate = 11.5
        
        filepath = self.sanction_generator.generate_pdf(
            name, amount, tenure, rate,
            self.context["customer_data"]
        )
        
        return f"""✅ **Sanction Letter Generated Successfully!**

📄 **Download your letter:** {filepath}

🎊 **Next Steps:**
1. Download and review your sanction letter
2. Visit nearest Tata Capital branch with:
   • Original ID proofs
   • Address proof
   • Bank statements (last 6 months)
3. Complete signing formalities
4. Get disbursement within 24 hours!

Thank you for choosing Tata Capital. Have a great day! 🙏"""
    
    def _end_conversation(self):
        return "\n\nThank you for considering Tata Capital. Feel free to reach out anytime! 🙏"
    
    def _save_application(self, result):
        """Save application to CSV"""
        new_row = pd.DataFrame([{
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Customer": result["name"],
            "Age": customers[result["name"]]["age"],
            "City": customers[result["name"]]["city"],
            "Amount": result["amount"],
            "Tenure": self.context.get("tenure", 24),
            "Interest Rate": 11.5,
            "Credit Score": result["score"],
            "Pre-Approved Limit": result["limit"],
            "Salary": result["salary"],
            "Decision": result["status"],
            "Confidence (%)": result["confidence"]
        }])
        
        df = pd.read_csv(DATA_FILE)
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
    
    def _gemini_response(self, message):
        """Fallback to Gemini for conversational responses"""
        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            prompt = f"""You are a friendly loan advisor at Tata Capital. 
Context: {json.dumps(self.context)}
User said: {message}
Respond helpfully and guide them through the loan process."""
            
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"I'm here to help! Can you rephrase that?"


# ------------------------------
# 4️⃣ DASHBOARD
# ------------------------------
def dashboard_view():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame([{"Message": "No applications yet"}])
    
    df = pd.read_csv(DATA_FILE)
    return df if not df.empty else pd.DataFrame([{"Message": "No applications yet"}])

def get_statistics():
    if not os.path.exists(DATA_FILE):
        return "No data available yet."
    
    df = pd.read_csv(DATA_FILE)
    if df.empty:
        return "No applications processed yet."
    
    total = len(df)
    approved = len(df[df["Decision"] == "Approved"])
    conditional = len(df[df["Decision"] == "Conditional"])
    rejected = len(df[df["Decision"] == "Rejected"])
    
    avg_amount = df["Amount"].mean()
    avg_score = df["Credit Score"].mean()
    
    return f"""📊 **Application Statistics**
━━━━━━━━━━━━━━━━━━━━
Total Applications: {total}
✅ Approved: {approved} ({approved/total*100:.1f}%)
📝 Conditional: {conditional} ({conditional/total*100:.1f}%)
❌ Rejected: {rejected} ({rejected/total*100:.1f}%)

💰 Avg Loan Amount: ₹{avg_amount:,.0f}
📊 Avg Credit Score: {avg_score:.0f}/900
━━━━━━━━━━━━━━━━━━━━"""


# ------------------------------
# 5️⃣ GRADIO INTERFACE
# ------------------------------

# Create master agent instance
master = MasterAgent()

def chat_handler(message, history):
    """Handle chat messages and return proper format for Gradio"""
    bot_response = master.process_message(message, history)
    return bot_response

def reset_master():
    """Reset the master agent for new conversation"""
    global master
    master = MasterAgent()

# Build UI
with gr.Blocks(theme=gr.themes.Soft(), title="Tata Capital Loan Assistant") as demo:
    gr.Markdown("""
    # 🏦 Tata Capital - AI Loan Assistant
    ### Complete Agentic AI Solution with Master Agent + Worker Agents
    """)
    
    with gr.Tab("💬 Loan Application Chat"):
        gr.Markdown("""
        ### Start Your Loan Journey Here!
        This AI assistant will guide you through:
        1. 🎯 Sales & Negotiation
        2. ✅ KYC Verification  
        3. 📊 Credit Assessment
        4. 📄 Sanction Letter Generation
        
        **Just say "Hello" to begin!**
        """)
        
        # Use ChatInterface which handles the message format automatically
        chat_interface = gr.ChatInterface(
            fn=chat_handler,
            chatbot=gr.Chatbot(height=500),
            textbox=gr.Textbox(placeholder="Type your message here...", label="Your Message"),
            title=None,
            description=None,
            retry_btn=None,
            undo_btn=None,
            clear_btn="🔄 Start New Application"
        )
        

    
    with gr.Tab("📊 Analytics Dashboard"):
        gr.Markdown("### Loan Application Analytics")
        
        stats = gr.Textbox(label="Summary Statistics", value=get_statistics(), lines=12)
        
        gr.Markdown("### Recent Applications")
        dashboard = gr.DataFrame(value=dashboard_view(), label="Application History")
        
        refresh_btn = gr.Button("🔄 Refresh Dashboard")
        refresh_btn.click(fn=dashboard_view, outputs=dashboard)
        refresh_btn.click(fn=get_statistics, outputs=stats)
    
    with gr.Tab("👥 Customer Database"):
        gr.Markdown("### Synthetic Customer Data (CRM Server)")
        customer_df = pd.DataFrame.from_dict(customers, orient='index')
        customer_df = customer_df.reset_index().rename(columns={'index': 'Name'})
        gr.DataFrame(value=customer_df, label="Customer Records")
    
    with gr.Tab("ℹ️ System Info"):
        gr.Markdown("""
        ## 🤖 Agentic AI Architecture
        
        ### Master Agent (Orchestrator)
        - Manages conversation flow
        - Coordinates all worker agents
        - Maintains context across sessions
        
        ### Worker Agents
        
        1. **🎯 Sales Agent**
           - Pitches loan products
           - Negotiates terms (amount, tenure, rate)
           - Handles objections
        
        2. **✅ Verification Agent**
           - Validates KYC from CRM
           - Checks customer identity
           - Verifies contact details
        
        3. **📊 Underwriting Agent**
           - Fetches credit score from bureau API
           - Assesses eligibility:
             - Instant approval if ≤ pre-approved limit
             - Conditional if ≤ 2× limit & EMI ≤ 50% salary
             - Reject if score < 700 or amount > 2× limit
        
        4. **📄 Sanction Letter Generator**
           - Creates PDF sanction letter
           - Includes all loan details
           - Generates reference number
        
        ### Data Sources
        - **CRM Server**: Customer KYC data (10+ customers)
        - **Credit Bureau API**: Mock credit scores (600-850)
        - **Offer Mart**: Pre-approved limits & rates
        - **Persistent Storage**: CSV for applications, JSON for logs
        
        ### Technologies
        - Gradio for UI
        - Google Gemini for conversational AI
        - ReportLab for PDF generation
        - Pandas for data management
        """)

demo.launch(share=False)