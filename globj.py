# coding:utf-8
"""Global objects."""
import re

user_agent = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0',
              ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
               'Chrome/73.0.3683.86 Safari/537.36'),
              ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
               'Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763'))
re_symbol = re.compile(r'[/\\|*?<>":]')


class ResponseError(Exception):
    """Exception for abnormal response."""

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class ValidationError(Exception):
    """Exception for wrong user-id or password."""

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


def name_verify(name: str, default: str) -> str:
    """Normalize file/folder name."""
    # TODO: Different behavior based on platform
    illegal_name = {'con', 'aux', 'nul', 'prn', 'com0', 'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7',
                    'com8', 'com9', 'lpt0', 'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'}

    step1 = re_symbol.sub('', name)  # Remove illegal symbol
    step2 = step1.strip('.')  # Remove '.' in the beginning and end
    if step2 in illegal_name or not step2:
        return default
    else:
        return step2


if __name__ == '__main__':
    print('/con?:', name_verify('/con?', 'IllegalName'))
    print('.hack"thank:', name_verify('.hack"thank', 'IllegalName'))
    print('...aux*Myname...:', name_verify('...aux*Myname...', 'IllegalName'))
    print('...:', name_verify('...', 'IllegalName'))
