import streamlit as st
import pandas as pd
import plotly.express as px


# ===================================
# 페이지 설정
# ===================================

st.set_page_config(
    page_title="영화 데이터 그래프 도감 1 - 시간",
    layout="wide"
)


# ===================================
# 제목
# ===================================

st.title("🎬 영화 데이터 그래프 도감 1 - 시간")

st.write(
    "1년 동안의 일별 박스오피스 데이터를 "
    "시간의 흐름에 따라 다양한 그래프로 살펴봅니다."
)


# ===================================
# 데이터 불러오기
# ===================================

@st.cache_data
def load_data():

    url = (
        "https://raw.githubusercontent.com/"
        "greatsong/modudata/main/data/kobis_daily.csv"
    )

    df = pd.read_csv(url)

    # 날짜를 진짜 날짜 형식으로 변환
    df["날짜"] = pd.to_datetime(
        df["날짜"].astype(str),
        format="%Y%m%d"
    )

    # 숫자 열을 숫자형으로 변환
    numeric_columns = [
        "순위",
        "일관객",
        "누적관객",
        "스크린수",
        "상영횟수"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    return df


# 데이터 불러오기
df = load_data()


# ===================================
# SECTION 1
# 선택한 영화의 날짜별 일관객 변화
# ===================================

st.header("📈 1. 영화별 일관객 변화")

st.write(
    "영화를 선택하면 해당 영화의 날짜별 "
    "일관객 변화를 확인할 수 있습니다."
)


# 영화 목록 만들기
movie_list = sorted(
    df["영화명"].dropna().unique()
)


# 영화 선택
selected_movie = st.selectbox(
    "영화를 선택하세요",
    movie_list
)


# 선택한 영화 데이터
movie_df = df[
    df["영화명"] == selected_movie
].copy()


# 날짜순 정렬
movie_df = movie_df.sort_values("날짜")


# 선 그래프
fig1 = px.line(
    movie_df,
    x="날짜",
    y="일관객",
    markers=True,
    title=f"{selected_movie}의 날짜별 일관객 변화",
    labels={
        "날짜": "날짜",
        "일관객": "일관객수"
    }
)


# 마우스를 올렸을 때 표시
fig1.update_traces(
    hovertemplate=
    "날짜: %{x|%Y-%m-%d}<br>"
    "일관객: %{y:,}명"
    "<extra></extra>"
)


# 그래프 설정
fig1.update_layout(
    xaxis_title="날짜",
    yaxis_title="일관객수",
    hovermode="x unified"
)


# 그래프 출력
st.plotly_chart(
    fig1,
    use_container_width=True
)


# 그래프로 알 수 있는 것
st.info(
    "💡 이 그래프로 알 수 있는 것: "
    "선택한 영화의 날짜별 관객 수 변화를 통해 "
    "시간에 따른 흥행 추이를 확인할 수 있습니다."
)


# ===================================
# SECTION 2
# 일관객 합계 상위 5개 영화
# 경과일별 일관객 변화
# ===================================

st.divider()

st.header("📊 2. 상위 5개 영화의 경과일별 일관객 변화")

st.write(
    "이 기간 동안 일관객 합계가 가장 많은 5편의 영화를 골라 "
    "각 영화의 첫 기록 날짜를 기준으로 흥행 변화를 비교합니다."
)


# -----------------------------------
# 영화별 일관객 합계 계산
# -----------------------------------

movie_sum = (
    df.groupby("영화명")["일관객"]
    .sum()
    .sort_values(ascending=False)
)


# 상위 5개 영화 선택
top5_movies = movie_sum.head(5).index.tolist()


# 상위 5개 영화 데이터
top5_df = df[
    df["영화명"].isin(top5_movies)
].copy()


# -----------------------------------
# 영화별 첫 기록 날짜 계산
# -----------------------------------

first_dates = (
    top5_df.groupby("영화명")["날짜"]
    .transform("min")
)


# 첫 기록 후 경과일 계산
top5_df["경과일"] = (
    top5_df["날짜"] - first_dates
).dt.days


# 정렬
top5_df = top5_df.sort_values(
    ["영화명", "경과일"]
)


# -----------------------------------
# 선 그래프
# -----------------------------------

fig2 = px.line(
    top5_df,
    x="경과일",
    y="일관객",
    color="영화명",
    markers=True,
    title="일관객 합계 상위 5개 영화의 경과일별 일관객 변화",
    labels={
        "경과일": "첫 기록 후 경과일",
        "일관객": "일관객수",
        "영화명": "영화명"
    }
)


# 마우스를 올렸을 때 표시
fig2.update_traces(
    hovertemplate=
    "경과일: %{x}일째<br>"
    "일관객: %{y:,}명"
    "<extra></extra>"
)


# 그래프 설정
fig2.update_layout(
    xaxis_title="첫 기록 후 경과일",
    yaxis_title="일관객수",
    hovermode="closest",
    legend_title="영화명"
)


# 그래프 출력
st.plotly_chart(
    fig2,
    use_container_width=True
)


# 그래프로 알 수 있는 것
st.info(
    "💡 이 그래프로 알 수 있는 것: "
    "상위 5개 영화의 관객 수가 첫 기록 이후 어떻게 증가하고 "
    "감소하는지 같은 시간 기준에서 비교할 수 있습니다."
)


# ===================================
# SECTION 3
# 날짜별 10위권 전체 일관객 합계
# ===================================

st.divider()

st.header("📈 3. 날짜별 박스오피스 10위권 전체 관객 수")

st.write(
    "매일 박스오피스 10위권에 오른 영화들의 "
    "일관객 수를 모두 합쳐 날짜별 변화를 살펴봅니다."
)


# -----------------------------------
# 날짜별 일관객 합계
# -----------------------------------

daily_total = (
    df.groupby(
        "날짜",
        as_index=False
    )["일관객"]
    .sum()
    .sort_values("날짜")
)


# -----------------------------------
# 관객 수가 가장 많은 상위 3일
# -----------------------------------

top3_days = (
    daily_total.nlargest(
        3,
        "일관객"
    )
)


# -----------------------------------
# 영역 그래프
# -----------------------------------

fig3 = px.area(
    daily_total,
    x="날짜",
    y="일관객",
    title="날짜별 박스오피스 10위권 전체 일관객 합계",
    labels={
        "날짜": "날짜",
        "일관객": "10위권 일관객 합계"
    }
)


# -----------------------------------
# 상위 3일 표시
# -----------------------------------

fig3.add_scatter(
    x=top3_days["날짜"],
    y=top3_days["일관객"],

    mode="markers+text",

    text=[
        date.strftime("%Y-%m-%d")
        for date in top3_days["날짜"]
    ],

    textposition="top center",

    marker=dict(size=10),

    name="관객 수 상위 3일",

    hovertemplate=
    "날짜: %{x|%Y-%m-%d}<br>"
    "10위권 관객 합계: %{y:,}명"
    "<extra></extra>"
)


# 그래프 설정
fig3.update_layout(
    xaxis_title="날짜",
    yaxis_title="10위권 일관객 합계",
    hovermode="x unified"
)


# 그래프 출력
st.plotly_chart(
    fig3,
    use_container_width=True
)


# 그래프로 알 수 있는 것
st.info(
    "💡 이 그래프로 알 수 있는 것: "
    "날짜별 전체 관객 수의 변화를 확인하고 "
    "관객이 가장 많이 극장을 찾은 시기를 파악할 수 있습니다."
)


# ===================================
# SECTION 4
# 영화별 일관객 합계 TOP 10
# ===================================

st.divider()

st.header("🏆 4. 영화별 일관객 합계 TOP 10")

st.write(
    "이 기간 동안 영화별 일관객을 모두 합산하여 "
    "관객 수가 가장 많은 영화 10편을 비교합니다."
)


# -----------------------------------
# 영화별 데이터 집계
# -----------------------------------

movie_total = (
    df.groupby(
        "영화명",
        as_index=False
    )
    .agg({
        "일관객": "sum",
        "날짜": "nunique"
    })
)


# 열 이름 변경
movie_total = movie_total.rename(
    columns={
        "일관객": "일관객합계",
        "날짜": "기록일수"
    }
)


# -----------------------------------
# 일관객 합계 TOP 10
# -----------------------------------

top10_movies = (
    movie_total
    .sort_values(
        "일관객합계",
        ascending=False
    )
    .head(10)
)


# 가로 막대그래프에서
# 가장 많은 영화가 위에 오도록 정렬
top10_movies = (
    top10_movies
    .sort_values(
        "일관객합계",
        ascending=True
    )
)


# -----------------------------------
# 가로 막대그래프
# -----------------------------------

fig4 = px.bar(
    top10_movies,

    x="일관객합계",
    y="영화명",

    orientation="h",

    title="영화별 일관객 합계 TOP 10",

    labels={
        "영화명": "영화명",
        "일관객합계": "일관객 합계"
    },

    custom_data=[
        "기록일수"
    ]
)


# -----------------------------------
# 마우스를 올렸을 때 표시
# -----------------------------------

fig4.update_traces(
    hovertemplate=
    "영화: %{y}<br>"
    "일관객 합계: %{x:,}명<br>"
    "10위권 기록 일수: %{customdata[0]}일"
    "<extra></extra>"
)


# 그래프 설정
fig4.update_layout(
    xaxis_title="일관객 합계",
    yaxis_title="영화명",
    showlegend=False
)


# 그래프 출력
st.plotly_chart(
    fig4,
    use_container_width=True
)


# -----------------------------------
# 이 그래프로 알 수 있는 것
# -----------------------------------

st.info(
    "💡 이 그래프로 알 수 있는 것: "
    "이 기간 동안 가장 많은 관객을 모은 영화들을 비교할 수 있으며, "
    "각 영화가 10위권에 얼마나 오래 기록되었는지도 확인할 수 있습니다."
)
