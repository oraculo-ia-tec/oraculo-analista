from google_auth_oauthlib.flow import InstalledAppFlow

scopes = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify"
]

flow = InstalledAppFlow.from_client_config(
    {
        "installed": {
            "client_id": "COLE_AQUI_SEU_CLIENT_ID",
            "client_secret": "COLE_AQUI_SEU_CLIENT_SECRET",
            "redirect_uris": ["http://localhost"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    },
    scopes=scopes,
)
creds = flow.run_local_server(port=0)
print("Refresh token:", creds.refresh_token)
