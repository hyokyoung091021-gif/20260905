import streamlit as st
import pandas as pd
import plotly.express as px


# ===================================
# 페이지 설정
# ===================================

st.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계",
    layout="wide"
)


# ===================================
# 제목
# ===================================

st.title("🎬 영화 데이터 그래프 도감 2 - 분포와 관계")

st.write(
    "1년간 박스오피스 10위권에 든 영화들의 데이터를 이용해 "
    "영화의 분포와 여러 변수 사이의 관계를 살펴봅니다."
)


# ===================================
# 데이터 불러오기
# ===================================

@st.cache_data
def load_data():

    url = (
        "https://raw.githubusercontent.com/"
        "greatsong/modudata/main/data/kobis_movies.csv"
    )

    df = pd.read_csv(url)

    # -------------------------------
    # 개봉일을 날짜 형식으로 변환
    # -------------------------------

    df["openDt"] = pd.to_datetime(
        df["openDt"].astype(str),
        format="%Y%m%d",
        errors="coerce"
    )

    # -------------------------------
    # 숫자 열을 숫자형으로 변환
    # -------------------------------

    numeric_columns = [
        "first_scrn",
        "first_show",
        "first_week_audi",
        "total_audi",
        "days_in_top10"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    # -------------------------------
    # 장르가 여러 개인 경우
    # 첫 번째 장르만 사용
    # -------------------------------

    df["genre"] = (
        df["genre"]
        .fillna("기타")
        .astype(str)
        .str.split("|")
        .str[0]
    )

    return df


# 데이터 불러오기
df = load_data()


# ===================================
# SECTION 1
# 장르별 영화 편수
# ===================================

st.header("🍩 1. 장르별 영화 편수")

st.write(
    "1년간 박스오피스 10위권에 오른 영화들을 "
    "첫 번째 장르를 기준으로 분류하여 영화 편수를 비교합니다."
)


# -----------------------------------
# 장르별 영화 편수 계산
# -----------------------------------

genre_count = (
    df["genre"]
    .value_counts()
    .reset_index()
)


# 열 이름 변경
genre_count.columns = [
    "장르",
    "영화편수"
]


# -----------------------------------
# 도넛 그래프
# -----------------------------------

fig1 = px.pie(
    genre_count,
    names="장르",
    values="영화편수",
    hole=0.4,
    title="장르별 영화 편수"
)


# -----------------------------------
# 마우스를 올렸을 때 표시
# -----------------------------------

fig1.update_traces(
    hovertemplate=
    "장르: %{label}<br>"
    "영화 편수: %{value}편<br>"
    "비율: %{percent}"
    "<extra></extra>"
)


# -----------------------------------
# 그래프 출력
# -----------------------------------

st.plotly_chart(
    fig1,
    use_container_width=True
)


# -----------------------------------
# 이 그래프로 알 수 있는 것
# -----------------------------------

st.info(
    "💡 이 그래프로 알 수 있는 것: "
    "박스오피스 10위권에 든 영화들이 어떤 장르에 많이 분포되어 있는지 "
    "확인할 수 있습니다."
)
# ===================================
# SECTION 2
# 장르별 영화 총 관객 트리맵
# ===================================

st.divider()

st.header("🗂️ 2. 장르별 영화 총 관객")

st.write(
    "장르별로 영화를 묶고, 각 영화의 칸 크기를 "
    "총 관객 수에 따라 나타냅니다."
)


# -----------------------------------
# 트리맵 데이터 준비
# -----------------------------------

treemap_df = df[
    ["genre", "movieNm", "total_audi"]
].copy()


# 총 관객 수가 없는 데이터 제거
treemap_df = treemap_df.dropna(
    subset=["total_audi"]
)


# -----------------------------------
# 트리맵 만들기
# -----------------------------------

fig2 = px.treemap(
    treemap_df,
    path=[
        "genre",
        "movieNm"
    ],
    values="total_audi",
    title="장르 안의 영화별 총 관객 수",
    hover_data={
        "total_audi": ":,"
    }
)


# -----------------------------------
# 마우스를 올렸을 때 표시
# -----------------------------------

fig2.update_traces(
    hovertemplate=
    "영화명: %{label}<br>"
    "총 관객: %{value:,}명"
    "<extra></extra>"
)


# -----------------------------------
# 그래프 출력
# -----------------------------------

st.plotly_chart(
    fig2,
    use_container_width=True
)


# -----------------------------------
# 이 그래프로 알 수 있는 것
# -----------------------------------

st.info(
    "💡 이 그래프로 알 수 있는 것: "
    "장르별 영화들의 규모와 각 영화의 총 관객 수를 한눈에 비교할 수 있으며, "
    "칸이 클수록 총 관객 수가 많음을 알 수 있습니다."
)
# ===================================
# SECTION 3
# 총 관객 수 분포
# ===================================

st.divider()

st.header("📊 3. 영화별 총 관객 수 분포")

st.write(
    "1년간 박스오피스 10위권에 든 영화들의 "
    "총 관객 수가 어느 구간에 많이 분포하는지 살펴봅니다."
)


# -----------------------------------
# 히스토그램에 사용할 데이터
# -----------------------------------

audi_df = df.dropna(
    subset=["total_audi"]
).copy()


# -----------------------------------
# 히스토그램
# -----------------------------------

fig3 = px.histogram(
    audi_df,
    x="total_audi",
    nbins=20,
    title="영화별 총 관객 수 분포",
    labels={
        "total_audi": "총 관객 수"
    }
)


# 마우스를 올렸을 때 표시
fig3.update_traces(
    hovertemplate=
    "총 관객 수 구간: %{x}<br>"
    "영화 편수: %{y}편"
    "<extra></extra>"
)


# 그래프 설정
fig3.update_layout(
    xaxis_title="총 관객 수",
    yaxis_title="영화 편수"
)


# 그래프 출력
st.plotly_chart(
    fig3,
    use_container_width=True
)


# ===================================
# 그래프 분석 문구 만들기
# ===================================


# -----------------------------------
# 가장 많은 영화가 몰린 구간 계산
# -----------------------------------

hist_count, bin_edges = pd.cut(
    audi_df["total_audi"],
    bins=20
).value_counts().sort_index().align(
    pd.cut(
        audi_df["total_audi"],
        bins=20
    ).value_counts().sort_index()
)


# 가장 많은 영화가 있는 구간
bin_result = pd.cut(
    audi_df["total_audi"],
    bins=20
)

most_common_interval = (
    bin_result.value_counts()
    .idxmax()
)


# -----------------------------------
# 가장 관객이 많은 영화 찾기
# -----------------------------------

max_movie = audi_df.loc[
    audi_df["total_audi"].idxmax()
]


max_movie_name = max_movie["movieNm"]

max_movie_audi = max_movie["total_audi"]


# -----------------------------------
# 그래프 아래 문구
# -----------------------------------

st.info(
    f"💡 이 그래프로 알 수 있는 것: "
    f"대부분의 영화는 총 관객 수 약 "
    f"{most_common_interval.left:,.0f}명 ~ "
    f"{most_common_interval.right:,.0f}명 구간에 가장 많이 몰려 있으며, "
    f"가장 많은 관객을 기록한 영화는 "
    f"「{max_movie_name}」로 "
    f"총 {max_movie_audi:,.0f}명이 관람했습니다."
)
