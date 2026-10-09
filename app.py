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
        box = st.empty()
        box.markdown("_Typing..._")
        reply = None
        last_error = None

        # Try each model until one answers. For each, first try with minimal
        # "thinking" (fastest); if a model doesn't support that, try without it.
        for model in MODELS:
            for fast in (True, False):
                config = types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=500,
                    thinking_config=types.ThinkingConfig(thinking_level="MINIMAL") if fast else None,
                )
                try:
                    text = ""
                    # Stream the answer so words appear as they are written
                    for chunk in client.models.generate_content_stream(
                        model=model, contents=history, config=config
                    ):
                        if chunk.text:
                            text += chunk.text
                            box.markdown(text + "▌")
                    if text:
                        reply = text
                        break
                except Exception as e:
                    last_error = e
                    if text:  # stream broke midway: keep what we have
                        reply = text
                        break
            if reply:
                break
            time.sleep(1)

        if not reply:
            reply = "Sorry, I'm having trouble right now. Please try again in a minute."
            st.error(f"Error details: {last_error}")
        box.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
