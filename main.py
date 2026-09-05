import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# --------------------------------------------------
# 1. 페이지 설정
# --------------------------------------------------

st.set_page_config(
    page_title="일일 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 일일 박스오피스")


# --------------------------------------------------
# 2. 한국 시간 기준 날짜 계산
# --------------------------------------------------

korea_now = datetime.now(ZoneInfo("Asia/Seoul"))

today = korea_now.date()
yesterday = today - timedelta(days=1)


# --------------------------------------------------
# 3. 사이드바 설정
# --------------------------------------------------

st.sidebar.header("🔎 조회 설정")

# 달력에서 날짜 선택
selected_date = st.sidebar.date_input(
    "조회 날짜",
    value=yesterday,
    max_value=yesterday
)

# 정렬 기준 선택
sort_option = st.sidebar.selectbox(
    "정렬 기준",
    [
        "순위순",
        "관객수순",
        "누적관객순",
        "스크린수순"
    ]
)

# 100만 관객 이상 영화만 볼지 선택
million_only = st.sidebar.checkbox(
    "🏆 100만 관객 이상만 보기"
)


# 선택한 날짜를 KOBIS API 형식으로 변환
target_dt = selected_date.strftime("%Y%m%d")


# --------------------------------------------------
# 4. KOBIS API 호출
# --------------------------------------------------

@st.cache_data(ttl=3600)
def get_boxoffice(target_dt):

    # Secrets에서 API 인증키를 가져옵니다.
    api_key = st.secrets["KOBIS_KEY"]

    url = (
        "https://www.kobis.or.kr/"
        "kobisopenapi/webservice/rest/boxoffice/"
        "searchDailyBoxOfficeList.json"
    )

    params = {
        "key": api_key,
        "targetDt": target_dt
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()
        data = response.json()

    except requests.RequestException as e:
        return None, f"KOBIS API 요청에 실패했습니다.\n\n{e}"

    except ValueError:
        return None, "API에서 올바른 JSON 데이터를 받지 못했습니다."

    # 인증키가 틀려도 HTTP 상태 코드는 200일 수 있으므로
    # faultInfo를 확인합니다.
    if "faultInfo" in data:

        fault = data["faultInfo"]

        error_code = fault.get(
            "errorCode",
            "알 수 없음"
        )

        error_message = fault.get(
            "message",
            "KOBIS API 오류가 발생했습니다."
        )

        return None, (
            f"KOBIS API 오류가 발생했습니다.\n\n"
            f"오류 코드: {error_code}\n"
            f"오류 내용: {error_message}\n\n"
            "KOBIS_KEY가 올바른지 확인해 주세요."
        )

    boxoffice_result = data.get("boxOfficeResult")

    if not boxoffice_result:
        return None, "박스오피스 결과가 없습니다."

    movie_list = boxoffice_result.get(
        "dailyBoxOfficeList",
        []
    )

    # 영화 목록이 없으면 집계 전으로 안내
    if not movie_list:
        return None, "그날은 아직 집계 전입니다"

    return movie_list, None


# API를 호출하는 동안 안내 문구를 보여 줍니다.
with st.spinner("🎬 박스오피스 데이터를 불러오는 중입니다..."):
    movies, error_message = get_boxoffice(target_dt)


# --------------------------------------------------
# 5. 오류 처리
# --------------------------------------------------

if error_message:

    if error_message == "그날은 아직 집계 전입니다":
        st.info("📅 그날은 아직 집계 전입니다.")
    else:
        st.error(error_message)

    st.stop()


# --------------------------------------------------
# 6. DataFrame 만들기
# --------------------------------------------------

df = pd.DataFrame(movies)


# 숫자로 변환할 열
number_columns = [
    "rank",
    "rankInten",
    "audiCnt",
    "audiAcc",
    "scrnCnt",
    "showCnt"
]

for column in number_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    ).fillna(0).astype(int)


# --------------------------------------------------
# 7. 영화명에 트로피 표시
# --------------------------------------------------

df["displayMovieNm"] = df.apply(
    lambda row: (
        f"{row['movieNm']} 🏆"
        if row["audiAcc"] > 1_000_000
        else row["movieNm"]
    ),
    axis=1
)


# --------------------------------------------------
# 8. 순위 증감 표시
# --------------------------------------------------

def make_rank_change(value):

    if value > 0:
        return f"🔴 ↑ {value}"

    elif value < 0:
        return f"🔵 ↓ {abs(value)}"

    else:
        return "－"


df["rankChange"] = df["rankInten"].apply(
    make_rank_change
)


