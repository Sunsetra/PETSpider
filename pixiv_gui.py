# coding:utf-8
"""GUI components of Pixiv tab."""
import os
from functools import partial

import requests
from PyQt5.QtCore import Qt, QSettings, QThread, pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QFormLayout, QGridLayout
from PyQt5.QtWidgets import QWidget, QGroupBox, QLineEdit, QPushButton, QCheckBox, QMessageBox, QTableWidget, QLabel

import globj
import pixiv


class LoginWidget(QWidget):
    login_success = pyqtSignal()

    def __init__(self, glovar):
        super().__init__()
        self.glovar = glovar
        self.settings = QSettings(os.path.join(os.path.abspath('.'), 'settings.ini'), QSettings.IniFormat)

        self.ledit_un = QLineEdit()
        self.ledit_pw = QLineEdit()
        self.ledit_pw.setEchoMode(QLineEdit.Password)
        self.cbox_cookie = QCheckBox('保存登陆状态')
        self.button_ok = QPushButton('登陆')
        self.button_ok.clicked.connect(self.login)
        self.login_thread = None

        self.init_ui()

    def init_ui(self):
        self.settings.beginGroup('Cookies')
        if self.settings.value('pixiv', ''):
            self.ledit_un.setPlaceholderText('(已保存)')
            self.ledit_pw.setPlaceholderText('(已保存)')
            self.cbox_cookie.setChecked(True)
        self.settings.endGroup()

        flay_input = QFormLayout()  # Input area layout
        flay_input.addRow('登陆名', self.ledit_un)
        flay_input.addRow('密码', self.ledit_pw)
        flay_input.addRow(self.cbox_cookie)

        vlay_ok = QVBoxLayout()  # GroupBox layout
        vlay_ok.addLayout(flay_input)
        vlay_ok.addWidget(self.button_ok, alignment=Qt.AlignHCenter)
        gbox_login = QGroupBox()
        gbox_login.setLayout(vlay_ok)
        gbox_login.setFixedSize(gbox_login.sizeHint())

        vlay_login = QVBoxLayout()  # self layout
        vlay_login.addWidget(gbox_login, alignment=Qt.AlignCenter)
        self.setLayout(vlay_login)

    def login(self):
        """
        Login behavior.
        If cookies in setting is not NULL, test it by fetching following.
        Or login by username and password.
        """
        self.set_disabled(True)
        proxy = self.glovar.proxy
        self.settings.beginGroup('Cookies')  # 读取cookies放在登陆时
        cookies = self.settings.value('pixiv', '')
        self.settings.endGroup()
        if cookies:
            self.glovar.session.cookies.update(cookies)
            try:
                pixiv.get_following(self.glovar.session, proxy)  # Cookies test
            except (ConnectionError, requests.Timeout):
                globj.show_messagebox(self, QMessageBox.Warning, '连接失败', '请检查网络或使用代理。')
            except globj.ResponseError:
                globj.show_messagebox(self, QMessageBox.Critical, '登陆失败', '请尝试清除cookies重新登陆。')
            else:
                self.login_success.emit()
            self.set_disabled(False)
        else:
            password = self.ledit_pw.text()
            username = self.ledit_un.text()
            self.login_thread = LoginThread(self.glovar.session, proxy, password, username)
            self.login_thread.start()
            self.login_thread.login_success.connect(self.set_cookies)
            self.login_thread.except_signal.connect(globj.show_messagebox)
            self.login_thread.finished.connect(partial(self.set_disabled, False))

    def set_cookies(self):
        self.settings.beginGroup('Cookies')
        if self.cbox_cookie.isChecked():
            self.settings.setValue('pixiv', self.glovar.session.cookies)
        else:
            self.settings.setValue('pixiv', '')
        self.settings.sync()
        self.settings.endGroup()
        self.login_success.emit()
        self.set_disabled(False)

    def set_disabled(self, status: bool):
        self.ledit_pw.setDisabled(status)
        self.ledit_un.setDisabled(status)
        self.cbox_cookie.setDisabled(status)
        self.button_ok.setDisabled(status)


class LoginThread(QThread):
    login_success = pyqtSignal()
    except_signal = pyqtSignal(object, int, str, str)

    def __init__(self, session, proxy, pw, uid):
        super().__init__()
        self.session = session
        self.proxy = proxy
        self.pw = pw
        self.uid = uid

    def run(self):
        try:
            pixiv.login(self.session, proxy=self.proxy, pw=self.pw, uid=self.uid)
        except (ConnectionError, requests.Timeout):
            self.except_signal.emit(self.parent(), QMessageBox.Warning, '连接失败', '请检查网络或使用代理。')
        except globj.ValidationError:
            self.except_signal.emit(self.parent(), QMessageBox.Critical, '错误', '用户名或密码错误。')
        except globj.ResponseError as e:
            self.except_signal.emit(self.parent(), QMessageBox.Critical,
                                    '未知错误', '返回值错误，请向开发者反馈\n{0}'.format(repr(e)))
        else:
            self.login_success.emit()


class MainWidget(QWidget):
    def __init__(self, glovar):
        super().__init__()
        self.glovar = glovar
        self.settings = QSettings(os.path.join(os.path.abspath('.'), 'settings.ini'), QSettings.IniFormat)

        self.ledit_pid = QLineEdit()
        self.ledit_uid = QLineEdit()
        self.ledit_num = QLineEdit()
        self.button_get = QPushButton('获取信息')
        self.button_fo = QPushButton('关注的新作品')
        self.button_dl = QPushButton('下载')

        self.init_ui()

    def init_ui(self):
        controller = QGridLayout()
        controller.addWidget(QLabel('图片ID'), 0, 0, 1, 1)
        controller.addWidget(self.ledit_pid, 0, 1, 1, 1)
        controller.addWidget(QLabel('用户ID'), 1, 0, 1, 1)
        controller.addWidget(self.ledit_uid, 1, 1, 1, 1)
        controller.addWidget(QLabel('数量'), 2, 0, 1, 1)
        controller.addWidget(self.ledit_num, 2, 1, 1, 1)
        controller.addWidget(self.button_get, 0, 6, 1, 1)
        controller.addWidget(self.button_fo, 1, 6, 1, 1)
        controller.addWidget(self.button_dl, 2, 6, 1, 1)

        previewer = QTableWidget()
        vlay_main = QVBoxLayout()
        vlay_main.addLayout(controller)
        vlay_main.addWidget(previewer)
        self.setLayout(vlay_main)
