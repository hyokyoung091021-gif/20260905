import streamlit as st
import pandas as pd
import plotly.express as px  # 이후 시각화 실습을 위해 사용할 수 있습니다.
from sklearn.model_selection import train_test_split  # 이후 예측 모델 실습을 위해 사용할 수 있습니다.

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/stroke.csv"
APP_TITLE = "뇌졸중 예측 실습실"

# Streamlit의 기본 페이지 메뉴를 사용합니다.
# main.py와 같은 폴더의 pages/1_탐색.py를 자동으로 왼쪽 사이드바에 표시합니다.
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🧠",
    layout="wide",
)

# 페이지 스타일
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.35rem;
        font-weight: 800;
        margin-bottom: 0.25rem;
    }
    .subtitle {
        color: #667085;
        font-size: 1rem;
        margin-bottom: 1.2rem;
    }
    div[data-testid="stMetric"] {
        background: #f4f7fb;
border: 1px solid #e2e8f0;
        padding: 16px;
        border-radius: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    """UTF-8 CSV 파일을 읽습니다."""
    df = pd.read_csv(DATA_URL, encoding="utf-8")
    return df


st.markdown(f'<div class="main-title">🧠 {APP_TITLE}</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">데이터를 먼저 살펴보고, 뇌졸중 예측 실습을 준비해 봅시다.</div>',
    unsafe_allow_html=True,
)

st.header("1. 어떤 데이터인가요?")
st.write(
    """
    이 데이터는 여러 사람의 인구학적 정보, 건강 관련 정보, 생활 습관 정보와
    뇌졸중 여부를 담고 있습니다. 각 행은 한 사람의 기록이며, `stroke` 열은
    뇌졸중 여부를 나타내는 목표 열입니다.

    이 화면은 데이터의 구조를 살펴보는 소개 단계입니다. 여기의 통계만으로
    개인의 뇌졸중 가능성을 판단할 수는 없으며, 실제 의료 판단을 대신하지 않습니다.
    """
)

try:
    df = load_data()

    required_columns = [
        "id", "gender", "age", "hypertension", "heart_disease",
        "ever_married", "work_type", "Residence_type",
        "avg_glucose_level", "bmi", "smoking_status", "stroke"
    ]
    missing_columns = [column for column in required_columns if column not in df.columns]

    if missing_columns:
        st.error("데이터에서 예상한 열을 찾지 못했습니다: " + ", ".join(missing_columns))
        st.stop()

    # 숫자형으로 변환해 stroke=1 개수와 비율을 안전하게 계산합니다.
    stroke_values = pd.to_numeric(df["stroke"], errors="coerce")
    total_people = len(df)
    column_count = len(df.columns)
    stroke_people = int((stroke_values == 1).sum())
    stroke_rate = (stroke_people / total_people * 100) if total_people else 0

    st.subheader("데이터 한눈에 보기")
    metric_columns = st.columns(4)
    metric_columns[0].metric("전체 사람 수", f"{total_people:,}명")
    metric_columns[1].metric("열 개수", f"{column_count:,}개")
    metric_columns[2].metric("stroke가 1인 사람 수", f"{stroke_people:,}명")
    metric_columns[3].metric("stroke가 1인 비율", f"{stroke_rate:.2f}%")

    st.caption(
        "※ 비율은 전체 행 수를 기준으로 계산했습니다. 데이터에 결측값이 있으면 "
        "해당 열의 분석 결과에 영향을 줄 수 있습니다."
    )

    st.header("2. 열 정보 살펴보기")
    st.write(
        "‘우리말 뜻’ 열은 교재를 참고해 직접 채울 수 있도록 비워 두었습니다. "
        "‘값의 종류’는 각 열의 자료형과 서로 다른 값의 개수를 나타냅니다."
    )

    column_info = []
    for column in df.columns:
        series = df[column]
        if pd.api.types.is_numeric_dtype(series):
            value_kind = "숫자형"
        else:
            value_kind = "문자형/범주형"

        unique_count = int(series.nunique(dropna=True))
        column_info.append(
            {
                "열 이름": column,
                "우리말 뜻": "",
                "값의 종류": f"{value_kind} · 고유값 {unique_count:,}개",
                "빈 값 개수": int(series.isna().sum()),
            }
        )

    info_df = pd.DataFrame(
        column_info,
        columns=["열 이름", "우리말 뜻", "값의 종류", "빈 값 개수"],
    )
    st.dataframe(info_df, use_container_width=True, hide_index=True)

    st.header("3. 데이터 첫 5행")
    st.write("원본 데이터의 첫 다섯 행을 표시합니다. 값은 별도로 바꾸지 않습니다.")
    st.dataframe(df.head(5), use_container_width=True, hide_index=True)

    st.header("4. 데이터 출처")
    st.write("교재를 참고하여 데이터 출처를 직접 적어 보세요.")
    st.text_area(
        "데이터 출처 (직접 작성)",
        placeholder="교재에 나온 데이터 출처를 여기에 적으세요.",
        height=100,
        key="data_source_note",
    )

except Exception as error:
    st.error("데이터를 불러오거나 표시하는 중 문제가 발생했습니다.")
    st.caption("인터넷 연결과 CSV 주소를 확인한 뒤 다시 실행해 주세요.")
    st.exception(error)
