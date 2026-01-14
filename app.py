import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import json
import base64

# ==========================================
# 🚨 [최종] website1 프로젝트의 API 키를 여기에 넣으세요!
# ==========================================
FINAL_KEY = "AIzaSyA-1Pu8fP-5HPIQWBLKkgJYuZWGkVmcXaQ"
# ==========================================

# 1. API 설정 (변수명을 바꿔서 캐시 문제를 우회합니다)
genai.configure(api_key=FINAL_KEY)

st.set_page_config(page_title="모두의 알림장", page_icon="🏫", layout="wide")

# 스타일 설정
st.markdown("""
    <style>
        .main { background-color: #f5f7f9; }
        .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #4A90E2; color: white; }
        .summary-box { background-color: white; padding: 20px; border-radius: 15px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

st.title("🏫 모두의 AI 알림장")
st.info("새로운 프로젝트 키로 연결되었습니다.")

# 모델 연결 테스트 및 선택
try:
    # 1.5 Flash 모델을 기본으로 사용합니다.
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 언어 선택
    lang_map = {"한국어": "ko", "English": "en", "中文": "zh", "Tiếng Việt": "vi", "日本語": "ja"}
    sel_lang = st.selectbox("번역할 언어를 선택하세요", list(lang_map.keys()))

    # 파일 업로드
    img_file = st.file_uploader("알림장 사진을 업로드하세요", type=['png', 'jpg', 'jpeg'])

    if img_file:
        img = Image.open(img_file)
        st.image(img, caption="업로드된 이미지", use_container_width=True)
        
        if st.button("AI 알림장 분석 시작"):
            with st.spinner("AI가 알림장을 읽고 번역 중입니다..."):
                try:
                    prompt = f"""
                    이 알림장 이미지를 분석해서 {sel_lang}로 설명해줘.
                    결과는 반드시 아래의 JSON 형식으로만 응답해줘:
                    {{
                        "summary": "알림장 핵심 요약 (불렛포인트)",
                        "translation": "전체 내용 번역",
                        "items": ["준비물1", "준비물2"]
                    }}
                    """
                    response = model.generate_content([prompt, img])
                    
                    # JSON 응답 정제
                    res_text = response.text
                    if "```json" in res_text:
                        res_text = res_text.split("```json")[1].split("```")[0]
                    
                    data = json.loads(res_text.strip())
                    
                    st.success("✅ 분석 완료!")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("📌 핵심 요약")
                        st.write(data.get("summary"))
                    with col2:
                        st.subheader("🎒 준비물")
                        for item in data.get("items", []):
                            st.write(f"- {item}")
                    
                    with st.expander("📄 전체 번역 보기"):
                        st.write(data.get("translation"))
                        
                except Exception as e:
                    st.error(f"분석 중 오류가 발생했습니다: {e}")
                    st.write("AI 응답 원문:")
                    st.write(response.text)

except Exception as e:
    st.error(f"🚨 모델 연결 실패: {e}")
    st.warning("API 키가 정확한지, 혹은 구글 서버 등록까지 1~2분만 기다려보세요.")
