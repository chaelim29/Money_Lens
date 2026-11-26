import streamlit as st
import pandas as pd
import requests
st.markdown("""
    <style>
    /* 전체 배경 */
    .stApp {
        background-color: #FFFFFF;
        color: #222222;
    }

    /* 글자색 */
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    label {
        color: #222222 !important;
    }

    /* 사이드바 */
    [data-testid="stSidebar"] {
        background-color: #F7F8FA;
    }

    /* 입력창 */
    input, textarea {
        background-color: #FFFFFF !important;
        color: #222222 !important;
    }
    </style>
""", unsafe_allow_html=True)


# ==================================================
# 1. 페이지 설정
# ==================================================

st.set_page_config(
    page_title="MONEY LENS",
    page_icon="💰",
    layout="wide"
)


# ==================================================
# 2. 디자인
# ==================================================

st.markdown("""
<style>
.stApp {
    background-color: #FAFCFA;
}

.block-container {
    max-width: 1100px;
    padding-top: 2rem;
}

.main-title {
    color: #16865B;
    font-size: 38px;
    font-weight: 800;
}

.hero {
    background-color: #EDF7F0;
    padding: 35px;
    border-radius: 18px;
}

.hero-title {
    font-size: 36px;
    font-weight: 800;
    color: #174B35;
}

.hero-text {
    font-size: 16px;
    color: #5C7064;
}

div.stButton > button {
    border-radius: 10px;
    border: 1px solid #DCE9DF;
    min-height: 48px;
}

div.stButton > button[kind="primary"] {
    background-color: #16865B;
    color: white;
}
</style>
""", unsafe_allow_html=True)


# ==================================================
# 3. 페이지 이동 함수
# ==================================================

def navigate(name):
    st.session_state.menu = name


# ==================================================
# 4. 금융감독원 정기예금 API
# ==================================================