# --------------------------------------------------
# 9. 100만 관객 필터
# --------------------------------------------------

if million_only:

    df = df[
        df["audiAcc"] > 1_000_000
    ].copy()

    if df.empty:
        st.info("🏆 누적관객 100만 명을 넘은 영화가 없습니다.")
        st.stop()


# --------------------------------------------------
# 10. 정렬
# --------------------------------------------------

if sort_option == "순위순":

    df = df.sort_values(
        "rank",
        ascending=True
    )

elif sort_option == "관객수순":

    df = df.sort_values(
        "audiCnt",
        ascending=False
    )

elif sort_option == "누적관객순":

    df = df.sort_values(
        "audiAcc",
        ascending=False
    )

elif sort_option == "스크린수순":

    df = df.sort_values(
        "scrnCnt",
        ascending=False
    )


# --------------------------------------------------
# 11. 조회 결과 요약
# --------------------------------------------------

st.subheader(
    f"📅 {selected_date.strftime('%Y년 %m월 %d일')}"
)

summary1, summary2, summary3 = st.columns(3)

with summary1:
    st.metric(
        "조회 영화 수",
        f"{len(df)}편"
    )

with summary2:
    st.metric(
        "해당일 전체 관객수",
        f"{df['audiCnt'].sum():,}명"
    )

with summary3:
    st.metric(
        "100만 관객 돌파 영화",
        f"{(df['audiAcc'] > 1_000_000).sum()}편"
    )


# --------------------------------------------------
# 12. 1위 영화 정보
# --------------------------------------------------

first_movie = df.iloc[0]

st.subheader(
    f"🥇 1위: {first_movie['displayMovieNm']}"
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "해당일 관객수",
        f"{first_movie['audiCnt']:,}명"
    )

with col2:
    st.metric(
        "누적 관객수",
        f"{first_movie['audiAcc']:,}명"
    )

with col3:
    st.metric(
        "스크린수",
        f"{first_movie['scrnCnt']:,}개"
    )


# --------------------------------------------------
# 13. 표시할 열 선택
# --------------------------------------------------

st.subheader("📋 박스오피스 표")

available_columns = [
    "순위",
    "전일 대비",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수"
]

selected_columns = st.multiselect(
    "표에 표시할 항목을 선택하세요.",
    available_columns,
    default=available_columns
)

# 아무 열도 선택하지 않은 경우
if not selected_columns:
    st.warning("표시할 항목을 하나 이상 선택해 주세요.")
else:

    # 원본 데이터에서 화면 표시용 DataFrame을 만듭니다.
    table_df = df[
        [
            "rank",
            "rankChange",
            "displayMovieNm",
            "openDt",
            "audiCnt",
            "audiAcc",
            "scrnCnt"
        ]
    ].copy()

    table_df.columns = available_columns

    # 사용자가 선택한 열만 표시합니다.
    table_df = table_df[selected_columns]

    # 숫자에 천 단위 쉼표를 표시합니다.
    format_dict = {}

    if "관객수" in selected_columns:
        format_dict["관객수"] = "{:,}"

    if "누적관객" in selected_columns:
        format_dict["누적관객"] = "{:,}"

    if "스크린수" in selected_columns:
        format_dict["스크린수"] = "{:,}"

    st.dataframe(
        table_df.style.format(format_dict),
        use_container_width=True,
        hide_index=True
    )


# --------------------------------------------------
# 14. 관객수 TOP 5 그래프
# --------------------------------------------------

st.subheader("📊 관객수 상위 5편")

top5 = (
    df.sort_values(
        "audiCnt",
        ascending=False
    )
    .head(5)
)

chart_df = top5.set_index(
    "displayMovieNm"
)[["audiCnt"]]

st.bar_chart(
    chart_df,
    x_label="영화명",
    y_label="관객수"
)


# --------------------------------------------------
# 15. CSV 다운로드
# --------------------------------------------------

st.subheader("💾 데이터 저장")

# 다운로드할 CSV는 원래 데이터 기준으로 만듭니다.
download_df = df[
    [
        "rank",
        "rankInten",
        "movieNm",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt"
    ]
].copy()

download_df.columns = [
    "순위",
    "전일대비순위증감",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수"
]

# CSV 파일로 변환합니다.
csv_data = download_df.to_csv(
    index=False,
    encoding="utf-8-sig"
)

st.download_button(
    label="📥 CSV로 다운로드",
    data=csv_data,
    file_name=f"boxoffice_{target_dt}.csv",
    mime="text/csv"
)
