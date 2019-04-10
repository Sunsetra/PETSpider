# coding:utf-8
"""A crawler for Pixiv, E-hentai and twitter."""
import os
import sys
from multiprocessing import freeze_support

import requests
from PyQt5.QtCore import Qt, QSettings, QCoreApplication
from PyQt5.QtGui import QFont, QGuiApplication
from PyQt5.QtWidgets import QAction, QApplication
from PyQt5.QtWidgets import QMainWindow, QTabWidget
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import globj
import pixiv_gui


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setFont(QFont('Arial', 10))
        self.resolution = QGuiApplication.primaryScreen().availableGeometry()
        self.reso_height = self.resolution.height()
        self.reso_width = self.resolution.width()
        self.settings = QSettings(os.path.join(os.path.abspath('.'), 'settings.ini'), QSettings.IniFormat)

        self.pixiv_wid = None  # Pixiv tab
        self.pixiv_var = None  # Pixiv global vars
        self.ehentai_wid = None
        self.ehentai_var = None
        self.twitter_wid = None
        self.twitter_var = None

        self.net_setting = None  # NetSetting instance

        self.init_ui()

    def init_ui(self):
        tab_widget = QTabWidget()  # Main widget of main window
        tab_widget.setTabShape(QTabWidget.Triangular)
        self.setCentralWidget(tab_widget)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('文件(&F)')
        file_menu.addSeparator()
        act_exit = QAction('退出(&Q)', self)
        act_exit.triggered.connect(QCoreApplication.quit)
        file_menu.addAction(act_exit)

        setting_menu = menu_bar.addMenu('设置(&S)')
        net_setting = QAction('网络设置(&N)', self)
        setting_menu.addAction(net_setting)
        net_setting.triggered.connect(self.net_setting_dialog)

        self.pixiv_wid = pixiv_gui.LoginWidget(self.pixiv_var)
        tab_widget.addTab(self.pixiv_wid, 'Pixiv')
        tab_widget.addTab(self.ehentai_wid, 'EHentai')
        tab_widget.addTab(self.twitter_wid, 'Twitter')

        self.frameGeometry().moveCenter(self.resolution.center())  # Open at middle of screen
        self.setWindowTitle('PETSpider')
        self.show()

    def init_var(self, tab: str):
        # 按tab类型读取相应保存的cookies并生成相应tab的session
        # 构建对应tab的全局变量并返回它
        if tab == 'Pixiv':
            session = requests.Session()  # Need to save cookies instead of login every time
        retries = Retry(total=5, backoff_factor=0.2)
        adp = HTTPAdapter(max_retries=retries)
        session.mount('http://', adp)
        session.mount('https://', adp)

        # 从设置中读取proxy，之后对proxy的更改从qlineedit中读取
        proxy = {'http': '127.0.0.1:1080', 'https': '127.0.0.1:1080'}
        global_var = globj.GlobalVar(session, proxy)
        return global_var  # 这个全局变量组传给相应分模块的各构造类的构造函数

    def net_setting_dialog(self):
        self.net_setting = globj.NetSettingDialog(self)
        self.net_setting.setAttribute(Qt.WA_DeleteOnClose)
        # self.net_setting.destroyed.connect(self.client_setting_checker)  # 此时检查设置文件的变动
        self.net_setting.show()


if __name__ == '__main__':
    freeze_support()  # Multiprocessing support when package
    if getattr(sys, 'frozen', False):  # Search for runtime path
        bundle_dir = getattr(sys, '_MEIPASS', None)
    else:
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())

    # try:
    #     uid = input('Input user id/email:')
    #     pw = input('Input password:')
    #     pixiv.login(session, proxy, uid, pw)
    # except (requests.Timeout, globj.ResponseError) as e:
    #     # Delete Window
    #     print(repr(e))
    # except globj.ValidationError as e:
    #     # Reenter pw and id
    #     print(repr(e))

    # try:
    #     # following = pixiv.get_following(session, proxy)
    #     # print(following)
    #
    #     new_items1 = pixiv.get_new(session, proxy, 8)
    #     print(new_items1)
    #     # new_items2 = pixiv.get_new(session, proxy, 20, user_id='947930')
    #     # new_items3 = pixiv.get_detail(session, '74008554', proxy)
    #     # print(len(new_items1), new_items1)
    #     # print(len(new_items2), new_items2)
    #     # print(len(new_items3), new_items3)
    #
    #     update = []
    #     for pid in new_items1:
    #         fet_pic = pixiv.fetcher(pid)
    #         if not fet_pic:
    #             print('Not in database.')
    #             fet_pic = pixiv.get_detail(session, pid, proxy)
    #             update.append(fet_pic)
    #         else:
    #             print('Fetch from database')
    #         file_path = pixiv.path_name(fet_pic, os.path.abspath('.'),
    #                                     {0: 'userName', 1: 'illustTitle'}, {0: 'illustId'})
    #         pixiv.download_pic(session, proxy, fet_pic, file_path)
    #         print('\n')
    #     pixiv.pusher(update)
    #
    #     # fet_pic = pixiv.fetcher('74008554')
    #     # if not fet_pic:
    #     #     new_item = pixiv.get_detail(session, '74008554', proxy)
    #     #     pixiv.pusher(new_item.values())
    #     #     fet_data = new_item
    #
    # # All exceptions must be catch in main
    # except requests.Timeout as e:
    #     session.close()
    #     print(repr(e))
    # except globj.ResponseError as e:
    #     session.close()
    #     print(repr(e))
