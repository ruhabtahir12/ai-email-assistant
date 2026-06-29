
import streamlit as st
from groq import Groq
import PyPDF2
from io import StringIO
import os

st.set_page_config(page_title="AI Email Reply Assistant", page_icon="✉️", layout="wide")

# Load API key from Streamlit Secrets
api_key = st.secrets["GROQ_API_KEY"]

st.title("✉️ AI Email Reply Assistant")
st.markdown("**Analyze email → Generate Summary, Sentiment, Subject & 4 Tone Replies**")

# Sidebar
with st.sidebar:
    st.subheader("Reply Language")
    language = st.selectbox(
        "Translate replies to:",
        ["English", "Urdu", "Arabic", "French", "Spanish", "German", "Chinese"]
    )
    st.markdown("---")
    st.subheader("Reply History")
    if "history" not in st.session_state:
        st.session_state.history = []

    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history[-5:])):
            st.caption(f"Session {len(st.session_state.history) - i}: {item['subject'][:40]}...")
    else:
        st.caption("No history yet.")

    if st.button("Clear History"):
        st.session_state.history = []
        st.success("History cleared!")

    st.markdown("---")
    st.caption("✅ Summary | Sentiment | Subject | 4 Tones | Export | History | Translation")

# File Upload + Text Input
uploaded_file = st.file_uploader("Upload Email File (.txt or .pdf)", type=["txt", "pdf"])
email_input = st.text_area("Or Paste Email Text Here:", height=200)

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        email_text = ""
        for page in pdf_reader.pages:
            email_text += page.extract_text()
    else:
        email_text = StringIO(uploaded_file.getvalue().decode("utf-8")).read()
    email_input = email_text

if st.button("Analyze & Generate All Replies", type="primary", use_container_width=True):
    if not email_input or not email_input.strip():
        st.error("Please paste email or upload file")
    else:
        with st.spinner("AI is analyzing email and generating responses..."):
            try:
                client = Groq(api_key=api_key)

                # Summary
                summary = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": f"Summarize this email in 2-3 sentences:\n\n{email_input}"}]
                ).choices[0].message.content

                # Sentiment
                sentiment_raw = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": f"Analyze the sentiment of this email. Reply with only one word: Positive, Negative, or Neutral.\n\n{email_input}"}]
                ).choices[0].message.content.strip()

                # Subject
                subject = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": f"Generate a professional subject line for a reply to this email:\n\n{email_input}"}]
                ).choices[0].message.content

                # Display Summary + Sentiment + Subject
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader("📋 Email Summary")
                    st.info(summary)
                with col2:
                    st.subheader("😊 Sentiment")
                    if "Positive" in sentiment_raw:
                        st.success(f"😊 {sentiment_raw}")
                    elif "Negative" in sentiment_raw:
                        st.error(f"😟 {sentiment_raw}")
                    else:
                        st.warning(f"😐 {sentiment_raw}")

                st.subheader("✉️ Suggested Subject Line")
                st.success(subject)

                # Generate 4 Tone Replies
                tones = ["Professional", "Friendly", "Formal", "Concise"]
                st.subheader("🔹 Replies in 4 Tones")
                all_replies = {}

                for tone in tones:
                    lang_instruction = f"Translate the reply to {language}." if language != "English" else ""
                    prompt = f"""Write a {tone.lower()} reply to this email.
Also correct any grammar or spelling errors in the reply.
{lang_instruction}

Email:
{email_input}

Make it helpful, polite, and appropriate for business communication."""

                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        max_tokens=650
                    )
                    reply = response.choices[0].message.content
                    all_replies[tone] = reply

                    st.subheader(f"🔸 {tone} Tone")
                    st.write(reply)

                    st.download_button(
                        label=f"⬇️ Download {tone} Reply",
                        data=reply,
                        file_name=f"{tone.lower()}_reply.txt",
                        mime="text/plain",
                        key=f"download_{tone}"
                    )

                    with st.expander(f"📋 Copy {tone} Reply"):
                        st.code(reply, language=None)

                    st.divider()

                # Export ALL replies
                st.subheader("📦 Export All Replies")
                all_text = f"EMAIL SUMMARY:\n{summary}\n\nSENTIMENT: {sentiment_raw}\n\nSUGGESTED SUBJECT: {subject}\n\n"
                all_text += "\n\n".join([f"--- {tone.upper()} TONE ---\n{reply}" for tone, reply in all_replies.items()])

                st.download_button(
                    label="⬇️ Download All Replies as .txt",
                    data=all_text,
                    file_name="all_email_replies.txt",
                    mime="text/plain",
                    key="download_all"
                )

                # Save to History
                st.session_state.history.append({
                    "subject": subject,
                    "summary": summary,
                    "sentiment": sentiment_raw,
                    "replies": all_replies
                })

            except Exception as e:
                st.error(f"Error: {str(e)}")

# Show History Section
if st.session_state.get("history"):
    st.markdown("---")
    st.subheader("🕘 Previous Sessions")
    for i, item in enumerate(reversed(st.session_state.history)):
        with st.expander(f"Session {len(st.session_state.history) - i} — {item['subject'][:60]}"):
            st.write(f"**Summary:** {item['summary']}")
            st.write(f"**Sentiment:** {item['sentiment']}")
            for tone, reply in item["replies"].items():
                st.write(f"**{tone}:** {reply[:150]}...")

st.caption("AI Email Reply Assistant — All Requirements Completed")
