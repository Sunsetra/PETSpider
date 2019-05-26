# coding:utf-8
"""E(x)hentai components."""
import random
import re

import requests
from bs4 import BeautifulSoup

from modules import globj

_LOGIN_URL = 'https://forums.e-hentai.org/index.php'
_ACCOUNT_URL = 'https://e-hentai.org/home.php'
_EXHENTAI_URL = 'https://exhentai.org/'


def _ban_checker(html: BeautifulSoup):
    if not html.head and 'Your IP address has been' in html.body.p.string:
        raise globj.ValidationError(html.body.p.string)


def login(se, proxy: dict, uid: str, pw: str) -> bool:
    """Login and set cookies for exhentai."""
    try:
        with se.post(_LOGIN_URL,
                     params={'act': 'Login', 'CODE': '01'},
                     data={'CookieDate': '1', 'UserName': uid, 'PassWord': pw},
                     headers={'User-Agent': random.choice(globj.GlobalVar.user_agent)},
                     proxies=proxy,
                     timeout=5) as login_res:
            login_html = BeautifulSoup(login_res.text, 'lxml')
            se.cookies.update(login_res.cookies)  # Set cookies

        if login_html.head.title.string == 'Please stand by...':
            with se.get(_EXHENTAI_URL,
                        proxies=proxy,
                        headers={'User-Agent': random.choice(globj.GlobalVar.user_agent)},
                        timeout=5) as ex_res:
                ex_html = BeautifulSoup(ex_res.text, 'lxml')
                _ban_checker(ex_html)
                if ex_html.head.title.string == 'ExHentai.org':
                    se.cookies.update(ex_res.cookies)  # Set cookies for exhentai
                    return True
                else:
                    raise globj.ValidationError('Cannot get into exhentai.')
        elif login_html.head.title.string == 'Log In':
            raise globj.ValidationError('Incorrect username or password.')
        else:
            raise globj.ResponseError('Abnormal response.')

    except requests.Timeout:
        raise requests.Timeout('Timeout during login.')
    except (globj.ResponseError, AttributeError) as e:
        raise globj.ResponseError('Login:' + repr(e))
    except globj.ValidationError:
        raise


def account_info(se, proxy: dict) -> tuple:
    """Get download limitation(used/all)."""
    try:
        with se.get(_ACCOUNT_URL,
                    headers={'User-Agent': random.choice(globj.GlobalVar.user_agent)},
                    proxies=proxy,
                    timeout=5) as info_res:
            info_html = BeautifulSoup(info_res.text, 'lxml')
        _ban_checker(info_html)
        info_node = info_html.find('div', class_='homebox')
        if info_node:
            limit = info_node('strong')
            return limit[0].string, limit[1].string
        else:
            raise globj.ResponseError('Abnormal response.')
    except requests.Timeout:
        raise requests.Timeout('Timeout during fetching account info.')
    except globj.ResponseError as e:
        raise globj.ResponseError('Fetching account info:' + repr(e))


def information(se, proxy: dict, addr: str):
    """
    Fetch gallery information, include misc info and thumbnail.
    Args:
        se: Session instance.
        proxy: (Optinal) The proxy used.
        addr: Gallery address.
    """
    re_thumb = re.compile(r'.*url\((.*)\).*')
    try:
        with se.get(addr,
                    params={'inline_set': 'ts_m'},
                    headers={'User-Agent': random.choice(globj.GlobalVar.user_agent)},
                    proxies=proxy,
                    timeout=5) as gallery_res:
            gallery_html = BeautifulSoup(gallery_res.text, 'lxml')
        _ban_checker(gallery_html)
        name = gallery_html.find('h1', id='gj').string
        misc = gallery_html.find_all('td', class_='gdt2')
        thumb = re_thumb.match(gallery_html.find('div', id='gd1').div['style']).group(1)
        if name and misc and thumb:
            return {
                'gid': addr.split('/')[-3],
                'name': name,
                'size': misc[4].string,
                'page': misc[5].string[:-6],
                'thumb': thumb
            }
        else:
            raise globj.ResponseError('Abnormal response.')
    except requests.Timeout:
        raise requests.Timeout('Timeout during fetching gallery info.')
    except (AttributeError, globj.ResponseError) as e:
        raise globj.ResponseError('Fetching gallery info:' + repr(e))


def fetch_keys(se, proxy: dict, addr: str, info: dict) -> dict:
    """
    Fetch keys(imgkeys and showkey) from gallery.
    Args:
        se: Session instance.
        proxy: (Optinal) The proxy used.
        addr: Gallery address.
        info: Information of the gallery.
    """
    re_imgkey = re.compile(r'https://exhentai\.org/s/(\w{10})/\d*-(\d{1,4})')
    re_showkey = re.compile(r'[\S\s]*showkey="(\w{11})"[\S\s]*')
    pn = int(info['page']) // 40 + 1  # range(0) has no element
    keys = dict()
    try:
        for p in range(pn):
            with se.get(addr,
                        params={'inline_set': 'ts_m', 'p': p},
                        headers={'User-Agent': random.choice(globj.GlobalVar.user_agent)},
                        proxies=proxy,
                        timeout=5) as gallery_res:
                gallery_html = BeautifulSoup(gallery_res.text, 'lxml')
            _ban_checker(gallery_html)

            # Fetch imgkey from every picture
            pics = gallery_html.find_all('div', class_='gdtm')
            for item in pics:
                match = re_imgkey.match(item.a['href'])
                keys[match.group(2)] = match.group(1)

        # Fetch showkey from first picture
        showkey_url = '/'.join(['https://exhentai.org/s', keys['1'], info['gid'] + '-1'])
        with se.get(showkey_url,
                    headers={'User-Agent': random.choice(globj.GlobalVar.user_agent)},
                    proxies=proxy,
                    timeout=5) as showkey_res:
            showkey_html = BeautifulSoup(showkey_res.text, 'lxml')
        _ban_checker(showkey_html)
        keys['0'] = re_showkey.match(showkey_html('script')[1].string).group(1)
        return keys
    except requests.Timeout:
        raise requests.Timeout('Timeout during fetching keys.')
    except AttributeError as e:
        raise globj.ResponseError('Fetching gallery keys:' + repr(e))


def download(se, proxy: dict, addr: str):
    """
    Download pictures from gallery.
    Args:
        se: Session instance.
        proxy: (Optinal) The proxy used.
        addr: Picture origin address.
    """


if __name__ == '__main__':
    pass
    # session = requests.session()
    # prox = {'http': 'socks5://127.0.0.1:1080', 'https': 'socks5://127.0.0.1:1080'}
    # account_info(session, prox)
