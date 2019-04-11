from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import QVBoxLayout, QFormLayout
from PyQt5.QtWidgets import QWidget, QGroupBox, QLineEdit, QPushButton, QCheckBox

import pixiv
import os


class LoginWidget(QWidget):
    def __init__(self, glovar):
        super().__init__()
        self.glovar = glovar
        self.settings = QSettings(os.path.join(os.path.abspath('.'), 'settings.ini'), QSettings.IniFormat)
        self.ledit_un = QLineEdit()
        self.ledit_pw = QLineEdit()
        self.cbox_cookie = QCheckBox('保存登陆状态')
        self.init_ui()

    def init_ui(self):
        vlay_login = QVBoxLayout()
        gbox_login = QGroupBox('登陆')
        vlay_ok = QVBoxLayout()
        flay_input = QFormLayout()

        self.ledit_pw.setEchoMode(QLineEdit.Password)
        button_ok = QPushButton('确定')
        button_ok.clicked.connect(self.login)
        flay_input.addRow('用户名', self.ledit_un)
        flay_input.addRow('密码', self.ledit_pw)
        flay_input.addRow(self.cbox_cookie)

        vlay_ok.addLayout(flay_input)
        vlay_ok.addWidget(button_ok, alignment=Qt.AlignHCenter)
        gbox_login.setLayout(vlay_ok)
        gbox_login.setFixedSize(gbox_login.sizeHint())
        vlay_login.addWidget(gbox_login, alignment=Qt.AlignCenter)
        self.setLayout(vlay_login)

    def login(self):
        username = self.ledit_un.text()
        password = self.ledit_pw.text()
        self.settings.beginGroup('NetSetting')
        if self.settings.value('pixiv_proxy', False):
            proxy = self.glovar.proxy
        else:
            proxy = {}
        self.settings.endGroup()
        print(self.glovar.session, self.glovar.proxy)
        print(proxy, password, username)
        if pixiv.login(self.glovar.session, proxy=proxy, pw=password, uid=username):
            # 试登陆：获取pixiv首页
            following = pixiv.get_following(self.glovar.session, proxy)  # 测试用
            print(following)  # 测试用
            if self.cbox_cookie.isChecked():
                self.settings.beginGroup('Cookies')
                self.settings.setValue('pixiv', self.glovar.session.cookies)
                self.settings.sync()
                self.settings.endGroup()
