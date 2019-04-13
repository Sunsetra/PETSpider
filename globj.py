# coding:utf-8
"""Global objects."""
import os
import platform
import random
import re

from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import QFormLayout, QHBoxLayout, QVBoxLayout
from PyQt5.QtWidgets import QWidget, QLineEdit, QGroupBox, QPushButton, QCheckBox, QMessageBox

_RE_SYMBOL = re.compile(r'[/\\|*?<>":]')
_RE_PROXY = re.compile(r'.*:([1-9]\d{0,3}|[1-5]\d{4}|6[0-4]\d{4}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])$')
_PLATFORM = platform.system()


class GlobalVar(object):
    def __init__(self, session, proxy: dict):
        self._user_agent = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0',
                            ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/73.0.3683.86 Safari/537.36'),
                            ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763'))
        self._session = session
        self._proxy = proxy

    @property
    def user_agent(self):  # Return random user agent
        return self._user_agent[random.randint(0, 2)]

    @property
    def session(self):
        return self._session

    @session.deleter
    def session(self):
        self._session.close()

    @property
    def proxy(self):
        return self._proxy

    @proxy.setter
    def proxy(self, new: dict):
        self._proxy = new


class NetSettingDialog(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        self.cbox_pixiv = QCheckBox('Pixiv')  # Proxy availability
        self.cbox_ehentai = QCheckBox('Ehentai')  # Proxy availability
        self.cbox_twitter = QCheckBox('Twitter')  # Proxy availability
        self.ledit_http = QLineEdit()  # Http proxy
        self.ledit_https = QLineEdit()  # Https proxy

        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)
        self.settings = QSettings(os.path.join(os.path.abspath('.'), 'settings.ini'), QSettings.IniFormat)
        self.init_ui()

    def init_ui(self):
        self.settings.beginGroup('NetSetting')
        setting_pixiv_proxy = int(self.settings.value('pixiv_proxy', False))
        setting_ehentai_proxy = int(self.settings.value('ehentai_proxy', False))
        setting_twitter_proxy = int(self.settings.value('twitter_proxy', False))
        setting_proxy = self.settings.value('proxy', {'http': '', 'https': ''})
        self.cbox_pixiv.setChecked(setting_pixiv_proxy)
        self.cbox_ehentai.setChecked(setting_ehentai_proxy)
        self.cbox_twitter.setChecked(setting_twitter_proxy)
        self.ledit_http.setPlaceholderText('服务器地址:端口号')
        self.ledit_https.setPlaceholderText('服务器地址:端口号')
        self.ledit_http.setText(setting_proxy['http'])
        self.ledit_https.setText(setting_proxy['https'])
        self.ledit_http.setContextMenuPolicy(Qt.NoContextMenu)
        self.ledit_https.setContextMenuPolicy(Qt.NoContextMenu)
        self.settings.endGroup()
        button_ok = QPushButton('确定', self)
        button_ok.setDefault(True)
        button_canc = QPushButton('取消', self)
        button_ok.clicked.connect(self.store)
        button_canc.clicked.connect(self.close)

        gbox_proxy = QGroupBox('代理设置')
        hlay_cbox = QHBoxLayout()  # Checkbox for different website
        hlay_cbox.addWidget(self.cbox_pixiv)
        hlay_cbox.addWidget(self.cbox_ehentai)
        hlay_cbox.addWidget(self.cbox_twitter)

        flay_proxy = QFormLayout()  # Lineedit for server_ip:port
        flay_proxy.setSpacing(20)
        flay_proxy.addRow('http://', self.ledit_http)
        flay_proxy.addRow('https://', self.ledit_https)

        vlay_cbox = QVBoxLayout()  # Combine into GroupBox
        vlay_cbox.setSpacing(20)
        vlay_cbox.addLayout(hlay_cbox)
        vlay_cbox.addLayout(flay_proxy)
        gbox_proxy.setLayout(vlay_cbox)

        hlay_proxy = QHBoxLayout()  # Confirm and cancel button
        hlay_proxy.addStretch(1)
        hlay_proxy.addWidget(button_ok)
        hlay_proxy.addWidget(button_canc)
        hlay_proxy.addStretch(1)

        vlay_proxy = QVBoxLayout()  # All component
        vlay_proxy.addWidget(gbox_proxy)
        vlay_proxy.addLayout(hlay_proxy)
        self.setLayout(vlay_proxy)

        self.setFixedSize(self.sizeHint())
        self.move(self.parent.x() + (self.parent.width() - self.sizeHint().width()) / 2,
                  self.parent.y() + (self.parent.height() - self.sizeHint().height()) / 2)
        self.setWindowTitle('网络设置')

    def store(self):
        http_proxy = self.ledit_http.text()
        https_proxy = self.ledit_https.text()
        if (_RE_PROXY.match(http_proxy) or not http_proxy) and (_RE_PROXY.match(https_proxy) or not https_proxy):
            self.settings.beginGroup('NetSetting')
            self.settings.setValue('pixiv_proxy', int(self.cbox_pixiv.isChecked()))
            self.settings.setValue('ehentai_proxy', int(self.cbox_ehentai.isChecked()))
            self.settings.setValue('twitter_proxy', int(self.cbox_twitter.isChecked()))
            self.settings.setValue('proxy', {'http': http_proxy, 'https': https_proxy})
            self.settings.sync()
            self.settings.endGroup()
            self.close()
        else:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle('错误')
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText('请输入正确的代理地址。')
            msg_box.addButton('确定', QMessageBox.AcceptRole)
            msg_box.exec()

    def keyPressEvent(self, k):
        if k.key() == Qt.Key_Escape:
            self.close()


class ResponseError(Exception):
    """Exception for abnormal response."""

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class ValidationError(Exception):
    """Exception for wrong user-id or password."""

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


def name_verify(name: str, default: str = 'NoName') -> str:
    """
    Normalize file/folder name.
    Args:
        name: A string of file/folder name.
        default: When the illegal name leads to an empty string, return this.
    Returns:
        A legal string for file/folder name.
    """
    if _PLATFORM == 'Windows':
        illegal_name = {'con', 'aux', 'nul', 'prn', 'com0', 'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7',
                        'com8', 'com9', 'lpt0', 'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'}
        step1 = _RE_SYMBOL.sub('', name)  # Remove illegal symbol
        step2 = step1.strip('.')  # Remove '.' at the beginning and end
        if step2 in illegal_name or not step2:
            return default
        return step2
    elif _PLATFORM == 'Linux':
        step1 = name.replace('/', '')  # Remove illegal '/'
        step2 = step1.lstrip('.')  # Remove '.' at the beginning
        if not step2:
            return default
        return step2


if __name__ == '__main__':
    print('/con?:', name_verify('/con?', 'IllegalName'))
    print('.hack"thank:', name_verify('.hack"thank', 'IllegalName'))
    print('...aux*Myname...:', name_verify('...aux*Myname...', 'IllegalName'))
    print('...:', name_verify('...', 'IllegalName'))
