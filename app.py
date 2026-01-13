import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import json
import base64
from gtts import gTTS
import io

# ==========================================
# 1. 설정 및 모델 "강제" 지정 (수정됨)
# ==========================================

if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("🚨 API 키가 없습니다! Secrets 설정을 확인해주세요.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# 🚨 [모델 연결 로직 수정]
# 2.5-flash(20회 제한)가 잡히는 것을 막기 위해 '1.5'가 포함된 모델만 강제로 찾습니다.
try:
    # 1. 서버에 있는 모델 명단을 다 가져옵니다.
    all_models = [m.name for m in genai.list_models()]
    
    final_model_name = None
    
    # 2. 우리가 원하는 "안전한 모델(1.5)" 우선순위 목록
    priority_targets = [
        "gemini-1.5-flash",       # 1순위: 표준 1.5 Flash
        "gemini-1.5-flash-001",   # 2순위: 구버전 호환 1.5 Flash
        "gemini-1.5-flash-002",   # 3순위: 최신 안정화 1.5 Flash
        "gemini-1.5-pro",         # 4순위: Flash가 정 안되면 Pro라도 씀
    ]

    # 3. 명단 대조 (2.5 버전이나 latest는 절대 안 뽑히게 함)
    for target in priority_targets:
        for available in all_models:
            # 명단에 target 이름이 포함되어 있고, "2.5"나 "latest"가 아니어야 함
            if target in available and "2.5" not in available and "latest" not in available:
                final_model_name = available
                break
        if final_model_name:
            break
            
    # 4. 모델 연결
    if final_model_name:
        model = genai.GenerativeModel(final_model_name)
        # (확인용) 사이드바에 연결된 모델명 표시 (성공 시 gemini-1.5-flash... 가 떠야 함)
        st.sidebar.success(f"✅ 연결 모델: {final_model_name}")
    else:
        # 비상용: 명단에서 못 찾아도 강제로 1.5를 지정 (라이브러리 믿고 던짐)
        model = genai.GenerativeModel('gemini-1.5-flash')
        st.sidebar.warning("⚠️ 강제 지정 모드: gemini-1.5-flash")

except Exception as e:
    st.error(f"❌ 모델 설정 오류: {e}")
    st.stop()


ASSETS_DIR = "assets"

# 페이지 설정
st.set_page_config(page_title="모두의 알림장", page_icon="🏫", layout="wide")

# 👇 [PWA 설정] 앱 모드 & 드래그 방지
st.markdown("""
    <style>
        body { -webkit-user-select: none; -moz-user-select: none; -ms-user-select: none; user-select: none; }
    </style>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="mobile-web-app-capable" content="yes">
""", unsafe_allow_html=True)

# ==========================================
# 2. 스타일 설정 (CSS)
# ==========================================
st.markdown("""
    <style>
        html, body, [class*="st-"] { font-size: 22px !important; }
        
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

        [data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] > div > div > small {
            display: none !important;
        }

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
        
        /* 텍스트 드래그 허용 */
        .summary-box, p, li, .stMarkdown, div[data-testid="stMarkdownContainer"] {
            -webkit-user-select: text !important;
            -moz-user-select: text !important;
            -ms-user-select: text !important;
            user-select: text !important;
            cursor: text !important;
        }

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

        /* PC 화면 대응 */
        @media (min-width: 768px) {
            .icon-item-box { width: 180px; }
            .unified-icon { width: 180px !important; height: 180px !important; min-width: 180px; min-height: 180px; }
            .unified-icon[style*="font-size: 50px"] { font-size: 100px !important; }
            .icon-text { font-size: 26px; width: 200px; margin-top: 15px; }
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

def get_tts_lang_code(lang_name):
    lang_map = {
        '한국어': 'ko', 'Korean': 'ko', '영어': 'en', 'English': 'en',
        '중국어': 'zh-CN', 'Chinese': 'zh-CN', '베트남어': 'vi', 'Vietnamese': 'vi',
        '필리핀어': 'tl', 'Tagalog': 'tl', 'Filipino': 'tl', '태국어': 'th', 'Thai': 'th',
        '일본어': 'ja', 'Japanese': 'ja', '러시아어': 'ru', 'Russian': 'ru',
        '몽골어': 'mn', '우즈베크어': 'uz', '캄보디아어': 'km'
    }
    return lang_map.get(lang_name.split(' ')[0], 'en')

# ==========================================
# 4. 다국어 UI 사전
# ==========================================
ui_lang = {
    "한국어": {
        "subtitle": "모든 가정을 위한 스마트 알림장<br><span class='subtitle-eng'>Smart Notice for All Families</span>",
        "tab_camera": "📸 사진 찍기", "tab_upload": "📂 앨범에서 가져오기", 
        "cam_label": "알림장이나 안내문을 사진 찍어 주세요", "upload_label": "👇 여기를 눌러 앨범에서 사진을 고르세요",
        "result_header": "🎨 준비물 그림 확인", "summary_header": "📢 핵심 내용 요약", "trans_btn": "번역문 보기"
    },
    "영어": { 
        "subtitle": "Smart Notice for All Families",
        "tab_camera": "📸 Take Photo", "tab_upload": "📂 Upload",
        "cam_label": "Please take a photo of the notice", "upload_label": "Upload Image File",
        "result_header": "🎨 Supplies Icons", "summary_header": "📢 Summary", "trans_btn": "View Translation"
    },
    "중국어": { 
        "subtitle": "为所有家庭提供的智能通知",
        "tab_camera": "📸 拍照", "tab_upload": "📂 上传照片",
        "cam_label": "请拍摄通知单或公告", "upload_label": "上传照片",
        "result_header": "🎨 准备物品图标", "summary_header": "📢 核心摘要", "trans_btn": "查看翻译"
    },
    "베트남어": { 
        "subtitle": "Thông báo thông minh cho mọi gia đình",
        "tab_camera": "📸 Chụp ảnh", "tab_upload": "📂 Tải ảnh lên",
        "cam_label": "Vui lòng chụp ảnh thông báo", "upload_label": "Tải ảnh lên",
        "result_header": "🎨 Hình ảnh chuẩn bị", "summary_header": "📢 Tóm tắt nội dung", "trans_btn": "Xem bản dịch"
    },
    "필리핀어": { 
        "subtitle": "Smart Notification para sa Lahat ng Pamilya",
        "tab_camera": "📸 Kumuha ng litrato", "tab_upload": "📂 I-upload",
        "cam_label": "Paki-picturan ang notice o anunsyo", "upload_label": "I-upload ang larawan",
        "result_header": "🎨 Mga Kailangan", "summary_header": "📢 Buod", "trans_btn": "Tingnan ang Salin"
    },
    "태국어": { 
        "subtitle": "การแจ้งเตือนอัจฉริยะสำหรับทุกครอบครัว",
        "tab_camera": "📸 ถ่ายภาพ", "tab_upload": "📂 อัปโหลด",
        "cam_label": "กรุณาถ่ายภาพประกาศ", "upload_label": "อัปโหลดรูปภาพ",
        "result_header": "🎨 สิ่งที่ต้องเตรียม", "summary_header": "📢 สรุป", "trans_btn": "ดูคำแปล"
    },
    "일본어": {
        "subtitle": "すべての家庭のためのスマート連絡帳",
        "tab_camera": "📸 写真を撮る", "tab_upload": "📂 アルバム",
        "cam_label": "連絡帳を撮影してください", "upload_label": "写真をアップロード",
        "result_header": "🎨 持ち物確認", "summary_header": "📢 要約", "trans_btn": "翻訳を見る"
    },
    "러시아어": { 
        "subtitle": "Умные уведомления для всех семей",
        "tab_camera": "📸 Сделать фото", "tab_upload": "📂 Загрузить",
        "cam_label": "Сфотографируйте уведомление", "upload_label": "Загрузить фото",
        "result_header": "🎨 Предметы", "summary_header": "📢 Сводка", "trans_btn": "Посмотреть перевод"
    },
    "몽골어": {
        "subtitle": "Бүх гэр бүлд зориулсан ухаалаг мэдэгдэл",
        "tab_camera": "📸 Зураг авах", "tab_upload": "📂 Байршуулах",
        "cam_label": "Мэдэгдлийн зургийг авна уу", "upload_label": "Зураг байршуулах",
        "result_header": "🎨 Бэлтгэл зүйлс", "summary_header": "📢 Хураангуй", "trans_btn": "Орчуулгыг харах"
    },
    "우즈베크어": { 
        "subtitle": "Barcha oilalar uchun aqlli xabarnoma",
        "tab_camera": "📸 Rasmga olish", "tab_upload": "📂 Yuklash",
        "cam_label": "E'lonni rasmga oling", "upload_label": "Rasmni yuklash",
        "result_header": "🎨 Kerakli narsalar", "summary_header": "📢 Xulosa", "trans_btn": "Tarjimani ko'rish"
    },
    "캄보디아어": { 
        "subtitle": "ការជូនដំណឹងឆ្លាតវៃសម្រាប់គ្រួសារទាំងអស់",
        "tab_camera": "📸 ថតរូប", "tab_upload": "📂 ផ្ទុកឡើង",
        "cam_label": "សូមចុចប៊ូតុងកាមេរ៉ាខាងក្រោម", "upload_label": "បញ្ចូលរូបថត",
        "result_header": "🎨 សម្ភារៈ", "summary_header": "📢 សង្ខេប", "trans_btn": "មើលការបកប្រែ"
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
# 6. 상단 배너 및 UI
# ==========================================
banner_candidates = ["banner.jpg", "banner.png", "banner.jpeg", "image_2c0b96.jpg"]
banner_found = False
for filename in banner_candidates:
    banner_path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(banner_path):
        st.image(banner_path, use_container_width=True)
        banner_found = True
        break 

if not banner_found:
    st.caption("※ 배너 이미지를 assets 폴더에 넣어주세요.")

st.markdown("""
    <h1 style='color: #FF9F1C; text-align: center; margin-top: 10px; margin-bottom: 0px;'>
        🏫 모두의 AI 알림장
    </h1>
""", unsafe_allow_html=True)

# ==========================================
# 7. 언어 선택
# ==========================================
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

st.divider()

# ==========================================
# 8. 메인 로직
# ==========================================
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
        
        [TASK]
        1. detected_lang: Name of the language.
        2. summary: Summarize in 'detected_lang'. Strict Noun-ending style. Format: [Title]\\n시간:...\\n장소:...\\n준비물:...\\n숙제:...
        3. translation: Translate FULL content.
        4. keywords: Extract ALL supplies. "file_key"=Korean noun, "display_word"=Target Lang, "emoji"=icon.
        
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
            
            # [결과 1] 준비물
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
                    html_content += f"<p class='icon-text'>{display_word}</p></div>"
                html_content += '</div>'
                st.markdown(html_content, unsafe_allow_html=True)
            else:
                 st.info("아이콘으로 표시할 내용이 없습니다.")

            st.write("") 
            
            # [결과 2] 요약 및 TTS
            st.markdown(f"### {current_ui['summary_header']}")
            summary_text = data.get('summary', '요약 없음')
            
            try:
                if summary_text.strip(): 
                    tts_lang = get_tts_lang_code(final_target_lang)
                    tts = gTTS(text=summary_text, lang=tts_lang)
                    mp3_fp = io.BytesIO()
                    tts.write_to_fp(mp3_fp)
                    mp3_fp.seek(0)
                    st.audio(mp3_fp.getvalue(), format='audio/mpeg') 
            except Exception as e:
                st.warning(f"🔊 음성 생성 실패: {e}")

            st.markdown(f"<div class='summary-box'>{summary_text.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
            
            st.write("")
            
            # [결과 3] 번역
            detected = data.get('detected_lang', final_target_lang)
            with st.expander(f"🌍 {current_ui['trans_btn']} ({detected})"):
                st.markdown(f"<div style='font-size: 20px; line-height: 1.8;'>{data.get('translation', '번역 실패')}</div>", unsafe_allow_html=True)
                
        except Exception as e:
            st.error("오류가 발생했습니다.")
            st.markdown(f"<div class='error-details'>{str(e)}</div>", unsafe_allow_html=True)

# ==========================================
# 9. 설치 가이드
# ==========================================
st.divider() 
with st.expander("📲 앱 설치 방법 보기 (Install App Guide)", expanded=False):
    st.markdown("""
    <div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px;'>
        <b style='color: #007BFF;'>안드로이드 (Samsung Galaxy)</b><br>
        1. 화면 오른쪽 위(또는 아래) <b>점 3개(⋮)</b> 클릭<br>
        2. <b>[홈 화면에 추가]</b> 또는 <b>[앱 설치]</b> 클릭<br>
        3. <b>[추가]</b> 버튼 클릭<br><br>
        <b style='color: #007BFF;'>아이폰 (iPhone iOS)</b><br>
        1. 화면 아래 <b>내보내기(공유) 버튼</b> 클릭<br>
        2. 메뉴를 올려서 <b>[홈 화면에 추가]</b> 클릭<br>
        3. 오른쪽 위 <b>[추가]</b> 클릭<br>
    </div>
    """, unsafe_allow_html=True)