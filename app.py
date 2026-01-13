import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import json
from gtts import gTTS
import io

# ==========================================
# 1. 페이지 및 앱 모드 설정 (가장 중요!)
# ==========================================
# 페이지 기본 설정
st.set_page_config(page_title="모두의 알림장", page_icon="🏫", layout="wide")

# 📱 [PWA 설정] 모바일에서 주소창 없애고 앱처럼 보이게 하는 코드
st.markdown("""
    <style>
        /* 모바일에서 꾹 눌러서 글자 선택되는 것 방지 (앱처럼 느낌) */
        body { -webkit-user-select: none; -moz-user-select: none; -ms-user-select: none; user-select: none; }
        /* 상단 흰색 여백 줄이기 (배너 꽉 차게) */
        .block-container { padding-top: 1rem !important; padding-bottom: 3rem !important; }
    </style>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
""", unsafe_allow_html=True)

# ==========================================
# 2. API 키 및 모델 설정
# ==========================================
# secrets.toml에서 API 키 가져오기
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("🚨 API 키가 없습니다! Streamlit 설정(Secrets)을 확인해주세요.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# 사용할 모델 설정 (Gemini 1.5 Flash - 속도 빠름)
model = genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# 3. CSS 스타일 (디자인 꾸미기)
# ==========================================
st.markdown("""
<style>
    /* 결과 박스 디자인 */
    .result-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 5px solid #FF9F1C;
    }
    /* 준비물 아이콘 그리드 (반응형) */
    .supplies-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        justify-content: flex-start;
    }
    .supply-item {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        width: 100px; /* 아이콘 박스 크기 */
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .supply-icon { font-size: 30px; display: block; margin-bottom: 5px; }
    .supply-name { font-size: 14px; font-weight: bold; color: #333; word-break: keep-all; }
    
    /* 중요 문구 강조 */
    .highlight { color: #d63031; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. 세션 상태 초기화 (새로고침 방지)
# ==========================================
if 'result' not in st.session_state:
    st.session_state.result = None
if 'audio_bytes' not in st.session_state:
    st.session_state.audio_bytes = None

# ==========================================
# 5. 폴더 경로 설정 (assets)
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(current_dir, "assets")

# ==========================================
# 6. [제목] 상단 배너 이미지 & 타이틀 배치
# ==========================================
# 1) 배너 파일 찾기 (이름이 달라도 다 찾아봄)
banner_candidates = ["banner.jpg", "banner.png", "banner.jpeg", "image_2c0b96.jpg"]
banner_found = False

for filename in banner_candidates:
    banner_path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(banner_path):
        st.image(banner_path, use_container_width=True)
        banner_found = True
        break 

# 2) 배너 아래 타이틀
st.markdown("""
    <h1 style='color: #FF9F1C; text-align: center; margin-top: 10px; margin-bottom: 20px;'>
        🏫 모두의 AI 알림장
    </h1>
""", unsafe_allow_html=True)

# ==========================================
# 7. 사용자 입력 (언어 & 사진)
# ==========================================
target_lang = st.radio(
    "번역할 언어를 선택하세요 (Choose Language)",
    ["한국어 (요약)", "English (영어)", "中文 (중국어)", "Tiếng Việt (베트남어)", "Pilipino (필리핀어)"],
    horizontal=True
)

uploaded_file = st.file_uploader("알림장 사진을 찍거나 올려주세요 📸", type=["jpg", "jpeg", "png"])

# ==========================================
# 8. AI 분석 로직
# ==========================================
if uploaded_file is not None:
    # 이미지 보여주기
    image = Image.open(uploaded_file)
    st.image(image, caption='업로드된 알림장', use_container_width=True)

    if st.button("🔍 AI 분석 시작 (Analyze)"):
        with st.spinner("AI가 알림장을 읽고 있어요... 잠시만 기다려주세요! 🤖"):
            try:
                # 프롬프트 설정 (JSON 출력 요청)
                prompt = f"""
                당신은 초등학교 알림장을 분석하는 AI 비서입니다.
                이 이미지를 '{target_lang}' 사용자를 위해 분석해서 JSON 형식으로 출력하세요.
                
                **필수 출력 형식 (JSON):**
                {{
                    "summary": "전체 내용 3줄 요약 (친절한 말투)",
                    "supplies": [
                        {{"name": "준비물1 이름", "icon": "✏️"}},
                        {{"name": "준비물2 이름", "icon": "📓"}}
                    ],
                    "deadline": "숙제나 준비물 마감일 (없으면 '없음')",
                    "full_translation": "전체 내용 번역"
                }}
                
                **주의사항:**
                1. 'supplies'에는 준비물과 관련된 아이콘(이모지)을 꼭 넣어주세요.
                2. 말투는 다문화 가정 학부모나 조부모님이 이해하기 쉽게 아주 친절하고 쉬운 단어를 쓰세요.
                3. 오직 JSON 데이터만 출력하세요. (코드 블록 ```json ... ``` 없이)
                """
                
                # Gemini에게 요청
                response = model.generate_content([prompt, image])
                
                # 결과 처리 (JSON 파싱)
                try:
                    text_response = response.text.strip()
                    # 혹시 코드블록이 있으면 제거
                    if text_response.startswith("```json"):
                        text_response = text_response[7:-3]
                    elif text_response.startswith("```"):
                        text_response = text_response[3:-3]
                        
                    result_json = json.loads(text_response)
                    st.session_state.result = result_json # 결과 저장
                    
                    # TTS 오디오 생성 (요약 내용 읽어주기)
                    tts_text = result_json.get("summary", "내용을 읽어드립니다.")
                    # 언어 코드 매핑
                    lang_code = 'ko'
                    if 'English' in target_lang: lang_code = 'en'
                    elif '中文' in target_lang: lang_code = 'zh-CN'
                    elif 'Việt' in target_lang: lang_code = 'vi'
                    
                    tts = gTTS(text=tts_text, lang=lang_code)
                    mp3_fp = io.BytesIO()
                    tts.write_to_fp(mp3_fp)
                    st.session_state.audio_bytes = mp3_fp.getvalue()

                except Exception as e:
                    st.error(f"내용 분석 중 오류가 발생했습니다: {e}")
                    st.write(response.text) # 디버깅용 원본 출력

            except Exception as e:
                st.error(f"AI 연결 오류: {e}")

# ==========================================
# 9. 결과 화면 출력
# ==========================================
if st.session_state.result:
    data = st.session_state.result
    
    st.divider()
    st.subheader("📢 분석 결과 (Result)")

    # 1. 오디오 플레이어
    if st.session_state.audio_bytes:
        st.audio(st.session_state.audio_bytes, format='audio/mp3')
        st.caption("🔊 재생 버튼을 누르면 내용을 읽어줍니다.")

    # 2. 3줄 요약 박스
    st.markdown(f"""
    <div class="result-box">
        <h3>📝 3줄 요약</h3>
        <p style="font-size: 1.1em; line-height: 1.6;">{data.get('summary', '요약 없음').replace(chr(10), '<br>')}</p>
    </div>
    """, unsafe_allow_html=True)

    # 3. 준비물 (아이콘 그리드)
    st.markdown("### 🎒 챙겨야 할 준비물")
    supplies = data.get('supplies', [])
    
    if supplies:
        grid_html = '<div class="supplies-grid">'
        for item in supplies:
            grid_html += f"""
            <div class="supply-item">
                <span class="supply-icon">{item.get('icon', '🎒')}</span>
                <span class="supply-name">{item.get('name', '준비물')}</span>
            </div>
            """
        grid_html += '</div>'
        st.markdown(grid_html, unsafe_allow_html=True)
    else:
        st.info("특별한 준비물이 없습니다. 😄")

    # 4. 마감일 & 전체 번역
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"📅 **마감일:** {data.get('deadline', '없음')}")
    
    with st.expander("📄 전체 번역 내용 보기"):
        st.write(data.get('full_translation', '번역 없음'))


# ==========================================
# 10. [하단] 앱 설치 방법 가이드 (맨 아래 배치)
# ==========================================
st.divider() # 구분선 한 줄 긋기

with st.expander("📲 앱 설치 방법 보기 (여기를 누르세요)", expanded=False):
    st.markdown("""
    <div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px;'>
        <b style='color: #007BFF;'>안드로이드 (갤럭시)</b><br>
        1. 화면 오른쪽 위(또는 아래) <b>점 3개(⋮)</b> 클릭<br>
        2. <b>[홈 화면에 추가]</b> 또는 <b>[앱 설치]</b> 클릭<br>
        3. <b>[추가]</b> 버튼 클릭<br>
        <br>
        <b style='color: #007BFF;'>아이폰 (iOS)</b><br>
        1. 화면 아래 <b>내보내기(공유) 버튼</b> 클릭<br>
        2. 메뉴를 올려서 <b>[홈 화면에 추가]</b> 클릭<br>
        3. 오른쪽 위 <b>[추가]</b> 클릭<br>
        <br>
        <hr>
        💡 <b>가족 채팅방</b>에 이 주소를 공유해두면 설치 없이도 편하게 쓸 수 있어요!
    </div>
    """, unsafe_allow_html=True)