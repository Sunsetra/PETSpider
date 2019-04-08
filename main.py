# coding:utf-8
"""A crawler for Pixiv, E-hentai and twitter."""
import os

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import globj
import pixiv

# Define misc
proxy = {'http': '127.0.0.1:1080', 'https': '127.0.0.1:1080'}

if __name__ == '__main__':
    session = requests.Session()  # Need to save cookies instead of login every time
    retries = Retry(total=5, backoff_factor=0.2)
    adp = HTTPAdapter(max_retries=retries)
    session.mount('http://', adp)
    session.mount('https://', adp)

    try:
        uid = input('Input user id/email:')
        pw = input('Input password:')
        pixiv.login(session, proxy, uid, pw)
    except (requests.Timeout, globj.ResponseError) as e:
        # Delete Window
        print(repr(e))
    except globj.ValidationError as e:
        # Reenter pw and id
        print(repr(e))

    try:
        # following = pixiv.get_following(session, proxy)
        # print(following)

        new_items1 = pixiv.get_new(session, proxy, 8)
        print(new_items1)
        # new_items2 = pixiv.get_new(session, proxy, 20, user_id='947930')
        # new_items3 = pixiv.get_detail(session, '74008554', proxy)
        # print(len(new_items1), new_items1)
        # print(len(new_items2), new_items2)
        # print(len(new_items3), new_items3)

        update = []
        for pid in new_items1:
            fet_pic = pixiv.fetcher(pid)
            if not fet_pic:
                print('Not in database.')
                fet_pic = pixiv.get_detail(session, pid, proxy)
                update.append(fet_pic)
            else:
                print('Fetch from database')
            file_path = pixiv.path_name(fet_pic, os.path.abspath('.'), {0: 'userName', 1: 'illustTitle'}, {0: 'illustId'})
            pixiv.download_pic(session, proxy, fet_pic, file_path)
            print('\n')
        pixiv.pusher(update)

        # fet_pic = pixiv.fetcher('74008554')
        # if not fet_pic:
        #     new_item = pixiv.get_detail(session, '74008554', proxy)
        #     pixiv.pusher(new_item.values())
        #     fet_data = new_item

    # All exceptions must be catch in main
    except requests.Timeout as e:
        session.close()
        print(repr(e))
    except globj.ResponseError as e:
        session.close()
        print(repr(e))
