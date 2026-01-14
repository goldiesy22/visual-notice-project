import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import json
import base64
from gtts import gTTS
import io

# ==========================================
# 🚨 [긴급] 여기에 방금 복사한 'My School App' 키를 넣으세요!
# ==========================================
MY_DIRECT_KEY = "AIzaSyCQqwCFatYYm9RVsPPaxeBv7qn765KcgvE"
# ==========================================

# 1. API 키 설정
if "여기에" in MY_DIRECT_KEY:
    st.error("🚨 12번째 줄에 API 키를 넣어주세요!")
    st.stop()

genai.configure(api_key=MY_DIRECT_KEY)

# 2. [만능 연결] 되는 거 아무거나 잡기 (1.5 우선 -> 안되면 2.0/Pro)
# 이 리스트에 있는 걸 순서대로 다 찔러봅니다.
candidates = [
    "models/gemini-1.5-flash",       # 1순위: 무제한 (베스트)
    "models/gemini-1.5-flash-001",   # 2순위: 무제한 (구버전)
    "models/gemini-2.0-flash-lite-preview-02-05", # 3순위: 2.0 Lite (약간의 제한)
    "models/gemini-1.5-pro",         # 4순위: Pro (하루 50회 제한)
    "models/gemini-pro"              # 5순위: 구형 (비상용)
]

active_model = None
connected_name = ""

with st.sidebar.status("🚀 긴급 모델 연결 중...", expanded=True) as status:
    for name in candidates:
        status.write(f"시도: `{name}`")
        try:
            model = genai.GenerativeModel(name)
            # 통신 테스트
            model.generate_content("test")
            
            # 성공하면 여기서 멈춤!
            active_model = model
            connected_name = name
            status.update(label=f"✅ 연결됨! ({name})", state="complete", expanded=False)
            st.sidebar.success(f"**연결 모델:**\n`{name}`")
            break
        except Exception as e:
            # 실패하면 다음 걸로 넘어감 (조용히)
            continue

# 끝까지 다 실패했을 경우
if not active_model:
    st.error("🚨 모든 모델 연결 실패! (키가 '만료(Expired)' 되었거나 오타가 있습니다.)")
    st.warning("👉 AI Studio에서 키를 다시 복사해서 12번째 줄에 붙여넣으세요.")
    st.stop()


# ==========================================
# 3. 앱 로직 (제출용 기능 구현)
# ==========================================
ASSETS_DIR = "assets"
st.set_page_config(page_title="모두의 알림장", page_icon="🏫", layout="wide")

# 스타일
st.markdown("""
    <style>
        body { -webkit-user-select: none; user-select: none; }
        .summary-box { background-color: #F0F7FF; padding: 20px; border-radius: 10px; border: 2px solid #4A90E2; font-size: 18px; }
        .icon-item-box { display: inline-block; margin: 10px; text-align: center; }
        .unified-icon { width: 80px; height: 80px; object-fit: contain; }
    </style>
""", unsafe_allow_html=True)

# 배너
banner_path = os.path.join(ASSETS_DIR, "banner.jpg")
if os.path.exists(banner_path): st.image(banner_path, use_container_width=True)

st.title("🏫 모두의 AI 알림장 (긴급모드)")

# 언어 선택
lang_options = ["한국어", "English", "中文", "Tiếng Việt", "Tagalog", "日本語"]
sel_lang = st.radio("언어 선택", lang_options, horizontal=True)

# 이미지 입력
tab1, tab2 = st.tabs(["📸 카메라", "📂 파일 업로드"])
img_file = None
with tab1:
    c = st.camera_input("촬영")
    if c: img_file = c
with tab2:
    u = st.file_uploader("업로드", type=['png','jpg','jpeg'])
    if u: img_file = u

# 분석 로직
if img_file:
    with st.spinner(f"분석 중... (모델: {connected_name})"):
        try:
            image = resize_image_for_speed(Image.open(img_file)) if 'resize_image_for_speed' in globals() else Image.open(img_file)
            
            prompt = f"""
            Analyze this notice image.
            Target Language: {sel_lang}
            Output JSON format:
            {{
                "summary": "Summarize the notice in {sel_lang} (bullet points)",
                "translation": "Translate the full text to {sel_lang}",
                "keywords": [ {{"display_word": "Item Name", "emoji": "✏️"}} ]
            }}
            """
            
            response = active_model.generate_content([prompt, image])
            
            # JSON 파싱 시도
            txt = response.text
            if "```json" in txt: txt = txt.split("```json")[1].split("```")[0]
            elif "```" in txt: txt = txt.split("```")[1].split("```")[0]
            
            data = json.loads(txt.strip(), strict=False)
            
            # 결과 출력
            st.divider()
            
            # 1. 준비물
            kws = data.get('keywords', [])
            if kws:
                st.markdown("### 🎒 준비물")
                cols = st.columns(len(kws)) if len(kws) > 0 else []
                for idx, item in enumerate(kws):
                    with st.container():
                        st.markdown(f"<div class='icon-item-box'><div style='font-size:40px'>{item.get('emoji','')}</div><div>{item.get('display_word','')}</div></div>", unsafe_allow_html=True)

            # 2. 요약
            st.markdown("### 📢 요약")
            st.markdown(f"<div class='summary-box'>{data.get('summary', '요약 실패')}</div>", unsafe_allow_html=True)
            
            # 3. 번역
            with st.expander("번역 전문 보기"):
                st.write(data.get('translation', '번역 실패'))
                
        except Exception as e:
            st.error(f"오류 발생: {e}")