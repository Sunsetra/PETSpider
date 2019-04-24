# coding:utf-8
"""Global objects."""
import os
import platform
import random
import re

from PyQt5.QtCore import Qt, QSettings, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFormLayout, QHBoxLayout, QVBoxLayout, QMenu, QLabel, QFileDialog, QSpinBox, QGridLayout
from PyQt5.QtWidgets import QWidget, QLineEdit, QGroupBox, QPushButton, QCheckBox, QMessageBox, QComboBox, QTabWidget

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
    """NetSetting dialog class."""
    closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.cbox_pixiv = QCheckBox('Pixiv')  # Proxy availability
        self.cbox_ehentai = QCheckBox('Ehentai')  # Proxy availability
        self.cbox_twitter = QCheckBox('Twitter')  # Proxy availability
        self.ledit_http = LineEditor()  # Http proxy
        self.ledit_https = LineEditor()  # Https proxy

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
        self.settings.endGroup()

        self.cbox_pixiv.setChecked(setting_pixiv_proxy)
        self.cbox_ehentai.setChecked(setting_ehentai_proxy)
        self.cbox_twitter.setChecked(setting_twitter_proxy)
        self.ledit_http.setPlaceholderText('服务器地址:端口号')
        self.ledit_https.setPlaceholderText('服务器地址:端口号')
        self.ledit_http.setText(setting_proxy['http'])
        self.ledit_https.setText(setting_proxy['https'])

        btn_ok = QPushButton('确定', self)
        btn_ok.setDefault(True)
        btn_canc = QPushButton('取消', self)
        btn_ok.clicked.connect(self.store)
        btn_canc.clicked.connect(self.close)

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
        hlay_proxy.addWidget(btn_ok)
        hlay_proxy.addWidget(btn_canc)
        hlay_proxy.addStretch(1)

        vlay_proxy = QVBoxLayout()  # All component
        vlay_proxy.addWidget(gbox_proxy)
        vlay_proxy.addLayout(hlay_proxy)
        self.setLayout(vlay_proxy)

        self.setFixedSize(self.sizeHint())
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

    def closeEvent(self, event):
        self.settings.beginGroup('NetSetting')
        setting_pixiv_proxy = int(self.settings.value('pixiv_proxy', False))
        setting_ehentai_proxy = int(self.settings.value('ehentai_proxy', False))
        setting_twitter_proxy = int(self.settings.value('twitter_proxy', False))
        setting_proxy = self.settings.value('proxy', {'http': '', 'https': ''})
        self.settings.endGroup()

        self.cbox_pixiv.setChecked(setting_pixiv_proxy)
        self.cbox_ehentai.setChecked(setting_ehentai_proxy)
        self.cbox_twitter.setChecked(setting_twitter_proxy)
        self.ledit_http.setText(setting_proxy['http'])
        self.ledit_https.setText(setting_proxy['https'])
        self.closed.emit()


