import os
from getpass import getpass

from otf_api import Otf, OtfAuth, OtfAuthConfig, OtfUser

USERNAME = os.getenv("OTF_EMAIL") or input("Enter your OTF email: ")
PASSWORD = os.getenv("OTF_PASSWORD") or getpass("Enter your OTF password: ")


def main():
    """
    OtfAuthConfig provides three options currently:
    - cache_tokens_plaintext: bool - Whether to cache the tokens in plaintext in the config file - this is an obvious
        security risk, but it's useful for development purposes. If you want to do this, it is at your own risk. The
        benefit is that after you log in with your username/password once, you can use the cached tokens to log in
        without providing your password again.
    """

    # This is the most configurable way to access the API but also the most verbose

    auth_config = OtfAuthConfig(cache_tokens_plaintext=True)

    auth = OtfAuth.create(USERNAME, PASSWORD, config=auth_config)
    user = OtfUser(auth=auth)
    print(user.otf_auth.auth_type)

    # You can also use `login` to log in with a username and password, with the config being optional
    user = OtfUser.login(USERNAME, PASSWORD, config=auth_config)
    print(user.otf_auth.auth_type)

    # If you have tokens available you can provide them using `from_tokens` instead of `login`

    user = OtfUser.from_tokens(
        user.cognito.access_token, user.cognito.id_token, user.cognito.refresh_token, config=auth_config
    )
    print(user.otf_auth.auth_type)

    # Likewise, if you have a Cognito instance you can provide that as well

    user = OtfUser.from_cognito(cognito=user.cognito, config=auth_config)
    print(user.otf_auth.auth_type)

    # If you have already logged in and you cached your tokens, you can use `from_cache` to create a user object
    # without providing any tokens

    user = OtfUser.from_cache(config=auth_config)
    print(user.otf_auth.auth_type)

    # if you want to clear the cached tokens, you can use `clear_cached_tokens`
    # if you want to clear the cached device data, you can use `clear_cached_device_data`
    # if you want to clear both, you can use `clear_cache`
    user.clear_cached_tokens()
    user.clear_cached_device_data()
    user.clear_cache()

    # now if we tried to log in from cache, it would raise a ValueError
    try:
        user = OtfUser.from_cache(config=auth_config)
    except ValueError as e:
        print(e)

    # to instantiate an Otf instance, you can provide either a user object or an auth object

    # if you provide a user then authenticate doesn't need to be called
    otf_from_user = Otf(user=user)
    print(otf_from_user.member_uuid)

    # whereas if you provide an auth object, authenticate will be called
    otf_from_auth = Otf(auth=auth)
    print(otf_from_auth.member_uuid)


if __name__ == "__main__":
    main()
