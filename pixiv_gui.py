# coding:utf-8
"""GUI components of Pixiv tab."""
import os
from functools import partial

import requests
from PyQt5.QtCore import Qt, QSettings, QThread, pyqtSignal, QVariant
from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout, QHeaderView, QTableWidgetItem,
                             QSplitter, QButtonGroup, QWidget, QGroupBox, QLineEdit, QPushButton, QCheckBox,
                             QMessageBox, QTableWidget, QLabel, QAbstractItemView, QSpinBox)
from PyQt5.QtGui import QBrush, QColor

import globj
import pixiv


class LoginWidget(QWidget):
    login_success = pyqtSignal(int, tuple)

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
        self.button_ok = QPushButton('登陆')
        self.button_ok.clicked.connect(self.login)
        self.login_thread = None
        self.verify_thread = None

        self.init_ui()

    def set_disabled(self, status: bool):
        self.ledit_pw.setDisabled(status)
        self.ledit_un.setDisabled(status)
        self.cbox_cookie.setDisabled(status)
        self.button_ok.setDisabled(status)

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
        password = self.ledit_pw.text()
        username = self.ledit_un.text()
        proxy = self.glovar.proxy

        self.settings.beginGroup('Cookies')
        cookies = self.settings.value('pixiv', '')
        self.settings.endGroup()
        if cookies and not password and not username:
            self.glovar.session.cookies.update(cookies)
            self.verify_thread = VerifyThread(self.glovar.session, self.glovar.proxy)
            self.verify_thread.verify_success.connect(self.set_cookies)
            self.verify_thread.except_signal.connect(globj.show_messagebox)
            self.verify_thread.finished.connect(partial(self.set_disabled, False))
            self.verify_thread.start()
        else:
            self.login_thread = LoginThread(self.glovar.session, proxy, password, username)
            self.login_thread.login_success.connect(self.set_cookies)
            self.login_thread.except_signal.connect(globj.show_messagebox)
            self.login_thread.finished.connect(partial(self.set_disabled, False))
            self.login_thread.start()

    def set_cookies(self, info):
        self.settings.beginGroup('Cookies')
        if self.cbox_cookie.isChecked():
            self.settings.setValue('pixiv', self.glovar.session.cookies)
        else:
            self.settings.setValue('pixiv', '')
        self.settings.sync()
        self.settings.endGroup()
        self.login_success.emit(0, info)
        self.set_disabled(False)


class LoginThread(QThread):
    login_success = pyqtSignal(tuple)
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
            info = pixiv.get_user(self.session, self.proxy)
        except (requests.exceptions.ProxyError,
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError) as e:
            self.except_signal.emit(self.parent(), QMessageBox.Warning, '连接失败', '请检查网络或使用代理。\n' + repr(e))
        except globj.ValidationError:
            self.except_signal.emit(self.parent(), QMessageBox.Critical, '错误', '登陆名或密码错误。')
        except globj.ResponseError as e:
            self.except_signal.emit(self.parent(), QMessageBox.Critical,
                                    '未知错误', '返回值错误，请向开发者反馈\n{0}'.format(repr(e)))
        else:
            self.login_success.emit(info)


class VerifyThread(QThread):
    verify_success = pyqtSignal(tuple)
    except_signal = pyqtSignal(object, int, str, str)

    def __init__(self, session, proxy):
        super().__init__()
        self.session = session
        self.proxy = proxy

    def run(self):
        try:
            info = pixiv.get_user(self.session, self.proxy)
        except (requests.exceptions.ProxyError,
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError) as e:
            self.except_signal.emit(self.parent(), QMessageBox.Warning, '连接失败', '请检查网络或使用代理。\n' + repr(e))
        except globj.ResponseError:
            self.except_signal.emit(self.parent(), QMessageBox.Critical, '登陆失败', '请尝试清除cookies重新登陆。')
        else:
            self.verify_success.emit(info)


