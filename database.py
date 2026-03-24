import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

def get_db():
    if not firebase_admin._apps:
        try:
            if "firebase" in st.secrets:
                # Firestore credentials from Streamlit Secrets
                cert = dict(st.secrets["firebase"])
                cred = credentials.Certificate(cert)
                firebase_admin.initialize_app(cred)
            else:
                st.warning("Firebase 설정이 st.secrets에 없습니다. 로컬 테스트 중이라면 .streamlit/secrets.toml 을 확인해주세요.")
                return None
        except Exception as e:
            st.error(f"Firebase 연결 실패: {e}")
            return None
            
    if firebase_admin._apps:
        return firestore.client()
    return None
