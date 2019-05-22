# coding:utf-8
"""Ehentai components."""
import requests
from bs4 import BeautifulSoup

from modules import globj

_LOGIN_URL = 'https://forums.e-hentai.org/index.php'
_ACCOUNT_URL = 'https://e-hentai.org/home.php'


def login(se, proxy: dict, uid: str, pw: str) -> bool:
    try:
        with se.post(_LOGIN_URL,
                     params={'act': 'Login', 'CODE': '01'},
                     data={'CookieDate': '1', 'UserName': uid, 'PassWord': pw},
                     proxies=proxy,
                     timeout=5) as login_res:
            login_html = BeautifulSoup(login_res.text, 'lxml')
            if login_html.head.title.string == 'Please stand by...':
                return True
            elif login_html.head.title.string == 'Log In':
                raise globj.ValidationError('Username or password incorrect')
            else:
                raise globj.ResponseError('Abnormal response during login.')
    except requests.Timeout:
        raise requests.Timeout('Timeout during Login.')
    except (globj.ResponseError, globj.ValidationError):
        raise


def account_info(se, proxy: dict):
    """Get download limitation(used/all)."""
    try:
        with se.get(_ACCOUNT_URL,
                    proxies=proxy,
                    cookies=se.cookies,
                    timeout=5) as info_res:
            info_html = BeautifulSoup(info_res.text, 'lxml')
        info_node = info_html.find('div', class_='homebox')
        if info_node:
            limit = info_node('strong')
            return limit[0], limit[1]
        else:
            raise globj.ResponseError('Abnormal response during getting account info.')
    except requests.Timeout:
        raise requests.Timeout('Timeout during Login.')


if __name__ == '__main__':
    pass
    # session = requests.session()
    # prox = {'http': 'socks5://127.0.0.1:1080', 'https': 'socks5://127.0.0.1:1080'}
    # account_info(session, prox)
