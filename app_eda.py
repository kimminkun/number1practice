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
# 페이지 클래스 정의
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
        - 설명: 2011–2012년 워싱턴 D.C.에서 시간별 자전거 대여량을 기록한 데이터  
        - 주요 변수:  
            - `datetime`, `season`, `holiday`, `workingday`, `weather`  
            - `temp`, `atemp`, `humidity`, `windspeed`  
            - `casual`, `registered`, `count`
        """)

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

class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")
        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별", ["선택 안함", "남성", "여성"],
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

# ---------------------
# EDA 페이지 클래스 (당신이 수정한 버전)
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Bike Sharing Demand EDA")

        uploaded = st.file_uploader("데이터셋 업로드 (train.csv)", type="csv")
        if not uploaded:
            st.info("train.csv 파일을 업로드 해주세요.")
            return

        df_temp = pd.read_csv(uploaded)
        if 'datetime' in df_temp.columns:   #커밋용
            uploaded.seek(0)
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

        st.subheader("📂 Upload Population Data")
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
                '충북': 'Chungbuk', '충남': 'Chungnam', '전북': 'Jeonbuk', '전남': 'Jeonnam',
                '경북': 'Gyeongbuk', '경남': 'Gyeongnam', '제주': 'Jeju'
            }
            pop_df['지역_영문'] = pop_df['지역'].map(region_map)

            # 각 탭에 시각화 코드 동일하게 삽입
            with tabs[0]:
                st.header("📊 Summary Statistics")
                buffer = io.StringIO()
                pop_df.info(buf=buffer)
                st.text(buffer.getvalue())
                st.dataframe(pop_df.describe())

            with tabs[1]:
        st.header("📈 Yearly Population Trend")
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
        st.markdown(f"**📍 Forecast 2035 Population: {forecast_2035:,.0f}**")

    # 3. 지역별 인구 변화량 (최근 5년)
    with tabs[2]:
        st.header("📉 Population Change by Region (Last 5 Years)")
        recent5 = pop_df[pop_df['연도'] >= pop_df['연도'].max() - 5]
        delta = recent5[pop_df['지역'] != '전국'].groupby('지역_영문')['인구'].agg(['first', 'last'])
        delta['change'] = delta['last'] - delta['first']
        delta['ratio'] = (delta['change'] / delta['first']) * 100
        delta = delta.sort_values('change', ascending=False)

        # 변화량
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        sns.barplot(data=delta.reset_index(), y='지역_영문', x='change', ax=ax1)
        for i, v in enumerate(delta['change']):
            ax1.text(v, i, f"{int(v/1000)}K", va='center')
        ax1.set_title("Population Change")
        ax1.set_xlabel("Change (people)")
        st.pyplot(fig1)

        # 변화율
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        delta_sorted = delta.sort_values('ratio', ascending=False)
        sns.barplot(data=delta_sorted.reset_index(), y='지역_영문', x='ratio', ax=ax2)
        for i, v in enumerate(delta_sorted['ratio']):
            ax2.text(v, i, f"{v:.1f}%", va='center')
        ax2.set_title("Population Change Rate")
        ax2.set_xlabel("Change Rate (%)")
        st.pyplot(fig2)

        st.markdown("> 상위에 위치한 지역은 인구가 많이 증가한 지역입니다. 변화율과 절대 변화량을 함께 고려하세요.")

    # 4. 증감률 상위 100건
    with tabs[3]:
        st.header("📋 Top 100 Yearly Population Changes")
        diff_df = pop_df[pop_df['지역'] != '전국'].copy()
        diff_df['증감'] = diff_df.groupby('지역')['인구'].diff()
        top100 = diff_df.sort_values('증감', ascending=False).head(100)
        styled = top100.style.format({'증감': "{:,.0f}"}).background_gradient(subset='증감', cmap='RdBu_r')
        st.dataframe(styled)

    # 5. 누적 영역 그래프
    with tabs[4]:
        st.header("📊 Regional Population Over Time")
        pivot_df = pop_df[pop_df['지역'] != '전국'].pivot(index='연도', columns='지역_영문', values='인구')
        pivot_df.fillna(0, inplace=True)
        fig3, ax3 = plt.subplots(figsize=(12, 6))
        pivot_df.plot.area(ax=ax3)
        ax3.set_title("Population by Region")
        ax3.set_xlabel("Year")
        ax3.set_ylabel("Population")
        st.pyplot(fig3)

else:
    st.warning("⚠️ Please upload `population_trends.csv` to begin analysis.")

        else:
            with tabs[0]:
                st.warning("📂 Please upload population_trends.csv to activate analysis tabs.")

# ---------------------
# 페이지 객체 및 네비게이션
# ---------------------
# 커스텀 Page 시스템 없이 radio로 처리
st.sidebar.title("📌 Navigation")
pages = {
    "Home": lambda: Home(Login, Register, FindPassword),
    "Login": Login,
    "Register": lambda: Register("Login"),
    "Find Password": FindPassword,
    "My Info": UserInfo,
    "EDA": EDA,
    "Logout": Logout
}

if st.session_state.logged_in:
    options = ["Home", "My Info", "EDA", "Logout"]
else:
    options = ["Home", "Login", "Register", "Find Password"]

choice = st.sidebar.radio("이동할 페이지를 선택하세요:", options)
pages[choice]()
