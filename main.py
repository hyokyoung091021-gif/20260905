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

    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")

    df = df.dropna(subset=["날짜", "평균기온"])
    df["연도"] = df["날짜"].dt.year

    return df


df = load_data()

# --------------------------------------------------
# 2025년까지의 데이터만 사용
# --------------------------------------------------
df = df[df["연도"] <= 2025].copy()

# --------------------------------------------------
# 연도별 평균기온 및 관측일수 계산
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

yearly = yearly.sort_values("연도").reset_index(drop=True)

# --------------------------------------------------
# 전체 기간 회귀분석
# 독립변수 = 1908년부터 지난 연수
# --------------------------------------------------
yearly["지난연수"] = yearly["연도"] - 1908

x_all = yearly["지난연수"].to_numpy()
y_all = yearly["연평균기온"].to_numpy()

slope_all, intercept_all = np.polyfit(x_all, y_all, 1)

# 1년에 몇 ℃ 변화하는지를 100년 단위로 변환
slope_all_100 = slope_all * 100

# 상관계수
correlation = np.corrcoef(x_all, y_all)[0, 1]

# --------------------------------------------------
# 최근 20년 회귀분석
# 2006~2025년 중 관측일 300일 이상인 해
# --------------------------------------------------
recent_start_year = 2025 - 19

recent = yearly[
    (yearly["연도"] >= recent_start_year) &
    (yearly["연도"] <= 2025)
].copy()

recent["지난연수"] = recent["연도"] - 1908

x_recent = recent["지난연수"].to_numpy()
y_recent = recent["연평균기온"].to_numpy()

# 최근 20년 자료가 2개 이상일 때 회귀 가능
if len(recent) >= 2:
    slope_recent, intercept_recent = np.polyfit(
        x_recent,
        y_recent,
        1
    )

    slope_recent_100 = slope_recent * 100
else:
    slope_recent = np.nan
    intercept_recent = np.nan
    slope_recent_100 = np.nan


# --------------------------------------------------
# 회귀식
# --------------------------------------------------
sign = "+" if intercept_all >= 0 else "-"

regression_equation = (
    f"연평균기온 = {slope_all:.4f} × (연도 - 1908) "
    f"{sign} {abs(intercept_all):.4f}"
)

# --------------------------------------------------
# 분석 기간 정보
# --------------------------------------------------
all_start_year = int(yearly["연도"].min())
all_end_year = int(yearly["]()
```
