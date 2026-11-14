
import streamlit as st

st.set_page_config(
    page_title="뇌졸중 예측 실습실",
    page_icon="🧠",
    layout="wide"
)

페이지 = {
    "뇌졸중 예측 실습실": [
        st.Page("pages/1_탐색.py", title="데이터 탐색", icon="🔍"),
        st.Page("pages/2_분류_모델.py", title="분류 모델", icon="🤖"),
        st.Page("pages/3_채점표.py", title="채점표", icon="📋"),
        st.Page("pages/4_전처리.py", title="데이터 전처리", icon="🧹"),
        st.Page("pages/5_내가_만든_모델_소개.py", title="내가 만든 모델 소개", icon="💡"),
    ]
}

선택한페이지 = st.navigation(페이지, position="sidebar")
선택한페이지.run()
