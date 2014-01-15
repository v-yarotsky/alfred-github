from ctypes import *
from ctypes import util

security = cdll.LoadLibrary(util.find_library("Security"))


class Keychain(object):
    def __init__(self, service):
        self.service = c_char_p(service)
        self.service_length = c_ulong(len(service))

    def store_password(self, account, password):
        account_length = c_ulong(len(account))
        account = c_char_p(account)
        password_length = c_ulong(len(password))
        password = create_string_buffer(password)
        security.SecKeychainAddGenericPassword(
                    None,
                    self.service_length,
                    self.service,
                    account_length,
                    account,
                    password_length,
                    password,
                    None
            )

    def get_password(self, account):
        account_length = c_ulong(len(account))
        account = c_char_p(account)
        password_length = pointer(c_ulong())
        password = pointer(c_char_p())

        security.SecKeychainFindGenericPassword(
                    None,
                    self.service_length,
                    self.service,
                    account_length,
                    account,
                    password_length,
                    password,
                    None
            )

        length = password_length.contents.value
        if not password.contents.value:
          return None
        else:
          return password.contents.value[0:length]

