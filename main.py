```python
import re
from itertools import combinations

import pandas as pd
import plotly.express as px
import streamlit as st


# ------------------------------------------
# 기본 설정
# ------------------------------------------
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


# ------------------------------------------
# 화면 디자인
# ------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #fffaf0, #f0f8f4);
    }
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #246b50;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #60756b;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.85);
        border: 1px solid #dce9df;
        padding: 15px;
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
    '우리 학교 급식 데이터에서 함께 등장하는 메뉴의 규칙을 찾아봐요.'
    '</div>',
    unsafe_allow_html=True,
)


# ------------------------------------------
# 데이터 불러오기
# ------------------------------------------
@st.cache_data(ttl=3600)
def load_data(url):
    df = pd.read_csv(url, encoding="utf-8")

    required = {"날짜", "식사", "메뉴"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            "CSV에 필요한 열이 없습니다: "
            + ", ".join(sorted(missing))
        )

    return df


# ------------------------------------------
# 메뉴 이름 정리
# 괄호와 괄호 안 내용 제거
# 예: 사과(부사) -> 사과
# 예: 김치(배추:국산) -> 김치
# ------------------------------------------
def clean_menu(name):
    name = str(name).strip()

    # 괄호 안의 내용 제거. 중첩 괄호도 반복 처리.
    previous = None
    while previous != name:
        previous = name
        name = re.sub(r"\([^()]*\)", "", name)

    # 공백 정리
    name = re.sub(r"\s+", " ", name).strip()

    # 빈 메뉴 및 결측값 제외
    if not name or name.lower() in {"nan", "none"}:
        return ""

    return name


# ------------------------------------------
# 하루 식단을 장바구니 하나로 변환
# ------------------------------------------
def make_baskets(df):
    baskets = []

    for menu_text in df["메뉴"].dropna():
        items = set()

        for raw_menu in str(menu_text).split("|"):
            menu = clean_menu(raw_menu)
            if menu:
                items.add(menu)

        # 메뉴가 하나 이상 있는 날만 분석
        if items:
            baskets.append(items)

    return baskets


# ------------------------------------------
# 연관 규칙 계산
# ------------------------------------------
def find_rules(baskets):
    total_days = len(baskets)

    if total_days == 0:
        return pd.DataFrame(), {}, 0

    # 각 메뉴의 출현 일수
    item_counts = {}

    # 두 메뉴가 함께 나온 일수
    pair_counts = {}

    for basket in baskets:
        for item in basket:
            item_counts[item] = item_counts.get(item, 0) + 1

        for a, b in combinations(sorted(basket), 2):
            pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1

    rules = []

    for (a, b), together in pair_counts.items():
        support = together / total_days

        # A -> B
        confidence_ab = together / item_counts[a]
        lift_ab = confidence_ab / (item_counts[b] / total_days)

        rules.append({
            "조건": a,
            "결과": b,
            "동시": together,
            "지지도": support,
            "신뢰도": confidence_ab,
            "향상도": lift_ab,
        })

        # B -> A
        confidence_ba = together / item_counts[b]
        lift_ba = confidence_ba / (item_counts[a] / total_days)

        rules.append({
            "조건": b,
            "결과": a,
            "동시": together,
            "지지도": support,
            "신뢰도": confidence_ba,
            "향상도": lift_ba,
        })

    rules_df = pd.DataFrame(
        rules,
        columns=[
            "조건", "결과", "동시",
            "지지도", "신뢰도", "향상도",
        ],
    )

    return rules_df, item_counts, len(pair_counts)


# ------------------------------------------
# 실행
# ------------------------------------------
try:
    df = load_data(DATA_URL)
except Exception as e:
    st.error(f"급식 데이터를 불러오지 못했어요: {e}")
    st.info(
        "GitHub 주소가 올바른지, CSV의 열 이름이 "
        "날짜·식사·메뉴인지 확인해 주세요."
    )
    st.stop()


# 중식 데이터만 사용
df["식사"] = df["식사"].astype(str).str.strip()
lunch = df[df["식사"].str.contains("중식", na=False)].copy()

if lunch.empty:
    st.warning(
        "중식 데이터를 찾지 못했어요. "
        "CSV의 식사 열에 중식이 어떻게 기록되어 있는지 확인해 주세요."
    )
    st.stop()

baskets = make_baskets(lunch)

if not baskets:
    st.warning("분석할 수 있는 메뉴 데이터가 없어요.")
    st.stop()

rules_df, item_counts, pair_count = find_rules(baskets)

if rules_df.empty:
    st.warning("함께 나온 메뉴 쌍이 없어 규칙을 만들 수 없어요.")
    st.stop()


# ------------------------------------------
# 요약 지표
# ------------------------------------------
total_days = len(baskets)
menu_count = len(item_counts)

c1, c2, c3 = st.columns(3)

c1.metric("🍚 급식 일수", f"{total_days:,}일")
c2.metric("🥗 메뉴 종류 수", f"{menu_count:,}종")
c3.metric("🤝 함께 나온 메뉴 쌍", f"{pair_count:,}쌍")

st.divider()


# ------------------------------------------
# 필터와 정렬
# ------------------------------------------
st.subheader("🔎 연관 규칙 탐색")

col1, col2 = st.columns([2, 1])

all_menus = sorted(item_counts.keys())

with col1:
    selected_menu = st.selectbox(
        "메뉴 선택",
        options=["전체 메뉴"] + all_menus,
        index=0,
        help="메뉴를 선택하면 그 메뉴가 조건 또는 결과에 포함된 규칙만 보여요.",
    )

with col2:
    sort_by = st.selectbox(
        "정렬 기준",
        options=["향상도 순", "신뢰도 순", "동시 순"],
        index=0,
    )

filtered = rules_df.copy()

if selected_menu != "전체 메뉴":
    filtered = filtered[
        (filtered["조건"] == selected_menu)
        | (filtered["결과"] == selected_menu)
    ]

sort_column = {
    "향상도 순": "향상도",
    "신뢰도 순": "신뢰도",
    "동시 순": "동시",
}[sort_by]

filtered = filtered.sort_values(
    by=[sort_column, "신뢰도", "동시"],
    ascending=[False, False, False],
).reset_index(drop=True)


# ------------------------------------------
# 규칙 표
# ------------------------------------------
st.subheader("📋 메뉴 연관 규칙")

st.caption(
    "지지도·신뢰도는 백분율로 표시해요. "
    "향상도는 1보다 크면 독립적으로 등장할 때보다 "
    "함께 나타나는 경향이 강하다는 뜻이에요."
)

display_df = filtered.copy()

display_df["지지도"] = display_df["지지도"].map(
    lambda x: f"{x:.1%}"
)
display_df["신뢰도"] = display_df["신뢰도"].map(
    lambda x: f"{x:.1%}"
)
display_df["향상도"] = display_df["향상도"].map(
    lambda x: f"{x:.3f}"
)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    height=420,
)

st.caption(
    f"현재 표시 중인 규칙: {len(filtered):,}개 "
    f"(메뉴 쌍 하나당 방향이 다른 규칙 두 개)"
)


# ------------------------------------------
# 향상도 상위 10개 막대그래프
# ------------------------------------------
st.divider()
st.subheader("📊 향상도 TOP 10")

if filtered.empty:
    st.info("선택한 메뉴에 해당하는 규칙이 없어요.")
else:
    top10 = filtered.sort_values(
        by=["향상도", "신뢰도", "동시"],
        ascending=[False, False, False],
    ).head(10).copy()

    top10["규칙"] = (
        top10["조건"] + " → " + top10["결과"]
    )

    # 가로 막대그래프에서 가장 큰 값이 위에 오도록 역순 정렬
    top10 = top10.sort_values("향상도", ascending=True)

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
            "향상도": "향상도 (Lift)",
            "규칙": "연관 규칙",
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
        height=max(350, 45 * len(top10) + 100),
        xaxis_title="향상도",
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

    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "메뉴를 선택하면 그래프도 해당 메뉴가 포함된 규칙만으로 "
        "다시 계산돼요. 같은 메뉴 쌍의 양방향 규칙은 "
        "향상도는 같을 수 있지만 신뢰도는 다를 수 있어요."
    )


# ------------------------------------------
# 지표 설명
# ------------------------------------------
with st.expander("📖 지지도·신뢰도·향상도란?"):
    st.markdown(
        """
        - **동시:** 조건 메뉴와 결과 메뉴가 같은 날 함께 나온 일수
        - **지지도:** 함께 나온 일수 ÷ 전체 분석 급식 일수
        - **신뢰도:** 조건 메뉴가 나온 날 중 결과 메뉴도 나온 비율
        - **향상도:** 신뢰도 ÷ 결과 메뉴의 전체 출현 비율

        **향상도 해석**
        - 1보다 큼: 우연히 독립적으로 등장할 때보다 함께 등장하는 경향이 강함
        - 1과 같음: 두 메뉴가 독립적으로 등장하는 경우와 비슷함
        - 1보다 작음: 함께 등장하는 경향이 상대적으로 약함

        이 결과는 과거 급식 기록의 동시 출현 관계를 나타내며,
        메뉴 사이의 인과관계를 증명하지는 않아요.
        """
    )

with st.expander("🗂️ 원본 데이터 확인"):
    st.dataframe(lunch, use_container_width=True, hide_index=True)
```
