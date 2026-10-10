import streamlit as st
import pandas as pd
import plotly.express as px
import re
from itertools import combinations

st.set_page_config(page_title="급식 규칙 찾기", page_icon="🍱", layout="wide")

URL = "https://raw.githubusercontent.com/teacher188-netizen/2026-datascience/refs/heads/main/inhwa_meals.csv"

st.title("🍱 급식 규칙 찾기")
st.caption("우리 학교 급식에서 함께 등장하는 메뉴의 규칙을 찾아봅니다.")

@st.cache_data(ttl=3600)
def load_data():
    df = pd.read_csv(URL, encoding="utf-8")
    required = ["날짜", "식사", "메뉴"]
    if not all(c in df.columns for c in required):
        raise ValueError(f"필요한 열: {required}, 실제 열: {list(df.columns)}")
    return df

def clean_menu(value):
    if pd.isna(value):
        return ""
    name = str(value).strip()
    while True:
        cleaned = re.sub(r"\([^()]*\)", "", name)
        if cleaned == name:
            break
        name = cleaned
    return re.sub(r"\s+", " ", name).strip()

try:
    df = load_data()
except Exception as e:
    st.error(f"CSV를 읽을 수 없습니다: {e}")
    st.stop()

df["식사"] = df["식사"].fillna("").astype(str).str.strip()
lunch = df[df["식사"].str.contains("중식", na=False)].copy()

if lunch.empty:
    st.warning("중식 데이터가 없습니다. 식사 열의 실제 값을 확인해 주세요.")
    st.stop()

baskets = []
for value in lunch["메뉴"]:
    if pd.isna(value):
        continue
    items = {clean_menu(x) for x in str(value).split("|")}
    items.discard("")
    if items:
        baskets.append(items)

if not baskets:
    st.warning("분석할 메뉴가 없습니다.")
    st.stop()

n = len(baskets)
item_counts = {}
pair_counts = {}

for basket in baskets:
    for item in basket:
        item_counts[item] = item_counts.get(item, 0) + 1
    for a, b in combinations(sorted(basket), 2):
        pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1

rules = []
for (a, b), together in pair_counts.items():
    support = together / n
    rules.append({
        "조건": a, "결과": b, "동시": together,
        "지지도": support,
        "신뢰도": together / item_counts[a],
        "향상도": (together / item_counts[a]) / (item_counts[b] / n),
    })
    rules.append({
        "조건": b, "결과": a, "동시": together,
        "지지도": support,
        "신뢰도": together / item_counts[b],
        "향상도": (together / item_counts[b]) / (item_counts[a] / n),
    })

rules_df = pd.DataFrame(
    rules,
    columns=["조건", "결과", "동시", "지지도", "신뢰도", "향상도"],
)

c1, c2, c3 = st.columns(3)
c1.metric("🍚 급식 일수", f"{n:,}일")
c2.metric("🥗 메뉴 종류 수", f"{len(item_counts):,}종")
c3.metric("🤝 함께 나온 메뉴 쌍", f"{len(pair_counts):,}쌍")

st.divider()
st.subheader("🔎 연관 규칙")

c1, c2 = st.columns(2)
with c1:
    menu = st.selectbox("메뉴 선택", ["전체 메뉴"] + sorted(item_counts))
with c2:
    sort_name = st.selectbox("정렬 기준", ["향상도 순", "신뢰도 순", "동시 순"])

filtered = rules_df.copy()
if menu != "전체 메뉴":
    filtered = filtered[(filtered["조건"] == menu) | (filtered["결과"] == menu)]

sort_col = {
    "향상도 순": "향상도",
    "신뢰도 순": "신뢰도",
    "동시 순": "동시",
}[sort_name]

filtered = filtered.sort_values(
    [sort_col, "신뢰도", "동시"],
    ascending=[False, False, False],
)

if filtered.empty:
    st.info("표시할 규칙이 없습니다.")
else:
    shown = filtered.copy()
    shown["지지도"] = shown["지지도"].map(lambda x: f"{x:.1%}")
    shown["신뢰도"] = shown["신뢰도"].map(lambda x: f"{x:.1%}")
    shown["향상도"] = shown["향상도"].map(lambda x: f"{x:.3f}")
    st.dataframe(shown, use_container_width=True, hide_index=True)

    st.subheader("📊 향상도 TOP 10")
    top = filtered.head(10).copy()
    top["규칙"] = top["조건"] + " → " + top["결과"]
    top = top.sort_values("향상도", ascending=True)

    fig = px.bar(
        top,
        x="향상도",
        y="규칙",
        orientation="h",
        text="향상도",
        hover_data=["동시", "지지도", "신뢰도"],
        labels={"향상도": "향상도 (Lift)", "규칙": "메뉴 규칙"},
        color="향상도",
        color_continuous_scale="Greens",
    )
    fig.update_traces(texttemplate="%{x:.2f}", textposition="outside")
    fig.update_layout(
        coloraxis_showscale=False,
        xaxis_title="향상도",
        yaxis_title="",
    )
    fig.add_vline(x=1, line_dash="dash", line_color="gray")
    st.plotly_chart(fig, use_container_width=True)

with st.expander("📖 지표 설명"):
    st.markdown("""
    - **동시:** 두 메뉴가 함께 나온 급식 일수
    - **지지도:** 두 메뉴가 함께 나온 일수 ÷ 전체 급식 일수
    - **신뢰도:** 조건 메뉴가 나온 날 중 결과 메뉴도 나온 비율
    - **향상도:** 신뢰도 ÷ 결과 메뉴의 전체 출현 비율
    - 향상도 1 초과: 독립적으로 등장할 때보다 함께 나오는 경향이 강함
    """)

with st.expander("🗂️ 중식 원본 데이터"):
    st.dataframe(lunch, use_container_width=True, hide_index=True)
