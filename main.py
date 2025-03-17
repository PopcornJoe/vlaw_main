# main.py

import streamlit as st
import streamlit_authenticator as stauth
from PIL import Image
from streamlit_option_menu import option_menu

# Import the helper function from auth_config.py
from auth_config import get_authenticator

import app
import try_2
import pdf_convert
import search_and_gen
import pdf_merge

def main():
    # 1. Create the authenticator using our separate file
    authenticator = get_authenticator()

    # 2. Use the old API call for 0.2.3
    login_result = authenticator.login("Login", "main")

    # 3. If the user hasn't submitted credentials yet, login_result is None
    if login_result is None:
        st.warning("Please enter your username and password.")
        st.stop()

    name, authentication_status, username = login_result

    if authentication_status is False:
        st.error("Username or password is incorrect.")
        st.stop()

    if authentication_status:
        st.sidebar.write(f"Welcome, {username}")
        authenticator.logout("Logout", "sidebar")

        logo = Image.open('Van-Hulsteyns-Logo-Large.png')
        st.sidebar.image(logo)

        with st.sidebar:
            selected = option_menu(
                menu_title="",
                options=["Search and generate", "Statement upload", "Summons Upload", "PDF convert", "Merge PDF"],
                default_index=0,
            )

        if selected == "Statement upload":
            app.legal_document_processor()
        elif selected == "Summons Upload":
            try_2.summons_upload()
        elif selected == "PDF convert":
            pdf_convert.pdf_convert()
        elif selected == "Search and generate":
            search_and_gen.app()
        elif selected == "Merge PDF":
            pdf_merge.merge_pdfs()

if __name__ == "__main__":
    main()
