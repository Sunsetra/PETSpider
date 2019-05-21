# coding:utf-8
"""A crawler for Pixiv, E-hentai and twitter."""
import os
import sys
from multiprocessing import freeze_support

import requests
from PyQt5.QtCore import QSettings, QCoreApplication
from PyQt5.QtGui import QFont, QGuiApplication, QIcon
from PyQt5.QtWidgets import QAction, QApplication, QMainWindow, QTabWidget, QMessageBox
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from modules import globj, pixiv_gui, pixiv


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
        self.pixiv_icon = QIcon(os.path.join(bundle_dir, 'icon', 'pixiv.png'))

        self.ehentai_wid = None
        self.ehentai_var = None
        self.twitter_wid = None
        self.twitter_var = None

        self.tab_widget = QTabWidget()  # Main widget of main window
        self.setCentralWidget(self.tab_widget)

        self.misc_setting = globj.MiscSettingDialog()
        self.misc_setting.closed.connect(self.misc_setting_checker)
        self.rule_setting = globj.SaveRuleDialog()

        self.init_ui()

    def init_ui(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('文件(&F)')
        act_clear_cookies = QAction('清除Cookie(&C)', self)
        act_clear_cookies.triggered.connect(self.clear_cookies)
        act_clear_db = QAction('清除数据库缓存(&D)', self)
        act_clear_db.triggered.connect(self.clear_db)
        act_exit = QAction('退出(&Q)', self)
        act_exit.triggered.connect(QCoreApplication.quit)
        file_menu.addAction(act_clear_cookies)
        file_menu.addAction(act_clear_db)
        file_menu.addSeparator()
        file_menu.addAction(act_exit)

        setting_menu = menu_bar.addMenu('设置(&S)')
        misc_setting = QAction('首选项(&P)', self)
        rule_setting = QAction('保存规则(&R)', self)
        setting_menu.addAction(misc_setting)
        setting_menu.addAction(rule_setting)
        misc_setting.triggered.connect(self.misc_setting_dialog)
        rule_setting.triggered.connect(self.rule_setting_dialog)

        self.tab_login('pixiv')

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
        self.settings.beginGroup('MiscSetting')
        proxy = self.settings.value('proxy', {})
        self.settings.endGroup()
        return globj.GlobalVar(session, proxy, bundle_dir)

    def tab_logout(self, tab: str, info=None):
        """Switch tab widget to main page."""
        if tab == 'pixiv':
            # Recreate main page instance because new main page needs user's name/id
            self.pixiv_main = pixiv_gui.MainWidget(self.pixiv_var, info)
            self.pixiv_main.logout_sig.connect(self.tab_login)
            self.tab_widget.removeTab(0)
            self.tab_widget.insertTab(0, self.pixiv_main, self.pixiv_icon, 'Pixiv')

    def tab_login(self, tab: str):
        """Switch tab widget to login page."""
        if tab == 'pixiv':
            # Recreate glovar instance bacause old session contains old cookies
            self.pixiv_var = self.init_var()
            self.pixiv_login = pixiv_gui.LoginWidget(self.pixiv_var)
            self.pixiv_login.login_success.connect(self.tab_logout)
            self.tab_widget.removeTab(0)
            self.tab_widget.insertTab(0, self.pixiv_login, self.pixiv_icon, 'Pixiv')

    def clear_cookies(self):
        self.settings.beginGroup('Cookies')
        self.settings.setValue('pixiv', '')
        self.settings.setValue('ehentai', '')
        self.settings.setValue('twitter', '')
        self.settings.sync()
        self.settings.endGroup()
        self.pixiv_login.clear_cookies()
        globj.show_messagebox(self, QMessageBox.Information, '清除完成', '成功清除登陆信息！')

    def clear_db(self):
        pixiv.cleaner()
        globj.show_messagebox(self, QMessageBox.Information, '清除完成', '成功清除数据库缓存！')

    def misc_setting_dialog(self):
        self.misc_setting.move(self.x() + (self.width() - self.misc_setting.sizeHint().width()) / 2,
                               self.y() + (self.height() - self.misc_setting.sizeHint().height()) / 2)
        self.misc_setting.show()

    def misc_setting_checker(self):
        """Make the proxy and thumbnail setting active immediately."""
        self.settings.beginGroup('MiscSetting')
        if int(self.settings.value('pixiv_proxy', False)):
            self.pixiv_var.proxy = self.settings.value('proxy', {})
        else:
            self.pixiv_var.proxy = {}
        if self.pixiv_main:  # Change thumbnail behavior
            setting_thumbnail = int(self.settings.value('thumbnail', True))
            self.pixiv_main.change_thumb(setting_thumbnail)
        self.settings.endGroup()

    def rule_setting_dialog(self):
        self.rule_setting.move(self.x() + (self.width() - self.rule_setting.sizeHint().width()) / 2,
                               self.y() + (self.height() - self.rule_setting.sizeHint().height()) / 2)
        self.rule_setting.show()

    def closeEvent(self, event):
        """Do cleaning before closing."""
        if self.pixiv_main:
            if self.pixiv_main.logout_fn():
                event.accept()
            else:
                event.ignore()


if __name__ == '__main__':
    freeze_support()  # Multiprocessing support when package
    if getattr(sys, 'frozen', False):  # Search for runtime path
        bundle_dir = getattr(sys, '_MEIPASS', None)
    else:
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
