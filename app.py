# Full updated Streamlit spam classifier app with styled Start/Stop button

import streamlit as st 
import streamlit.components.v1 as components
import pickle
import string
import re
import time
import nltk
import requests
import matplotlib.pyplot as plt
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

nltk.download('punkt')
nltk.download('stopwords')
ps = PorterStemmer()

st.set_page_config(page_title="Spam Classifier", layout="wide")

# Load model and vectorizer
tfidf = pickle.load(open('vectorizer.pkl', 'rb'))
model = pickle.load(open('model.pkl', 'rb'))

def transform_text(text):
    text = text.lower()
    text = nltk.word_tokenize(text)
    y = [i for i in text if i.isalnum()]
    y = [ps.stem(i) for i in y if i not in stopwords.words('english') and i not in string.punctuation]
    return " ".join(y)

def highlight_keywords(msg):
    keywords = {
        "free": "🤑 **FREE**",
        "win": "🏆 **WIN**",
        "urgent": "⚠️ **URGENT**",
        "offer": "🍱 **OFFER**",
        "cash": "💰 **CASH**",
        "prize": "🎉 **PRIZE**",
        "claim": "📥 **CLAIM**"
    }
    for word, emoji_word in keywords.items():
        msg = re.sub(fr"\b{word}\b", emoji_word, msg, flags=re.IGNORECASE)
    return msg

@st.cache_data
def fetch_messages():
    try:
        resp = requests.get("https://gist.githubusercontent.com/your-username/your-gist-id/raw/sms_spam_10.json")
        resp.raise_for_status()
        return resp.json().get("messages", [])
    except:
        return [
            "You have won a FREE ticket to Bahamas! Claim now!",
            "Reminder: Your meeting is scheduled for 3PM.",
            "Get cash back on your next recharge offer!",
            "This is a limited time offer. Act now!",
            "Don't forget to submit the report by tomorrow.",
            "URGENT: Your account will be suspended if not updated.",
            "Hi, are you coming to the party tonight?",
            "Win ₹10,000 now just by answering 3 questions!",
            "Congratulations! You've been selected for a prize.",
            "Your Amazon delivery has been shipped."
        ]

@st.cache_data
def save_classification_log():
    with open("spam_log.txt", "w", encoding="utf-8") as f:
        for msg in st.session_state.spam:
            f.write(f"SPAM: {msg}\n")
        for msg in st.session_state.not_spam:
            f.write(f"NOT_SPAM: {msg}\n")

# Session state init
for key in ['spam', 'not_spam', 'dark_mode', 'auto_mode', 'api_index']:
    if key not in st.session_state:
        st.session_state[key] = [] if 'spam' in key else (False if 'mode' in key else 0)

if 'api_messages' not in st.session_state:
    st.session_state.api_messages = fetch_messages()

# Theme
dark_mode = st.session_state.dark_mode
bg_color = "#1a1b1f" if dark_mode else "#ffffff"
text_color = "#FFFFFF" if dark_mode else "#000000"
card_spam_bg = "#4d0000" if dark_mode else "#ffe6e6"
card_not_spam_bg = "#003322" if dark_mode else "#e6fff2"
section_bg = "#222" if dark_mode else "#ffffff"

