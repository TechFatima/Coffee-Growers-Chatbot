import base64
import os
import time
from datetime import datetime

import chromadb
import cohere
import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader

# -----------------------
# Setup
# -----------------------
load_dotenv()
co = cohere.Client(os.getenv("cohere_api_key"))

client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection("rag_collection")

st.set_page_config(page_title="Coffee Growers Chatbot", layout="wide", initial_sidebar_state="expanded")

# -----------------------
# Helpers
# -----------------------

def img_to_base64(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return ""


def pack_chunks(lines, max_chars=800):
    packed = []
    buf = ""
    for line in lines:
        if not line:
            continue
        if len(buf) + len(line) + 1 > max_chars:
            packed.append(buf.strip())
            buf = line
        else:
            buf = f"{buf} {line}".strip()
    if buf:
        packed.append(buf.strip())
    return packed


# -----------------------
# Background image
# -----------------------

bg_path = os.path.join(os.path.dirname(__file__), "COFFEE BOOKS.jpg")
bg_b64 = img_to_base64(bg_path)
bg_css = f"url('data:image/jpeg;base64,{bg_b64}')" if bg_b64 else "none"

# -----------------------
# Styles
# -----------------------

css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Cormorant+Garamond:wght@400;600;700&display=swap');

.stApp{
  background-color:#2b1a12;
  background-image:
    __BG_CSS__,
    radial-gradient(ellipse at 10% 20%, rgba(255,235,205,0.08) 0, rgba(0,0,0,0) 45%),
    radial-gradient(ellipse at 80% 10%, rgba(255,228,196,0.06) 0, rgba(0,0,0,0) 40%),
    linear-gradient(180deg, rgba(43,26,18,0.98) 0%, rgba(30,18,12,0.98) 100%);
  background-size:cover;
  background-position:center 25%;
  background-attachment:fixed;
  color:#f5e6d3;
  font-family:"Cormorant Garamond", Georgia, "Times New Roman", serif;
}

.stApp::before{
  content:"";
  position:fixed;
  top:0;
  left:0;
  right:0;
  height:120px;
  background:linear-gradient(180deg, rgba(43,26,18,0.98) 0%, rgba(43,26,18,0.7) 60%, rgba(0,0,0,0) 100%);
  z-index:0;
  pointer-events:none;
}

.stApp::after{
  content:"";
  position:fixed;
  inset:0;
  background:rgba(0,0,0,0.08);
  backdrop-filter:blur(0.8px) saturate(1.15);
  z-index:0;
  pointer-events:none;
}

.stApp > div{position:relative;z-index:1;}

header{display:none !important;}
section[data-testid="stSidebarNav"]{display:none !important;}
div[data-testid="stToolbar"]{display:none !important;}
div[data-testid="stDecoration"]{display:none !important;}
button[data-testid="collapsedControl"]{display:none !important;}

.block-container{padding-top:8.2rem;padding-bottom:0.8rem;}

.header-wrap{
  position:fixed;
  top:1.2rem;
  left:calc(50% + 150px);
  transform:translateX(-50%);
  background:rgba(43,26,18,0.96);
  backdrop-filter:blur(4px);
  padding:0.9rem 0;
  margin:0 auto;
  z-index:10;
  border-bottom:1px solid rgba(255,255,255,0.08);
  text-align:center;
  border-radius:16px;
  overflow:hidden;
  max-width:900px;
  width:calc(100% - 2rem - 300px);
}

.title{font-family:"Playfair Display", "Cormorant Garamond", serif;font-size:2.2rem;line-height:1.2;margin-bottom:0.2rem;}
.subtitle{font-style:italic;color:#e9d6be;margin-bottom:0.8rem;}

.chat-container{display:flex;flex-direction:column;gap:14px;width:100%;max-width:980px;margin:0 auto;padding:0.2rem 0 0.5rem;}
.chat-hint{margin:0.5rem 0 0.8rem 0;color:#e9d6be;font-style:italic;}
.message-row{display:flex;width:100%;margin:2px 0;}
.message-row.user{justify-content:flex-end;}
.message-row.bot{justify-content:flex-start;}
.user-box{align-self:flex-end;background:linear-gradient(135deg,#7b4a39,#5a3329);color:#fdf3e3;padding:12px 16px;border-radius:18px 18px 4px 18px;max-width:min(72%, 620px);font-size:15px;line-height:1.45;box-shadow:0 6px 16px rgba(0,0,0,0.18);white-space:pre-wrap;word-break:break-word;}
.bot-box{align-self:flex-start;background:rgba(93,64,55,0.95);color:#f5e6d3;padding:12px 16px;border-radius:18px 18px 18px 4px;max-width:min(72%, 620px);font-size:15px;line-height:1.45;box-shadow:0 6px 16px rgba(0,0,0,0.16);white-space:pre-wrap;word-break:break-word;}

.typing-box{align-self:flex-start;background:#4a332b;color:#f5e6d3;padding:10px 14px;border-radius:18px 18px 18px 4px;max-width:min(72%, 620px);font-size:14px;display:flex;align-items:center;gap:8px;opacity:0.9;}
.typing-dots{display:inline-flex;gap:4px;}
.typing-dot{width:6px;height:6px;background:#f5e6d3;border-radius:50%;display:inline-block;animation:dot 1.1s infinite;}
.typing-dot:nth-child(2){animation-delay:0.15s;}
.typing-dot:nth-child(3){animation-delay:0.3s;}

.coffee{position:fixed;top:-50px;font-size:28px;animation:fall 8s linear infinite;opacity:0.25;}
@keyframes fall{0%{transform:translateY(-50px);}100%{transform:translateY(900px);}}
.c1{left:10%}.c2{left:30%;animation-delay:2s}.c3{left:50%;animation-delay:4s}.c4{left:70%;animation-delay:1s}.c5{left:90%;animation-delay:3s}

.notice{background:#e6d4b8;color:#3a271d;padding:12px 14px;border-left:6px solid #6f4b3a;border-radius:8px;box-shadow:0 6px 18px rgba(0,0,0,0.18);font-style:italic;margin-top:10px;}

section[data-testid="stFileUploader"]{background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);border-radius:10px;padding:8px 12px;max-width:520px;}
section[data-testid="stFileUploader"] > div{padding:6px 0;}
div[data-testid="stFileUploaderDropzone"]{padding:10px 12px;min-height:60px;}

/* Chat input */
div[data-testid="stChatInput"]{background:rgba(62,43,34,0.85);border:1px solid rgba(198,164,123,0.45);border-radius:12px;padding:6px 8px;margin-top:-6px;box-shadow:0 0 0 2px rgba(111,75,58,0.25);}
div[data-testid="stChatInput"]:focus-within{border-color:#c69a6b;box-shadow:0 0 0 2px rgba(198,154,107,0.35);}
div[data-testid="stChatInput"] textarea{color:#f5e6d3;font-family:"Cormorant Garamond", Georgia, "Times New Roman", serif;}
div[data-testid="stChatInput"] textarea:focus{outline:none;box-shadow:none;}
div[data-testid="stChatInput"] div[data-baseweb="textarea"]{border:0 !important;box-shadow:none !important;}
div[data-testid="stChatInput"] div[data-baseweb="textarea"]:focus-within{border:0 !important;box-shadow:none !important;}
div[data-testid="stChatInput"] div[data-baseweb="textarea"] > div{border:0 !important;box-shadow:none !important;}
div[data-testid="stChatInput"] div[data-baseweb="textarea"] textarea{caret-color:#e7d1b5;}
div[data-testid="stChatInput"] textarea{border:none !important;box-shadow:none !important;}
div[data-testid="stChatInput"] textarea:focus{border:none !important;box-shadow:none !important;outline:none !important;}
div[data-testid="stChatInput"] button{color:#e7d1b5;background:#5b3c2f;border:1px solid rgba(198,154,107,0.5);}
div[data-testid="stChatInput"] button:hover{background:#6a4636;border-color:#c69a6b;}
div[data-testid="stChatInput"] button:focus{outline:none;box-shadow:none;}

/* Loader */
.brew-loader{display:flex;align-items:center;gap:10px;color:#f0dec7;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.12);border-radius:10px;padding:10px 14px;width:fit-content;}
.brew-cup{display:inline-block;font-size:20px;animation:flip 0.9s ease-in-out infinite;transform-origin:center;}
.brew-cup:nth-child(2){animation-delay:0.15s;}.brew-cup:nth-child(3){animation-delay:0.3s;}
.brew-text{font-style:italic;letter-spacing:0.3px;}
@keyframes flip{0%{transform:rotateY(0deg);}50%{transform:rotateY(180deg);}100%{transform:rotateY(360deg);}}
@keyframes dot{0%,80%,100%{transform:translateY(0);opacity:0.4;}40%{transform:translateY(-4px);opacity:1;}}

/* Sidebar */
section[data-testid="stSidebar"]{
  display:block !important;
  visibility:visible !important;
  opacity:1 !important;
  transform:none !important;
  width:300px !important;
  min-width:300px !important;
  z-index:20 !important;
  position:relative !important;
}
section[data-testid="stSidebar"] > div{background:#2b1a12;border-right:1px solid rgba(255,255,255,0.08);padding:0.5rem 0.5rem;height:100vh;overflow-y:auto;overflow-x:hidden;display:flex;flex-direction:column;}
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span{color:#f5e6d3;}
section[data-testid="stSidebar"] section[data-testid="stFileUploader"]{max-width:100%;}
div[data-testid="stSidebarContent"]{height:100%;overflow-y:auto;padding-right:6px;}
</style>

<div class="coffee c1">☕</div><div class="coffee c2">☕</div><div class="coffee c3">☕</div><div class="coffee c4">☕</div><div class="coffee c5">☕</div>
"""

css = css.replace("__BG_CSS__", bg_css)
st.markdown(css, unsafe_allow_html=True)

# -----------------------
# Header
# -----------------------

st.markdown(
    '<div class="header-wrap">'
    '<div class="title">☕ Coffee Growers Chatbot</div>'
    '<div class="subtitle">Helping coffee growers grow better beans 🌱☕</div>'
    "</div>",
    unsafe_allow_html=True,
)

# -----------------------
# Session state
# -----------------------

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -----------------------
# Sidebar: Upload
# -----------------------

with st.sidebar:
    st.subheader("Upload Coffee Documents")
    files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True, key="pdf_upload")

    if files and st.button("Store in Coffee Library ☕"):
        st.toast("Got it. Filing your pages in the coffee library…", icon="☕")

        chunks = []
        for file in files:
            reader = PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            for line in text.split("\n"):
                if line.strip():
                    chunks.append(line.strip())

        if not chunks:
            st.error("No readable text found in the PDFs. Try a text-based PDF.")
        else:
            try:
                with st.spinner("Brewing embeddings…"):
                    packed = pack_chunks(chunks, max_chars=900)
                    embeddings = []
                    batch_size = 40

                    for i in range(0, len(packed), batch_size):
                        batch = packed[i:i + batch_size]
                        try:
                            embeddings += co.embed(
                                texts=batch,
                                model="embed-english-v3.0",
                                input_type="search_document",
                            ).embeddings
                        except Exception:
                            time.sleep(2)
                            embeddings += co.embed(
                                texts=batch,
                                model="embed-english-v3.0",
                                input_type="search_document",
                            ).embeddings
                        time.sleep(0.8)

                    ids = [str(i) for i in range(len(packed))]
                    collection.add(documents=packed, embeddings=embeddings, ids=ids)

                st.markdown(
                    '<div class="notice">Dear friend, your pages have arrived safe. Consider them lovingly filed in the coffee library.</div>',
                    unsafe_allow_html=True,
                )
            except Exception as e:
                st.error("Embedding error. Check internet or API key.")
                st.exception(e)

# -----------------------
# Chat input + response
# -----------------------

query = st.chat_input("Ask about coffee farming...")
if query:
    live_user = st.empty()
    live_user.markdown(f'<div class="message-row user"><div class="user-box">{query}</div></div>', unsafe_allow_html=True)

    typing_slot = st.empty()
    typing_slot.markdown(
        '<div class="message-row bot"><div class="typing-box">'
        '<span>☕</span><span>Brewing your reply</span>'
        '<span class="typing-dots"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span></span>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    try:
        try:
            q_embed = co.embed(texts=[query], model="embed-english-v3.0", input_type="search_query").embeddings[0]
        except Exception:
            time.sleep(1.5)
            q_embed = co.embed(texts=[query], model="embed-english-v3.0", input_type="search_query").embeddings[0]

        results = collection.query(query_embeddings=[q_embed], n_results=3)
        context = "\n".join(results["documents"][0])
        prompt = f"""Context:\n{context}\n\nQuestion:\n{query}\n\nAnswer:\n"""

        try:
            response = co.chat(message=prompt, max_tokens=1400)
        except Exception:
            time.sleep(1.5)
            response = co.chat(message=prompt, max_tokens=1400)

        answer = response.text
    except Exception as e:
        answer = f"⚠️ Connection issue. {e}"

    typing_slot.empty()
    live_user.empty()
    st.session_state.chat_history.append({"q": query, "a": answer, "ts": datetime.now().strftime("%Y-%m-%d")})

# -----------------------
# Chat history
# -----------------------

st.markdown('<div class="chat-container">', unsafe_allow_html=True)
if not st.session_state.chat_history:
    st.markdown('<div class="chat-hint">Ask a question below and I’ll answer here.</div>', unsafe_allow_html=True)
for item in st.session_state.chat_history:
    q = item["q"] if isinstance(item, dict) else item[0]
    a = item["a"] if isinstance(item, dict) else item[1]
    st.markdown(f'<div class="message-row user"><div class="user-box">{q}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="message-row bot"><div class="bot-box">{a}</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)