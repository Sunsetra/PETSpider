# coding:utf-8
"""Global objects."""
import platform
import random
import re

_RE_SYMBOL = re.compile(r'[/\\|*?<>":]')
_PLATFORM = platform.system()


class GlobalVar(object):
    def __init__(self, session, proxy: dict):
        self._user_agent = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0',
                            ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/73.0.3683.86 Safari/537.36'),
                            ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763'))
        self._session = session
        self._proxy = proxy

    @property
    def user_agent(self):  # Return random user agent
        return self._user_agent[random.randint(0, 2)]

    @property
    def session(self):
        return self._session

    @session.deleter
    def session(self):
        self._session.close()

    @property
    def proxy(self):
        return self._proxy

    @proxy.setter
    def proxy(self, new: dict):
        self._proxy = new


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


def name_verify(name: str, default: str = 'NoName') -> str:
    """
    Normalize file/folder name.
    Args:
        name: A string of file/folder name.
        default: When the illegal name leads to an empty string, return this.
    Returns:
        A legal string for file/folder name.
    """
    if _PLATFORM == 'Windows':
        illegal_name = {'con', 'aux', 'nul', 'prn', 'com0', 'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7',
                        'com8', 'com9', 'lpt0', 'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'}
        step1 = _RE_SYMBOL.sub('', name)  # Remove illegal symbol
        step2 = step1.strip('.')  # Remove '.' at the beginning and end
        if step2 in illegal_name or not step2:
            return default
        return step2
    elif _PLATFORM == 'Linux':
        step1 = name.replace('/', '')  # Remove illegal '/'
        step2 = step1.lstrip('.')  # Remove '.' at the beginning
        if not step2:
            return default
        return step2


if __name__ == '__main__':
    print('/con?:', name_verify('/con?', 'IllegalName'))
    print('.hack"thank:', name_verify('.hack"thank', 'IllegalName'))
    print('...aux*Myname...:', name_verify('...aux*Myname...', 'IllegalName'))
    print('...:', name_verify('...', 'IllegalName'))
