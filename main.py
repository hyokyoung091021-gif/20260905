import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans


# --------------------------------------------------
# 페이지 설정
# --------------------------------------------------
st.set_page_config(
    page_title="영화 유형 나누기",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 영화 유형 나누기")
st.caption("영화의 흥행 특성을 바탕으로 K-평균 군집화를 수행합니다.")


# --------------------------------------------------
# 데이터 불러오기
# --------------------------------------------------
DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "main/data/kobis_movies.csv"
)

REQUIRED_COLUMNS = [
    "movieCd",
    "movieNm",
    "openDt",
    "genre",
    "nation",
    "first_scrn",
    "first_show",
    "first_date",
    "peak",
    "first_week_audi",
    "total_audi",
    "days_in_top10",
]

try:
    df = pd.read_csv(DATA_URL, encoding="utf-8")
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]

if missing_columns:
    st.error(
        "데이터에 필요한 열이 없습니다: "
        + ", ".join(missing_columns)
    )
    st.stop()


# --------------------------------------------------
# 숫자형 변환
# --------------------------------------------------
numeric_columns = [
    "first_scrn",
    "first_week_audi",
    "total_audi",
    "days_in_top10",
]

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")


# --------------------------------------------------
# 군집화에 사용할 네 가지 속성 만들기
# --------------------------------------------------
# 스크린 수와 누적 관객은 상용로그(log10)
df["스크린 수"] = df["first_scrn"].apply(
    lambda x: __import__("math").log10(x)
    if pd.notna(x) and x > 0
    else float("nan")
)

df["누적 관객"] = df["total_audi"].apply(
    lambda x: __import__("math").log10(x)
    if pd.notna(x) and x > 0
    else float("nan")
)

df["10위권 일수"] = df["days_in_top10"]

# 롱런 지수 = 누적 관객 / 첫 주 관객
# 20 초과는 20으로 제한
df["롱런 지수"] = (
    df["total_audi"] / df["first_week_audi"]
).clip(upper=20)


FEATURES = [
    "스크린 수",
    "누적 관객",
    "10위권 일수",
    "롱런 지수",
]


# --------------------------------------------------
# 결측값 / 첫 주 관객 0인 영화 제외
# --------------------------------------------------
total_movies = len(df)

cluster_df = df.dropna(
    subset=FEATURES + ["first_week_audi"]
).copy()

cluster_df = cluster_df[
    cluster_df["first_week_audi"] > 0
].copy()

used_movies = len(cluster_df)


# --------------------------------------------------
# 상단 정보
# --------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.metric("전체 영화 편수", f"{total_movies:,}편")

with col2:
    st.metric("묶은 영화 편수", f"{used_movies:,}편")


if used_movies < 3:
    st.error("군집화를 수행하려면 최소 3편 이상의 영화가 필요합니다.")
    st.stop()


# --------------------------------------------------
# 속성 선택
# --------------------------------------------------
st.subheader("🔧 영화 유형을 나눌 속성")

selected_features = st.multiselect(
    "군집화에 사용할 속성을 두 개 이상 선택하세요.",
    FEATURES,
    default=FEATURES
)

if len(selected_features) < 2:
    st.warning("군집화를 위해 속성을 두 개 이상 선택해 주세요.")
    st.stop()


# --------------------------------------------------
# 표준화 + K-평균
# --------------------------------------------------
scaler = StandardScaler()

X = scaler.fit_transform(
    cluster_df[selected_features]
)

kmeans = KMeans(
    n_clusters=3,
    random_state=42,
    n_init=10
)

cluster_df["군집번호"] = kmeans.fit_predict(X)


# --------------------------------------------------
# 군집 번호를 누적 관객 평균 순서에 따라
# ㉮ / ㉯ / ㉰로 변경
# --------------------------------------------------
cluster_order = (
    cluster_df
    .groupby("군집번호")["total_audi"]
    .mean()
    .sort_values(ascending=False)
    .index
    .tolist()
)

label_map = {
    cluster_order[0]: "㉮",
    cluster_order[1]: "㉯",
    cluster_order[2]: "㉰",
}

cluster_df["영화 유형"] = cluster_df["군집번호"].map(label_map)


# --------------------------------------------------
# 2차원 산점도
# --------------------------------------------------
st.subheader("📊 2차원 영화 유형 산점도")

axis_options = selected_features

axis_col1, axis_col2 = st.columns(2)

with axis_col1:
    x_feature = st.selectbox(
        "가로축",
        axis_options,
        index=0,
        key="x_feature"
    )

with axis_col2:
    y_default = 1 if len(axis_options) > 1 else 0

    y_feature = st.selectbox(
        "세로축",
        axis_options,
        index=y_default,
        key="y_feature"
    )


fig_2d = px.scatter(
    cluster_df,
    x=x_feature,
    y=y_feature,
    color="영화 유형",
    hover_name="movieNm",
    hover_data={
        "영화 유형": True,
        x_feature: ":.2f",
        y_feature: ":.2f",
        "movieNm": False,
    },
    labels={
        x_feature: x_feature,
        y_feature: y_feature,
        "영화 유형": "영화 유형",
    },
    title=f"{x_feature} × {y_feature}"
)

