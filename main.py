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

        self.pixiv_var = None  # Pixiv global vars
        self.pixiv_login = None  # Pixiv login page
        self.pixiv_main = None  # Pixiv main page

        self.ehentai_wid = None
        self.ehentai_var = self.init_var()
        self.twitter_wid = None
        self.twitter_var = self.init_var()

        self.tab_widget = QTabWidget()  # Main widget of main window
        self.tab_widget.setTabShape(QTabWidget.Triangular)
        self.setCentralWidget(self.tab_widget)

        self.net_setting = globj.NetSettingDialog()
        self.net_setting.closed.connect(self.net_setting_checker)
        self.dl_setting = globj.DownloadSettingDialog()
        # self.dl_setting.closed.connect(self.dl_setting_checker)

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
        dl_setting = QAction('下载设置(&D)', self)
        setting_menu.addAction(net_setting)
        setting_menu.addAction(dl_setting)
        net_setting.triggered.connect(self.net_setting_dialog)
        dl_setting.triggered.connect(self.dl_setting_dialog)

        self.tab_login(0)

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

    def tab_logout(self, index: int, info=None):
        """Switch tab widget to main page."""
        if index == 0:
            # Recreate main page instance because new main page needs user name/id
            self.pixiv_main = pixiv_gui.MainWidget(self.pixiv_var, info)
            self.pixiv_main.logout.connect(self.tab_login)
            self.tab_widget.removeTab(index)
            self.tab_widget.insertTab(0, self.pixiv_main, 'Pixiv')

    def tab_login(self, index: int):
        """Switch tab widget to login page."""
        if index == 0:
            # Recreate glovar instance bacause old session contains old cookies
            self.pixiv_var = self.init_var()
            self.pixiv_login = pixiv_gui.LoginWidget(self.pixiv_var)
            self.pixiv_login.login_success.connect(self.tab_logout)
            self.tab_widget.removeTab(index)
            self.tab_widget.insertTab(0, self.pixiv_login, 'Pixiv')

    def net_setting_dialog(self):
        self.net_setting.move(self.x() + (self.width() - self.net_setting.sizeHint().width()) / 2,
                              self.y() + (self.height() - self.net_setting.sizeHint().height()) / 2)
        self.net_setting.show()

    def net_setting_checker(self):
        self.settings.beginGroup('NetSetting')
        if int(self.settings.value('pixiv_proxy', False)):
            self.pixiv_var.proxy = self.settings.value('proxy', {})
        else:
            self.pixiv_var.proxy = {}
        # There also need ehentai and twitter proxy changer later
        self.settings.endGroup()

    def dl_setting_dialog(self):
        self.dl_setting.move(self.x() + (self.width() - self.dl_setting.sizeHint().width()) / 2,
                             self.y() + (self.height() - self.dl_setting.sizeHint().height()) / 2)
        self.dl_setting.show()

    # def dl_setting_checker(self):
    #     self.settings.beginGroup('DownloadSetting')
    #     if int(self.settings.value('pixiv_proxy', False)):
    #         self.pixiv_var.proxy = self.settings.value('proxy', {})
    #     else:
    #         self.pixiv_var.proxy = {}
    #     self.settings.endGroup()


if __name__ == '__main__':
    freeze_support()  # Multiprocessing support when package
    if getattr(sys, 'frozen', False):  # Search for runtime path
        bundle_dir = getattr(sys, '_MEIPASS', None)
    else:
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
