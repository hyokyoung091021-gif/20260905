import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --------------------------------------------------
# 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="기온 예측기",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울 기온 예측기")
st.write(
    "서울의 연평균기온 변화를 바탕으로 회귀 직선을 만들고, "
    "연도를 선택하여 예상 연평균기온을 확인할 수 있습니다."
)

# --------------------------------------------------
# 데이터 불러오기
# --------------------------------------------------
DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "bb860932644270ad1199f10d3e7670e30231bce4/data/seoul.csv"
)

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")

    # 날짜를 날짜 형식으로 변환
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    # 기온을 숫자로 변환
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")

    # 날짜 또는 평균기온이 없는 행 제거
    df = df.dropna(subset=["날짜", "평균기온"])

    # 연도 추출
    df["연도"] = df["날짜"].dt.year

    return df


df = load_data()

# --------------------------------------------------
# 2025년까지의 데이터만 사용
# --------------------------------------------------
df = df[df["연도"] <= 2025].copy()

# --------------------------------------------------
# 연도별 관측일 수와 연평균기온 계산
# --------------------------------------------------
yearly = (
    df.groupby("연도")
    .agg(
        연평균기온=("평균기온", "mean"),
        관측일수=("평균기온", "count")
    )
    .reset_index()
)

# 관측일이 300일 이상인 해만 사용
yearly = yearly[yearly["관측일수"] >= 300].copy()

# 연도순 정렬
yearly = yearly.sort_values("연도").reset_index(drop=True)

# --------------------------------------------------
# 회귀분석
# 독립변수 = 1908년부터 지난 연수
# --------------------------------------------------
yearly["지난연수"] = yearly["연도"] - 1908

x = yearly["지난연수"].to_numpy()
y = yearly["연평균기온"].to_numpy()

# 1차 회귀 직선
slope, intercept = np.polyfit(x, y, 1)

# 예측값
yearly["회귀예측기온"] = intercept + slope * yearly["지난연수"]

# 상관계수
correlation = np.corrcoef(x, y)[0, 1]

# --------------------------------------------------
# 회귀식 표시
# --------------------------------------------------
sign = "+" if intercept >= 0 else "-"

regression_equation = (
    f"연평균기온 = {slope:.4f} × (연도 - 1908) "
    f"{sign} {abs(intercept):.4f}"
)

# --------------------------------------------------
# 기본 정보
# --------------------------------------------------
st.subheader("📊 분석에 사용한 데이터")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("사용한 연도 수", f"{len(yearly)}년")

with col2:
    st.metric("시작 연도", f"{yearly['연도'].min()}년")

with col3:
    st.metric("끝 연도", f"{yearly['연도'].max()}년")

with col4:
    st.metric("상관계수", f"{correlation:.3f}")

st.write(f"**회귀식:** `{regression_equation}`")

st.info(
    "분석 대상은 2025년 이하의 연도 중 관측일이 300일 이상인 해입니다. "
    "회귀분석에서는 1908년을 기준으로 해당 연도까지 몇 년이 지났는지를 "
    "독립변수로 사용했습니다."
)

# --------------------------------------------------
# 산점도 + 회귀 직선
# --------------------------------------------------
st.subheader("📈 연도별 연평균기온과 회귀 직선")

# 회귀선을 1900~2100년까지 표시
prediction_years = np.arange(1900, 2101)
prediction_elapsed = prediction_years - 1908
prediction_temperatures = (
    intercept + slope * prediction_elapsed
)

fig = go.Figure()

# 실제 연평균기온 산점도
fig.add_trace(
    go.Scatter(
        x=yearly["연도"],
        y=yearly["연평균기온"],
        mode="markers",
        name="실제 연평균기온",
        marker=dict(
            size=8,
            opacity=0.75
        ),
        customdata=yearly["관측일수"],
        hovertemplate=(
            "<b>%{x}년</b><br>"
            "연평균기온: %{y:.2f}℃<br>"
            "관측일수: %{customdata}일"
            "<extra></extra>"
        )
    )
)

# 회귀 직선
fig.add_trace(
    go.Scatter(
        x=prediction_years,
        y=prediction_temperatures,
        mode="lines",
        name="회귀 직선",
        line=dict(width=3),
        hovertemplate=(
            "<b>%{x}년</b><br>"
            "회귀 예상기온: %{y:.2f}℃"
            "<extra></extra>"
        )
    )
)

fig.update_layout(
    xaxis_title="연도",
    yaxis_title="연평균기온 (℃)",
    xaxis=dict(
        tickmode="linear",
        dtick=10
    ),
    hovermode="x unified",
    height=600,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

st.plotly_chart(fig, use_container_width=True)

st.caption(
    f"상관계수 r = {correlation:.3f} · "
    f"사용 연도 {len(yearly)}개 · "
    f"{yearly['연도'].min()}~{yearly['연도'].max()}년"
)

# --------------------------------------------------
# 연도 선택 슬라이더
# --------------------------------------------------
st.subheader("🔮 연도별 예상 기온")

selected_year = st.slider(
    "예상 기온을 확인할 연도를 선택하세요.",
    min_value=1900,
    max_value=2100,
    value=2025,
    step=1
)

selected_elapsed = selected_year - 1908
predicted_temperature = (
    intercept + slope * selected_elapsed
)

st.markdown(
    f"""
    <div style="
        padding: 30px;
        border-radius: 20px;
        background: linear-gradient(135deg, #eef7ff, #f8fbff);
        text-align: center;
        margin-top: 20px;
        margin-bottom: 20px;
    ">
        <div style="font-size: 24px; font-weight: bold;">
            {selected_year}년 예상 연평균기온
        </div>
        <div style="
            font-size: 56px;
            font-weight: bold;
            margin-top: 10px;
        ">
            {predicted_temperature:.2f}℃
        </div>
        <div style="font-size: 16px; margin-top: 10px;">
            회귀 직선을 이용한 추정값
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# 선택한 연도를 그래프에서 강조
# --------------------------------------------------
selected_actual = yearly[yearly["연도"] == selected_year]

if not selected_actual.empty:
    actual_temperature = selected_
