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
import app
import try_2
import pdf_convert
import search_and_gen
import pdf_merge

# Convert st.secrets["credentials"] into a mutable dictionary.
credentials = json.loads(json.dumps(st.secrets["credentials"]))

# Define a local cookie configuration for ephemeral login (no persistence)
cookie_config = {
    "name": "dummy_cookie_name",  # placeholder
    "key": "dummy_key",           # placeholder
    "expiry_days": 0              # 0 means no persistent cookie
}

# Initialize the authenticator using the mutable credentials and local cookie_config
authenticator = stauth.Authenticate(
    credentials,
    cookie_config["name"],
    cookie_config["key"],
    cookie_config["expiry_days"]
)

# Render the login widget
name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    st.sidebar.write(f"Welcome, {username}")
    authenticator.logout("Logout", "sidebar")
    
    logo = Image.open('Van-Hulsteyns-Logo-Large.png')
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

elif authentication_status is False:
    st.error("Username or password is incorrect.")
elif authentication_status is None:
    st.warning("Please enter your username and password.")
