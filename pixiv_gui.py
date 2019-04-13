from PyQt5.QtCore import Qt, QSettings, QThread, pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QFormLayout
from PyQt5.QtWidgets import QWidget, QGroupBox, QLineEdit, QPushButton, QCheckBox, QMessageBox

import pixiv
import requests
import globj
import os


class LoginWidget(QWidget):
    def __init__(self, glovar):
        super().__init__()
        self.glovar = glovar
        self.settings = QSettings(os.path.join(os.path.abspath('.'), 'settings.ini'), QSettings.IniFormat)

        self.ledit_un = QLineEdit()
        self.ledit_pw = QLineEdit()
        self.cbox_cookie = QCheckBox('保存登陆状态')
        self.login_thread = None

        self.init_ui()

    def init_ui(self):
        flay_input = QFormLayout()  # Input area layout
        self.ledit_pw.setEchoMode(QLineEdit.Password)
        flay_input.addRow('用户名', self.ledit_un)
        flay_input.addRow('密码', self.ledit_pw)
        flay_input.addRow(self.cbox_cookie)
        button_ok = QPushButton('确定')
        button_ok.clicked.connect(self.login)

        vlay_ok = QVBoxLayout()  # GroupBox layout
        vlay_ok.addLayout(flay_input)
        vlay_ok.addWidget(button_ok, alignment=Qt.AlignHCenter)
        gbox_login = QGroupBox('登陆')
        gbox_login.setLayout(vlay_ok)
        gbox_login.setFixedSize(gbox_login.sizeHint())

        vlay_login = QVBoxLayout()  # self layout
        vlay_login.addWidget(gbox_login, alignment=Qt.AlignCenter)
        self.setLayout(vlay_login)

    def login(self):
        username = self.ledit_un.text()
        password = self.ledit_pw.text()
        proxy = self.glovar.proxy
        # if self.settings.value('pixiv'):  # 读取cookies试登陆应放在主线程中
        #     try:
        #         following = pixiv.get_following(self.glovar.session, proxy)  # Cookies test
        #     except globj.ResponseError:
        #         pass
        #     else:
        #         return True
        self.login_thread = LoginThread(self.glovar.session, proxy, password, username)
        self.login_thread.start()
        self.login_thread.login_success.connect(self.set_cookies)
        self.login_thread.except_signal.connect(self.show_messagebox)

    def set_cookies(self):
        if self.cbox_cookie.isChecked():
            self.settings.beginGroup('Cookies')
            self.settings.setValue('pixiv', self.glovar.session.cookies)
            self.settings.sync()
            self.settings.endGroup()

    def show_messagebox(self, style, title: str, message: str):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setIcon(style)
        msg_box.setText(message)
        msg_box.addButton('确定', QMessageBox.AcceptRole)
        msg_box.exec()


class LoginThread(QThread):
    login_success = pyqtSignal()
    except_signal = pyqtSignal(int, str, str)

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
            self.except_signal.emit(QMessageBox.Warning, '警告', '连接超时。\n请检查网络或使用代理。')
        except globj.ValidationError:
            self.except_signal.emit(QMessageBox.Critical, '错误', '用户名或密码错误。')
        except globj.ResponseError as e:
            self.except_signal.emit(QMessageBox.Critical, '错误', '返回值错误，请向开发者反馈\n{0}'.format(repr(e)))
        self.login_success.emit()


class MainWidget(QWidget):
    def __init__(self, glovar):
        super().__init__()
        self.glovar = glovar
        self.settings = QSettings(os.path.join(os.path.abspath('.'), 'settings.ini'), QSettings.IniFormat)

        self.init_ui()
