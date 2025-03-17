# auth_config.py

import streamlit_authenticator as stauth

def get_authenticator():
    """
    Returns a Streamlit Authenticator object configured with
    your credentials, cookie, and session settings.

    Note: This is written for streamlit-authenticator==0.2.3
    where the constructor signature is:
    Authenticate(credentials, cookie_name, cookie_key, cookie_expiry_days)
    """
    credentials = {
        "usernames": {
            "BarbaraS@vhlaw.co.za": {
                "email": "BarbaraS@vhlaw.co.za",
                "name": "BarbaraS@vhlaw.co.za",
                "password": "$2b$12$p1IcU.icMEClnjgypAEB5unUmYDlr0TvslRtRKfKnFsWal/uO8itq"
            }
        }
    }

    cookie_name = "dummy_cookie_name"
    cookie_key = "dummy_key"
    cookie_expiry_days = 0  # Must be the 4th positional argument in v0.2.3

    authenticator = stauth.Authenticate(
        credentials,
        cookie_name,
        cookie_key,
        cookie_expiry_days
    )
    return authenticator
