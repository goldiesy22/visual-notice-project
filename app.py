import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import json
import base64

# ==========================================
# 1. 설정 (Configuration)
# ==========================================

# ⚠️ [필수] 여기에 사용자님의 실제 API 키를 붙여넣으세요!
GOOGLE_API_KEY = "AIzaSyBePQTVzbiFaPH7InG7pmkYr_3YCbaRfK0"

# 🚨 [수정 완료] 오류가 나던 '2.5' 버전을 '1.5'로 변경했습니다. (무료 사용량 넉넉함)
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

ASSETS_DIR = "assets"

# 페이지 설정
st.set_page_config(page_title="모두의 알림장", page_icon="🏫", layout="wide")

# ==========================================
# 2. 로직 및 함수
# ==========================================
if 'custom_input' not in st.session_state:
    st.session_state['custom_input'] = ''

def apply_input():
    st.session_state['custom_input'] = st.session_state.widget_input

def resize_image_for_speed(image, max_width=800):
    try:
        w_percent = (max_width / float(image.size[0]))
        h_size = int((float(image.size[1]) * float(w_percent)))
        resized_img = image.resize((max_width, h_size), Image.Resampling.LANCZOS)
        return resized_img
    except Exception as e:
        return image

def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

# ==========================================
# 3. 다국어 UI 사전
# ==========================================
ui_lang = {
    "한국어": {
        "subtitle": "모든 가정을 위한 스마트 알림장<br><span class='subtitle-eng'>Smart Notice for All Families</span>",
        "tab_camera": "📸 사진 찍기",
        "tab_upload": "📂 앨범에서 가져오기",
        "cam_label": "⬇️ 아래 파란색 버튼을 눌러 사진을 찍으세요",
        "upload_label": "⬇️ 아래 파란색 버튼을 눌러 앨범을 여세요",
        "result_header": "🎨 준비물 그림 확인",
        "summary_header": "📢 핵심 내용 요약", "trans_btn": "번역문 보기"
    },
    "영어": {
        "subtitle": "Smart Notice for All Families",
        "tab_camera": "📸 Take Photo", "tab_upload": "📂 Upload",
        "cam_label": "Please take a photo of the notice",
        "upload_label": "Upload Image File",
        "result_header": "🎨 Supplies Icons",
        "summary_header": "📢 Summary", "trans_btn": "View Translation"
    },
    "중국어": {
        "subtitle": "为所有家庭提供的智能通知",
        "tab_camera": "📸 拍照", "tab_upload": "📂 上传照片",
        "cam_label": "请拍摄通知单或公告",
        "upload_label": "上传照片",
        "result_header": "🎨 准备物品图标",
        "summary_header": "📢 核心摘要", "trans_btn": "查看翻译"
    },
    "베트남어": {
        "subtitle": "Thông báo thông minh cho mọi gia đình",
        "tab_camera": "📸 Chụp ảnh", "tab_upload": "📂 Tải ảnh lên",
        "cam_label": "Vui lòng chụp ảnh thông báo",
        "upload_label": "Tải ảnh lên",
        "result_header": "🎨 Hình ảnh chuẩn bị",
        "summary_header": "📢 Tóm tắt nội dung", "trans_btn": "Xem bản dịch"
    },
    "필리핀어": {
        "subtitle": "Smart Notification para sa Lahat ng Pamilya",
        "tab_camera": "📸 Kumuha ng litrato", "tab_upload": "📂 I-upload",
        "cam_label": "Paki-picturan ang notice o anunsyo",
        "upload_label": "I-upload ang larawan",
        "result_header": "🎨 Mga Kailangan",
        "summary_header": "📢 Buod", "trans_btn": "Tingnan ang Salin"
    },
    "태국어": {
        "subtitle": "การแจ้งเตือนอัจฉริยะสำหรับทุกครอบครัว",
        "tab_camera": "📸 ถ่ายภาพ", "tab_upload": "📂 อัปโหลด",
        "cam_label": "กรุณาถ่ายภาพประกาศ",
        "upload_label": "อัปโหลดรูปภาพ",
        "result_header": "🎨 สิ่งที่ต้องเตรียม",
        "summary_header": "📢 สรุป", "trans_btn": "ดูคำแปล"
    },
    "일본어": {
        "subtitle": "すべての家庭のためのスマート連絡帳",
        "tab_camera": "📸 写真を撮る", "tab_upload": "📂 アルバム",
        "cam_label": "連絡帳を撮影してください",
        "upload_label": "写真をアップロード",
        "result_header": "🎨 持ち物確認",
        "summary_header": "📢 要約", "trans_btn": "翻訳を見る"
    },
    "러시아어": {
        "subtitle": "Умные уведомления для всех семей",
        "tab_camera": "📸 Сделать фото", "tab_upload": "📂 Загрузить",
        "cam_label": "Сфотографируйте уведомление",
        "upload_label": "Загрузить фото",
        "result_header": "🎨 Предметы",
        "summary_header": "📢 Сводка", "trans_btn": "Посмотреть перевод"
    },
    "몽골어": {
        "subtitle": "Бүх гэр бүлд зориулсан ухаалаг мэдэгдэл",
        "tab_camera": "📸 Зураг авах", "tab_upload": "📂 Байршуулах",
        "cam_label": "Мэдэгдлийн зургийг авна уу",
        "upload_label": "Зураг байршуулах",
        "result_header": "🎨 Бэлтгэл зүйлс",
        "summary_header": "📢 Хураангуй", "trans_btn": "Орчуулгыг харах"
    },
    "우즈베크어": {
        "subtitle": "Barcha oilalar uchun aqlli xabarnoma",
        "tab_camera": "📸 Rasmga olish", "tab_upload": "📂 Yuklash",
        "cam_label": "E'lonni rasmga oling",
        "upload_label": "Rasmni yuklash",
        "result_header": "🎨 Kerakli narsalar",
        "summary_header": "📢 Xulosa", "trans_btn": "Tarjimani ko'rish"
    },
    "캄보디아어": {
        "subtitle": "ការជូនដំណឹងឆ្លាតវៃសម្រាប់គ្រួសារទាំងអស់",
        "tab_camera": "📸 ថតរូប", "tab_upload": "📂 ផ្ទុកឡើង",
        "cam_label": "សូមថតរូបសេចក្តីជូនដំណឹង", 
        "upload_label": "បញ្ចូលរូបថត",
        "result_header": "🎨 សម្ភារៈ",
        "summary_header": "📢 សង្ខេប", "trans_btn": "មើលការបកប្រែ"
    }
}

