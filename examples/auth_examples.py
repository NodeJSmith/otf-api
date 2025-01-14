import os
from getpass import getpass

from otf_api import Otf, OtfUser


def main():
    username = os.getenv("OTF_EMAIL") or input("Enter your OTF email: ")
    password = os.getenv("OTF_PASSWORD") or getpass("Enter your OTF password: ")

    # You can use `login` to log in with a username and password
    user = OtfUser(username, password)
    print(user.email_address)

    # If you have tokens available you can provide them using `from_tokens` instead of `login`
    user = OtfUser(**user.cognito.tokens)
    print(user.email_address)

    # if you have cached tokens you can attempt to log in with no arguments
    # if no cached credentials are found a NoCredentialsError will be raised
    user = OtfUser()
    print(user.email_address)

    # however you login, you'll pass the user object to the Otf object

    otf = Otf(user=user)

    print(otf.member.email)


if __name__ == "__main__":
    main()
