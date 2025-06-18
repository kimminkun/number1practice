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

        # Kaggle 데이터셋 출처 및 소개
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
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

region_map = {
    '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
    '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
    '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
    '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
    '제주': 'Jeju'
}---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA")
        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded:
            st.info("Please upload population_trends.csv to proceed.")
            return

        # Read and preprocess
        df = pd.read_csv(uploaded)
        # Replace '-' with 0 for Sejong region
        sejong_mask = df['지역'] == '세종'
        df.loc[sejong_mask] = df.loc[sejong_mask].replace('-', 0)
        # Convert relevant columns to numeric
        numeric_cols = ['인구', '출생아수(명)', '사망자수(명)']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric)

        # Create tabs
        tabs = st.tabs([
            "결측치 및 중복 확인",
            "기초 통계",
            "연도별 추이",
            "지역별 변화량",
            "증감률 상위",
            "누적영역그래프"
        ])

        # Tab 1: Missing & Duplicates
        with tabs[0]:
            st.subheader("결측치 및 중복 확인")
            st.write("**Missing values per column**")
            st.write(df.isnull().sum())
            st.write("**Duplicate rows count**: {}".format(df.duplicated().sum()))

        # Tab 2: Basic Statistics
        with tabs[1]:
            st.subheader("기초 통계")
            buf = io.StringIO()
            df.info(buf=buf)
            st.text(buf.getvalue())
            st.write(df.describe())

        # Tab 3: Yearly Total Population Trend
        with tabs[2]:
            st.subheader("Total Population Trend by Year")
            df_nation = df[df['지역'] == '전국'].sort_values('연도')
            fig, ax = plt.subplots()
            sns.lineplot(data=df_nation, x='연도', y='인구', marker='o', ax=ax)
            ax.set_title("Total Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            # Project 2035 population based on last 3 years net change
            last3 = df_nation.tail(3)
            last_year = last3['연도'].iloc[-1]
            latest_pop = last3['인구'].iloc[-1]
            avg_net = (last3['출생아수(명)'] - last3['사망자수(명)']).mean()
            proj_year = 2035
            proj_pop = latest_pop + avg_net * (proj_year - last_year)
            ax.scatter(proj_year, proj_pop)
            ax.annotate(f"2035 Projection: {int(proj_pop):,}", (proj_year, proj_pop))
            st.pyplot(fig)

        # Tab 4: Regional Population Change Ranking
        with tabs[3]:
            st.subheader("Population Change by Region (Last 5 Years)")
            years = sorted(df['연도'].unique())
            last5 = years[-5:]
            pivot = df.pivot(index='지역', columns='연도', values='인구')
            change = (pivot[last5[-1]] - pivot[last5[0]]).drop('전국')
            change.index = change.index.map(region_map)
            change = change.sort_values(ascending=False)
            fig, ax = plt.subplots()
            sns.barplot(x=change.values / 1000, y=change.index, ax=ax)
            ax.set_title("Population Change by Region (Last 5 Years)")
            ax.set_xlabel("Change (Thousands)")
            ax.set_ylabel("Region")
            for p in ax.patches:
                width = p.get_width()
                ax.text(width + 0.1, p.get_y() + p.get_height() / 2, f"{width:.1f}", va='center')
            st.pyplot(fig)
            # Percentage change
            pct = ((pivot[last5[-1]] - pivot[last5[0]]) / pivot[last5[0]] * 100).drop('전국')
            pct.index = pct.index.map(region_map)
            pct = pct.sort_values(ascending=False)
            fig2, ax2 = plt.subplots()
            sns.barplot(x=pct.values, y=pct.index, ax=ax2)
            ax2.set_title("Percentage Change by Region (Last 5 Years)")
            ax2.set_xlabel("Change (%)")
            ax2.set_ylabel("Region")
            for p in ax2.patches:
                width = p.get_width()
                ax2.text(width + 0.5, p.get_y() + p.get_height() / 2, f"{width:.1f}%", va='center')
            st.pyplot(fig2)
            st.write("This shows the absolute and relative population changes over the last 5 years for each region.")

        # Tab 5: Top Diff Cases
        with tabs[4]:
            st.subheader("Top 100 Population Changes by Year and Region")
            df_sorted = df[df['지역'] != '전국'].sort_values(['지역', '연도'])
            df_sorted['diff'] = df_sorted.groupby('지역')['인구'].diff()
            top100 = df_sorted.sort_values('diff', ascending=False).head(100)
            styled = (top100[['지역', '연도', 'diff']]
                      .style.format({'diff': '{:,.0f}'})
                      .applymap(lambda v: 'background-color: lightblue' if v > 0 else 'background-color: lightcoral', subset=['diff']))
            st.write(styled)

        # Tab 6: Cumulative Area Chart
        with tabs[5]:
            st.subheader("Cumulative Area Chart of Population by Region")
            pivot2 = df.pivot(index='연도', columns='지역', values='인구').drop('전국', axis=1)
            pivot2.rename(columns=region_map, inplace=True)
            fig, ax = plt.subplots()
            pivot2.plot.area(ax=ax, colormap='tab20')
            ax.set_title("Population by Region Over Time")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            st.pyplot(fig)



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