def get_ui_language(user_input):
    if not user_input: return ui_lang["한국어"]
    text = user_input.lower()
    if any(x in text for x in ['china', 'chinese', 'taiwan', '중국', '대만']): return ui_lang["중국어"]
    if any(x in text for x in ['viet', '베트남']): return ui_lang["베트남어"]
    if any(x in text for x in ['phil', 'tagalog', '필리핀']): return ui_lang["필리핀어"]
    if any(x in text for x in ['thai', '태국']): return ui_lang["태국어"]
    if any(x in text for x in ['japan', '일본']): return ui_lang["일본어"]
    if any(x in text for x in ['russia', '러시아', 'kazakh']): return ui_lang["러시아어"]
    if any(x in text for x in ['mongol', '몽골']): return ui_lang["몽골어"]
    if any(x in text for x in ['uzbek', '우즈벡']): return ui_lang["우즈베크어"]
    if any(x in text for x in ['cambodia', 'khmer', '캄보디아']): return ui_lang["캄보디아어"]
    return ui_lang["영어"]

# ==========================================
# 4. 메인 화면 구성 및 언어 선택
# ==========================================
st.markdown("""
    <h1 style='color: #FF9F1C; text-align: center; margin-bottom: 0px;'>🏫 모두의 AI 알림장</h1>
""", unsafe_allow_html=True)

st.markdown("### 🌍 언어를 선택하세요 (Language)")

radio_options = [
    "한국어 (Korean, 한국어)", "중국어 (Chinese, 中文)", "베트남어 (Vietnamese, Tiếng Việt)",
    "영어 (English, English)", "필리핀어 (Tagalog, Filipino)", "태국어 (Thai, ภาษาไทย)",
    "일본어 (Japanese, 日本語)", "러시아어 (Russian, Русский)", "몽골어 (Mongolian, Монгол хэл)",
    "우즈베크어 (Uzbek, Oʻzbekcha)", "캄보디아어 (Cambodian, ភាសាខ្មែរ)", "직접 입력 (Type Language)"
]

selected_radio = st.radio("Label Hidden", radio_options, horizontal=False, label_visibility="collapsed")

final_target_lang = "한국어"
current_ui = ui_lang["한국어"]

if selected_radio == "직접 입력 (Type Language)":
    col1, col2 = st.columns([3, 1])
    with col1:
        st.text_input("나라/언어 입력", placeholder="예: France, Nepal", label_visibility="collapsed", key="widget_input", on_change=apply_input)
    with col2:
        st.button("적용 (Apply)", on_click=apply_input, use_container_width=True)

    saved_val = st.session_state.get('custom_input', '').strip()
    if saved_val:
        final_target_lang = saved_val
        current_ui = get_ui_language(final_target_lang)
    else:
        current_ui = ui_lang["한국어"]
        final_target_lang = ""