class FetchThread(QThread):
    fetch_success = pyqtSignal(list)
    except_signal = pyqtSignal(object, int, str, str)

    def __init__(self, session, proxy, pid, uid, num):
        super().__init__()
        self.session = session
        self.proxy = proxy
        self.pid = pid
        self.uid = uid
        self.num = num

    def run(self):
        try:
            if self.pid:
                new_set = {self.pid}
            else:
                new_set = pixiv.get_new(self.session, self.proxy, user_id=self.uid, num=self.num)
            updater = []
            results = []
            for pid in new_set:
                fet_pic = pixiv.fetcher(pid)
                if not fet_pic:
                    print('Not in database.')
                    fet_pic = pixiv.get_detail(self.session, pid=pid, proxy=self.proxy)
                    updater.append(fet_pic)
                else:
                    print('Fetch from database')
                results.append(fet_pic)
            pixiv.pusher(updater)
        except (requests.exceptions.ProxyError,
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError) as e:
            self.except_signal.emit(self.parent(), QMessageBox.Warning, '连接失败', '请检查网络或使用代理。\n' + repr(e))
        except globj.ResponseError as e:
            self.except_signal.emit(self.parent(), QMessageBox.Critical,
                                    '未知错误', '返回值错误，请向开发者反馈\n{0}'.format(repr(e)))
        else:
            self.fetch_success.emit(results)


