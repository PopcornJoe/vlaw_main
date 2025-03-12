import streamlit as st
import streamlit_authenticator as stauth
import copy
import json
from PIL import Image
from streamlit_option_menu import option_menu
from datetime import datetime

import app
import try_2
import pdf_convert
import search_and_gen
import pdf_merge

def to_plain_dict(obj):
    """Recursively convert a st.secrets AttrDict or list into a plain Python dict or list."""
    if isinstance(obj, dict):
        new_dict = {}
        for k, v in obj.items():
            new_dict[k] = to_plain_dict(v)
        return new_dict
    elif isinstance(obj, list):
        return [to_plain_dict(item) for item in obj]
    else:
        return obj

def main():
    # 1) Clone the 'credentials' section of st.secrets into a local dictionary
    #    This ensures no references back to st.secrets.
    raw_credentials = st.secrets.get("credentials", {})
    credentials = to_plain_dict(raw_credentials)

    # 2) Define ephemeral cookie config
    cookie_config = {
        "name": "dummy_cookie_name",
        "key": "dummy_key",
        "expiry_days": 0  # ephemeral
    }

    # 3) Initialize the authenticator with the local dictionary
    authenticator = stauth.Authenticate(
        credentials,
        cookie_config["name"],
        cookie_config["key"],
        cookie_config["expiry_days"]
    )

    # 4) Render the login form
    name, authentication_status, username = authenticator.login("Login", location="main")

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

    elif authentication_status is False:
        st.error("Username or password is incorrect.")
    else:
        # authentication_status is None
        st.warning("Please enter your username and password.")

if __name__ == "__main__":
    main()