else:
    st.session_state['custom_input'] = ''
    lang_key = selected_radio.split(" ")[0]
    current_ui = ui_lang.get(lang_key, ui_lang["한국어"])
    if "(" in selected_radio:
        final_target_lang = selected_radio.split("(")[1].split(",")[0].strip()
    else:
        final_target_lang = lang_key

# ==========================================
# 5. 스타일 설정 (CSS) - 🚨 버튼 정밀 타겟팅 수정
# ==========================================
is_korean_mode = ("Korean" in final_target_lang) or (final_target_lang == "한국어")

st.markdown("""
    <style>
        /* 아이콘 통일 스타일 */
        .unified-icon { width: 60px; height: 60px; object-fit: contain; display: block; margin: 0 auto; }
        .unified-emoji-container { width: 60px; height: 60px; display: flex; justify-content: center; align-items: center; font-size: 50px; margin: 0 auto; }
        .icon-text { text-align: center; font-weight: bold; margin-top: 8px; font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

if is_korean_mode:
    st.markdown("""
        <style>
            html, body, [class*="st-"] { font-size: 22px !important; }
            
            /* [공통] 기본 파란 버튼 스타일 */
            div.stButton > button, button[kind="primary"],
            div[data-testid="stFileUploader"] button {
                background-color: #007BFF !important; color: white !important;
                border: none !important; font-weight: bold !important; border-radius: 8px !important;
                position: relative; overflow: hidden; 
            }

            /* 🚨 중요 수정: '모든' 버튼이 아니라 'primary(메인)' 버튼만 골라서 스타일 적용 */
            div[data-testid="stCameraInput"] button[kind="primary"] {
                background-color: #007BFF !important; 
                text-indent: -9999px; /* 영어 숨기기 */
                padding: 40px 0px !important;
            }
            div[data-testid="stCameraInput"] button[kind="primary"]::after {
                content: "📸 사진찍기";
                text-indent: 0;
                color: white !important;
                display: flex;
                justify-content: center;
                align-items: center;
                position: absolute;
                top: 0; left: 0;
                width: 100%; height: 100%;
                font-size: 24px !important;
                font-weight: bold;
                background-color: #007BFF;
            }

            /* 🚨 중요 수정: 삭제(Clear) 버튼은 'secondary'만 타겟팅 */
            div[data-testid="stCameraInput"] button[kind="secondary"] {
                text-indent: -9999px; /* 영어 숨기기 */
            }
            div[data-testid="stCameraInput"] button[kind="secondary"]::after {
                content: "🗑 다시 찍기";
                text-indent: 0;
                display: block;
                position: absolute;
                top: 50%; left: 50%;
                transform: translate(-50%, -50%);
                font-size: 18px !important;
                font-weight: bold;
                color: #333 !important; /* 글씨 색상 */
            }

            /* 2. [앨범 버튼] */
            [data-testid="stFileUploaderDropzone"] button {
                text-indent: -9999px;
                min-width: 180px !important;
            }
            [data-testid="stFileUploaderDropzone"] button::after {
                content: "📂 사진 찾아보기";
                text-indent: 0;
                color: white !important;
                display: flex;
                justify-content: center;
                align-items: center;
                position: absolute;
                top: 0; left: 0;
                width: 100%; height: 100%;
                font-size: 20px !important;
                font-weight: bold;
                background-color: #007BFF;
            }

            [data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] > div > div > small {
                display: none !important;
            }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
            html, body, [class*="st-"] { font-size: 22px !important; }
            div.stButton > button, button[kind="primary"],
            div[data-testid="stCameraInput"] button, div[data-testid="stFileUploader"] button {
                background-color: #007BFF !important; color: white !important;
                border: none !important; font-weight: bold !important;
                padding: 10px 20px !important; border-radius: 8px !important;
            }
        </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <style>
        .subtitle-text { text-align: center; color: #555; margin-bottom: 20px; font-weight: bold; line-height: 1.5; }
        .subtitle-eng { font-size: 1.0em; color: #555; display: block; margin-top: 5px; }
        .summary-box { background-color: #F0F7FF; padding: 25px; border-radius: 15px; border: 3px solid #4A90E2; font-size: 24px; line-height: 1.8; color: #333; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 6. 탭 및 기능
# ==========================================
st.divider()

st.markdown(f"<div class='subtitle-text'><h3>{current_ui['subtitle']}</h3></div>", unsafe_allow_html=True)
st.write("")

tab1, tab2 = st.tabs([current_ui['tab_camera'], current_ui['tab_upload']])
img_file = None

with tab1:
    camera_img = st.camera_input(current_ui['cam_label'])
    if camera_img: img_file = camera_img
with tab2:
    uploaded_img = st.file_uploader(current_ui['upload_label'], type=['png', 'jpg', 'jpeg'])
    if uploaded_img: img_file = uploaded_img

# ==========================================
# 7. AI 분석
# ==========================================
if img_file and final_target_lang:
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == "여기에_새로운_API_키를_붙여넣으세요":
         st.error("⚠️ Google API 키가 설정되지 않았습니다. app.py 파일 상단의 키 값을 확인해주세요.")
    else:
        with st.spinner(f"🤖 AI가 분석 중입니다... (Target: {final_target_lang})"):
            raw_image = Image.open(img_file)
            image = resize_image_for_speed(raw_image)

            output_format_example = """
            {
                "detected_lang": "Mongolian",
                "summary": "Margash...",
                "translation": "(Translation)",
                "keywords": [
                    {"file_key": "운동화", "display_word": "Sneakers", "emoji": "👟"}
                ]
            }
            """

            prompt = f"""
            You are a smart assistant for school notices.

            [INPUT INFO]
            User Input: "{final_target_lang}"

            [TASK 1: DETECT LANGUAGE]
            1. Determine the target language based on user input.

            [TASK 2: PROCESSING]
            1. **detected_lang**: Name of the language.
            2. **summary**:
               - **Language**: Write STRICTLY in 'detected_lang'.
               - **CRITICAL**: Translate ALL labels (Time, Place, Supplies, Homework) into 'detected_lang'.
                 (e.g., If 'detected_lang' is English, use "Time:", NOT "시간:").
               - **Prohibition**: Do NOT use Korean characters if 'detected_lang' is not Korean.
               - **Goal**: Summarize for elderly users (Easy to read), but **NEVER** use words like "Grandma(할머니)".
               - **Style**: Strictly **Noun-ending (명사형)**. No full sentences.
               - **Format Example (Target: English)**:
                 [Field Trip Notice]

                 Time: May 10th (Fri)
                 Place: Citizen Park
                 Supplies: Lunch box, Water
               - **Format Example (Target: Korean)**:
                 [현장학습 안내]

                 시간: 5. 10(금)
                 장소: 시민공원
                 준비물: 도시락, 물
               - Use '\\n' for line breaks.

            3. **translation**: Translate the FULL content into 'detected_lang'.

            4. **keywords**: Extract 3 key items.
               - "file_key": The word in **KOREAN** (Standard noun for file matching). e.g., "운동화".
               - "display_word": The word in **'detected_lang'** (For display). e.g., "Sneakers".
               - "emoji": Matching emoji.

            [OUTPUT JSON]
            {output_format_example}
            """

            try:
                response = model.generate_content([prompt, image])
                text_response = response.text
                if "```json" in text_response:
                    text_response = text_response.split("```json")[1].split("```")[0]
                elif "```" in text_response:
                    text_response = text_response.split("```")[1].split("```")[0]

                data = json.loads(text_response.strip(), strict=False)

                st.divider()

                # [결과 1] 아이콘 출력
                st.markdown(f"### {current_ui['result_header']}")
                if 'keywords' in data:
                    cols = st.columns(len(data['keywords']))
                    for idx, item in enumerate(data['keywords']):
                        file_key = item.get('file_key', '').strip()
                        display_word = item.get('display_word', item.get('word', ''))
                        emoji = item.get('emoji', '❓')
                        icon_path = None
                        for ext in ['.png', '.jpg', '.jpeg']:
                            path = os.path.join(ASSETS_DIR, file_key + ext)
                            if os.path.exists(path):
                                icon_path = path; break

                        with cols[idx]:
                            if icon_path:
                                img_base64 = get_image_base64(icon_path)
                                st.markdown(f"<img src='data:image/png;base64,{img_base64}' class='unified-icon'>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div class='unified-emoji-container'>{emoji}</div>", unsafe_allow_html=True)
                            
                            st.markdown(f"<p class='icon-text'>{display_word}</p>", unsafe_allow_html=True)

                st.write("")

                # [결과 2] 요약
                st.markdown(f"### {current_ui['summary_header']}")
                summary_text = data.get('summary', '요약 없음').replace('\n', '<br>')
                st.markdown(f"<div class='summary-box'>{summary_text}</div>", unsafe_allow_html=True)

                st.write("")

                # [결과 3] 전체 번역문
                detected = data.get('detected_lang', final_target_lang)
                with st.expander(f"🌍 {current_ui['trans_btn']} ({detected})"):
                    st.markdown(f"<div style='font-size: 20px; line-height: 1.8;'>{data.get('translation', '번역 실패')}</div>", unsafe_allow_html=True)

            except Exception as e:
                st.error("오류가 발생했습니다.")
                st.markdown(f"<div class='error-details'>{str(e)}</div>", unsafe_allow_html=True)