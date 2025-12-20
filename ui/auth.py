from __future__ import annotations
import streamlit as st


def is_logged_in() -> bool:
    return bool(st.session_state.get("auth_user_mail"))

def require_login() -> None:
    
    #simple UI gate. If not logged in, show login form and stop rendering the page.

    if is_logged_in():
        return

    st.title("🔐 Login")
    st.caption("Please login to access the Smart Energy Dashboard.")

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="user@example.com")
        password = st.text_input("Password", type="password", placeholder="********")
        submitted = st.form_submit_button("Log in")

    if submitted:
        #temporarty placeholder: accept any non-empty input, replace later with FASTAPI authentication

        if email.strip() and password.strip():
            st.session_state.auth_user_mail = email.strip()
            st.success("Logged in (temporary).")
            st.rerun()

        else:
            st.error("Please enter email and password.")

    st.stop()

def logout_button() -> None:
        #placing in the sidebar to allow logout

        if is_logged_in():
            st.sidebar.write(f"Signed in as **{st.session_state.auth_user_mail}**")
            if st.sidebar.button("Log out"):
                st.session_state.pop("auth_user_email", None)
                st.rerun()