import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import json
import base64 

# ==========================================
# 1. 설정 (Configuration)
# ==========================================

# ⚠️ API 키 설정 (Secrets 사용)
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("🚨 API 키가 없습니다! Streamlit 웹사이트의 'Secrets' 설정을 확인해주세요.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# 🚨 [모델] 속도 제한 없고 안정적인 버전
model = genai.GenerativeModel('gemini-flash-latest') 

ASSETS_DIR = "assets"

# 페이지 설정
st.set_page_config(page_title="모두의 알림장", page_icon="🏫", layout="wide")

# 페이지 설정 (이게 제일 위에 있어야 함)
st.set_page_config(page_title="모두의 알림장", page_icon="🏫", layout="wide")

# 👇 [여기 추가] 모바일에서 주소창 없애고 앱처럼 보이게 하는 코드
st.markdown("""
    <style>
        /* 모바일에서 꾹 눌러서 글자 선택되는 것 방지 (앱처럼 느낌) */
        body { -webkit-user-select: none; -moz-user-select: none; -ms-user-select: none; user-select: none; }
    </style>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
""", unsafe_allow_html=True)

# ==========================================
# 2. 스타일 설정 (CSS) - 하늘색 박스 복구 완료
# ==========================================
st.markdown("""
    <style>
        html, body, [class*="st-"] { font-size: 22px !important; }
        
        /* 1. 파란색 버튼 스타일 */
        div.stButton > button, 
        button[kind="primary"],
        div[data-testid="stCameraInput"] button {
            background-color: #007BFF !important; 
            color: white !important;
            border: none !important; 
            font-weight: bold !important; 
            font-size: 20px !important; 
            padding: 10px 20px !important; 
            border-radius: 8px !important;
        }
        div.stButton > button:hover {
            background-color: #0056b3 !important; 
        }

        /* 2. 파일 업로더 텍스트 숨기기 */
        [data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] > div > div > small {
            display: none !important;
        }

        /* 3. 부제목 스타일 */
        .subtitle-text {
            text-align: center; 
            color: #555; 
            margin-top: 0px; 
            margin-bottom: 20px;
            font-weight: bold; 
            line-height: 1.5;
        }
        .subtitle-eng {
            font-size: 1.0em; 
            color: #555;       
            display: block;    
            margin-top: 5px;  
        }

        /* 4. [복구됨] 요약 박스 스타일 (원래 하늘색 디자인) */
        .summary-box {
            background-color: #F0F7FF; 
            padding: 25px; 
            border-radius: 15px; 
            border: 3px solid #4A90E2; 
            font-size: 24px; 
            line-height: 1.8; 
            color: #333;
            margin-top: 10px;
            margin-bottom: 20px;
        }

        /* 5. 아이콘 레이아웃 (90px 고정 + 자동 줄바꿈) */
        .icon-row-container {
            display: flex;
            flex-wrap: wrap;       
            gap: 30px;             
            justify-content: flex-start; 
            margin-bottom: 20px;
            padding: 10px 0;
        }
        .icon-item-box {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 90px;      
            flex-shrink: 0;   
        }
        .unified-icon {
            width: 90px !important;  
            height: 90px !important; 
            min-width: 90px;         
            min-height: 90px;        
            object-fit: contain; 
            display: block;
        }
        .icon-text {
            text-align: center;
            font-weight: bold;
            margin-top: 10px;
            font-size: 18px;    
            width: 110px;       
            word-wrap: break-word; 
            line-height: 1.3;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 필수 함수들
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
# 4. 다국어 UI 사전
# ==========================================
ui_lang = {
    "한국어": {
        "subtitle": "모든 가정을 위한 스마트 알림장<br><span class='subtitle-eng'>Smart Notice for All Families</span>",
        "tab_camera": "📸 사진 찍기", 
        "tab_upload": "📂 앨범에서 가져오기", 
        "cam_label": "알림장이나 안내문을 사진 찍어 주세요", 
        "upload_label": "👇 여기를 눌러 앨범에서 사진을 고르세요",
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
        "cam_label": "សូមចុចប៊ូតុងកាមេរ៉ាខាងក្រោម", 
        "upload_label": "បញ្ចូលរូបថត",
        "result_header": "🎨 សម្ភារៈ",
        "summary_header": "📢 សង្ខេប", "trans_btn": "មើលការបកប្រែ"
    }
}

# ==========================================
# 5. 스마트 UI 매칭 함수
# ==========================================
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
# 6. [제목] 상단 배너 이미지 & 타이틀 배치
# ==========================================

# 1) 배너 파일 찾기 (jpg, png, jpeg 다 찾아봄)
banner_candidates = ["banner.jpg", "banner.png", "banner.jpeg", "image_2c0b96.jpg"]
banner_found = False

for filename in banner_candidates:
    banner_path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(banner_path):
        st.image(banner_path, use_container_width=True)
        banner_found = True
        break # 파일을 찾았으면 반복 중단

# 2) 배너가 없을 경우 (경고 대신 그냥 타이틀만 띄움)
if not banner_found:
    # 혹시 파일이 안 올라갔을까 봐 작게 알려줌 (나중에 삭제 가능)
    st.caption("※ 배너 이미지를 assets 폴더에 넣어주세요.")

# 3) 그 아래에 타이틀 문구 배치
st.markdown("""
    <h1 style='color: #FF9F1C; text-align: center; margin-top: 10px; margin-bottom: 0px;'>
        🏫 모두의 AI 알림장
    </h1>
""", unsafe_allow_html=True)

# ==========================================
# 7. 언어 선택 및 입력 로직
# ==========================================
st.markdown("### 🌍 언어를 선택하세요 (Language)")

radio_options = [
    "한국어 (Korean, 한국어)", 
    "중국어 (Chinese, 中文)", 
    "베트남어 (Vietnamese, Tiếng Việt)", 
    "영어 (English, English)", 
    "필리핀어 (Tagalog, Filipino)", 
    "태국어 (Thai, ภาษาไทย)", 
    "일본어 (Japanese, 日本語)", 
    "러시아어 (Russian, Русский)", 
    "몽골어 (Mongolian, Монгол хэл)", 
    "우즈베크어 (Uzbek, Oʻzbekcha)", 
    "캄보디아어 (Cambodian, ភាសាខ្មែរ)", 
    "직접 입력 (Type Language)"
]

selected_radio = st.radio("Label Hidden", radio_options, horizontal=False, label_visibility="collapsed")

final_target_lang = "한국어"
current_ui = ui_lang["한국어"]

if selected_radio == "직접 입력 (Type Language)":
    col1, col2 = st.columns([3, 1])
    with col1:
        st.text_input(
            "나라/언어 입력", 
            placeholder="예: France, Nepal",
            label_visibility="collapsed",
            key="widget_input",
            on_change=apply_input 
        )
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

st.divider()

# ==========================================
# 8. 메인 화면
# ==========================================
st.markdown(f"""
    <div class='subtitle-text'><h3>{current_ui['subtitle']}</h3></div>
""", unsafe_allow_html=True)

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
# 9. AI 분석 실행
# ==========================================
if img_file and final_target_lang:
    with st.spinner(f"🤖 AI가 분석 중입니다... (Target: {final_target_lang})"):
        
        raw_image = Image.open(img_file)
        image = resize_image_for_speed(raw_image)
        
        output_format_example = """
        {
            "detected_lang": "Mongolian",
            "summary": "Margash...",
            "translation": "(Translation)",
            "keywords": [
                {"file_key": "운동화", "display_word": "운동화 (Language)", "emoji": "👟"}
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
           - Write ONLY in 'detected_lang'.
           - **Goal**: Summarize for elderly users (Easy to read), but **NEVER** use words like "Grandma(할머니)", "Grandchild(손주)". 
           - **Style**: Strictly **Noun-ending (명사형)**. No full sentences (e.g., do not use '입니다', '하세요'). No conversational tone.
           - **Format**:
             [Title]
             (Empty Line)
             시간: MM. DD(Day)
             장소: ...
             준비물: ...
             숙제: ...
             (Add other keys if necessary)
           - **Constraint**: Keep it concise. No long sentences.
           - Use '\\n' for line breaks.
           
        3. **translation**: Translate the FULL content into 'detected_lang'.
        
        4. **keywords**: Extract **ALL** necessary supplies or key items mentioned in the notice.
           - **Constraint**: Do NOT limit the number. If there are 5 items, extract 5. If 1, extract 1. (Max 8 items).
           - "file_key": The word in **KOREAN** (Standard noun for file matching). e.g., "운동화".
           - "display_word": The word in **'detected_lang'**. 
             **IMPORTANT**: If 'detected_lang' is Korean, this MUST be in Korean. 
             e.g., If detected_lang is English -> "Sneakers", If Korean -> "운동화".
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
            
            # [결과 1] 준비물 아이콘 (Flexbox 적용 - 크기 고정)
            st.markdown(f"### {current_ui['result_header']}")
            
            keywords_data = data.get('keywords', [])
            
            if keywords_data:
                html_content = '<div class="icon-row-container">'
                
                for item in keywords_data:
                    file_key = item.get('file_key', '').strip()
                    display_word = item.get('display_word', item.get('word', ''))
                    emoji = item.get('emoji', '❓')
                    
                    icon_path = None
                    for ext in ['.png', '.jpg', '.jpeg']:
                        path = os.path.join(ASSETS_DIR, file_key + ext)
                        if os.path.exists(path): icon_path = path; break
                    
                    html_content += '<div class="icon-item-box">'
                    
                    if icon_path:
                        img_base64 = get_image_base64(icon_path)
                        html_content += f"<img src='data:image/png;base64,{img_base64}' class='unified-icon'>"
                    else:
                        html_content += f"<div class='unified-icon' style='font-size: 50px; display: flex; align-items: center; justify-content: center;'>{emoji}</div>"
                        
                    html_content += f"<p class='icon-text'>{display_word}</p>"
                    html_content += '</div>'

                html_content += '</div>'
                st.markdown(html_content, unsafe_allow_html=True)
            else:
                 st.info("아이콘으로 표시할 내용이 없습니다.")

            st.write("") 
            
            # [결과 2] 요약 (하늘색 박스)
            st.markdown(f"### {current_ui['summary_header']}")
            summary_text = data.get('summary', '요약 없음').replace('\n', '<br>')
            st.markdown(f"""
                <div class='summary-box'>
                    {summary_text}
                </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            
            # [결과 3] 전체 번역문
            detected = data.get('detected_lang', final_target_lang)
            with st.expander(f"🌍 {current_ui['trans_btn']} ({detected})"):
                st.markdown(f"<div style='font-size: 20px; line-height: 1.8;'>{data.get('translation', '번역 실패')}</div>", unsafe_allow_html=True)
                
        except Exception as e:
            st.error("오류가 발생했습니다.")
            st.markdown(f"<div class='error-details'>{str(e)}</div>", unsafe_allow_html=True)

# ==========================================
# 10. [사이드바] 앱 설치 및 사용 가이드
# ==========================================
with st.sidebar:
    st.header("📲 앱처럼 편하게 쓰기")
    st.markdown("매번 인터넷 주소를 치지 않고, **바탕화면 아이콘**으로 접속하는 방법입니다.")
    
    st.divider()
    
    # 1. 갤럭시 (안드로이드) 안내
    with st.expander("🤖 갤럭시(삼성) 설치법"):
        st.markdown("""
        1. 화면 오른쪽 위(또는 아래)의 **점 3개(⋮)** 또는 **줄 3개(≡)** 버튼을 누르세요.
        2. 메뉴에서 **[홈 화면에 추가]** (또는 '앱 설치')를 찾아서 누르세요.
        3. **[추가]** 버튼을 누르세요
        """)

    # 2. 아이폰 (iOS) 안내
    with st.expander("🍎 아이폰(iOS) 설치법"):
        st.markdown("""
        1. 화면 맨 아래 가운데에 있는 **내보내기 버튼(네모 위 화살표)**을 누르세요.
        2. 메뉴를 위로 올려서 **[홈 화면에 추가]**를 누르세요.
        3. 오른쪽 위 **[추가]**를 누르세요.
        """)
        
    st.divider()
    
    # 3. 카카오톡 공유 안내 (어르신용 필살기)
    st.info("💡 **가장 쉬운 방법!**\n\n가족 채팅방이나 '나에게 보내기'로 이 주소를 공유해두세요. 필요할 때마다 카톡에서 바로 누르면 됩니다.")


이 코드와 기능과 디자인은 다 똑같이 가는거야. 새로 발급받은 키만 원래 자리에 넣으면 되는 거 아냐? 
