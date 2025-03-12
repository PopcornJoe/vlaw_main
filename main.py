import streamlit as st
import streamlit_authenticator as stauth
import json
from PIL import Image
from streamlit_option_menu import option_menu
from datetime import datetime

# Import your custom modules
import app
import try_2
import pdf_convert
import search_and_gen
import pdf_merge

def to_plain_dict(d):
    """Recursively convert a dict-like object into a plain Python dict."""
    if isinstance(d, dict):
        return {k: to_plain_dict(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [to_plain_dict(item) for item in d]
    else:
        return d

def main():
    # 1. Get credentials from st.secrets under the key "credentials"
    #    This expects your secrets file to have a [credentials] table.
    credentials = to_plain_dict(st.secrets["credentials"])
    
    # 2. Define a local cookie configuration for ephemeral login (no persistence)
    cookie_config = {
        "name": "dummy_cookie_name",  # placeholder; not used persistently
        "key": "dummy_key",           # placeholder secret key
        "expiry_days": 0              # 0 days means the session cookie expires immediately
    }
    
    # 3. Initialize streamlit_authenticator with the plain credentials and local cookie config
    authenticator = stauth.Authenticate(
        credentials,
        cookie_config["name"],
        cookie_config["key"],
        cookie_config["expiry_days"]
    )
    
    # 4. Render the login form; specify location as a keyword argument
    name, authentication_status, username = authenticator.login("Login", location="main")
    
    # 5. Check login state and show main app if logged in
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
        st.warning("Please enter your username and password.")

if __name__ == "__main__":
    main()