@st.cache_data(ttl=3600)
def get_deposit_products():

    api_key = st.secrets["FSS_API_KEY"]

    url = (
        "https://finlife.fss.or.kr/"
        "finlifeapi/depositProductsSearch.json"
    )

    base_list = []
    option_list = []

    page = 1

    # 페이지별 데이터 수집
    while True:

        params = {
            "auth": api_key,
            "topFinGrpNo": "020000",
            "pageNo": page
        }

        response = requests.get(
            url,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        result = response.json()["result"]

        if result.get("err_cd") != "000":
            raise Exception(
                result.get("err_msg", "API 조회 오류")
            )

        # 상품 기본정보 수집
        base_list.extend(
            result.get("baseList", [])
        )

        # 상품 금리정보 수집
        option_list.extend(
            result.get("optionList", [])
        )

        max_page = int(
            result.get("max_page_no", page)
        )

        if page >= max_page:
            break

        page += 1

    # 데이터프레임 변환
    base_df = pd.DataFrame(base_list)
    option_df = pd.DataFrame(option_list)

    if base_df.empty or option_df.empty:
        return pd.DataFrame()

    # 상품코드와 금융회사 코드를 기준으로 결합
    df = pd.merge(
        base_df,
        option_df,
        on=["fin_co_no", "fin_prdt_cd"],
        how="inner"
    )

    # 필요한 컬럼 선택
    columns = [
        "kor_co_nm",
        "fin_prdt_nm",
        "fin_prdt_cd",
        "save_trm",
        "intr_rate_type_nm",
        "intr_rate",
        "intr_rate2",
        "join_way",
        "spcl_cnd",
        "join_member",
        "max_limit"
    ]

    df = df[
        [col for col in columns if col in df.columns]
    ].copy()

    # 숫자형 데이터 변환
    df["save_trm"] = pd.to_numeric(
        df["save_trm"], errors="coerce"
    )

    df["intr_rate"] = pd.to_numeric(
        df["intr_rate"], errors="coerce"
    )

    df["intr_rate2"] = pd.to_numeric(
        df["intr_rate2"], errors="coerce"
    )

    return df


# ==================================================
# 5. 상단 메뉴
# ==================================================

menu_list = [
    "HOME",
    "청년 정책",
    "예·적금",
    "대출·금리",
    "경제 뉴스"
]

if "menu" not in st.session_state:
    st.session_state.menu = "HOME"

st.markdown(
    '<div class="main-title">💰 MONEY LENS</div>',
    unsafe_allow_html=True
)

menu = st.radio(
    "메뉴",
    menu_list,
    horizontal=True,
    label_visibility="collapsed",
    key="menu"
)

st.divider()


# ==================================================
# 6. HOME
# ==================================================

if menu == "HOME":

    st.markdown("""
    <div class="hero">
        <div class="hero-title">
            청년의 금융생활,<br>
            더 똑똑하게.
        </div>
        <p class="hero-text">
            복잡한 금융정보를 한곳에서 확인하고<br>
            나에게 맞는 정보를 찾아보세요.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    st.subheader("어떤 금융정보를 찾고 있나요?")

    categories = [
        ("🏛️", "청년 정책"),
        ("💰", "예·적금"),
        ("📊", "대출·금리"),
        ("📰", "경제 뉴스")
    ]

    cols = st.columns(4)

    for i, (icon, name) in enumerate(categories):

        with cols[i]:

            st.button(
                f"{icon}\n{name}",
                use_container_width=True,
                on_click=navigate,
                args=(name,)
            )

    st.write("")
    st.divider()

    st.subheader("🤖 AI 금융정보 검색")

    question = st.text_input(
        "궁금한 내용을 입력하세요.",
        placeholder="예: 사회초년생에게 적합한 적금이 있을까?"
    )

    if st.button(
        "금융정보 탐색하기",
        type="primary"
    ):

        if question.strip():

            st.session_state.question = question

            st.info(
                "AI 금융 상담 기능은 다음 단계에서 연결할 예정입니다."
            )

            st.write("입력한 질문:", question)

        else:
            st.warning("질문을 입력해 주세요.")


# ==================================================
# 7. 청년 정책 페이지
# ==================================================

elif menu == "청년 정책":

    st.title("🏛️ 청년 지원 정책")

    st.write(
        "청년을 위한 다양한 지원 정책과 혜택을 확인하세요."
    )

    st.divider()

    st.subheader("관심 주제")

    for example in [
        "청년도약계좌",
        "청년 월세 지원",
        "취업 지원 정책"
    ]:

        st.button(
            example,
            use_container_width=True
        )

    st.info("청년 정책 데이터는 다음 개발 단계에서 연결합니다.")


# ==================================================
# 8. 정기예금 페이지
# ==================================================

elif menu == "예·적금":

    st.title("💰 정기예금 비교")

    st.write(
        "금융감독원에 등록된 은행별 정기예금 상품을 비교합니다."
    )

    st.divider()

    st.subheader("🏦 정기예금 상품 조회")

    # 저축 기간 선택
    period = st.selectbox(
        "저축 기간을 선택하세요.",
        ["6개월", "12개월", "24개월", "36개월"]
    )

    months = int(
        period.replace("개월", "")
    )

    # API 조회 버튼
    if st.button(
        "정기예금 조회하기",
        type="primary"
    ):

        try:

            with st.spinner(
                "금융감독원에서 정기예금 데이터를 가져오고 있습니다..."
            ):

                df = get_deposit_products()

            st.session_state.deposit_data = df

        except Exception as e:

            st.error(
                f"데이터 조회에 실패했습니다: {e}"
            )

    # 조회한 데이터가 있을 경우
    if "deposit_data" in st.session_state:

        df = st.session_state.deposit_data.copy()

        if df.empty:

            st.warning("조회된 정기예금 상품이 없습니다.")

        else:

            # 선택한 저축 기간 필터링
            filtered = df[
                df["save_trm"] == months
            ].copy()

            # 최고우대금리 기준 내림차순 정렬
            filtered = filtered.sort_values(
                by="intr_rate2",
                ascending=False,
                na_position="last"
            ).reset_index(drop=True)

            st.divider()

            st.subheader(
                f"📊 {period} 정기예금 비교 결과"
            )

            st.write(
                f"조회된 금리 옵션: {len(filtered)}개"
            )

            if not filtered.empty:

                # ==========================================
                # 8-1. 은행별 검색 및 상품명 검색
                # ==========================================

        

                col1, col2 = st.columns(2)

                with col1:

                    bank_list = ["전체 은행"] + sorted(
                        filtered["kor_co_nm"].dropna().unique().tolist()
                    )

                    selected_bank = st.selectbox(
                        "은행 선택",
                        bank_list
                    )

                with col2:

                    search_name = st.text_input(
                        "상품명 검색",
                        placeholder="예: 정기예금"
                    )

                # 검색 조건 적용
                search_df = filtered.copy()

                # 은행 선택
                if selected_bank != "전체 은행":

                    search_df = search_df[
                        search_df["kor_co_nm"] == selected_bank
                    ]

                # 상품명 검색
                if search_name.strip():

                    search_df = search_df[
                        search_df["fin_prdt_nm"].str.contains(
                            search_name.strip(),
                            case=False,
                            na=False
                        )
                    ]

                # 금리순 정렬
                search_df = search_df.sort_values(
                    by="intr_rate2",
                    ascending=False,
                    na_position="last"
                ).reset_index(drop=True)

                st.caption(
                    f"검색 결과: {len(search_df)}개 상품"
                )

                # ==========================================
                # 8-2. 검색 결과 상품 비교
                # ==========================================

                if not search_df.empty:

                    display_df = search_df[
                        [
                            "kor_co_nm",
                            "fin_prdt_nm",
                            "intr_rate",
                            "intr_rate2",
                            "intr_rate_type_nm"
                        ]
                    ].copy()

                    display_df.columns = [
                        "은행명",
                        "상품명",
                        "기본금리(%)",
                        "최고우대금리(%)",
                        "이자계산방식"
                    ]

                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True
                    )

                    # ==========================================
                    # 8-3. 상품 상세정보
                    # ==========================================

                    st.divider()

                    st.subheader("🔎 상품 상세정보")

                    product_index = st.selectbox(
                        "상세정보를 확인할 상품을 선택하세요.",
                        options=list(range(len(search_df))),
                        format_func=lambda i: (
                            f"{search_df.iloc[i]['kor_co_nm']} | "
                            f"{search_df.iloc[i]['fin_prdt_nm']}"
                        ),
                        key="product_detail"
                    )

                    product = search_df.iloc[product_index]

                    st.markdown(
                        f"### {product['fin_prdt_nm']}"
                    )

                    st.write(
                        "**금융회사:**",
                        product["kor_co_nm"]
                    )

                    col1, col2 = st.columns(2)

                    col1.metric(
                        "기본금리",
                        f"{product['intr_rate']}%"
                        if pd.notna(product["intr_rate"])
                        else "-"
                    )

                    col2.metric(
                        "최고우대금리",
                        f"{product['intr_rate2']}%"
                        if pd.notna(product["intr_rate2"])
                        else "-"
                    )

                    st.divider()

                    st.write(
                        "**저축 기간:**",
                        f"{int(product['save_trm'])}개월"
                    )

                    st.write(
                        "**이자 계산 방식:**",
                        product["intr_rate_type_nm"]
                    )

                    st.write(
                        "**가입 방법:**",
                        product["join_way"]
                    )

                    st.write(
                        "**가입 대상:**",
                        product["join_member"]
                    )

                    st.write(
                        "**우대 조건:**",
                        product["spcl_cnd"]
                    )

                    st.write(
                        "**최고 가입 한도:**",
                        product["max_limit"]
                    )

                else:

                    st.warning(
                        "검색 조건에 맞는 정기예금 상품이 없습니다."
                    )

            else:

                st.warning(
                    "선택한 저축 기간의 정기예금 상품이 없습니다."
                )

            st.caption(
                "금리 및 상품 조건은 금융회사 공시 기준이며 "
                "실제 가입 전 해당 금융회사에서 확인해야 합니다."
            )


# ==================================================
# 9. 대출·금리 페이지
# ==================================================

elif menu == "대출·금리":

    st.title("📊 대출 및 금리")

    st.write(
        "다양한 대출 제도와 금리 정보를 확인하세요."
    )

    st.divider()

    st.subheader("관심 주제")

    for example in [
        "청년 전세대출",
        "정책 서민금융",
        "대출 금리 비교"
    ]:

        st.button(
            example,
            use_container_width=True
        )

    st.info("대출 데이터는 다음 개발 단계에서 연결합니다.")


# ==================================================
# 10. 경제 뉴스 페이지
# ==================================================

elif menu == "경제 뉴스":

    st.title("📰 경제 뉴스")

    st.write(
        "어려운 경제 이슈를 쉽게 이해해 보세요."
    )

    st.divider()

    st.subheader("관심 주제")

    for example in [
        "기준금리 동향",
        "물가 및 환율",
        "금융시장 주요 이슈"
    ]:

        st.button(
            example,
            use_container_width=True
        )

    st.info("경제 뉴스 데이터는 다음 개발 단계에서 연결합니다.")


# ==================================================
# 11. 하단
# ==================================================

st.divider()

st.caption(
    "MONEY LENS | 청년 맞춤형 금융정보 큐레이터"
)
