import streamlit as st
import requests
import pandas as pd
from datetime import timedelta
import re

# --------------------------------------------------
# 기본 설정
# --------------------------------------------------

st.set_page_config(
    page_title="학교별 시험기간 급식 칼로리 비교",
    page_icon="🍚",
    layout="wide"
)

st.title("🍚 시험기간 전후 급식 칼로리 비교")
st.write("""
동산고등학교, 가좌고등학교, 인화여자고등학교의 중식 급식 데이터를 이용하여  
**시험이 시작되는 주와 시험 전 주의 급식 칼로리 차이**를 비교합니다.
""")


# --------------------------------------------------
# API 키
# --------------------------------------------------

try:
    API_KEY = st.secrets["NEIS_KEY"]
except:
    API_KEY = ""


# --------------------------------------------------
# 학교 목록
# --------------------------------------------------

SCHOOLS = [
    "동산고등학교",
    "가좌고등학교",
    "인화여자고등학교"
]


# --------------------------------------------------
# 학교 정보 찾기
# --------------------------------------------------

@st.cache_data
def get_school_info(school_name):

    url = "https://open.neis.go.kr/hub/schoolInfo"

    params = {
        "KEY": API_KEY,
        "Type": "json",
        "SCHUL_NM": school_name,
        "pSize": 100
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "schoolInfo" not in data:
        return None

    rows = data["schoolInfo"][1]["row"]

    # 정확히 이름이 같은 학교 찾기
    for school in rows:

        if school["SCHUL_NM"] == school_name:

            return {
                "학교명": school["SCHUL_NM"],
                "교육청코드": school["ATPT_OFCDC_SC_CODE"],
                "학교코드": school["SD_SCHUL_CODE"],
                "지역": school["LCTN_SC_NM"]
            }

    return None


# --------------------------------------------------
# 칼로리 숫자로 변환
# --------------------------------------------------

def convert_calorie(cal_info):

    if cal_info is None:
        return None

    # 예시:
    # "850.3 Kcal"
    # "850.3"
    # 등의 형태에서 숫자만 추출

    numbers = re.findall(r"[\d.]+", str(cal_info))

    if len(numbers) > 0:
        return float(numbers[0])

    return None


# --------------------------------------------------
# 급식 데이터 가져오기
# --------------------------------------------------

@st.cache_data
def get_meal_data(atpt_code, school_code, start_date, end_date):

    url = "https://open.neis.go.kr/hub/mealServiceDietInfo"

    params = {
        "KEY": API_KEY,
        "Type": "json",
        "ATPT_OFCDC_SC_CODE": atpt_code,
        "SD_SCHUL_CODE": school_code,
        "MMEAL_SC_CODE": "2",  # 중식
        "MLSV_FROM_YMD": start_date.strftime("%Y%m%d"),
        "MLSV_TO_YMD": end_date.strftime("%Y%m%d"),
        "pSize": 1000,
        "pIndex": 1
    }

    response = requests.get(url, params=params)
    data = response.json()

    # 데이터가 없는 경우
    if "mealServiceDietInfo" not in data:
        return pd.DataFrame()

    rows = data["mealServiceDietInfo"][1]["row"]

    result = []

    for row in rows:

        calorie = convert_calorie(row.get("CAL_INFO"))

        result.append({
            "날짜": pd.to_datetime(row["MLSV_YMD"]),
            "칼로리": calorie,
            "메뉴": row.get("DDISH_NM", "")
        })

    df = pd.DataFrame(result)

    return df


# --------------------------------------------------
# 시험 시작일이 포함된 주 계산
# --------------------------------------------------

def get_week_dates(exam_start_date):

    # 월요일 찾기
    monday = exam_start_date - timedelta(
        days=exam_start_date.weekday()
    )

    # 일요일
    sunday = monday + timedelta(days=6)

    return monday, sunday


# --------------------------------------------------
# 사이드바
# --------------------------------------------------

st.sidebar.header("📅 시험 시작일 설정")

st.sidebar.write("""
각 학교의 시험 시작일을 입력하세요.

프로그램은 자동으로:

- 시험 시작일이 포함된 월요일~일요일
- 그 전 주의 월요일~일요일

을 비교합니다.
""")


exam_dates = {}

for school in SCHOOLS:

    exam_dates[school] = st.sidebar.date_input(
        f"{school} 시험 시작일",
        key=school
    )


# --------------------------------------------------
# 분석 시작 버튼
# --------------------------------------------------

if st.button("🔍 세 학교 급식 칼로리 비교", use_container_width=True):

    if not API_KEY:

        st.error("""
        NEIS API 키가 설정되지 않았습니다.

        Streamlit Secrets에 다음과 같이 설정하세요.

        NEIS_KEY = "여기에_API_키"
        """)

        st.stop()


    all_results = []
    all_daily_data = []


    # --------------------------------------------------
    # 학교별 분석
    # --------------------------------------------------

    for school_name in SCHOOLS:

        st.subheader(f"🏫 {school_name}")

        # ----------------------------
        # 학교 정보 가져오기
        # ----------------------------

        school_info = get_school_info(school_name)

        if school_info is None:

            st.error(
                f"{school_name}의 학교 정보를 찾지 못했습니다."
            )

            continue


        st.write(
            f"📍 지역: {school_info['지역']}"
        )


        # ----------------------------
        # 시험 주 계산
        # ----------------------------

        exam_date = exam_dates[school_name]

        exam_week_start, exam_week_end = get_week_dates(
            exam_date
        )

        previous_week_start = (
            exam_week_start - timedelta(days=7)
        )

        previous_week_end = (
            exam_week_start - timedelta(days=1)
        )


        st.info(f"""
        **시험 시작일:** {exam_date}

        **시험 주:**  
        {exam_week_start} ~ {exam_week_end}

        **시험 전 주:**  
        {previous_week_start} ~ {previous_week_end}
        """)


        # ----------------------------
        # 시험 주 급식 데이터
        # ----------------------------

        exam_df = get_meal_data(

            school_info["교육청코드"],
            school_info["학교코드"],

            exam_week_start,
            exam_week_end
        )


        # ----------------------------
        # 시험 전 주 급식 데이터
        # ----------------------------

        previous_df = get_meal_data(

            school_info["교육청코드"],
            school_info["학교코드"],

            previous_week_start,
            previous_week_end
        )


        # ----------------------------
        # 데이터가 없는 경우
        # ----------------------------

        if exam_df.empty:

            st.warning(
                "시험 주의 급식 데이터가 없습니다."
            )


        if previous_df.empty:

            st.warning(
                "시험 전 주의 급식 데이터가 없습니다."
            )


        # ----------------------------
        # 총 칼로리
        # ----------------------------

        exam_total = (
            exam_df["칼로리"].sum()
            if not exam_df.empty
            else 0
        )


        previous_total = (
            previous_df["칼로리"].sum()
            if not previous_df.empty
            else 0
        )


        # ----------------------------
        # 하루 평균 칼로리
        # ----------------------------

        exam_average = (
            exam_df["칼로리"].mean()
            if not exam_df.empty
            else 0
        )


        previous_average = (
            previous_df["칼로리"].mean()
            if not previous_df.empty
            else 0
        )


        # ----------------------------
        # 칼로리 차이
        # ----------------------------

        total_difference = (
            exam_total - previous_total
        )

        average_difference = (
            exam_average - previous_average
        )


        # ----------------------------
        # 결과 표시
        # ----------------------------

        col1, col2, col3 = st.columns(3)


        with col1:

            st.metric(
                "시험 주 총칼로리",
                f"{exam_total:,.1f} kcal"
            )


        with col2:

            st.metric(
                "시험 전 주 총칼로리",
                f"{previous_total:,.1f} kcal"
            )


        with col3:

            st.metric(
                "총칼로리 차이",
                f"{total_difference:+,.1f} kcal"
            )


        col4, col5, col6 = st.columns(3)


        with col4:

            st.metric(
                "시험 주 하루 평균",
                f"{exam_average:,.1f} kcal"
            )


        with col5:

            st.metric(
                "시험 전 주 하루 평균",
                f"{previous_average:,.1f} kcal"
            )


        with col6:

            st.metric(
                "하루 평균 차이",
                f"{average_difference:+,.1f} kcal"
            )


        # ----------------------------
        # 결과 저장
        # ----------------------------

        all_results.append({

            "학교": school_name,

            "시험 시작일": exam_date,

            "시험 주 총칼로리": exam_total,

            "시험 전 주 총칼로리": previous_total,

            "총칼로리 차이":
                total_difference,

            "시험 주 하루 평균":
                exam_average,

            "시험 전 주 하루 평균":
                previous_average,

            "하루 평균 차이":
                average_difference
        })


        # ----------------------------
        # 일별 데이터 저장
        # ----------------------------

        if not exam_df.empty:

            temp_exam = exam_df.copy()

            temp_exam["학교"] = school_name

            temp_exam["기간"] = "시험 주"

            all_daily_data.append(temp_exam)


        if not previous_df.empty:

            temp_previous = previous_df.copy()

            temp_previous["학교"] = school_name

            temp_previous["기간"] = "시험 전 주"

            all_daily_data.append(temp_previous)


    # --------------------------------------------------
    # 세 학교 종합 비교
    # --------------------------------------------------

    if len(all_results) > 0:

        st.divider()

        st.header("📊 세 학교 종합 비교")


        result_df = pd.DataFrame(all_results)


        # ----------------------------
        # 결과 표
        # ----------------------------

        st.subheader("📋 학교별 칼로리 비교")

        st.dataframe(

            result_df,

            use_container_width=True,

            hide_index=True
        )


        # ----------------------------
        # 총칼로리 비교 그래프
        # ----------------------------

        st.subheader(
            "🍚 시험 주와 시험 전 주 총칼로리 비교"
        )


        chart_df = result_df.set_index("학교")[

            [
                "시험 주 총칼로리",
                "시험 전 주 총칼로리"
            ]

        ]


        st.bar_chart(chart_df)


        # ----------------------------
        # 하루 평균 비교
        # ----------------------------

        st.subheader(
            "📈 하루 평균 칼로리 비교"
        )


        average_chart = result_df.set_index("학교")[

            [
                "시험 주 하루 평균",
                "시험 전 주 하루 평균"
            ]

        ]


        st.bar_chart(average_chart)


        # ----------------------------
        # 칼로리 차이 그래프
        # ----------------------------

        st.subheader(
            "📊 시험 주와 시험 전 주의 칼로리 차이"
        )


        difference_chart = result_df.set_index("학교")[

            "하루 평균 차이"

        ]


        st.bar_chart(difference_chart)


        # --------------------------------------------------
        # 일별 데이터
        # --------------------------------------------------

        if len(all_daily_data) > 0:

            st.divider()

            st.header("📅 일별 급식 칼로리 데이터")


            daily_df = pd.concat(
                all_daily_data,
                ignore_index=True
            )


            daily_df = daily_df[

                [
                    "학교",
                    "기간",
                    "날짜",
                    "칼로리",
                    "메뉴"
                ]

            ]


            st.dataframe(

                daily_df,

                use_container_width=True,

                hide_index=True

            )


        # --------------------------------------------------
        # 결론 자동 생성
        # --------------------------------------------------

        st.divider()

        st.header("📝 분석 결과")


        for _, row in result_df.iterrows():

            school = row["학교"]

            difference = row["하루 평균 차이"]


            if difference > 0:

                st.write(
                    f"🔺 **{school}**은(는) "
                    f"시험 주의 하루 평균 칼로리가 "
                    f"시험 전 주보다 "
                    f"**{difference:,.1f} kcal 높았습니다.**"
                )


            elif difference < 0:

                st.write(
                    f"🔻 **{school}**은(는) "
                    f"시험 주의 하루 평균 칼로리가 "
                    f"시험 전 주보다 "
                    f"**{abs(difference):,.1f} kcal 낮았습니다.**"
                )


            else:

                st.write(
                    f"➖ **{school}**은(는) "
                    f"시험 주와 시험 전 주의 "
                    f"하루 평균 칼로리가 같습니다."
                )
