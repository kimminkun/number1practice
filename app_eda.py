import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        st.markdown("""
                ---
                **Bike Sharing Demand 데이터셋**  
                - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
                - 설명: 2011–2012년 캘리포니아 주의 수도인 미국 워싱턴 D.C. 인근 도시에서 시간별 자전거 대여량을 기록한 데이터  
                - 주요 변수:  
                  - `datetime`: 날짜 및 시간  
                  - `season`: 계절  
                  - `holiday`: 공휴일 여부  
                  - `workingday`: 근무일 여부  
                  - `weather`: 날씨 상태  
                  - `temp`, `atemp`: 기온 및 체감온도  
                  - `humidity`, `windspeed`: 습도 및 풍속  
                  - `casual`, `registered`, `count`: 비등록·등록·전체 대여 횟수  
                """)

# ---------------------
# 나머지 페이지 클래스 (Login, Register 등) 생략 (그대로 사용)
# ---------------------

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("\U0001F4CA Bike Sharing Demand EDA")

        uploaded = st.file_uploader("데이터셋 업로드 (train.csv)", type="csv")
        if not uploaded:
            st.info("train.csv 파일을 업로드 해주세요.")
            return

        # 먼저 일반적으로 읽고, datetime 열 여부 확인
        df_temp = pd.read_csv(uploaded)
        if 'datetime' in df_temp.columns:
            uploaded.seek(0)  # 포인터 초기화
            df = pd.read_csv(uploaded, parse_dates=['datetime'])
        else:
            df = df_temp
            st.warning("⚠️ 'datetime' 열이 없어 시간 기반 분석은 제한됩니다.")

        tabs = st.tabs([
            "9. Population Summary",
            "10. Yearly Trend",
            "11. Regional Change",
            "12. Top Changes",
            "13. Area Chart"
        ])

        st.subheader("\U0001F4C1 Upload Population Data")
        pop_file = st.file_uploader("Upload population_trends.csv", type="csv", key="pop")
        if pop_file:
            pop_df = pd.read_csv(pop_file)

            pop_df.loc[pop_df['지역'] == '세종'] = pop_df.loc[pop_df['지역'] == '세종'].replace("-", 0)
            pop_df.replace("-", 0, inplace=True)
            pop_df.fillna(0, inplace=True)

            for col in ['인구', '출생아수(명)', '사망자수(명)']:
                pop_df[col] = pd.to_numeric(pop_df[col], errors='coerce').fillna(0)

            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon', '광주': 'Gwangju',
                '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong', '경기': 'Gyeonggi', '강원': 'Gangwon',
                '충북': 'Chungbuk', '충남': 'Chungnam', '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk',
                '경남': 'Gyeongnam', '제주': 'Jeju'
            }
            pop_df['지역_영문'] = pop_df['지역'].map(region_map)

            with tabs[0]:
                st.header("\U0001F4CA Summary Statistics")
                buffer = io.StringIO()
                pop_df.info(buf=buffer)
                st.text(buffer.getvalue())
                st.dataframe(pop_df.describe())

            with tabs[1]:
                st.header("\U0001F4C8 Yearly Population Trend")
                total_df = pop_df[pop_df['지역'] == '전국']
                fig, ax = plt.subplots()
                sns.lineplot(data=total_df, x='연도', y='인구', marker='o', ax=ax)

                recent = total_df.sort_values('연도').tail(3)
                birth_sum = recent['출생아수(명)'].sum()
                death_sum = recent['사망자수(명)'].sum()
                forecast_2035 = total_df['인구'].iloc[-1] + (birth_sum - death_sum)

                ax.axvline(x=2035, color='gray', linestyle='--')
                ax.scatter(2035, forecast_2035, color='red', label='Forecast 2035')
                ax.annotate(f'{forecast_2035:,.0f}', xy=(2035, forecast_2035), xytext=(2035 + 0.5, forecast_2035),
                            va='center', color='red')

                ax.set_title("Population Trend")
                ax.set_xlabel("Year")
                ax.set_ylabel("Population")
                ax.legend()
                st.pyplot(fig)

                st.markdown(f"**\U0001F4CC Forecast 2035 Population: {forecast_2035:,.0f}**")

            with tabs[2]:
                st.header("\U0001F4C9 Regional Population Change (Last 5 Years)")
                recent5 = pop_df[pop_df['연도'] >= pop_df['연도'].max() - 5]
                delta = recent5[pop_df['지역'] != '전국'].groupby('지역_영문')['인구'].agg(['first', 'last'])
                delta['change'] = delta['last'] - delta['first']
                delta['ratio'] = (delta['change'] / delta['first']) * 100
                delta = delta.sort_values('change', ascending=False)

                fig, ax = plt.subplots(figsize=(10, 6))
                sns.barplot(data=delta.reset_index(), y='지역_영문', x='change', ax=ax)
                for i, v in enumerate(delta['change']):
                    ax.text(v, i, f"{int(v/1000)}K", va='center')
                ax.set_title("Population Change by Region")
                ax.set_xlabel("Change (people)")
                st.pyplot(fig)

                st.markdown("> The bar chart above shows regional population changes over the last 5 years."
                            " Areas with increasing population appear at the top.")

                fig2, ax2 = plt.subplots(figsize=(10, 6))
                delta_sorted = delta.sort_values('ratio', ascending=False)
                sns.barplot(data=delta_sorted.reset_index(), y='지역_영문', x='ratio', ax=ax2)
                for i, v in enumerate(delta_sorted['ratio']):
                    ax2.text(v, i, f"{v:.1f}%", va='center')
                ax2.set_title("Population Growth Rate by Region")
                ax2.set_xlabel("Change Rate (%)")
                st.pyplot(fig2)

            with tabs[3]:
                st.header("\U0001F4CA Top 100 Yearly Increases")
                diff_df = pop_df[pop_df['지역'] != '전국'].copy()
                diff_df['증감'] = diff_df.groupby('지역')['인구'].diff()
                top100 = diff_df.sort_values('증감', ascending=False).head(100)
                styled = top100.style.format({'증감': "{:,.0f}"}).background_gradient(subset='증감', cmap='RdBu_r')
                st.dataframe(styled)

            with tabs[4]:
                st.header("\U0001F4CA Population by Region Over Time")
                pivot_df = pop_df[pop_df['지역'] != '전국'].pivot(index='연도', columns='지역_영문', values='인구')
                pivot_df.fillna(0, inplace=True)

                fig, ax = plt.subplots(figsize=(12, 6))
                pivot_df.plot.area(ax=ax)
                ax.set_title("Population by Region")
                ax.set_xlabel("Year")
                ax.set_ylabel("Population")
                st.pyplot(fig)

        else:
            with tabs[0]:
                st.warning("\U0001F4C1 Please upload population_trends.csv to activate analysis tabs.")

# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()
