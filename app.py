import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import sys

# ======================================================
# 👇 [진실의 방] 여기에 'My School App' 키를 붙여넣으세요
# ======================================================
TEST_KEY = "AIzaSyCQqwCFatYYm9RVsPPaxeBv7qn765KcgvE"
# ======================================================

st.set_page_config(page_title="긴급 진단", layout="wide")
st.title("🚑 API 키 긴급 정밀 진단")

# 1. 키 검사
if "여기에" in TEST_KEY:
    st.error("🚨 12번째 줄에 API 키를 입력하지 않았습니다!")
    st.stop()

# 2. 설정 적용
try:
    genai.configure(api_key=TEST_KEY)
    st.info(f"🔑 입력된 키 확인: {TEST_KEY[:10]}... (앞 10자리만 표시)")
except Exception as e:
    st.error(f"설정 단계 오류: {e}")

# 3. 모델 직접 타격 테스트 (1.5 Flash)
st.markdown("---")
st.subheader("📡 1. 구글 서버 연결 테스트")

target_model = "models/gemini-1.5-flash"
st.write(f"시도하는 모델: `{target_model}`")

try:
    model = genai.GenerativeModel(target_model)
    response = model.generate_content("Hello")
    
    # 성공 시
    st.success("🎉 연결 성공! (이 키는 완벽합니다)")
    st.balloons()
    st.markdown(f"**AI 응답:** {response.text}")
    
    st.success("✅ 이제 이 코드를 지우고, 원래 앱 코드로 돌아가서 키만 넣으시면 됩니다!")

except Exception as e:
    # 실패 시 진짜 이유 출력
    st.error("💥 연결 실패! 구글이 보낸 에러 메시지 원본:")
    st.code(str(e), language="bash")
    
    # 에러 분석
    err_msg = str(e)
    if "API_KEY_INVALID" in err_msg or "expired" in err_msg:
        st.warning("👉 [진단] '만료된 키'입니다. 코드를 수정하고 **[Save]** 버튼을 확실히 눌렀는지 확인하세요. 옛날 키가 계속 돌고 있습니다.")
    elif "404" in err_msg and "not found" in err_msg:
        st.warning("👉 [진단] '모델 없음'입니다. 이 키는 'Default Project' 키일 확률이 높습니다. 'My School App' 프로젝트 키가 맞나요?")
    elif "429" in err_msg:
        st.warning("👉 [진단] '사용량 초과'입니다. 무료 사용량을 다 썼거나, 실험용 모델입니다.")