fig_2d.update_traces(
    marker=dict(size=9)
)

fig_2d.update_layout(
    legend_title_text="영화 유형",
    hovermode="closest"
)

st.plotly_chart(
    fig_2d,
    use_container_width=True
)


# --------------------------------------------------
# 3차원 산점도
# --------------------------------------------------
st.subheader("🌐 3차원 영화 유형 산점도")

if len(selected_features) < 3:
    st.info(
        "3차원 산점도를 만들려면 군집화에 사용할 속성을 "
        "3개 이상 선택해야 합니다."
    )
else:
    z_col1, z_col2, z_col3 = st.columns(3)

    with z_col1:
        x3_feature = st.selectbox(
            "X축",
            selected_features,
            index=0,
            key="x3_feature"
        )

    with z_col2:
        y3_feature = st.selectbox(
            "Y축",
            selected_features,
            index=1,
            key="y3_feature"
        )

    with z_col3:
        z3_feature = st.selectbox(
            "Z축",
            selected_features,
            index=2,
            key="z3_feature"
        )

    fig_3d = px.scatter_3d(
        cluster_df,
        x=x3_feature,
        y=y3_feature,
        z=z3_feature,
        color="영화 유형",
        hover_name="movieNm",
        hover_data={
            "영화 유형": True,
            x3_feature: ":.2f",
            y3_feature: ":.2f",
            z3_feature: ":.2f",
            "movieNm": False,
        },
        labels={
            x3_feature: x3_feature,
            y3_feature: y3_feature,
            z3_feature: z3_feature,
            "영화 유형": "영화 유형",
        },
        title=f"{x3_feature} × {y3_feature} × {z3_feature}"
    )

    fig_3d.update_traces(
        marker=dict(size=4)
    )

    fig_3d.update_layout(
        legend_title_text="영화 유형",
        scene=dict(
            xaxis_title=x3_feature,
            yaxis_title=y3_feature,
            zaxis_title=z3_feature,
        )
    )

    st.plotly_chart(
        fig_3d,
        use_container_width=True
    )


# --------------------------------------------------
# 유형별 통계
# --------------------------------------------------
st.subheader("📋 영화 유형별 특징")

summary = (
    cluster_df
    .groupby("영화 유형")
    .agg(
        영화_편수=("movieNm", "count"),
        스크린수_평균=("first_scrn", "mean"),
        누적관객_평균=("total_audi", "mean"),
        십위권일수_평균=("days_in_top10", "mean"),
        롱런지수_평균=("롱런 지수", "mean"),
    )
    .reset_index()
)

# ㉮ → ㉯ → ㉰ 순서
label_order = ["㉮", "㉯", "㉰"]

summary["영화 유형"] = pd.Categorical(
    summary["영화 유형"],
    categories=label_order,
    ordered=True
)

summary = summary.sort_values("영화 유형")

summary_display = summary.rename(
    columns={
        "영화 유형": "영화 유형",
        "영화_편수": "편수",
        "스크린수_평균": "스크린 수 평균",
        "누적관객_평균": "누적 관객 평균",
        "십위권일수_평균": "10위권 일수 평균",
        "롱런지수_평균": "롱런 지수 평균",
    }
).copy()

summary_display["편수"] = summary_display["편수"].map(
    lambda x: f"{x:,}"
)

summary_display["스크린 수 평균"] = summary_display[
    "스크린 수 평균"
].map(lambda x: f"{x:,.1f}")

summary_display["누적 관객 평균"] = summary_display[
    "누적 관객 평균"
].map(lambda x: f"{x:,.0f}")

summary_display["10위권 일수 평균"] = summary_display[
    "10위권 일수 평균"
].map(lambda x: f"{x:,.1f}")

summary_display["롱런 지수 평균"] = summary_display[
    "롱런 지수 평균"
].map(lambda x: f"{x:,.2f}")

st.dataframe(
    summary_display,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# 유형별 누적 관객 상위 영화 5편
# --------------------------------------------------
st.subheader("🎞️ 유형별 누적 관객 상위 영화 5편")

top_movies = {}

for label in label_order:
    movies = (
        cluster_df[cluster_df["영화 유형"] == label]
        .sort_values("total_audi", ascending=False)
        .head(5)
    )

    top_movies[label] = movies

    st.markdown(f"### {label}")

    if len(movies) == 0:
        st.write("해당 유형의 영화가 없습니다.")
    else:
        movie_list = movies[
            ["movieNm", "total_audi"]
        ].copy()

        movie_list.columns = [
            "영화 제목",
            "누적 관객"
        ]

        movie_list["누적 관객"] = movie_list[
            "누적 관객"
        ].map(lambda x: f"{x:,}명")

        st.dataframe(
            movie_list,
            use_container_width=True,
            hide_index=True
        )


# --------------------------------------------------
# 분석에 사용한 속성 설명
# --------------------------------------------------
st.divider()

st.caption(
    "군집화 속성: 스크린 수(log10), 누적 관객(log10), "
    "10위권 일수, 롱런 지수(누적 관객 ÷ 첫 주 관객, 최대 20). "
    "군집화 전 선택한 속성은 표준화한 뒤 K-평균으로 3개 유형으로 분류했습니다."
)
