
import re
from itertools import combinations

import pandas as pd
import plotly.express as px
import streamlit as st


# --------------------------------------------------
# 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="급식 규칙 찾기",
    page_icon="🍱",
    layout="wide",
)

DATA_URL = (
    "https://raw.githubusercontent.com/"
    "teacher188-netizen/2026-datascience/"
    "refs/heads/main/inhwa_meals.csv"
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #fffaf2;
    }
    h1, h2, h3 {
        color: #67452d;
    }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #f0dfc9;
        padding: 14px;
        border-radius: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🍱 급식 규칙 찾기")
st.write(
    "급식 메뉴를 하나의 묶음으로 보고, "
    "어떤 메뉴들이 함께 나오는지 찾아봅니다."
)


# --------------------------------------------------
# 데이터 불러오기 및 메뉴 정리
# --------------------------------------------------
@st.cache_data
def load_data():
    data = pd.read_csv(DATA_URL, encoding="utf-8")

    required_columns = {"날짜", "식사", "메뉴"}
    missing_columns = required_columns - set(data.columns)

    if missing_columns:
        raise ValueError(
            "CSV에 필요한 열이 없습니다: "
            + ", ".join(sorted(missing_columns))
        )

    data = data[["날짜", "식사", "메뉴"]].copy()
    data = data.dropna(subset=["날짜", "메뉴"])

    data["날짜"] = data["날짜"].astype(str).str.strip()
    data["식사"] = data["식사"].astype(str).str.strip()
    data["메뉴"] = data["메뉴"].astype(str)

    # 중식 데이터만 사용
    lunch = data[
        data["식사"].str.contains("중식", na=False)
    ].copy()

    def clean_menu(name):
        name = str(name).strip()

        # 괄호와 괄호 안의 내용 제거
        previous = None
        while previous != name:
            previous = name
            name = re.sub(r"\([^()]*\)", "", name)

        # 공백 정리
        name = re.sub(r"\s+", " ", name).strip()
        return name

    baskets = []

    for _, row in lunch.iterrows():
        raw_items = str(row["메뉴"]).split("|")
        cleaned_items = set()

        for item in raw_items:
            item = clean_menu(item)

            if item and item.lower() != "nan":
                cleaned_items.add(item)

        if cleaned_items:
            baskets.append(
                {
                    "날짜": row["날짜"],
                    "메뉴목록": sorted(cleaned_items),
                }
            )

    return lunch, baskets


try:
    raw_lunch, baskets = load_data()
except Exception as error:
    st.error("급식 데이터를 불러오지 못했습니다.")
    st.write("CSV 주소와 파일 형식을 확인해 주세요.")
    st.code(str(error))
    st.stop()

if not baskets:
    st.warning("분석할 중식 메뉴 데이터가 없습니다.")
    st.stop()


# --------------------------------------------------
# 메뉴 출현 횟수와 함께 나온 횟수 계산
# --------------------------------------------------
menu_days = {}
pair_days = {}

for basket in baskets:
    items = basket["메뉴목록"]

    for item in items:
        menu_days[item] = menu_days.get(item, 0) + 1

    for item_a, item_b in combinations(items, 2):
        pair = tuple(sorted((item_a, item_b)))
        pair_days[pair] = pair_days.get(pair, 0) + 1

total_days = len(baskets)
distinct_menu_count = len(menu_days)
unique_pair_count = len(pair_days)


# --------------------------------------------------
# 연관 규칙 생성
# 조건 → 결과와 결과 → 조건을 모두 생성
# --------------------------------------------------
rule_rows = []

for (item_a, item_b), together_count in pair_days.items():
    support = together_count / total_days

    # A → B
    confidence_ab = together_count / menu_days[item_a]
    lift_ab = confidence_ab / (menu_days[item_b] / total_days)

    rule_rows.append(
        {
            "조건": item_a,
            "결과": item_b,
            "동시": together_count,
            "지지도": support,
            "신뢰도": confidence_ab,
            "향상도": lift_ab,
        }
    )

    # B → A
    confidence_ba = together_count / menu_days[item_b]
    lift_ba = confidence_ba / (menu_days[item_a] / total_days)

    rule_rows.append(
        {
            "조건": item_b,
            "결과": item_a,
            "동시": together_count,
            "지지도": support,
            "신뢰도": confidence_ba,
            "향상도": lift_ba,
        }
    )

