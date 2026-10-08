import time
import streamlit as st
from google import genai
from google.genai import types

# ---- Change these for each client ----
BUSINESS_NAME = "Daazon"
# Tried in order. If one is busy or unavailable, the next one is used.
MODELS = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]
# --------------------------------------

st.set_page_config(page_title=f"{BUSINESS_NAME} Assistant", page_icon="👜")

# Load the business information the bot is allowed to use
with open("faq.txt", encoding="utf-8") as f:
    FAQ = f.read()

SYSTEM_PROMPT = f"""You are the friendly customer assistant for {BUSINESS_NAME}.
Answer ONLY using the business information below.
If the answer is not in the information, say you're not sure and suggest
contacting the business directly using the phone number listed.
Keep answers short, friendly and clear.
Never make up colors, stock, prices or details that are not listed.
When a customer seems ready to buy, tell them exactly how to order.
Reply in the same language the customer writes in.

BUSINESS INFORMATION:
{FAQ}
"""

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

st.title(f"👜 {BUSINESS_NAME} Assistant")
st.caption("Ask about our bags, prices, materials, delivery and how to order.")

# Keep the conversation in memory while the page is open
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show previous messages
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Handle a new question
if prompt := st.chat_input("Type your question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Gemini calls the assistant role "model"
    history = [
        types.Content(
            role="user" if m["role"] == "user" else "model",
            parts=[types.Part(text=m["content"])],
        )
        for m in st.session_state.messages
    ]

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = None
            last_error = None
            # Try each model, with one quick retry, until one answers
            for model in MODELS:
                for attempt in range(2):
                    try:
                        response = client.models.generate_content(
                            model=model,
                            contents=history,
                            config=types.GenerateContentConfig(
                                system_instruction=SYSTEM_PROMPT,
                                max_output_tokens=500,
                            ),
                        )
                        reply = response.text or "Sorry, I couldn't answer that. Please try again."
                        break
                    except Exception as e:
                        last_error = e
                        time.sleep(2)
                if reply:
                    break

            if not reply:
                reply = "Sorry, I'm having trouble right now. Please try again in a minute."
                st.error(f"Error details: {last_error}")
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
