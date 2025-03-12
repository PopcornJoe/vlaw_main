import streamlit as st
import streamlit_authenticator as stauth
import json
import pdfplumber
import re
from PIL import Image
from streamlit_option_menu import option_menu
import os
import zipfile
import io
from datetime import datetime

# Import your existing modules
import app
import try_2
import pdf_convert
import search_and_gen
import pdf_merge

def main():
    # 1. Read the JSON string from secrets
    creds_json = st.secrets["auth"]["credentials"]

    # 2. Convert that JSON string to a Python dictionary
    credentials = json.loads(creds_json)

    # 3. Initialize streamlit_authenticator with ephemeral cookie settings
    authenticator = stauth.Authenticate(
        credentials,
        "dummy_cookie_name",  # placeholder cookie name
        "dummy_key",          # placeholder secret key
        0                     # expiry_days=0 => ephemeral login (no persistence)
    )

    # 4. Render the login form (pass location as a keyword argument)
    name, authentication_status, username = authenticator.login("Login", location="main")

    # 5. Check login state
    if authentication_status:
        st.sidebar.write(f"Welcome, {username}")
        authenticator.logout("Logout", "sidebar")

        # Your main app content
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

    elif authentication_status is False:
        st.error("Username or password is incorrect.")
    elif authentication_status is None:
        st.warning("Please enter your username and password.")

if __name__ == "__main__":
    main()