class DownloadSettingDialog(QTabWidget):
    """DownloadSetting dialog class."""
    closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)
        self.settings = QSettings(os.path.join(os.path.abspath('.'), 'settings.ini'), QSettings.IniFormat)

        self.root_path = None  # Root path, initial from setting ini.
        self.folder_rule = {0: 'illustId'}
        self.file_rule = {0: 'illustId'}
        self.btn_root = QPushButton('浏览')
        self.btn_root.clicked.connect(self.choose_dir)

        self.sbox_folder = QSpinBox()
        self.sbox_folder.setMinimum(1)
        self.sbox_folder.setMaximum(5)
        self.sbox_folder.valueChanged.connect(self.folder_updater)
        self.sbox_file = QSpinBox()
        self.sbox_file.setMinimum(1)
        self.sbox_file.setMaximum(5)
        self.sbox_file.valueChanged.connect(self.file_updater)
        self.cbox_folder_list = [LayerSelector() for i in range(5)]
        for wid in self.cbox_folder_list:
            wid.currentIndexChanged.connect(self.update_rule)
        self.cbox_file_list = [LayerSelector() for i in range(5)]
        for wid in self.cbox_file_list:
            wid.currentIndexChanged.connect(self.update_rule)
        self.hlay_folder_cbox = QHBoxLayout()
        self.hlay_file_cbox = QHBoxLayout()

        self.ledit_prev = LineEditor()
        self.ledit_prev.setReadOnly(True)
        self.ledit_prev.setContextMenuPolicy(Qt.NoContextMenu)

        self.init_ui()

    def init_ui(self):
        self.setFont(QFont('Arial', 10))
        self.settings.beginGroup('DownloadSetting')
        self.root_path = self.settings.value('root_path', os.path.abspath('.'))
        self.settings.endGroup()
        self.previewer()

        glay_folder = QGridLayout()
        glay_folder.addWidget(QLabel('根目录'), 0, 0, 1, 1)
        glay_folder.addWidget(self.btn_root, 0, 1, 1, 2)
        glay_folder.addWidget(QLabel('文件夹层级'), 1, 0, 1, 1)
        glay_folder.addWidget(self.sbox_folder, 1, 1, 1, 2)

        glay_file = QGridLayout()
        glay_file.addWidget(QLabel('文件名层级'), 0, 0, 1, 1)
        glay_file.addWidget(self.sbox_file, 0, 1, 1, 2)

        btn_ok = QPushButton('确定', self)
        btn_ok.setDefault(True)
        btn_canc = QPushButton('取消', self)
        btn_ok.clicked.connect(self.store)
        btn_canc.clicked.connect(self.close)

        hlay_btn = QHBoxLayout()  # Confirm and cancel button
        hlay_btn.addStretch(1)
        hlay_btn.addWidget(btn_ok)
        hlay_btn.addWidget(btn_canc)
        hlay_btn.addStretch(1)

        vlay_pixiv = QVBoxLayout()
        vlay_pixiv.addLayout(glay_folder)
        vlay_pixiv.addLayout(self.hlay_folder_cbox)
        vlay_pixiv.addLayout(glay_file)
        vlay_pixiv.addLayout(self.hlay_file_cbox)
        vlay_pixiv.addWidget(self.ledit_prev)
        vlay_pixiv.addLayout(hlay_btn)
        wid_pixiv = QWidget()
        wid_pixiv.setLayout(vlay_pixiv)

        self.addTab(wid_pixiv, 'Pixiv')

        for wid in self.cbox_folder_list:
            self.hlay_folder_cbox.addWidget(wid)
        for wid in self.cbox_file_list:
            self.hlay_file_cbox.addWidget(wid)
        self.setFixedSize(self.sizeHint())
        self.folder_updater(1)
        self.file_updater(1)
        self.setWindowTitle('下载设置')

    def store(self):
        self.settings.beginGroup('DownloadSetting')
        self.settings.setValue('root_path', self.root_path)
        self.settings.sync()
        self.settings.endGroup()
        self.close()

    def choose_dir(self):
        self.settings.beginGroup('DownloadSetting')
        setting_root_path = self.settings.value('root_path', os.path.abspath('.'))
        self.root_path = QFileDialog.getExistingDirectory(self, '选择目录', setting_root_path)
        self.settings.endGroup()
        self.previewer()

    def folder_updater(self, new):
        now = self.hlay_folder_cbox.count()
        if now < new:
            for i in range(now, new):
                self.hlay_folder_cbox.addWidget(self.cbox_folder_list[i])
                self.cbox_folder_list[i].show()
        else:
            for i in range(4, new - 1, -1):
                self.hlay_folder_cbox.removeWidget(self.cbox_folder_list[i])
                self.cbox_folder_list[i].hide()
        self.update_rule()

    def file_updater(self, new):
        now = self.hlay_file_cbox.count()
        if now < new:
            for i in range(now, new):
                self.hlay_file_cbox.addWidget(self.cbox_file_list[i])
                self.cbox_file_list[i].show()
        else:
            for i in range(4, new - 1, -1):
                self.hlay_file_cbox.removeWidget(self.cbox_file_list[i])
                self.cbox_file_list[i].hide()
        self.update_rule()

    def update_rule(self):
        name_dic = {'PID': 'illustId',
                    '画廊名': 'illustTitle',
                    '画师ID': 'userId',
                    '画师名': 'userName',
                    '创建日期': 'createDate'}
        self.folder_rule = {i: name_dic[self.cbox_folder_list[i].currentText()] for i in range(self.sbox_folder.value())}
        self.file_rule = {i: name_dic[self.cbox_file_list[i].currentText()] for i in range(self.sbox_file.value())}
        self.previewer()

    def previewer(self):
        path = self.root_path
        for layer in self.folder_rule.values():
            path = os.path.join(path, layer)
        all_name = [layer for layer in self.file_rule.values()]
        name = '_'.join(all_name)
        path = os.path.join(path, name + '.jpg')
        self.ledit_prev.setText(path)

    def keyPressEvent(self, k):
        if k.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        self.closed.emit()


class LayerSelector(QComboBox):
    def __init__(self):
        super().__init__()
        self.addItems(['PID', '画廊名', '画师ID', '画师名', '创建日期'])


class LineEditor(QLineEdit):
    """Custom QLineEdit. Support cut, copy, paste and select all."""
    def __init__(self):
        super().__init__()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        act_select_all = menu.addAction('全选')
        act_cut = menu.addAction('剪切')
        act_copy = menu.addAction('复制')
        act_paste = menu.addAction('粘贴')
        if not self.text():
            act_select_all.setEnabled(False)
            act_cut.setEnabled(False)
            act_copy.setEnabled(False)
        else:
            act_cut.setEnabled(self.hasSelectedText())
            act_copy.setEnabled(self.hasSelectedText())
        action = menu.exec(self.mapToGlobal(event.pos()))
        if action == act_cut:
            self.cut()
        elif action == act_copy:
            self.copy()
        elif action == act_select_all:
            self.selectAll()
        elif action == act_paste:
            self.paste()


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


def show_messagebox(parent, style, title: str, message: str):
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setIcon(style)
    msg_box.setText(message)
    msg_box.addButton('确定', QMessageBox.AcceptRole)
    msg_box.exec()


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
