import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import json
import base64

# ==========================================
# 1. 보안 및 API 설정 (Secrets 사용)
# ==========================================
if "GOOGLE_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("🚨 API 키가 없습니다! Streamlit Secrets 설정을 확인해주세요.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

ASSETS_DIR = "assets"
st.set_page_config(page_title="모두의 알림장", page_icon="🏫", layout="wide")

# ==========================================
# 2. 필수 함수
# ==========================================
if 'custom_input' not in st.session_state:
    st.session_state['custom_input'] = ''

def apply_input():
    st.session_state['custom_input'] = st.session_state.widget_input

def resize_image_for_speed(image, max_width=800):
    try:
        w_percent = (max_width / float(image.size[0]))
        h_size = int((float(image.size[1]) * float(w_percent)))
        return image.resize((max_width, h_size), Image.Resampling.LANCZOS)
    except:
        return image

def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

# ==========================================
# 3. 다국어 UI 사전 (빠짐없이 모두 포함!)
# ==========================================
ui_lang = {
    "한국어": {
        "subtitle": "모든 가정을 위한 스마트 알림장<br><span class='subtitle-eng'>Smart Notice for All Families</span>",
        "tab_camera": "📸 촬영", "tab_upload": "📂 앨범",
        "cam_label": "⬇️ 아래 카메라 버튼을 눌러주세요",
        "upload_label": "⬇️ 아래 버튼을 눌러 앨범을 여세요",
        "result_header": "🎨 준비물 그림 확인",
        "summary_header": "📢 핵심 내용 요약", "trans_btn": "번역문 보기"
    },
    "영어": {
        "subtitle": "Smart Notice for All Families",
        "tab_camera": "📸 Camera", "tab_upload": "📂 Upload",
        "cam_label": "Please tap the camera button below",
        "upload_label": "Upload Image File",
        "result_header": "🎨 Supplies Icons",
        "summary_header": "📢 Summary", "trans_btn": "View Translation"
    },
    "중국어": {
        "subtitle": "为所有家庭提供的智能通知",
        "tab_camera": "📸 拍照", "tab_upload": "📂 相册",
        "cam_label": "请点击下方的相机按钮",
        "upload_label": "请上传图片",
        "result_header": "🎨 准备物品图标",
        "summary_header": "📢 核心摘要", "trans_btn": "查看翻译"
    },
    "베트남어": {
        "subtitle": "Thông báo thông minh cho mọi gia đình",
        "tab_camera": "📸 Chụp ảnh", "tab_upload": "📂 Tải lên",
        "cam_label": "Vui lòng nhấn nút máy ảnh bên dưới",
        "upload_label": "Tải ảnh lên",
        "result_header": "🎨 Hình ảnh chuẩn bị",
        "summary_header": "📢 Tóm tắt nội dung", "trans_btn": "Xem bản dịch"
    },
    "필리핀어": {
        "subtitle": "Smart Notification para sa Lahat ng Pamilya",
        "tab_camera": "📸 Kamera", "tab_upload": "📂 I-upload",
        "cam_label": "Paki-pindot ang camera button sa ibaba",
        "upload_label": "I-upload ang larawan",
        "result_header": "🎨 Mga Kailangan",
        "summary_header": "📢 Buod", "trans_btn": "Tingnan ang Salin"
    },
    "태국어": {
        "subtitle": "การแจ้งเตือนอัจฉริยะสำหรับทุกครอบครัว",
        "tab_camera": "📸 กล้อง", "tab_upload": "📂 อัปโหลด",
        "cam_label": "กรุณากดปุ่มกล้องด้านล่าง",
        "upload_label": "อัปโหลดรูปภาพ",
        "result_header": "🎨 สิ่งที่ต้องเตรียม",
        "summary_header": "📢 สรุป", "trans_btn": "ดูคำแปล"
    },
    "일본어": {
        "subtitle": "すべての家庭のためのスマート連絡帳",
        "tab_camera": "📸 カメラ", "tab_upload": "📂 アルバム",
        "cam_label": "下のカメラボタンを押してください",
        "upload_label": "写真をアップロード",
        "result_header": "🎨 持ち物確認",
        "summary_header": "📢 要約", "trans_btn": "翻訳を見る"
    },
    "러시아어": {
        "subtitle": "Умные уведомления для всех семей",
        "tab_camera": "📸 Камера", "tab_upload": "📂 Загрузить",
        "cam_label": "Нажмите кнопку камеры ниже",
        "upload_label": "Загрузить фото",
        "result_header": "🎨 Предметы",
        "summary_header": "📢 Сводка", "trans_btn": "Посмотреть перевод"
    },
    "몽골어": {
        "subtitle": "Бүх гэр бүлд зориулсан ухаалаг мэдэгдэл",
        "tab_camera": "📸 Камер", "tab_upload": "📂 Хуулах",
        "cam_label": "Доорх камерын товчийг дарна уу",
        "upload_label": "Зураг оруулах",
        "result_header": "🎨 Бэлтгэл зүйлс",
        "summary_header": "📢 Хураангуй", "trans_btn": "Орчуулгыг харах"
    },
    "우즈베크어": {
        "subtitle": "Barcha oilalar uchun aqlli xabarnoma",
        "tab_camera": "📸 Kamera", "tab_upload": "📂 Yuklash",
        "cam_label": "Quyidagi kamera tugmasini bosing",
        "upload_label": "Rasmni yuklash",
        "result_header": "🎨 Kerakli narsalar",
        "summary_header": "📢 Xulosa", "trans_btn": "Tarjimani ko'rish"
    },
    "캄보디아어": {
        "subtitle": "ការជូនដំណឹងឆ្លាតវៃសម្រាប់គ្រួសារទាំងអស់",
        "tab_camera": "📸 កាមេរ៉ា", "tab_upload": "📂 ផ្ទុកឡើង",
        "cam_label": "សូមចុចប៊ូតុងកាមេរ៉ាខាងក្រោម",
        "upload_label": "បញ្ចូលរូបថត",
        "result_header": "🎨 សម្ភារៈ",
        "summary_header": "📢 សង្ខេប", "trans_btn": "មើលការបកប្រែ"
    }
}

