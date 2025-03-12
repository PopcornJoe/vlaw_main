import streamlit as st
import streamlit_authenticator as stauth
import pdfplumber
import re
from PIL import Image
from streamlit_option_menu import option_menu
import os
import zipfile
import io
from datetime import datetime
import app
import try_2
import pdf_convert
import search_and_gen
import pdf_merge

logo = Image.open('Van-Hulsteyns-Logo-Large.png')

def main():
    # 1) Load only the credentials (no cookie config)
    credentials = st.secrets["credentials"]

    # 2) Pass dummy cookie name/key, and set expiry_days=0 for no persistence
    authenticator = stauth.Authenticate(
        credentials,
        "dummy_cookie_name",  # placeholder
        "dummy_key",          # placeholder
        0                     # 0 days => ephemeral session
    )

    # 3) Display the login form
    name, authentication_status, username = authenticator.login("Login", "main")

    if authentication_status:
        # Show your main content only if logged in
        st.sidebar.image(logo)
        with st.sidebar:
            selected = option_menu(
                menu_title="",
                options=["Search and generate", "Statement upload", "Summons Upload"],
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

        # You can still offer a logout button if you like,
        # though ephemeral sessions typically end when the user closes the browser
        authenticator.logout("Logout", "sidebar")

    elif authentication_status is False:
        st.error("Username or password is incorrect.")
    elif authentication_status is None:
        st.warning("Please enter your username and password.")

if __name__ == "__main__":
    main()