rules_df = pd.DataFrame(
    rule_rows,
    columns=[
        "조건",
        "결과",
        "동시",
        "지지도",
        "신뢰도",
        "향상도",
    ],
)


# --------------------------------------------------
# 전체 요약
# --------------------------------------------------
st.subheader("📊 급식 데이터 요약")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("분석한 중식 일수", f"{total_days:,}일")

with col2:
    st.metric("서로 다른 메뉴 종류", f"{distinct_menu_count:,}개")

with col3:
    st.metric("서로 다른 동시 출현 메뉴 짝", f"{unique_pair_count:,}쌍")

st.caption(
    "메뉴 짝은 순서와 관계없이 한 쌍으로 계산합니다. "
    "연관 규칙 표에는 조건과 결과의 방향을 바꾼 규칙도 각각 표시합니다."
)


# --------------------------------------------------
# 필터
# --------------------------------------------------
st.divider()
st.subheader("🔎 연관 규칙 찾아보기")

filter_col1, filter_col2 = st.columns(2)

menu_options = ["전체 메뉴"] + sorted(menu_days.keys())

with filter_col1:
    selected_menu = st.selectbox(
        "특정 메뉴가 포함된 규칙",
        menu_options,
        key="rule_menu_select",
    )

with filter_col2:
    sort_option = st.selectbox(
        "정렬 기준",
        ["향상도 높은 순", "신뢰도 높은 순", "함께 나온 횟수 많은 순"],
        key="rule_sort_select",
    )

min_together = st.slider(
    "최소 함께 나온 날짜 수",
    min_value=1,
    max_value=10,
    value=1,
    step=1,
    help="선택한 횟수보다 적게 함께 나온 메뉴 규칙은 제외합니다.",
)

filtered = rules_df[
    rules_df["동시"] >= min_together
].copy()

if selected_menu != "전체 메뉴":
    filtered = filtered[
        (filtered["조건"] == selected_menu)
        | (filtered["결과"] == selected_menu)
    ].copy()

if sort_option == "향상도 높은 순":
    filtered = filtered.sort_values(
        ["향상도", "신뢰도", "동시"],
        ascending=False,
    )
elif sort_option == "신뢰도 높은 순":
    filtered = filtered.sort_values(
        ["신뢰도", "향상도", "동시"],
        ascending=False,
    )
else:
    filtered = filtered.sort_values(
        ["동시", "향상도", "신뢰도"],
        ascending=False,
    )

st.write(f"**현재 조건에 맞는 규칙: {len(filtered):,}개**")


# --------------------------------------------------
# 연관 규칙 표
# --------------------------------------------------
st.subheader("📋 메뉴 연관 규칙")

if filtered.empty:
    st.info(
        "현재 조건에 맞는 규칙이 없습니다. "
        "최소 함께 나온 날짜 수를 낮추거나 다른 메뉴를 선택해 보세요."
    )