def get_ui_language(user_input):
    if not user_input: return ui_lang["한국어"]
    text = user_input.lower()
    # 주요 언어 매핑
    mapping = {
        'china': '중국어', 'chinese': '중국어', 'taiwan': '중국어', '중국': '중국어',
        'viet': '베트남어', '베트남': '베트남어',
        'phil': '필리핀어', 'tagalog': '필리핀어', '필리핀': '필리핀어',
        'thai': '태국어', '태국': '태국어',
        'japan': '일본어', '일본': '일본어',
        'russia': '러시아어', '러시아': '러시아어',
        'mongol': '몽골어', '몽골': '몽골어',
        'uzbek': '우즈베크어', '우즈벡': '우즈베크어',
        'cambodia': '캄보디아어', 'khmer': '캄보디아어', '캄보디아': '캄보디아어'
    }
    for key, val in mapping.items():
        if key in text: return ui_lang[val]
    return ui_lang["영어"]

# ==========================================
# 4. 메인 화면 구성
# ==========================================
st.markdown("<h1 style='color: #FF9F1C; text-align: center;'>🏫 모두의 AI 알림장</h1>", unsafe_allow_html=True)

st.markdown("### 🌍 언어를 선택하세요 (Language)")
radio_options = [
    "한국어 (Korean)", "중국어 (Chinese)", "베트남어 (Vietnamese)",
    "영어 (English)", "필리핀어 (Tagalog)", "태국어 (Thai)",
    "일본어 (Japanese)", "러시아어 (Russian)", "몽골어 (Mongolian)",
    "우즈베크어 (Uzbek)", "캄보디아어 (Cambodian)", "직접 입력 (Type Language)"
]
selected_radio = st.radio("Label Hidden", radio_options, horizontal=False, label_visibility="collapsed")

final_target_lang = "한국어"
current_ui = ui_lang["한국어"]

if "직접 입력" in selected_radio:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.text_input("나라/언어 입력", placeholder="예: Nepal, France", key="widget_input", on_change=apply_input, label_visibility="collapsed")
    with col2:
        st.button("적용", on_click=apply_input, use_container_width=True)
    
    saved_val = st.session_state.get('custom_input', '').strip()
    if saved_val:
        final_target_lang = saved_val
        current_ui = get_ui_language(final_target_lang)
