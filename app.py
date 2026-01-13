import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import json
import base64
from gtts import gTTS
import io

# ==========================================
# 👇 [여기만 고치세요] 따옴표("") 안에 새 키를 붙여넣으세요!
# ==========================================
MY_DIRECT_KEY = "AIzaSyCQqwCFatYYm9RVsPPaxeBv7qn765KcgvE"
# ==========================================


# 1. API 키 설정 (Secrets 무시하고 위에서 적은 키를 씁니다)
if "여기에" in MY_DIRECT_KEY:
    st.error("🚨 코드 12번째 줄에 API 키를 아직 안 넣으셨어요!")
    st.stop()

try:
    genai.configure(api_key=MY_DIRECT_KEY)
except Exception as e:
    st.error(f"🚨 키 형식이 잘못되었습니다: {e}")
    st.stop()

# 2. 모델 연결 테스트
st.sidebar.markdown(f"**🛠 도구 버전:** `{genai.__version__}`")

target_model = None
candidates = [
    "models/gemini-1.5-flash", 
    "models/gemini-1.5-flash-001",
    "models/gemini-1.5-pro"
]

with st.sidebar.status("🚀 연결 테스트 중...", expanded=True) as status:
    for name in candidates:
        status.write(f"시도: `{name}`")
        try:
            model = genai.GenerativeModel(name)
            # 실제 통신 시도
            response = model.generate_content("Hello")
            target_model = model
            status.update(label="✅ 연결 성공!", state="complete", expanded=False)
            st.sidebar.success(f"✅ 연결됨: `{name}`")
            break
        except Exception as e:
            status.write(f"❌ 실패: {str(e)}")

if not target_model:
    st.error("🚨 연결 실패! 키는 맞지만, 구글이 이 키로 1.5 모델 사용을 막고 있습니다.")
    st.warning("새 프로젝트에서 키를 만드신 게 확실한가요? (Default Project 아님)")
    st.stop()

# ==========================================
# 3. 앱 로직 (연결 성공 시에만 실행됨)
# ==========================================
ASSETS_DIR = "assets"
st.set_page_config(page_title="모두의 알림장", page_icon="🏫", layout="wide")

st.markdown("""
    <style>
        body { user-select: none; }
        .subtitle-text { text-align: center; color: #555; font-weight: bold; }
        .unified-icon { width: 90px; height: 90px; object-fit: contain; }
    </style>
""", unsafe_allow_html=True)

# 필수 함수들
if 'custom_input' not in st.session_state: st.session_state['custom_input'] = ''
def apply_input(): st.session_state['custom_input'] = st.session_state.widget_input
def get_image_base64(path):
    with open(path, "rb") as f: return base64.b64encode(f.read()).decode()

# 배너
banner_path = os.path.join(ASSETS_DIR, "banner.jpg") # 예시 이름
if os.path.exists(banner_path): st.image(banner_path, use_container_width=True)

st.markdown("<h1 style='text-align: center;'>🏫 모두의 AI 알림장</h1>", unsafe_allow_html=True)

# 언어 선택 UI (간소화)
lang_map = {"한국어":"ko", "English":"en", "中文":"zh", "Tiếng Việt":"vi", "Tagalog":"tl"}
st.markdown("### 🌍 언어 선택")
sel_lang = st.radio("언어", list(lang_map.keys()), horizontal=True, label_visibility="collapsed")
target_lang_code = lang_map[sel_lang]
target_lang_name = sel_lang

st.divider()

# 이미지 입력
tab1, tab2 = st.tabs(["📸 카메라", "📂 파일 업로드"])
img_file = None
with tab1:
    cam = st.camera_input("사진 찍기")
    if cam: img_file = cam
with tab2:
    up = st.file_uploader("파일 선택", type=['png','jpg','jpeg'])
    if up: img_file = up

if img_file:
    with st.spinner("분석 중..."):
        img = Image.open(img_file)
        prompt = f"Analyze this school notice. Translate to {target_lang_name}. Return JSON with summary, translation, and keywords."
        try:
            # 위에서 연결된 target_model 사용
            res = target_model.generate_content([prompt, img])
            st.success("✅ 분석 완료!")
            st.write(res.text) # 결과 일단 텍스트로 출력 (테스트용)
        except Exception as e:
            st.error(f"분석 중 오류: {e}")