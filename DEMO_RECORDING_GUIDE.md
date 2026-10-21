# 2-Minute Demo Video Recording Guide (demo.mp4)

Per the Capstone Brief (Page 14):
> **Demo video (Max 2 minutes):** A question answered from the documents with a follow-up, plus one handover or "I don't know".

---

## 🎙️ Recommended 2-Minute Script for Your Demo Video

### Part 1: Introduction (15 seconds)
- **You (to camera/screen):**  
  *"Hello! This is our demonstration of VoiceOps 2026, an automated customer support agent for ZentroMart powered by Gnani.ai STT/TTS and Document Grounded RAG."*

---

### Part 2: Question Answered from Documents with Follow-Up (60 seconds)

1. **Turn 1 (Greeting & Identification):**
   - **You (speaking to mic):** *"Hello, I need help with my order."*
   - **Agent (Voice Reply):** *"Hello! I am ZentroMart's AI assistant. To check details for your order, please provide your order ID."*
   - *(Points to note: Agent identifies as an AI assistant per STY-1).*

2. **Turn 2 (Order ID & Verification Gate):**
   - **You (speaking):** *"My order number is 8978 2837."*
   - **Agent (Voice Reply):** *"Got your order number 8978 2837. For your security, please confirm the last 4 digits of your registered phone number or your delivery pincode."*
   - *(Points to note: Identity verification gate IDV-2 withholding order details).*

3. **Turn 3 (Caller Identity Verification):**
   - **You (speaking):** *"The last four digits are 4533."*
   - **Agent (Voice Reply):** *"Thank you! Your identity has been verified. I can see your order 8978 2837. How can I assist you with this order?"*

4. **Turn 4 (Follow-Up Question from Documents):**
   - **You (speaking):** *"How long will a refund take if I return it?"*
   - **Agent (Voice Reply):** *"Refunds to your ZentroMart Wallet are instant, within 2 hours of initiation."*
   - *(Points to note: Coreference memory knowing it refers to the same order and grounds the wallet policy).*

---

### Part 3: Handover or "I Don't Know" (35 seconds)

- **You (speaking):** *"I demand 500 rupees compensation right now for the delay."*
- **Agent (Voice Reply):** *"I apologize, but our policy does not allow direct cash compensation. I have created a ticket and escalated this to our team for review."*
- *(Points to note: Refuses out-of-policy demand, creates a ticket via tools, and hands over to human).*

---

### Part 4: Conclusion (10 seconds)
- **You:** *"All voice responses are powered by Gnani TTS (timbre-v2.5, Kaveri) and transcribed via Gnani STT. Thank you!"*
