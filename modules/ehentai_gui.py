# coding:utf-8
"""GUI components for Ehentai tab."""
import os
from functools import partial

import requests
from PyQt5.QtCore import Qt, QSettings, QThread, pyqtSignal
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QFormLayout, QWidget, QGroupBox, QLineEdit, QPushButton,
                             QCheckBox, QLabel, QSplitter, QFileDialog, QMessageBox)

from modules import globj, ehentai


class LoginWidget(QWidget):
    login_success = pyqtSignal(str, tuple)

    def __init__(self, glovar):
        super().__init__()
        self.glovar = glovar
        self.settings = QSettings(os.path.join(os.path.abspath('.'), 'settings.ini'), QSettings.IniFormat)

        self.ledit_un = QLineEdit()
        self.ledit_un.setContextMenuPolicy(Qt.NoContextMenu)
        self.ledit_pw = QLineEdit()
        self.ledit_pw.setContextMenuPolicy(Qt.NoContextMenu)
        self.ledit_pw.setEchoMode(QLineEdit.Password)
        self.cbox_cookie = QCheckBox('保存登陆状态')
        self.btn_ok = QPushButton('登陆')
        self.btn_ok.setDefault(True)
        self.btn_ok.clicked.connect(self.login)
        self.login_thread = None
        self.verify_thread = None

        self.init_ui()

    def set_disabled(self, status: bool):
        self.ledit_pw.setDisabled(status)
        self.ledit_un.setDisabled(status)
        self.cbox_cookie.setDisabled(status)
        self.btn_ok.setDisabled(status)

    def init_ui(self):
        self.settings.beginGroup('Cookies')
        if self.settings.value('ehentai', ''):
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
        vlay_ok.addWidget(self.btn_ok, alignment=Qt.AlignHCenter)
        gbox_login = QGroupBox()
        gbox_login.setLayout(vlay_ok)
        gbox_login.setFixedSize(gbox_login.sizeHint())

        vlay_login = QVBoxLayout()  # self layout
        vlay_login.addWidget(gbox_login, alignment=Qt.AlignCenter)
        self.setLayout(vlay_login)

    def login(self):
        """
        Login behavior.
        If cookies in setting is not NULL, test it by fetching limitation,
        or login by username and password.
        """
        self.set_disabled(True)
        password = self.ledit_pw.text()
        username = self.ledit_un.text()
        proxy = self.glovar.proxy

        self.settings.beginGroup('Cookies')
        cookies = self.settings.value('ehentai', '')
        self.settings.endGroup()
        if cookies and not password and not username:
            self.glovar.session.cookies.update(cookies)
            self.verify_thread = VerifyThread(self, self.glovar.session, self.glovar.proxy)
            self.verify_thread.verify_success.connect(self.set_cookies)
            self.verify_thread.except_signal.connect(globj.show_messagebox)
            self.verify_thread.finished.connect(partial(self.set_disabled, False))
            self.verify_thread.start()
        else:
            self.login_thread = LoginThread(self, self.glovar.session, proxy, password, username)
            self.login_thread.login_success.connect(self.set_cookies)
            self.login_thread.except_signal.connect(globj.show_messagebox)
            self.login_thread.finished.connect(partial(self.set_disabled, False))
            self.login_thread.start()

    def set_cookies(self, info):
        self.settings.beginGroup('Cookies')
        if self.cbox_cookie.isChecked():
            self.settings.setValue('ehentai', self.glovar.session.cookies)
        else:
            self.settings.setValue('ehentai', '')
        self.settings.sync()
        self.settings.endGroup()
        self.login_success.emit('ehentai', info)
        self.set_disabled(False)

    def clear_cookies(self):
        self.ledit_un.clear()
        self.ledit_un.setPlaceholderText('')
        self.ledit_pw.clear()
        self.ledit_pw.setPlaceholderText('')
        self.cbox_cookie.setChecked(False)


class LoginThread(QThread):
    login_success = pyqtSignal(tuple)
    except_signal = pyqtSignal(object, int, str, str)

    def __init__(self, parent, session, proxy, pw, uid):
        super().__init__()
        self.parent = parent
        self.session = session
        self.proxy = proxy
        self.pw = pw
        self.uid = uid

    def run(self):
        try:
            ehentai.login(self.session, proxy=self.proxy, pw=self.pw, uid=self.uid)
            info = ehentai.account_info(self.session, self.proxy)
        except requests.exceptions.RequestException as e:
            self.except_signal.emit(self.parent, QMessageBox.Warning, '连接失败', '请检查网络或使用代理。\n' + repr(e))
        except globj.ValidationError:
            self.except_signal.emit(self.parent, QMessageBox.Critical, '错误', '登陆名或密码错误。')
        except globj.ResponseError as e:
            self.except_signal.emit(self.parent, QMessageBox.Critical,
                                    '未知错误', '返回值错误，请向开发者反馈\n{0}'.format(repr(e)))
        else:
            self.login_success.emit(info)


