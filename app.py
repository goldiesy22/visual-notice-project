import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="모델 확인기", page_icon="🔎")

st.title("🔎 사용 가능한 모델 목록 확인")

# 1. API 키 확인
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    st.success("✅ API 키가 감지되었습니다.")
    genai.configure(api_key=api_key)
else:
    st.error("🚨 API 키가 없습니다. Secrets 설정을 확인하세요.")
    st.stop()

# 2. 모델 목록 조회
st.markdown("### 👇 내 API 키로 쓸 수 있는 모델들")

try:
    found_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            st.code(m.name) # 여기에 뜨는 이름을 그대로 복사해야 함
            found_models.append(m.name)

    if not found_models:
        st.warning("⚠️ 사용 가능한 모델이 하나도 안 뜹니다. API 키 권한 문제일 수 있습니다.")

except Exception as e:
    st.error(f"오류 발생: {str(e)}")
    st.write("팁: requirements.txt에 'google-generativeai>=0.7.0'이 있는지 확인하세요.")