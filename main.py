import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="서울 연평균 기온 변화",
    page_icon="🌡️",
    layout="wide"
)

# 데이터 주소
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"

# 제목
st.title("🌡️ 서울의 연평균 기온 변화")
st.write("1907년 이후 서울의 연평균 기온이 어떻게 변해 왔는지 살펴봅니다.")

# 데이터 불러오기
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")

    # 날짜를 날짜 형식으로 변환
    df["날짜"] = pd.to_datetime(df["날짜"])

    # 연도 추출
    df["연도"] = df["날짜"].dt.year

    # 평균기온을 숫자로 변환
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")

    return df


try:
    df = load_data()

    # 연도별 평균기온 계산
    yearly_temp = (
        df.groupby("연도")["평균기온"]
        .mean()
        .reset_index()
        .dropna()
    )

    # 화면에 표시할 기간 선택
    min_year = int(yearly_temp["연도"].min())
    max_year = int(yearly_temp["연도"].max())

    st.sidebar.header("기간 선택")

    start_year, end_year = st.sidebar.slider(
        "연도 범위",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )

    # 선택한 기간만 표시
    chart_data = yearly_temp[
        (yearly_temp["연도"] >= start_year)
        & (yearly_temp["연도"] <= end_year)
    ].copy()

    # 주요 정보
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("시작 연도", f"{start_year}년")

    with col2:
        st.metric("마지막 연도", f"{end_year}년")

    with col3:
        st.metric(
            "평균기온",
            f"{chart_data['평균기온'].mean():.1f} °C"
        )

    st.subheader("연도별 평균기온")

    # 선 그래프
    st.line_chart(
        chart_data.set_index("연도")["평균기온"],
        y_label="평균기온 (°C)"
    )

    st.caption(
        "※ 각 연도의 일평균기온을 평균하여 연평균 기온을 계산했습니다."
    )

    # 데이터 보기
    with st.expander("연도별 평균기온 데이터 보기"):
        display_data = chart_data.copy()
        display_data["평균기온"] = display_data["평균기온"].round(2)
        st.dataframe(
            display_data,
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error("데이터를 불러오는 중 문제가 발생했습니다.")
    st.exception(e)