class VerifyThread(QThread):
    verify_success = pyqtSignal(tuple)
    except_signal = pyqtSignal(object, int, str, str)

    def __init__(self, parent, session, proxy):
        super().__init__()
        self.parent = parent
        self.session = session
        self.proxy = proxy

    def run(self):
        try:
            info = ehentai.account_info(self.session, self.proxy)
        except (requests.exceptions.ProxyError,
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError) as e:
            self.except_signal.emit(self.parent, QMessageBox.Warning, '连接失败', '请检查网络或使用代理。\n' + repr(e))
        except globj.ResponseError:
            self.except_signal.emit(self.parent, QMessageBox.Critical, '登陆失败', '请尝试清除cookies重新登陆。')
        else:
            self.verify_success.emit(info)


class MainWidget(QWidget):
    logout_sig = pyqtSignal(str)

    def __init__(self, glovar, info):
        super().__init__()
        self.glovar = glovar
        self.settings = QSettings(os.path.join(os.path.abspath('.'), 'settings.ini'), QSettings.IniFormat)

        self.ledit_addr = globj.LineEditor()
        self.cbox_rename = QCheckBox('按序号重命名')
        self.cbox_rename.setToolTip('勾选后将以图片在画廊中的序号重命名而非使用原图片名。')
        self.btn_get = QPushButton('获取信息')
        self.btn_dl = QPushButton('下载')

        self.user_info = QLabel('下载限额：{0}/{1}'.format(info[0], info[1]))
        self.btn_refresh = QPushButton('刷新限额')
        self.btn_logout = QPushButton('退出登陆')

        self.init_ui()

    def init_ui(self):
        hlay_addr = QHBoxLayout()
        hlay_addr.addWidget(QLabel('画廊地址'))
        hlay_addr.addWidget(self.ledit_addr)
        hlay_addr.setStretch(0, 0)
        hlay_cbox = QHBoxLayout()
        hlay_cbox.addWidget(self.cbox_rename)
        hlay_cbox.setAlignment(Qt.AlignLeft)
        hlay_acts = QHBoxLayout()
        hlay_acts.addStretch(1)
        hlay_acts.addWidget(self.btn_get)
        hlay_acts.addWidget(self.btn_dl)
        hlay_acts.addStretch(1)

        vlay_left = QVBoxLayout()
        vlay_left.addLayout(hlay_addr)
        vlay_left.addLayout(hlay_cbox)
        vlay_left.addLayout(hlay_acts)
        left_wid = QWidget()
        left_wid.setLayout(vlay_left)

        vlay_right = QVBoxLayout()
        vlay_right.addWidget(self.user_info, alignment=Qt.AlignHCenter)
        vlay_right.addWidget(self.btn_refresh)
        vlay_right.addWidget(self.btn_logout)
        right_wid = QWidget()
        right_wid.setLayout(vlay_right)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(3)
        splitter.addWidget(left_wid)
        splitter.addWidget(right_wid)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.handle(1).setDisabled(True)

        vlay_main = QVBoxLayout()
        vlay_main.addWidget(splitter)
        self.setLayout(vlay_main)


class SaveRuleSettingTab(QWidget):

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.root_path = None
        self.ledit_prev = globj.LineEditor()
        self.ledit_prev.setReadOnly(True)
        self.ledit_prev.setContextMenuPolicy(Qt.NoContextMenu)

        self.restore()
        self.init_ui()

    def init_ui(self):
        btn_root = QPushButton('浏览')
        btn_root.clicked.connect(self.choose_dir)

        hlay_root = QHBoxLayout()
        hlay_root.addWidget(QLabel('根目录'))
        hlay_root.addWidget(btn_root)

        vlay_ehentai = QVBoxLayout()
        vlay_ehentai.addLayout(hlay_root)
        vlay_ehentai.addWidget(self.ledit_prev)
        vlay_ehentai.setAlignment(Qt.AlignTop)
        self.setLayout(vlay_ehentai)
        self.setMinimumSize(self.sizeHint())

    def choose_dir(self):
        self.settings.beginGroup('RuleSetting')
        setting_root_path = self.settings.value('ehentai_root_path', os.path.abspath('.'))
        root_path = QFileDialog.getExistingDirectory(self, '选择目录', setting_root_path)
        self.settings.endGroup()
        if root_path:  # When click Cancel, root_path is None
            self.root_path = root_path
            self.previewer()

    def previewer(self):
        if globj.PLATFORM == 'Windows':
            root_path = self.root_path.replace('/', '\\')
        else:
            root_path = self.root_path
        self.ledit_prev.setText(root_path)

    def store(self):
        self.settings.beginGroup('RuleSetting')
        self.settings.setValue('ehentai_root_path', self.root_path)
        self.settings.sync()
        self.settings.endGroup()

    def restore(self):
        self.settings.beginGroup('RuleSetting')
        self.root_path = self.settings.value('ehentai_root_path', os.path.abspath('.'))
        self.settings.endGroup()
        self.previewer()
