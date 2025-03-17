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
    # 1. Build a dictionary for streamlit_authenticator from secrets
    # st.secrets["credentials"] will look like:
    # {
    #   "usernames": {
    #       "BarbaraS@vhlaw.co.za": {
    #           "email": "...",
    #           "name": "...",
    #           "password": "..."
    #       },
    #       ...
    #   }
    # }
    credentials_dict = {
        "usernames": dict(st.secrets["credentials"]["usernames"])
    }

    # 2. Cookie/session settings
    cookie_name = "dummy_cookie_name"
    cookie_key = "dummy_key"
    expiry_days = 0

    # 3. Create the authenticator object
    authenticator = stauth.Authenticate(
        credentials=credentials_dict,
        cookie_name=cookie_name,
        key=cookie_key,
        expiry_days=expiry_days
    )

    # 4. Show the login form (old API style, valid if pinned to v0.2.3)
    login_result = authenticator.login("Login", "main")

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