else:
    display_df = filtered.copy()

    display_df["지지도"] = (
        display_df["지지도"] * 100
    ).map(lambda value: f"{value:.1f}%")

    display_df["신뢰도"] = (
        display_df["신뢰도"] * 100
    ).map(lambda value: f"{value:.1f}%")

    display_df["향상도"] = display_df["향상도"].map(
        lambda value: f"{value:.2f}"
    )

    display_df["동시"] = display_df["동시"].map(
        lambda value: f"{value:,}일"
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------
# 향상도 상위 10개 그래프
# --------------------------------------------------
st.divider()
st.subheader("📈 향상도가 높은 규칙 TOP 10")

if filtered.empty:
    st.info("그래프를 표시할 규칙이 없습니다.")
else:
    chart_df = filtered.nlargest(10, "향상도").copy()
    chart_df["규칙"] = (
        chart_df["조건"] + " → " + chart_df["결과"]
    )

    chart_df = chart_df.sort_values("향상도", ascending=True)

    fig = px.bar(
        chart_df,
        x="향상도",
        y="규칙",
        orientation="h",
        text="향상도",
        hover_data={
            "조건": True,
            "결과": True,
            "동시": True,
            "신뢰도": ":.1%",
            "지지도": ":.1%",
            "향상도": ":.2f",
            "규칙": False,
        },
        labels={
            "향상도": "향상도",
            "규칙": "연관 규칙",
            "동시": "함께 나온 날짜 수",
            "신뢰도": "신뢰도",
            "지지도": "지지도",
        },
    )

    fig.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside",
        cliponaxis=False,
    )
    fig.update_layout(
        height=max(400, len(chart_df) * 38),
        xaxis_title="향상도",
        yaxis_title="",
        margin=dict(l=20, r=60, t=25, b=20),
    )

    st.plotly_chart(fig, use_container_width=True)

st.caption(
    "향상도는 두 메뉴가 우연히 함께 나오는 정도와 비교해 "
    "얼마나 더 자주 함께 나오는지를 나타냅니다. "
    "향상도가 1보다 크면 독립적으로 나올 때보다 함께 나오는 경향이 있습니다."
)


# --------------------------------------------------
# 함께 나온 적 없는 메뉴 짝
# --------------------------------------------------
st.divider()
st.subheader("🚫 함께 나온 적 없는 짝")

st.write(
    "선택한 메뉴와 한 번도 같은 급식에 나오지 않은 메뉴를 찾습니다. "
    "다른 메뉴도 최소 10일 이상 등장했을 때만 표시합니다."
)

absent_menu = st.selectbox(
    "확인할 메뉴를 선택하세요",
    sorted(menu_days.keys()),
    key="absent_pair_menu_select",
)

st.metric(
    f"'{absent_menu}'가 나온 날짜 수",
    f"{menu_days[absent_menu]:,}일",
)

absent_rows = []

for other_menu, other_days in menu_days.items():
    if other_menu == absent_menu:
        continue

    if other_days < 10:
        continue

    pair = tuple(sorted((absent_menu, other_menu)))

    if pair not in pair_days:
        absent_rows.append(
            {
                "메뉴": other_menu,
                "등장 날짜 수": other_days,
            }
        )

absent_df = pd.DataFrame(
    absent_rows,
    columns=["메뉴", "등장 날짜 수"],
)

if absent_df.empty:
    st.info(
        "조건에 맞는 메뉴가 없습니다. "
        "선택한 메뉴와 모든 메뉴가 적어도 한 번씩 함께 나왔거나, "
        "다른 메뉴의 등장 횟수가 10일 미만일 수 있습니다."
    )
else:
    absent_df = absent_df.sort_values(
        "등장 날짜 수",
        ascending=False,
    ).reset_index(drop=True)

    st.write(
        f"**함께 나온 적 없는 메뉴: {len(absent_df):,}개**"
    )

    st.dataframe(
        absent_df,
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------
# 지표 설명
# --------------------------------------------------
with st.expander("📖 지지도·신뢰도·향상도란?"):
    st.markdown(
        """
        - **지지도**: 전체 중식 중 두 메뉴가 함께 나온 날의 비율입니다.
        - **신뢰도**: 조건 메뉴가 나온 날 중 결과 메뉴도 함께 나온 비율입니다.
        - **향상도**: 두 메뉴가 독립적으로 나올 때와 비교해 함께 나오는 경향을 나타냅니다.
        - **동시**: 두 메뉴가 같은 중식에 나온 날짜 수입니다.

        향상도가 1보다 크면 함께 나오는 경향이 독립적인 경우보다 강하고,
        1이면 독립적인 경우와 비슷하며, 1보다 작으면 함께 나오는 경향이 약합니다.
        """
    )

with st.expander("🍚 분석에 사용한 중식 데이터 보기"):
    st.dataframe(
        raw_lunch,
        use_container_width=True,
        hide_index=True,
    )
