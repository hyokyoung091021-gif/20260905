import streamlit as st
import pandas as pd
import plotly.express as px


# -----------------------------------
# 페이지 설정
# -----------------------------------
st.set_page_config(
    page_title="영화 데이터 그래프 도감 1 - 시간",
    layout="wide"
)

st.title("🎬 영화 데이터 그래프 도감 1 - 시간")
st.write("1년 동안의 일별 박스오피스 데이터를 다양한 시간 그래프로 살펴봅니다.")


# -----------------------------------
# 데이터 불러오기
# -----------------------------------
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv"

    df = pd.read_csv(url)

    # 날짜를 진짜 날짜(datetime) 형식으로 변환
    df["날짜"] = pd.to_datetime(
        df["날짜"].astype(str),
        format="%Y%m%d"
    )

    # 숫자 데이터 변환
    numeric_columns = [
        "순위",
        "일관객",
        "누적관객",
        "스크린수",
        "상영횟수"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


df = load_data()


# ===================================
# SECTION 1
# 영화별 날짜에 따른 일관객 변화
# ===================================

st.header("📈 1. 영화별 일관객 변화")

st.write(
    "영화를 선택하면 해당 영화가 10위권에 기록된 날짜별 일관객 변화를 확인할 수 있습니다."
)


# 영화 목록 만들기
movie_list = sorted(df["영화명"].dropna().unique())


# 드롭다운
selected_movie = st.selectbox(
    "영화를 선택하세요",
    movie_list
)


# 선택한 영화 데이터
movie_df = df[df["영화명"] == selected_movie].copy()

# 날짜순 정렬
movie_df = movie_df.sort_values("날짜")


# 선 그래프
fig = px.line(
    movie_df,
    x="날짜",
    y="일관객",
    markers=True,
    title=f"🎬 {selected_movie}의 날짜별 일관객 변화",
    labels={
        "날짜": "날짜",
        "일관객": "일관객수"
    },
    hover_data={
        "날짜": "|%Y-%m-%d",
        "일관객": ":,"
    }
)

fig.update_traces(
    hovertemplate=
    "날짜: %{x|%Y-%m-%d}<br>"
    "관객수: %{y:,}명"
    "<extra></extra>"
)

fig.update_layout(
    xaxis_title="날짜",
    yaxis_title="일관객수",
    hovermode="x unified"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# -----------------------------------
# 이 그래프로 알 수 있는 것
# -----------------------------------
st.info(
    "💡 이 그래프로 알 수 있는 것: "
    "여기에 이 그래프를 통해 알 수 있는 내용을 한 문장으로 작성합니다."
)


# ===================================
# SECTION 2
# 앞으로 추가할 그래프
# ===================================

st.divider()

st.header("📊 2. 다음 시간 그래프")

st.write("앞으로 이 구역에 새로운 시간 관련 그래프를 추가합니다.")

# 앞으로 그래프 추가 예정


# ===================================
# SECTION 3
# 앞으로 추가할 그래프
# ===================================

st.divider()
st.header("2. 흥행 대작 다섯 편의 곡선")
top5 = df.groupby("영화명")["일관객"].sum().nlargest(5).index
five = df[df["영화명"].isin(top5)].sort_values("날짜")
fig2 = px.line(five, x="날짜", y="일관객", color="영화명", markers=True)
st.plotly_chart(fig2, width="stretch")
st.caption("이 그래프로 알 수 있는 것: (한 문장으로 적어 보세요)")
st.header("📊 3. 다음 시간 그래프")

st.write("앞으로 이 구역에 새로운 시간 관련 그래프를 추가합니다.")