class MainWidget(QWidget):
    logout = pyqtSignal(int)

    def __init__(self, glovar, info):
        super().__init__()
        self.glovar = glovar
        self.info = info
        self.settings = QSettings(os.path.join(os.path.abspath('.'), 'settings.ini'), QSettings.IniFormat)
        self.fetch_thread = None

        self.ledit_pid = globj.LineEditor()
        self.ledit_uid = globj.LineEditor()
        self.ledit_num = QSpinBox()
        self.ledit_num.setContextMenuPolicy(Qt.NoContextMenu)
        self.ledit_num.setMaximum(999)
        self.ledit_num.clear()

        self.button_fo = QPushButton('关注的更新')
        self.button_fo.setCheckable(True)
        self.button_pid = QPushButton('按PID搜索')
        self.button_pid.setCheckable(True)
        self.button_uid = QPushButton('按UID搜索')
        self.button_uid.setCheckable(True)
        self.button_loc = QPushButton('本地搜索')
        self.button_loc.setCheckable(True)
        self.button_group = QButtonGroup()
        self.button_group.addButton(self.button_fo, 1)
        self.button_group.addButton(self.button_pid, 2)
        self.button_group.addButton(self.button_uid, 3)
        self.button_group.addButton(self.button_loc, 4)
        self.button_group.buttonClicked[int].connect(self.change_stat)

        self.user_info = QLabel('{0}({1})'.format(self.info[1], self.info[0]))
        self.button_logout = QPushButton('退出登陆')
        self.button_logout.clicked.connect(partial(self.logout.emit, 0))
        self.button_get = QPushButton('获取信息')
        self.button_get.clicked.connect(self.fetch_new)
        self.button_dl = QPushButton('下载')

        self.table_viewer = QTableWidget()  # Detail viewer of fetched info
        self.table_viewer.setWordWrap(False)
        self.table_viewer.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_viewer.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_viewer.verticalScrollBar().setContextMenuPolicy(Qt.NoContextMenu)
        self.table_viewer.setColumnCount(6)
        self.table_viewer.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table_viewer.setHorizontalHeaderLabels(['PID', '画廊名', '画师ID', '画师名', '页数', '创建日期'])
        self.table_viewer.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_viewer.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_viewer.horizontalHeader().setStyleSheet('QHeaderView::section{background-color:#66CCFF;}')
        self.table_viewer.horizontalHeader().setHighlightSections(False)

        self.ledit_pid.setDisabled(True)
        self.ledit_num.setDisabled(True)
        self.ledit_uid.setDisabled(True)
        self.init_ui()

    def init_ui(self):
        glay_lup = QHBoxLayout()
        glay_lup.addWidget(self.button_fo)
        glay_lup.addWidget(self.button_pid)
        glay_lup.addWidget(self.button_uid)
        glay_lup.addWidget(self.button_loc)

        glay_ldown = QGridLayout()
        glay_ldown.addWidget(QLabel('画廊ID'), 0, 0, 1, 1)
        glay_ldown.addWidget(self.ledit_pid, 0, 1, 1, 5)
        glay_ldown.addWidget(QLabel('用户ID'), 1, 0, 1, 1)
        glay_ldown.addWidget(self.ledit_uid, 1, 1, 1, 5)
        glay_ldown.addWidget(QLabel('数量'), 2, 0, 1, 1)
        glay_ldown.addWidget(self.ledit_num, 2, 1, 1, 1)
        glay_ldown.setColumnStretch(1, 1)
        glay_ldown.setColumnStretch(2, 5)

        vlay_left = QVBoxLayout()
        vlay_left.addLayout(glay_lup)
        vlay_left.addLayout(glay_ldown)
        left_wid = QWidget()
        left_wid.setLayout(vlay_left)

        vlay_right = QVBoxLayout()
        vlay_right.addWidget(self.user_info)
        vlay_right.addWidget(self.button_logout)
        vlay_right.addWidget(self.button_get)
        vlay_right.addWidget(self.button_dl)
        right_wid = QWidget()
        right_wid.setLayout(vlay_right)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(3)
        splitter.addWidget(left_wid)
        splitter.addWidget(right_wid)
        splitter.handle(1).setDisabled(True)

        vlay_main = QVBoxLayout()
        vlay_main.addWidget(splitter)
        vlay_main.addWidget(self.table_viewer)
        self.setLayout(vlay_main)

    def set_disabled(self, status: bool):
        self.button_get.setDisabled(status)
        self.button_dl.setDisabled(status)
        self.button_logout.setDisabled(status)

    def change_stat(self, bid):
        func = {1: self.new_stat,
                2: self.pid_stat,
                3: self.uid_stat,
                4: self.loc_stat}
        self.ledit_num.clear()
        self.ledit_pid.clear()
        self.ledit_uid.clear()
        func[bid]()

    def new_stat(self):
        self.button_uid.setChecked(False)
        self.button_pid.setChecked(False)
        self.button_loc.setChecked(False)
        self.button_fo.setChecked(True)
        self.ledit_uid.setDisabled(True)
        self.ledit_pid.setDisabled(True)
        self.ledit_num.setDisabled(False)

    def pid_stat(self):
        self.button_fo.setChecked(False)
        self.button_loc.setChecked(False)
        self.button_uid.setChecked(False)
        self.button_pid.setChecked(True)
        self.ledit_uid.setDisabled(True)
        self.ledit_num.setDisabled(True)
        self.ledit_pid.setDisabled(False)

    def uid_stat(self):
        self.button_fo.setChecked(False)
        self.button_loc.setChecked(False)
        self.button_pid.setChecked(False)
        self.button_uid.setChecked(True)
        self.ledit_pid.setDisabled(True)
        self.ledit_uid.setDisabled(False)
        self.ledit_num.setDisabled(False)

    def loc_stat(self):
        self.button_pid.setChecked(False)
        self.button_uid.setChecked(False)
        self.button_fo.setChecked(False)
        self.button_loc.setChecked(True)
        self.ledit_uid.setDisabled(False)
        self.ledit_pid.setDisabled(False)
        self.ledit_num.setDisabled(False)

    def tabulate(self, items):
        self.table_viewer.setSortingEnabled(False)
        self.table_viewer.clearContents()
        self.table_viewer.setRowCount(len(items))
        index = 0
        for item in items:
            illust_id = QTableWidgetItem()
            illust_id.setTextAlignment(Qt.AlignCenter)
            illust_id.setData(Qt.EditRole, QVariant(int(item['illustId'])))
            illust_id.setBackground(QBrush(QColor('#CCFFFF')))
            self.table_viewer.setItem(index, 0, illust_id)

            self.table_viewer.setItem(index, 1, QTableWidgetItem(item['illustTitle']))

            user_id = QTableWidgetItem()
            user_id.setTextAlignment(Qt.AlignCenter)
            user_id.setData(Qt.EditRole, QVariant(int(item['userId'])))
            user_id.setBackground(QBrush(QColor('#CCFFFF')))
            self.table_viewer.setItem(index, 2, user_id)

            self.table_viewer.setItem(index, 3, QTableWidgetItem(item['userName']))

            page_count = QTableWidgetItem()
            page_count.setTextAlignment(Qt.AlignCenter)
            page_count.setData(Qt.EditRole, QVariant(item['pageCount']))
            page_count.setBackground(QBrush(QColor('#CCFFFF')))
            self.table_viewer.setItem(index, 4, page_count)

            create_date = QTableWidgetItem()
            create_date.setTextAlignment(Qt.AlignCenter)
            create_date.setData(Qt.EditRole, QVariant(item['createDate']))
            self.table_viewer.setItem(index, 5, create_date)
            index += 1
        self.table_viewer.setSortingEnabled(True)

    def fetch_new(self):
        """When fetch info button clicked, call get_detail function in pixiv.py."""
        self.set_disabled(True)
        pid = self.ledit_pid.text()
        uid = self.ledit_uid.text()
        num = self.ledit_num.value() if self.ledit_num.value() else 0

        self.fetch_thread = FetchThread(self.glovar.session, self.glovar.proxy, pid, uid, num)
        self.fetch_thread.fetch_success.connect(self.tabulate)
        self.fetch_thread.except_signal.connect(globj.show_messagebox)
        self.fetch_thread.finished.connect(partial(self.set_disabled, False))
        self.fetch_thread.start()

