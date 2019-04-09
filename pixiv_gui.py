from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QGuiApplication
from PyQt5.QtWidgets import QMainWindow, QWidget, QGroupBox, QTabWidget, QLabel, QLineEdit, QPushButton
from PyQt5.QtWidgets import QVBoxLayout, QFormLayout
from PyQt5.QtWidgets import QAction, QApplication
import sys
import requests
from PyQt5.QtCore import QCoreApplication
from requests.adapters import HTTPAdapter
from urllib3 import Retry

import pixiv
import globj


class LoginWidget(QWidget):
    def __init__(self, glovar):
        super().__init__()
        self.glovar = glovar
        self.ledit_un = QLineEdit()
        self.ledit_pw = QLineEdit()
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

        vlay_ok.addLayout(flay_input)
        vlay_ok.addWidget(button_ok, alignment=Qt.AlignHCenter)
        gbox_login.setLayout(vlay_ok)
        gbox_login.setFixedSize(gbox_login.sizeHint())
        vlay_login.addWidget(gbox_login, alignment=Qt.AlignCenter)
        self.setLayout(vlay_login)

    def login(self):
        username = self.ledit_un.text()
        password = self.ledit_pw.text()
        if pixiv.login(self.glovar.session, proxy=self.glovar.proxy, pw=password, uid=username):
            print('Login Success.')
