
from pathlib import Path
import streamlit as st

st.set_page_config(
    page_title="뇌졸중 예측 실습실",
    page_icon="🧠",
    layout="wide"
)

기준폴더 = Path(__file__).parent

# pages 폴더 위치 자동 확인
if (기준폴더 / "pages").exists():
    페이지폴더 = 기준폴더 / "pages"
elif (기준폴더 / ".devcontainer" / "pages").exists():
    페이지폴더 = 기준폴더 / ".devcontainer" / "pages"
else:
    st.error("pages 폴더를 찾을 수 없습니다.")
    st.stop()

페이지파일 = [
    ("1_탐색.py", "데이터 탐색", "🔍"),
    ("2_분류_모델.py", "분류 모델", "🤖"),
    ("3_채점표.py", "채점표", "📋"),
    ("4_전처리.py", "데이터 전처리", "🧹"),
    ("5_내가_만든_모델_소개.py", "내가 만든 모델 소개", "💡"),
]

페이지목록 = []

for 파일명, 제목, 아이콘 in 페이지파일:
    경로 = 페이지폴더 / 파일명

    if 경로.exists():
        페이지목록.append(
            st.Page(str(경로), title=제목, icon=아이콘)
        )
    else:
        st.warning(f"페이지 파일을 찾을 수 없습니다: {파일명}")

if not 페이지목록:
    st.error("실행할 페이지가 없습니다.")
    st.stop()

선택한페이지 = st.navigation(
    {"뇌졸중 예측 실습실": 페이지목록},
    position="sidebar"
)

선택한페이지.run()