else:
    st.session_state['custom_input'] = ''
    lang_key = selected_radio.split(" ")[0]
    current_ui = ui_lang.get(lang_key, ui_lang["한국어"])
    final_target_lang = lang_key

# ==========================================
# 5. 스타일 설정 (CSS) - 🚨 아이콘 전략 (오류 해결 핵심)
# ==========================================
st.markdown("""
    <style>
        .unified-icon { width: 60px; height: 60px; object-fit: contain; display: block; margin: 0 auto; }
        .unified-emoji-container { width: 60px; height: 60px; display: flex; justify-content: center; align-items: center; font-size: 50px; margin: 0 auto; }
        .icon-text { text-align: center; font-weight: bold; margin-top: 8px; font-size: 18px; }
        
        html, body, [class*="st-"] { font-size: 22px !important; }

        /* [전역 초기화] 카메라 내부 모든 버튼 투명화 */
        div[data-testid="stCameraInput"] button {
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            text-indent: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
            width: auto !important;
            color: inherit !important;
        }
        /* 기존 글씨 숨기기 */
        div[data-testid="stCameraInput"] button > div { display: none !important; }

        /* [전환 버튼 보호] SVG(아이콘) 있는 버튼은 건드리지 않음 */
        div[data-testid="stCameraInput"] button:has(svg) {
            background-color: transparent !important;
        }

        /* [촬영 버튼 꾸미기] SVG 없는 버튼 = 촬영 버튼 */
        div[data-testid="stCameraInput"] button:not(:has(svg)) {
            background-color: #007BFF !important; 
            border-radius: 50% !important;
            width: 80px !important;
            height: 80px !important;
            margin: 0 auto !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }
        /* 📸 아이콘 삽입 */
        div[data-testid="stCameraInput"] button:not(:has(svg))::after {
            content: "📸" !important;
            font-size: 40px !important;
            display: block !important;
            line-height: 1 !important;
        }
        
        /* 앨범 업로드 버튼 */
        div[data-testid="stFileUploader"] button {
            background-color: #007BFF !important; color: white !important;
            border: none !important; font-weight: bold !important; border-radius: 8px !important;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 6. 메인 기능 탭
# ==========================================
st.divider()
st.markdown(f"<div class='subtitle-text'><h3>{current_ui['subtitle']}</h3></div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs([current_ui['tab_camera'], current_ui['tab_upload']])
img_file = None

with tab1:
    camera_img = st.camera_input(current_ui['cam_label'])
    if camera_img: img_file = camera_img
with tab2:
    uploaded_img = st.file_uploader(current_ui['upload_label'], type=['png', 'jpg', 'jpeg'])
    if uploaded_img: img_file = uploaded_img

# ==========================================
# 7. AI 분석 및 결과 출력
# ==========================================
if img_file and final_target_lang:
    with st.spinner(f"🤖 AI가 분석 중입니다... (Target: {final_target_lang})"):
        try:
            raw_image = Image.open(img_file)
            image = resize_image_for_speed(raw_image)

            prompt = f"""
            Analyze this school notice image. Target Language: {final_target_lang}.
            Output format: JSON.
            Keys: detected_lang, summary(strict noun-ending style, translated labels), translation, keywords(3 items with file_key, display_word, emoji).
            """
            
            response = model.generate_content([prompt, image])
            text_response = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(text_response)

            st.divider()
            # 1. 준비물 아이콘
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
                        if os.path.exists(path): icon_path = path; break
                    with cols[idx]:
                        if icon_path:
                            img_base64 = get_image_base64(icon_path)
                            st.markdown(f"<img src='data:image/png;base64,{img_base64}' class='unified-icon'>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div class='unified-emoji-container'>{emoji}</div>", unsafe_allow_html=True)
                        st.markdown(f"<p class='icon-text'>{display_word}</p>", unsafe_allow_html=True)

            # 2. 요약문
            st.write("")
            st.markdown(f"### {current_ui['summary_header']}")
            summary_text = data.get('summary', '요약 없음').replace('\n', '<br>')
            st.markdown(f"<div class='summary-box'>{summary_text}</div>", unsafe_allow_html=True)

            # 3. 번역문
            st.write("")
            with st.expander(f"🌍 {current_ui['trans_btn']}"):
                st.write(data.get('translation', '번역 실패'))

        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")