```python
import re
from itertools import combinations

import pandas as pd
import plotly.express as px
import streamlit as st


# ==========================================
# 1. 앱 설정
# ==========================================
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


# ==========================================
# 2. 화면 디자인
# ==========================================
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #fffaf0, #eff8f0);
    }

    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #246b50;
        margin-bottom: 0.2rem;
    }

    .sub-title {
        font-size: 1rem;
        color: #61776b;
        margin-bottom: 1.5rem;
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid #dce9df;
        padding: 16px;
        border-radius: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-title">🍱 급식 규칙 찾기</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="sub-title">'
    '우리 학교 급식 메뉴에서 함께 등장하는 규칙을 찾아보세요!'
    '</div>',
    unsafe_allow_html=True,
)


# ==========================================
# 3. CSV 불러오기
# ==========================================
@st.cache_data(ttl=3600)
def load_data():
    data = pd.read_csv(DATA_URL, encoding="utf-8")

    required_columns = ["날짜", "식사", "메뉴"]

    for column in required_columns:
        if column not in data.columns:
            raise ValueError(
                f"CSV에 '{column}' 열이 없습니다. "
                f"현재 열 이름: {list(data.columns)}"
            )

    return data


try:
    df = load_data()
except Exception as error:
    st.error("급식 데이터를 불러오지 못했습니다.")
    st.code(str(error))
    st.info(
        "CSV 주소와 날짜, 식사, 메뉴 열 이름을 확인해 주세요."
    )
    st.stop()


# ==========================================
# 4. 메뉴 이름 정리
# ==========================================
def clean_menu(value):
    if pd.isna(value):
        return ""

    name = str(value).strip()

    # 괄호 안 내용 제거
    # 예: 사과(부사) -> 사과
    # 예: 김치(배추:국산) -> 김치
    previous = None

    while previous != name:
        previous = name
        name = re.sub(r"\([^()]*\)", "", name)

    name = re.sub(r"\s+", " ", name).strip()

    if name.lower() in ("", "nan", "none"):
        return ""

    return name


# ==========================================
# 5. 중식 데이터 선택
# ==========================================
df["식사"] = df["식사"].fillna("").astype(str).str.strip()

lunch = df[
    df["식사"].str.contains("중식", na=False)
].copy()

if lunch.empty:
    st.warning(
        "중식 데이터를 찾을 수 없습니다. "
        "CSV의 식사 열에 중식이 기록되어 있는지 확인해 주세요."
    )
    st.stop()


# ==========================================
# 6. 하루 식단을 장바구니로 변환
# ==========================================
def make_baskets(data):
    baskets = []

    for menu_text in data["메뉴"]:
        if pd.isna(menu_text):
            continue

        items = set()

        for raw_item in str(menu_text).split("|"):
            item = clean_menu(raw_item)

            if item:
                items.add(item)

        if items:
            baskets.append(items)

    return baskets


baskets = make_baskets(lunch)

if not baskets:
    st.warning("분석할 수 있는 메뉴가 없습니다.")
    st.stop()


# ==========================================
# 7. 메뉴 출현 횟수와 메뉴 쌍 계산
# ==========================================
def analyze_baskets(baskets):
    total_days = len(baskets)

    item_counts = {}
    pair_counts = {}

    for basket in baskets:
        for item in basket:
            item_counts[item] = item_counts.get(item, 0) + 1

        # 한 날짜 안에서 같은 메뉴는 한 번만 계산
        for item_a, item_b in combinations(sorted(basket), 2):
            pair = (item_a, item_b)
            pair_counts[pair] = pair_counts.get(pair, 0) + 1

    rules = []

    for (item_a, item_b), together in pair_counts.items():
        support = together / total_days

        # A -> B
        confidence_ab = together / item_counts[item_a]
        lift_ab = confidence_ab / (
            item_counts[item_b] / total_days
        )

        rules.append(
            {
                "조건": item_a,
                "결과": item_b,
                "동시": together,
                "지지도": support,
                "신뢰도": confidence_ab,
                "향상도": lift_ab,
            }
        )

        # B -> A
        confidence_ba = together / item_counts[item_b]
        lift_ba = confidence_ba / (
            item_counts[item_a] / total_days
        )

        rules.append(
            {
                "조건": item_b,
                "결과": item_a,
                "동시": together,
                "지지도": support,
                "신뢰도": confidence_ba,
                "향상도": lift_ba,
            }
        )

    columns = [
        "조건",
        "결과",
        "동시",
        "지지도",
        "신뢰도",
        "향상도",
    ]

    rules_df = pd.DataFrame(rules, columns=columns)

    return item_counts, pair_counts, rules_df


item_counts, pair_counts, rules_df = analyze_baskets(baskets)


# ==========================================
# 8. 요약 정보
# ==========================================
total_days = len(baskets)
total_menus = len(item_counts)
total_pairs = len(pair_counts)

col1, col2, col3 = st.columns(3)

col1.metric("🍚 급식 일수", f"{total_days:,}일")
col2.metric("🥗 메뉴 종류 수", f"{total_menus:,}종")
col3.metric("🤝 함께 나온 메뉴 쌍", f"{total_pairs:,}쌍")

st.divider()


# ==========================================
# 9. 메뉴 선택 및 정렬
# ==========================================
st.subheader("🔎 연관 규칙 찾기")

left, right = st.columns([2, 1])

menu_list = sorted(item_counts.keys())

with left:
    selected_menu = st.selectbox(
        "메뉴 선택",
        ["전체 메뉴"] + menu_list,
    )

with right:
    sort_option = st.selectbox(
        "정렬 기준",
        ["향상도 순", "신뢰도 순", "동시 순"],
    )


# 메뉴 필터
filtered = rules_df.copy()

if selected_menu != "전체 메뉴":
    filtered = filtered[
        (filtered["조건"] == selected_menu)
        | (filtered["결과"] == selected_menu)
    ].copy()


# 정렬
sort_columns = {
    "향상도 순": "향상도",
    "신뢰도 순": "신뢰도",
    "동시 순": "동시",
}

sort_column = sort_columns[sort_option]

filtered = filtered.sort_values(
    by=[sort_column, "신뢰도", "동시"],
    ascending=[False, False, False],
).reset_index(drop=True)


# ==========================================
# 10. 규칙 표 표시
# ==========================================
st.subheader("📋 연관 규칙 표")

st.caption(
    "지지도와 신뢰도는 백분율로 표시합니다. "
    "향상도가 1보다 크면 독립적으로 등장할 때보다 "
    "함께 나타나는 경향이 강합니다."
)

if filtered.empty:
    st.info("표시할 규칙이 없습니다.")
else:
    display_table = filtered.copy()

    display_table["지지도"] = display_table["지지도"].map(
        lambda value: f"{value:.1%}"
    )

    display_table["신뢰도"] = display_table["신뢰도"].map(
        lambda value: f"{value:.1%}"
    )

    display_table["향상도"] = display_table["향상도"].map(
        lambda value: f"{value:.3f}"
    )

    st.dataframe(
        display_table[
            [
                "조건",
                "결과",
                "동시",
                "지지도",
                "신뢰도",
                "향상도",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        height=420,
    )

    st.caption(
        f"현재 표시 중인 규칙: {len(filtered):,}개"
    )


# ==========================================
# 11. 향상도 상위 10개 가로 막대그래프
# ==========================================
st.divider()
st.subheader("📊 향상도 TOP 10")

if filtered.empty:
    st.info("그래프로 나타낼 규칙이 없습니다.")
else:
    top10 = filtered.sort_values(
        by=["향상도", "신뢰도", "동시"],
        ascending=[False, False, False],
    ).head(10).copy()

    top10["규칙"] = (
        top10["조건"] + " → " + top10["결과"]
    )

    # 가로 막대그래프에서 높은 값이 위로 오도록 정렬
    top10 = top10.sort_values(
        "향상도",
        ascending=True,
    )

    fig = px.bar(
        top10,
        x="향상도",
        y="규칙",
        orientation="h",
        text="향상도",
        hover_data={
            "조건": True,
            "결과": True,
            "동시": True,
            "지지도": ":.1%",
            "신뢰도": ":.1%",
            "향상도": ":.3f",
            "규칙": False,
        },
        labels={
            "향상도": "향상도",
            "규칙": "메뉴 규칙",
        },
        color="향상도",
        color_continuous_scale="Greens",
    )

    fig.update_traces(
        texttemplate="%{x:.2f}",
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_layout(
        height=max(350, 48 * len(top10) + 100),
        xaxis_title="향상도 (Lift)",
        yaxis_title="",
        coloraxis_showscale=False,
        margin=dict(l=20, r=60, t=30, b=30),
    )

    fig.add_vline(
        x=1,
        line_dash="dash",
        line_color="gray",
        annotation_text="향상도 = 1",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ==========================================
# 12. 분석 지표 설명
# ==========================================
with st.expander("📖 분석 지표 알아보기"):
    st.markdown(
        """
        **동시**

        두 메뉴가 같은 날 함께 나온 급식 일수입니다.

        **지지도**

        두 메뉴가 함께 나온 일수를 전체 분석 급식 일수로
        나눈 값입니다.

        **신뢰도**

        조건 메뉴가 나온 날 중 결과 메뉴도 나온 비율입니다.

        **향상도**

        신뢰도를 결과 메뉴의 전체 출현 비율로 나눈 값입니다.

        - 향상도 > 1: 독립적으로 등장할 때보다 함께 나오는 경향이 강함
        - 향상도 = 1: 독립적인 등장과 비슷함
        - 향상도 < 1: 함께 나오는 경향이 상대적으로 약함

        향상도가 높다고 해서 두 메뉴 사이에 인과관계가
        있다는 뜻은 아닙니다.
        """
    )


# ==========================================
# 13. 원본 데이터 확인
# ==========================================
with st.expander("🗂️ 중식 원본 데이터 확인"):
    st.dataframe(
        lunch,
        use_container_width=True,
        hide_index=True,
    )
```
