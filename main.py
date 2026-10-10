import streamlit as st
import pandas as pd
import plotly.express as px
import re
from itertools import combinations

st.set_page_config(
    page_title="급식 규칙 찾기",
    page_icon="🍱",
    layout="wide",
)

URL = (
    "https://raw.githubusercontent.com/"
    "teacher188-netizen/2026-datascience/"
    "refs/heads/main/inhwa_meals.csv"
)

# ==========================================
# 1. 제목과 디자인
# ==========================================
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #fffaf0, #eff8f0);
    }
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.9);
        border: 1px solid #dce9df;
        padding: 15px;
        border-radius: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🍱 급식 규칙 찾기")
st.caption("우리 학교 급식에서 함께 등장하는 메뉴의 규칙을 찾아봅니다.")


# ==========================================
# 2. CSV 불러오기
# ==========================================
@st.cache_data(ttl=3600)
def load_data():
    data = pd.read_csv(URL, encoding="utf-8")

    required = ["날짜", "식사", "메뉴"]
    missing = [col for col in required if col not in data.columns]

    if missing:
        raise ValueError(
            f"필요한 열이 없습니다: {missing}. "
            f"현재 열 이름: {list(data.columns)}"
        )

    return data


try:
    df = load_data()
except Exception as error:
    st.error(f"급식 데이터를 불러오지 못했습니다: {error}")
    st.stop()


# ==========================================
# 3. 메뉴 이름 정리
# ==========================================
def clean_menu(value):
    if pd.isna(value):
        return ""

    name = str(value).strip()

    # 괄호와 괄호 안 내용 제거
    while True:
        cleaned = re.sub(r"\([^()]*\)", "", name)
        if cleaned == name:
            break
        name = cleaned

    name = re.sub(r"\s+", " ", name).strip()

    if name.lower() in ("", "nan", "none"):
        return ""

    return name


# ==========================================
# 4. 중식 데이터 선택
# ==========================================
df["식사"] = df["식사"].fillna("").astype(str).str.strip()

lunch = df[
    df["식사"].str.contains("중식", na=False)
].copy()

if lunch.empty:
    st.warning("중식 데이터가 없습니다. CSV의 식사 열을 확인해 주세요.")
    st.stop()


# ==========================================
# 5. 하루를 장바구니 하나로 만들기
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
# 6. 메뉴별 출현 일수와 함께 나온 일수 계산
# ==========================================
total_days = len(baskets)
item_counts = {}
pair_counts = {}

for basket in baskets:
    for item in basket:
        item_counts[item] = item_counts.get(item, 0) + 1

    for a, b in combinations(sorted(basket), 2):
        pair = (a, b)
        pair_counts[pair] = pair_counts.get(pair, 0) + 1


# ==========================================
# 7. 양방향 연관 규칙 계산
# ==========================================
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

columns = ["조건", "결과", "동시", "지지도", "신뢰도", "향상도"]
rules_df = pd.DataFrame(rules, columns=columns)


# ==========================================
# 8. 전체 요약
# ==========================================
c1, c2, c3 = st.columns(3)

c1.metric("🍚 급식 일수", f"{total_days:,}일")
c2.metric("🥗 메뉴 종류 수", f"{len(item_counts):,}종")
c3.metric("🤝 함께 나온 메뉴 쌍", f"{len(pair_counts):,}쌍")

st.divider()


# ==========================================
# 9. 연관 규칙 필터
# ==========================================
st.subheader("🔎 연관 규칙 찾기")

col1, col2 = st.columns([2, 1])

menu_list = sorted(item_counts.keys())

with col1:
    selected_menu = st.selectbox(
        "규칙에서 찾아볼 메뉴",
        ["전체 메뉴"] + menu_list,
        key="rule_menu_select",
    )

with col2:
    sort_name = st.selectbox(
        "정렬 기준",
        ["향상도 순", "신뢰도 순", "동시 순"],
        key="rule_sort_select",
    )

min_together = st.slider(
    "최소 동시 일수",
    min_value=1,
    max_value=10,
    value=1,
    step=1,
    help="이 일수보다 적게 함께 나온 규칙은 표와 그래프에서 제외합니다.",
)

# 동시 일수 필터
filtered = rules_df[
    rules_df["동시"] >= min_together
].copy()

# 선택 메뉴 필터
if selected_menu != "전체 메뉴":
    filtered = filtered[
        (filtered["조건"] == selected_menu)
        | (filtered["결과"] == selected_menu)
    ].copy()

sort_columns = {
    "향상도 순": "향상도",
    "신뢰도 순": "신뢰도",
    "동시 순": "동시",
}

sort_column = sort_columns[sort_name]

filtered = filtered.sort_values(
    by=[sort_column, "신뢰도", "동시"],
    ascending=[False, False, False],
).reset_index(drop=True)


