import streamlit as st
import google.generativeai as genai

# ==========================================
# 👇여기에 방금 받은 'My School App' 키를 넣으세요!
# ==========================================
MY_DIRECT_KEY = "AIzaSyDC0TbYKns966JZBv-1dWGbq-rBQs0guh4" 
# ==========================================

st.set_page_config(page_title="키 진단", page_icon="🔑")

st.title("🔑 내 API 키 정밀 진단")

if "여기에" in MY_DIRECT_KEY:
    st.error("🚨 코드 6번째 줄에 키를 아직 안 넣으셨습니다!")
    st.stop()

genai.configure(api_key=MY_DIRECT_KEY)

if st.button("내 키로 사용 가능한 모델 조회하기 (Click)", type="primary"):
    try:
        # 내 키로 접근 가능한 모든 모델을 가져옵니다.
        my_models = [m.name for m in genai.list_models()]
        
        if not my_models:
            st.error("🚨 목록이 비어있습니다! (원인: API가 활성화 안 됨 or 키 오류)")
            st.info("💡 5분 정도 기다렸다가 다시 버튼을 눌러보세요.")
        else:
            st.success(f"✅ 조회 성공! 총 {len(my_models)}개 모델 발견")
            st.write("👇 내 키로 쓸 수 있는 모델들:")
            st.code(my_models)
            
            # 1.5 Flash가 있는지 확인
            if "models/gemini-1.5-flash" in my_models:
                st.balloons()
                st.success("🎉 대성공! 'models/gemini-1.5-flash'가 목록에 있습니다!")
                st.info("이제 원래 코드로 돌아가셔도 됩니다.")
            else:
                st.warning("⚠️ 1.5 Flash가 아직 목록에 안 떴습니다. 조금만 더 기다리세요.")

    except Exception as e:
        st.error("🚨 조회 중 오류 발생!")
        st.code(str(e))
        st.markdown("""
        **[해결책]**
        1. 키가 정확한지 다시 확인하세요 (공백 주의).
        2. 방금 만든 키라면 **5분 뒤에** 다시 시도하세요.
        """)