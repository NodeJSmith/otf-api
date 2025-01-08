import os
from getpass import getpass

from otf_api import Otf, OtfUser
from otf_api.auth.auth import OtfAuth

USERNAME = os.getenv("OTF_EMAIL") or input("Enter your OTF email: ")
PASSWORD = os.getenv("OTF_PASSWORD") or getpass("Enter your OTF password: ")


def main():
    """
    OtfAuthConfig provides three options currently:
    """

    # You can use `login` to log in with a username and password
    user = OtfUser.login(USERNAME, PASSWORD)
    print(user.otf_auth.auth_type)

    # If you have tokens available you can provide them using `from_tokens` instead of `login`
    user = OtfUser.from_tokens(**user.cognito.tokens)
    print(user.otf_auth.auth_type)

    # Likewise, if you have a Cognito instance you can provide that as well
    user = OtfUser.from_cognito(cognito=user.cognito)
    print(user.otf_auth.auth_type)

    # If you have already logged in and you cached your tokens, you can use `from_cache` to create a user object
    # without providing any tokens
    user = OtfUser.from_cache()
    print(user.otf_auth.auth_type)

    # if you want to clear both, you can use `clear_cache`
    user.clear_cache()

    # for more granular control you can access the `otf_auth` attribute
    # if you want to clear the cached tokens, you can use `clear_cached_tokens`
    # if you want to clear the cached device data, you can use `clear_cached_device_data`
    user.otf_auth.clear_cached_tokens()
    user.otf_auth.clear_cached_device_data()

    # now if we tried to log in from cache, it would raise a ValueError
    try:
        user = OtfUser.from_cache()
    except ValueError as e:
        print(e)

    # to instantiate an Otf instance, you can provide either a user object or an auth object

    # if you provide a user then authenticate doesn't need to be called
    otf_from_user = Otf(user=user)
    print(otf_from_user.member_uuid)

    # whereas if you provide an auth object, authenticate will be called
    auth = OtfAuth.create(USERNAME, PASSWORD)

    otf_from_auth = Otf(auth=auth)
    print(otf_from_auth.member_uuid)


if __name__ == "__main__":
    main()
