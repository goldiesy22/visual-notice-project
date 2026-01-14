import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import json
import base64

# ==========================================
# 🔑 [필수] 성공했던 website1 프로젝트의 API 키를 입력하세요
# ==========================================
FINAL_KEY = "AIzaSyA-1Pu8fP-5HPIQWBLKkgJYuZWGkVmcXaQ" 
# ==========================================

# 1. API 설정
genai.configure(api_key=FINAL_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. 페이지 기본 설정
st.set_page_config(page_title="모두의 알림장", page_icon="🏫", layout="wide")

# 3. 고급 스타일링 (CSS)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
        .main { background-color: #f8f9fa; }
        .stButton>button { 
            width: 100%; border-radius: 12px; height: 3.5em; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; font-weight: bold; border: none; transition: 0.3s;
        }
        .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .result-card { 
            background-color: white; padding: 25px; border-radius: 20px; 
            border: 1px solid #eee; box-shadow: 0 10px 30px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
        .prep-item {
            display: inline-block; background: #eef2ff; padding: 8px 15px;
            border-radius: 50px; margin: 5px; color: #4338ca; font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)

# 4. 앱 헤더
st.markdown("<h1 style='text-align: center; color: #1e293b;'>🏫 모두의 AI 알림장</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748b;'>사진 한 장으로 준비물부터 번역까지 한 번에!</p>", unsafe_allow_html=True)

st.divider()

# 5. 메인 레이아웃 (좌: 입력, 우: 결과)
col_in, col_out = st.columns([1, 1.2], gap="large")

with col_in:
    st.subheader("📸 알림장 올리기")
    
    # 언어 선택
    lang_map = {
        "한국어 🇰🇷": "Korean", 
        "English 🇺🇸": "English", 
        "中文 🇨🇳": "Chinese", 
        "Tiếng Việt 🇻🇳": "Vietnamese", 
        "日本語 🇯🇵": "Japanese",
        "Tagalog 🇵🇭": "Tagalog"
    }
    sel_lang_name = st.selectbox("어느 나라 언어로 번역할까요?", list(lang_map.keys()))
    target_lang = lang_map[sel_lang_name]

    # 업로드 방식 선택
    input_mode = st.radio("업로드 방식", ["파일 업로드", "카메라 촬영"], horizontal=True)
    
    img_file = None
    if input_mode == "파일 업로드":
        img_file = st.file_uploader("이미지 파일 선택", type=['png', 'jpg', 'jpeg'])
    else:
        img_file = st.camera_input("알림장 촬영")

    if img_file:
        st.image(img_file, caption="인식된 이미지", use_container_width=True)

with col_out:
    st.subheader("📋 분석 결과")
    
    if img_file:
        if st.button("✨ 스마트 분석 시작"):
            with st.spinner("AI가 꼼꼼하게 읽고 있습니다..."):
                try:
                    img = Image.open(img_file)
                    prompt = f"""
                    Analyze this school notice image. 
                    1. Translate all content to {target_lang}.
                    2. Summarize the key points in {target_lang} using bullet points.
                    3. List all necessary items (preparation) specifically mentioned.
                    4. Return the result strictly in the following JSON format:
                    {{
                        "summary": "...",
                        "translation": "...",
                        "items": ["item1", "item2"]
                    }}
                    """
                    
                    response = model.generate_content([prompt, img])
                    
                    # JSON 파싱 안전장치
                    res_text = response.text
                    if "```json" in res_text:
                        res_text = res_text.split("```json")[1].split("```")[0]
                    elif "```" in res_text:
                        res_text = res_text.split("```")[1].split("```")[0]
                    
                    data = json.loads(res_text.strip())

                    # --- 결과 화면 출력 ---
                    st.markdown("<div class='result-card'>", unsafe_allow_html=True)
                    
                    # 1. 요약
                    st.markdown("### 📢 주요 내용 요약")
                    st.write(data.get("summary"))
                    
                    st.divider()
                    
                    # 2. 준비물
                    st.markdown("### 🎒 꼭 챙겨야 할 것")
                    items = data.get("items", [])
                    if items:
                        item_html = "".join([f"<span class='prep-item'>✅ {i}</span>" for i in items])
                        st.markdown(item_html, unsafe_allow_html=True)
                    else:
                        st.write("특별한 준비물이 없습니다.")
                    
                    st.divider()
                    
                    # 3. 전체 번역
                    st.markdown("### 🌐 전체 번역 내용")
                    st.info(data.get("translation"))
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.balloons()

                except Exception as e:
                    st.error(f"분석 중 오류가 발생했습니다: {e}")
                    st.info("알림장 내용이 너무 복잡하거나 흐릿할 수 있습니다. 다시 찍어보세요!")
    else:
        st.info("왼쪽에서 이미지를 먼저 업로드하거나 촬영해주세요.")

# 6. 푸터
st.divider()
st.caption("© 2026 모두의 AI 알림장 - 다문화 가정을 위한 학교 소식 안내 도우미")