# Custom CSS for animated gradient button
st.markdown(f"""
    <style>
        html, body, [data-testid="stApp"] {{
            background-color: {bg_color};
            color: {text_color};
        }}
        .gradient-button {{
            padding: 10px 22px;
            font-size: 14px;
            font-weight: 600;
            color: #000000;
            background: white;
            border: 3px solid;
            border-image-slice: 1;
            border-width: 3px;
            border-image-source: linear-gradient(270deg, #ff6ec4, #7873f5, #4ADEDE, #ff6ec4);
            border-radius: 8px;
            animation: gradient-border 3s linear infinite;
            cursor: pointer;
            transition: transform 0.2s ease-in-out;
        }}
        .gradient-button:hover {{
            transform: scale(1.05);
        }}
        @keyframes gradient-border {{
            0% {{ border-image-source: linear-gradient(0deg, #ff6ec4, #7873f5, #4ADEDE, #ff6ec4); }}
            50% {{ border-image-source: linear-gradient(180deg, #ff6ec4, #7873f5, #4ADEDE, #ff6ec4); }}
            100% {{ border-image-source: linear-gradient(360deg, #ff6ec4, #7873f5, #4ADEDE, #ff6ec4); }}
        }}
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown(f"<h1 style='color:{text_color};'>📧 Email/SMS Spam Classifier</h1>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    toggle_label = "🌙 Dark Mode" if not st.session_state.dark_mode else "☀️ Light Mode"
    new_toggle = st.toggle(toggle_label, key="dark_mode_toggle", value=st.session_state.dark_mode)
    if new_toggle != st.session_state.dark_mode:
        st.session_state.dark_mode = new_toggle
        st.rerun()

    st.markdown("---")
    st.markdown("### 📦 Message Stats")
    st.metric("🚫 Spam", len(st.session_state.spam))
    st.metric("✅ Not Spam", len(st.session_state.not_spam))

    st.markdown("### 📊 Bar Chart")
    fig1, ax1 = plt.subplots(figsize=(2, 2))
    ax1.bar(["Spam", "Not Spam"], [len(st.session_state.spam), len(st.session_state.not_spam)], color=["red", "green"])
    ax1.set_xticks([])
    st.pyplot(fig1)

# Input area
left_col, _ = st.columns([2, 1])
with left_col:
    with st.form("auto_form", clear_on_submit=False):
        if st.session_state.auto_mode:
            submitted = st.form_submit_button("⏹️ Stop Auto")
        else:
            submitted = st.form_submit_button("▶️ Start Auto Detect")

        # Apply gradient styling
        st.markdown("<script>const btn = parent.document.querySelector('button[kind=\"primary\"]'); if (btn) btn.className = 'gradient-button';</script>", unsafe_allow_html=True)

        if submitted:
            st.session_state.auto_mode = not st.session_state.auto_mode
            st.rerun()

    text_box = st.empty()

    if st.session_state.auto_mode:
        if st.session_state.api_index >= len(st.session_state.api_messages):
            st.session_state.api_index = 0
        input_sms = st.session_state.api_messages[st.session_state.api_index]
        st.session_state.api_index += 1

        typed = ""
        for char in input_sms:
            typed += char
            text_box.text_area("", value=typed, height=100, label_visibility="collapsed")
            time.sleep(0.05)

        with st.spinner("🔍 Predicting..."):
            time.sleep(1)
            transformed = transform_text(input_sms)
            vec_input = tfidf.transform([transformed])
            proba = model.predict_proba(vec_input)[0]
            result = model.predict(vec_input)[0]
            confidence = proba[result] * 100

        st.session_state.auto_mode = False

    else:
        input_sms = text_box.text_area("", height=100, label_visibility="collapsed")
        result = None
        confidence = None
        if input_sms.strip() != "":
            with st.spinner("🔍 Predicting..."):
                time.sleep(1.5)
                transformed = transform_text(input_sms)
                vec_input = tfidf.transform([transformed])
                proba = model.predict_proba(vec_input)[0]
                result = model.predict(vec_input)[0]
                confidence = proba[result] * 100

    if input_sms.strip() and result is not None:
        classification_color = "#ffcccc" if result == 1 else "#ccffcc"
        classification_text = "🔵 <strong>Spam</strong>" if result == 1 else "🔴 <strong>Not Spam</strong>"
        classification_font_color = "#990000" if result == 1 else "#006633"

        if result == 1:
            st.session_state.spam.append(input_sms)
            sound_url = "sounds/spam_alert.mp3"
        else:
            st.session_state.not_spam.append(input_sms)
            sound_url = "sounds/not_spam_alert.mp3"

        save_classification_log()

        components.html(f"""
            <button id="play-audio" style="display:none;" onclick="new Audio('{sound_url}').play();"></button>
            <script>document.getElementById("play-audio").click();</script>
        """, height=0)

        st.markdown(f"""
            <div class='fade-in' style='background-color: {classification_color}; color: {classification_font_color}; 
            border-radius: 8px; padding: 12px 16px; margin-top: 10px; font-weight: bold; font-size: 16px; 
            border: 1px solid #aaa;'>
                {classification_text}
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class='fade-in' style='font-size: 15px; margin-top: 5px; color: gray;'>
                🔍 <em>Confidence Score:</em> <strong>{confidence:.2f}%</strong>
            </div>
        """, unsafe_allow_html=True)

# Divider
st.markdown("<hr style='margin-top: 2rem;'>", unsafe_allow_html=True)

# Message Log
st.markdown(f"""
    <div style='border: 1px solid #888; border-radius: 10px; padding: 15px; 
    background-color: {section_bg}; color: {text_color}; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);'>
""", unsafe_allow_html=True)

st.markdown(f"### 📂 Message Log", unsafe_allow_html=True)
spam_col, not_spam_col = st.columns(2)

with spam_col:
    st.markdown("**🚫 Spam**")
    st.markdown("<div style='max-height: 300px; overflow-y: auto;'>", unsafe_allow_html=True)
    for msg in reversed(st.session_state.spam):
        highlighted = highlight_keywords(msg)
        st.markdown(f"""
            <div class='fade-in' style='border: 1px solid #cc0000; background-color: {card_spam_bg}; padding: 10px; 
            margin-bottom: 10px; border-radius: 6px; font-size: 14px; color: #990000; font-family: Arial;'>
                {highlighted}
            </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with not_spam_col:
    st.markdown("**✅ Not Spam**")
    st.markdown("<div style='max-height: 300px; overflow-y: auto;'>", unsafe_allow_html=True)
    for msg in reversed(st.session_state.not_spam):
        highlighted = highlight_keywords(msg)
        st.markdown(f"""
            <div class='fade-in' style='border: 1px solid #339966; background-color: {card_not_spam_bg}; padding: 10px; 
            margin-bottom: 10px; border-radius: 6px; font-size: 14px; color: #006633; font-family: Arial;'>
                {highlighted}
            </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
