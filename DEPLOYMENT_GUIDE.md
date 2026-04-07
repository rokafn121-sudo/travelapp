# 🚀 가족과 함께 사용하는 방법 (쉬운 순서대로)

성공적으로 배포하신 것을 축하드립니다! 🎉
Streamlit Cloud를 이용한 배포 방법을 다시 정리해놓았습니다. (나중에 참고하세요!)

---

## 방법: 인터넷에 배포하기 (Streamlit Cloud)

### 1. 준비물
- GitHub 아이디, Streamlit 아이디

### 2. 코드 올리기 (중요!)
1.  [GitHub](https://github.com/)에 로그인 -> **New repository** -> 이름 `travel-tracker`
2.  **공개 설정(Public/Private) 주의**: 
    - **Public (공개)**: 누구나 볼 수 있음 (무료 계정 배포 쉬움)
    - **Private (비공개)**: 나만 볼 수 있음 (Streamlit Cloud 연결 시 권한 설정 필요)
    - **팁**: 처음에 배포가 잘 안되면 일단 **Public**으로 시도해보세요.
3.  **Create repository** 클릭.
4.  **uploading an existing file** 클릭.
5.  내 폴더(`travel_budget_tracker`)에서 다음 파일만 드래그:
    - `app.py`, `utils.py`, `requirements.txt`, `profile.png`, `data/` 폴더
6.  **Commit changes** 클릭.

### 3. 배포하기
1.  [Streamlit Cloud](https://share.streamlit.io/) 로그인.
2.  **Create app** -> **Deploy a public app from GitHub**.
3.  **GitHub URL**: `app.py` 파일의 전체 주소 복사해서 붙여넣기.
    - 예: `https://github.com/내아이디/travel-tracker/blob/main/app.py`
4.  **Deploy!** 클릭.


