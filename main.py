# coding:utf-8
"""A crawler for Pixiv, E-hentai and twitter."""
import os
import sys
from multiprocessing import freeze_support

import requests
from PyQt5.QtCore import QSettings, QCoreApplication
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

        self.pixiv_var = self.init_var()  # Pixiv global vars
        self.pixiv_login = pixiv_gui.LoginWidget(self.pixiv_var)  # Pixiv login page
        self.pixiv_login.login_success.connect(self.pixiv_tab_changer)
        self.pixiv_main = pixiv_gui.MainWidget(self.pixiv_var)  # Pixiv main page

        self.ehentai_wid = None
        self.ehentai_var = self.init_var()
        self.twitter_wid = None
        self.twitter_var = self.init_var()

        self.tab_widget = QTabWidget()  # Main widget of main window
        self.tab_widget.setTabShape(QTabWidget.Triangular)
        self.setCentralWidget(self.tab_widget)

        self.net_setting = globj.NetSettingDialog()
        self.net_setting.closed.connect(self.net_setting_checker)  # Check changes of settings

        self.init_ui()

    def init_ui(self):
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

        self.tab_widget.addTab(self.pixiv_login, 'Pixiv')
        self.tab_widget.addTab(self.ehentai_wid, 'EHentai')
        self.tab_widget.addTab(self.twitter_wid, 'Twitter')

        self.frameGeometry().moveCenter(self.resolution.center())  # Open at middle of screen
        self.setWindowTitle('PETSpider')
        self.show()

    def init_var(self):
        """
        Construct global instances for every class.
        Return:
            A globj.GlobalVar class instance, should be
            passed to construct func of every modal.
        """
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.2)
        adp = HTTPAdapter(max_retries=retries)
        session.mount('http://', adp)
        session.mount('https://', adp)
        self.settings.beginGroup('NetSetting')
        proxy = self.settings.value('proxy', {})
        self.settings.endGroup()
        return globj.GlobalVar(session, proxy)

    def net_setting_dialog(self):
        self.net_setting.move(self.x() + (self.width() - self.net_setting.sizeHint().width()) / 2,
                              self.y() + (self.height() - self.net_setting.sizeHint().height()) / 2)
        self.net_setting.show()

    def pixiv_tab_changer(self):
        self.tab_widget.removeTab(0)
        self.tab_widget.insertTab(0, self.pixiv_main, 'Pixiv')

    def net_setting_checker(self):
        self.settings.beginGroup('NetSetting')
        if int(self.settings.value('pixiv_proxy', False)):
            self.pixiv_var.proxy = self.settings.value('proxy', {})
        else:
            self.pixiv_var.proxy = {}
        # There also need ehentai and twitter proxy changer later
        self.settings.endGroup()


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
    #     #         fet_pic = pixiv.fetcher(pid)
    #     #         if not fet_pic:
    #     #             print('Not in database.')
    #     #             fet_pic = pixiv.get_detail(session, pid, proxy)
    #     #             update.append(fet_pic)
    #     #         else:
    #     #             print('Fetch from database')
    #     #         file_path = pixiv.path_name(fet_pic, os.path.abspath('.'),
    #     #                                     {0: 'userName', 1: 'illustTitle'}, {0: 'illustId'})
    #     #         pixiv.download_pic(session, proxy, fet_pic, file_path)
    #     #         print('\n')
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
