import sys
def main() -> None:
    sys.exit(
        'Este utilitário foi descontinuado. O projeto agora usa envio SMTP com '
        'EMAIL_HOST, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_USE_TLS, '
        'EMAIL_USE_SSL e EMAIL_REMETENTE.'
    )


if __name__ == "__main__":
    main()
