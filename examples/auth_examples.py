import os

from otf_api import Otf, OtfUser


def main():
    username = os.getenv("OTF_EMAIL")
    password = os.getenv("OTF_PASSWORD")

    # You can log in with a username and password
    user = OtfUser(username, password)
    print(user.email_address)

    # If you have tokens available you can provide them using `from_tokens` instead of `login`
    user = OtfUser(**user.cognito.tokens)
    print(user.email_address)

    # if you have cached tokens you can attempt to log in with no arguments
    # if no cached credentials are found then one of two things will happen
    # 1. if you are able to provide input in the console you will be prompted for credentials
    # 2. if you are not able to provide input in the console a NoCredentialsError will be raised
    user = OtfUser()
    print(user.email_address)

    OtfUser.clear_cache()

    # the below will now prompt for username/password since there are no cached credentials and
    # no username/password was provided
    otf = Otf()

    print(otf.member.email)


if __name__ == "__main__":
    main()