# ==========================================
# 10. 필터 적용 후 규칙 개수
# ==========================================
st.markdown(
    f"**현재 조건에 맞는 규칙: {len(filtered):,}개**"
)

# ==========================================
# 11. 연관 규칙 표
# ==========================================
st.subheader("📋 연관 규칙 표")

st.caption(
    "지지도와 신뢰도는 백분율입니다. "
    "향상도가 1보다 크면 독립적으로 등장할 때보다 "
    "함께 나오는 경향이 강합니다."
)

if filtered.empty:
    st.info(
        "조건에 맞는 규칙이 없습니다. "
        "최소 동시 일수를 낮추거나 다른 메뉴를 선택해 보세요."
    )
else:
    shown = filtered.copy()

    shown["지지도"] = shown["지지도"].map(
        lambda x: f"{x:.1%}"
    )
    shown["신뢰도"] = shown["신뢰도"].map(
        lambda x: f"{x:.1%}"
    )
    shown["향상도"] = shown["향상도"].map(
        lambda x: f"{x:.3f}"
    )

    st.dataframe(
        shown[columns],
        use_container_width=True,
        hide_index=True,
        height=420,
    )


# ==========================================
# 12. 향상도 TOP 10 그래프
# ==========================================
st.subheader("📊 향상도 TOP 10")

if filtered.empty:
    st.info("그래프로 나타낼 규칙이 없습니다.")
else:
    top = filtered.sort_values(
        by=["향상도", "신뢰도", "동시"],
        ascending=[False, False, False],
    ).head(10).copy()

    top["규칙"] = top["조건"] + " → " + top["결과"]
    top = top.sort_values("향상도", ascending=True)

    fig = px.bar(
        top,
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
        height=max(350, 48 * len(top) + 100),
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


# ==========================================
# 13. 함께 나온 적 없는 짝
# ==========================================
st.divider()
st.subheader("🚫 함께 나온 적 없는 짝")

st.write(
    "메뉴 하나를 고르면 그 메뉴와 같은 날 한 번도 함께 나오지 않았지만, "
    "혼자서는 10일 이상 등장한 메뉴를 찾아줍니다."
)

selected_absent_menu = st.selectbox(
    "함께 나온 적 없는 짝을 찾을 기준 메뉴",
    menu_list,
    key="absent_pair_menu_select",
)

selected_days = item_counts[selected_absent_menu]

st.markdown(
    f"**선택한 메뉴: {selected_absent_menu}** · "
    f"출현 일수: **{selected_days:,}일**"
)

# 선택 메뉴와 한 번도 함께 나오지 않은 메뉴 찾기
absent_rows = []

for other_menu, other_days in item_counts.items():
    if other_menu == selected_absent_menu:
        continue

    pair = tuple(sorted((selected_absent_menu, other_menu)))

    # 혼자서 10일 이상 나오고, 두 메뉴의 동시 출현 기록이 없어야 함
    if other_days >= 10 and pair not in pair_counts:
        absent_rows.append({
            "메뉴": other_menu,
            "나온 날 수": other_days,
        })

absent_df = pd.DataFrame(
    absent_rows,
    columns=["메뉴", "나온 날 수"],
)

if absent_df.empty:
    st.info(
        "이 메뉴와 함께 나온 적이 없고, 혼자서는 10일 이상 나온 "
        "메뉴가 없습니다."
    )
else:
    absent_df = absent_df.sort_values(
        by=["나온 날 수", "메뉴"],
        ascending=[False, True],
    ).reset_index(drop=True)

    st.markdown(
        f"**함께 나온 적 없는 메뉴: {len(absent_df):,}종**"
    )

    st.dataframe(
        absent_df,
        use_container_width=True,
        hide_index=True,
    )


# ==========================================
# 14. 지표 설명
# ==========================================
with st.expander("📖 지지도·신뢰도·향상도 설명"):
    st.markdown(
        """
        - **동시:** 두 메뉴가 같은 날 함께 나온 급식 일수
        - **지지도:** 함께 나온 일수 ÷ 전체 분석 급식 일수
        - **신뢰도:** 조건 메뉴가 나온 날 중 결과 메뉴도 나온 비율
        - **향상도:** 신뢰도 ÷ 결과 메뉴의 전체 출현 비율

        향상도가 1보다 크면 독립적으로 등장할 때보다
        함께 나타나는 경향이 강합니다.
        이는 상관관계이며 인과관계를 의미하지는 않습니다.
        """
    )


# ==========================================
# 15. 원본 데이터 확인
# ==========================================
with st.expander("🗂️ 중식 원본 데이터 확인"):
    st.dataframe(
        lunch,
        use_container_width=True,
        hide_index=True,
    )
```
