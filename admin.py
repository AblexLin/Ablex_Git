#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import uic
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QIcon, QPixmap, QPalette, QBrush, QFontDatabase
from PyQt5.QtWidgets import (QFileDialog, QMessageBox, QListWidgetItem)

import res_rc
import progress_dialog
import run
import utils
from pkg_detect import PkgDetect
from pkg_table_widget import PkgWidget

_translate = QtCore.QCoreApplication.translate


class AdminDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(AdminDialog, self).__init__(parent)

        self.init_ui()
        self.init_app()

    def init_ui(self):

        uic.loadUi(os.path.join(
                os.path.dirname(__file__), "res/punggol-admin.ui"), self)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedSize(593, 427)

        self.pkg_list.setSortingEnabled(True)

        self.version_table = PkgWidget(self.tab_2)
        self.version_table.setGeometry(16, 50, 460, 330)
        self.__err_output()

    def init_app(self):
        # base_default_version = 3228  sys_default_version = 2-301-3228
        base_default_version, sys_default_version = utils.get_default_punggol_version2()
        self.base_default_version = base_default_version
        self.sys_default_version = sys_default_version

        self.base_versions = [] # [3228, 3285...]
        for b in utils.all_punggol_base():
            self.base_versions.append(utils.get_base_version_from_path(b))

        self.sys_versions = [] # [2-301-3228, 2-302-3228...]
        for c in utils.all_punggol_sys():
            self.sys_versions.append(utils.get_sys_version_from_path(c))

        for bv in self.base_versions:
            self.__show_version('base', bv)
            if bv == self.base_default_version:
                self.__make_default('base', bv)

        for cv in self.sys_versions:
            self.__show_version('sys', cv)
            if cv == self.sys_default_version:
                self.__make_default('sys', cv)

        self.__check_version_match(self.base_cb.currentText(), self.config_cb.currentText())

        # only on lark
        self.pkg_detect_worker = QThread(self)
        self.pkg_detect_worker.start()
        self.pkg_detect = PkgDetect()
        self.pkg_detect.moveToThread(self.pkg_detect_worker)
        self.pkg_detect.startDetect.emit(1500)

        self.connect_signals()

    def connect_signals(self):
        """信号-槽连接"""
        self.setup_btn.clicked.connect(self.setup_pkg)
        self.browse_btn.clicked.connect(self.__browse_files)
        self.delete_btn.clicked.connect(self.delete_item)
        self.version_table.gotoDelete.connect(self.delete_item)
        self.run_btn.clicked.connect(self.run_punggol)
        self.base_cb.currentTextChanged.connect(self.__on_base_changed)
        self.config_cb.currentTextChanged.connect(self.__on_config_changed)
        self.pkg_detect.foundPackage.connect(self.__on_found_package)
        self.pkg_detect.removeUdisk.connect(self.__on_remove_udisk)

    def __show_version(self, package, version):
        """显示已安装版本"""
        if 'base' == package:
            self.__combo_add(self.base_cb, version)
        else:
            self.__combo_add(self.config_cb, version)
        self.version_table.insert_pkg(**{'package': package, 'version': version})

    def setup_pkg(self):
        """安装"""
        count = self.pkg_list.count()
        if 0 >= count:
            QMessageBox.warning(self, '警告', '无可用安装包!', QMessageBox.Yes)
            return

        item = self.pkg_list.currentItem()
        if item:
            self.__setup_pkg(item.text())
        else:
            QMessageBox.warning(self, '警告', '未选择安装包!', QMessageBox.Yes)

    def __setup_pkg(self, pkg):
        """安装进度对话框"""
        header = utils.tar_detect(pkg)
        if header and ('package' in header) and ('version' in header):
            setup_dlg = progress_dialog.ProgressDialog(pkg, self)
            setup_dlg.exec()
        else:
            QMessageBox.warning(self, '警告', '请选择正确的安装(升级)包!', QMessageBox.Yes)

    def delete_item(self):
        """删除版本"""
        row_index = self.version_table.currentRow()
        if -1 != row_index:
            name = self.version_table.item(row_index, 1).text()
            package, version = utils.get_info_from_name(name)
            if QMessageBox.Yes == QMessageBox.question(self, "提示",
                                                       '''确认要删除"punggol-2-{}"吗?'''.format(name),
                                                       QMessageBox.Yes | QMessageBox.No):
                if 'base' == package and 1 == self.version_table.base_count:
                    # 最后一个base版本删除时删除.desktop
                    utils.rm_desktop()
                self.version_table.delete_pkg(row_index, package)
                self.__del_version(package, version, row_index)

    def __del_combox_item(self, package, version):
        if 'base' == package:
            index = self.base_cb.findText(version)
            assert -1 != index
            self.base_cb.removeItem(index)
        else:
            index = self.config_cb.findText(version)
            assert -1 != index
            self.config_cb.removeItem(index)

    def __set_default_item(self, package, version, row):
        # 该方法仅当删除默认版本，设置下一个默认版本时使用
        assert '' != package
        assert '' != version
        assert -1 != row

        if 'base' == package:
            index = self.base_cb.findText(version)
            assert -1 != index
            self.base_cb.setCurrentIndex(index)
        else:
            index = self.config_cb.findText(version)
            assert -1 != index
            self.config_cb.setCurrentIndex(index)

        self.version_table.set_default(row)

    def __del_version(self, package, version, row):
        """删除版本"""
        utils.remove_pg_dir(package, version)
        need_rewrite = False
        next_default_ver = ''
        self.__del_combox_item(package, version)
        if 'base' == package:
            if self.base_default_version == version:
                # 先查找上面一个item，再查找下面一个item
                if 0 <= (row - 1):
                    row -= 1
                elif row < self.version_table.base_count:
                    pass
                else:
                    row = -1

                if -1 != row:
                    _, next_default_ver = utils.get_info_from_name(self.version_table.item(row, 1).text())
                    self.__set_default_item(package, next_default_ver, row)
                need_rewrite = True
                self.base_default_version = next_default_ver
        else:
            assert isinstance(self.sys_default_version, str)
            if self.sys_default_version == version:
                if 0 <= (row - self.version_table.base_count - 1):
                    row -= 1
                elif row < self.version_table.rowCount():
                    pass
                else:
                    row = -1
                if -1 != row:
                    _, next_default_ver = utils.get_info_from_name(self.version_table.item(row, 1).text())
                    self.__set_default_item(package, next_default_ver, row)
                need_rewrite = True
                self.sys_default_version = next_default_ver

        if need_rewrite:
            if '' == next_default_ver:
                utils.write_config(utils.CONFIG, package, 'version', '')
                utils.write_config(utils.CONFIG, package, 'location', '')
            else:
                utils.write_config(utils.CONFIG, package, 'version', next_default_ver)
                utils.write_config(utils.CONFIG, package, 'location',
                                   os.path.join(utils.APP_ROOT, 'punggol-2-{}-{}'.format(package, next_default_ver)))

    def run_punggol(self):
        """ 运行punggol """
        base_version = self.base_cb.currentText()
        sys_version = self.config_cb.currentText()

        if base_version == '' or sys_version == '':
            QMessageBox.warning(self, '警告', '请正确选择版本!', QMessageBox.Yes)
            return

        if base_version != self.base_default_version:
            self.version_table.change_default('base', base_version)
            self.base_default_version = base_version
            utils.write_config(utils.CONFIG, 'base', 'version', base_version)
            utils.write_config(utils.CONFIG, 'base', 'location',
                               os.path.join(utils.APP_ROOT, 'punggol-2-base-{}'.format(base_version)))

        if self.sys_default_version != sys_version:
            self.version_table.change_default('sys', sys_version)
            self.sys_default_version = sys_version
            utils.write_config(utils.CONFIG, 'sys', 'version', sys_version)
            utils.write_config(utils.CONFIG, 'sys', 'location',
                               os.path.join(utils.APP_ROOT, 'punggol-2-sys-{}'.format(sys_version)))

        base_path = os.path.join(utils.APP_ROOT, 'punggol-2-base-{}'.format(base_version))
        sys_path = os.path.join(utils.APP_ROOT, 'punggol-2-sys-{}'.format(sys_version))
        self.__run_punggol(base_path, sys_path)

    def __run_punggol(self, base_path, sys_path):
        """ 运行punggol """
        try:
            run.run_punggol(base_path, sys_path)
        except Exception as e:
            print(e)
            QMessageBox.warning(self, '警告', '启动Punggol失败!', QMessageBox.Close)

    def add_version(self, package, version):
        """增加版本"""
        utils.write_config(utils.CONFIG, package, 'version', version)
        utils.write_config(utils.CONFIG, package, 'location',
                           os.path.join(utils.APP_ROOT, 'punggol-2-{}-{}'.format(package, version)))

        if 'base' == package:
            self.base_default_version = version
            if 0 == self.version_table.base_count:
                # 第一个base版本安装时生成.desktop
                utils.gen_desktop()
        else:
            self.sys_default_version = version

        self.version_table.insert_pkg(**{'package': package, 'version': version})
        self.version_table.change_default(package, version)

        if 'base' == package:
            index = self.base_cb.findText(version)
            if -1 == index:
                index = self.__combo_add(self.base_cb, version)
                self.base_cb.setCurrentIndex(index)
            else:
                self.base_cb.setCurrentIndex(index)
        else:
            index = self.config_cb.findText(version)
            if -1 == index:
                index = self.__combo_add(self.config_cb, version)
                self.config_cb.setCurrentIndex(index)
            else:
                self.config_cb.setCurrentIndex(index)

    def __make_default(self, package, version):
        """修改默认版本的显示"""
        self.version_table.change_default(package, version)
        if 'base' == package:
            index = self.base_cb.findText(version)
            if -1 != index:
                self.base_cb.setCurrentIndex(index)
        else:
            index = self.config_cb.findText(version)
            if -1 != index:
                self.config_cb.setCurrentIndex(index)

    def __browse_files(self):
        fileName, _ = QFileDialog.getOpenFileName(self,
                                                  "选择安装(升级)包", '',
                                                  "Tar Files (*.tar.gz)")
        if fileName:
            header = utils.tar_detect(fileName)
            if header and ('package' in header) and ('version' in header):
                setup_dlg = progress_dialog.ProgressDialog(fileName, self)
                setup_dlg.exec()
            else:
                QMessageBox.warning(self, '警告', '请选择正确的安装(升级)包!', QMessageBox.Yes)

    def __err_output(self, msg=''):
        if '' == msg:
            self.err_label.clear()
        else:
            self.err_label.setText("<p><b><font color=red>%s</font></b></p>" % msg)

    def __on_base_changed(self, text):
        another = self.config_cb.currentText()
        self.__check_version_match(text, another)

    def __on_config_changed(self, text):
        another = self.base_cb.currentText()
        self.__check_version_match(another, text)

    def __check_version_match(self, base, sys):
        """base、sys版本匹配校验"""
        if '' == base or '' == sys:
            self.run_btn.setEnabled(False)
            self.__err_output('Punggol安装不完整!')
        else:
            self.run_btn.setEnabled(True)
            self.__err_output('')
        # else: 暂时去除版本匹配功能
        #     if utils.base_version_match(base, sys):
        #         self.run_btn.setEnabled(True)
        #         self.__err_output()
        #     else:
        #         self.run_btn.setEnabled(False)
        #         self.__err_output('版本不匹配')

    def __on_found_package(self, path, package, version):

        item = QListWidgetItem(path)
        str1 = _translate("Info", "Package: ")
        str2 = _translate("Info", "Version: ")
        t1 = str1 + package + "\n"
        t2 = str2 + version
        context = t1 + t2
        item.setToolTip(context)
        self.pkg_list.addItem(item)

    def __on_remove_udisk(self, path):

        items = self.pkg_list.findItems(path, Qt.MatchStartsWith)
        if items:
            for item in items:
                self.pkg_list.takeItem(self.pkg_list.row(item))

    def on_setup_finished(self):
        pass

    def __combo_add(self, widget, text):
        index = widget.count()
        for i in range(widget.count()):
            if widget.itemText(i) < text:
                index = i
                break
        widget.insertItem(index, text)
        return index


if __name__ == "__main__":
    """参数1为'startpunggol时启动punggol，否则启动punggol-admin'"""
    if 1 < len(sys.argv) and 'startpunggol' == sys.argv[1]:
        base_default_path, sys_default_path = utils.get_default_punggol_path2()
        if base_default_path != '' and sys_default_path != '':
            run.run_punggol(base_default_path, sys_default_path)
        else:
            print('请确保程序已正常安装')
            exit(-1)
    else:
        app = QtWidgets.QApplication(sys.argv)
        QFontDatabase.addApplicationFont("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf")
        dlg = AdminDialog()
        dlg.setWindowIcon(QIcon(":/admin_icon"))
        dlg.exec_()
