import streamlit as st
import streamlit_authenticator as stauth
from PIL import Image
from streamlit_option_menu import option_menu
import app
import try_2
import pdf_convert
import search_and_gen
import pdf_merge

def main():
    # 1. Hardcode your credentials in a normal Python dict
    # NOTE: This is not recommended for real secrets in a public repo.
    #       It's just the most straightforward way to bypass st.secrets issues.
    credentials = {
        "usernames": {
            "BarbaraS@vhlaw.co.za": {
                "email": "BarbaraS@vhlaw.co.za",
                "name": "BarbaraS@vhlaw.co.za",
                "password": "$2b$12$p1IcU.icMEClnjgypAEB5unUmYDlr0TvslRtRKfKnFsWal/uO8itq"
            }
        }
    }

    # 2. Define ephemeral cookie config
    cookie_name = "dummy_cookie_name"
    cookie_key = "dummy_key"
    expiry_days = 0  # ephemeral: no persistent login

    # 3. Initialize streamlit_authenticator
    authenticator = stauth.Authenticate(credentials, cookie_name, cookie_key, expiry_days)

    # 4. Show login form
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
        st.warning("Please enter your username and password.")

if __name__ == "__main__":
    main()
