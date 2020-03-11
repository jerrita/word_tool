import os
import sys

from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QMessageBox

from gui import *


# 字典文件必！须！使用utf-8编码！utf-8-bom都不行！


class MyWidget(QWidget, Ui_Form):
    def __init__(self, parent=None):
        super(MyWidget, self).__init__(parent)
        self.setupUi(self)
        self.status = False
        self.BtnGo.setDisabled(True)
        self.BtnStatus.setDisabled(True)  # 必须有字典才可开启
        self.BtnExportError.setDisabled(True)
        self.setWindowTitle('背词小助手 build 0.1')

    def chooseBtnClicked(self):
        choose = QFileDialog.getExistingDirectory()
        self.EditDir.setText(choose)

    def rowChanged(self):
        self.EditNow.setFocus()

    def flushBtnClicked(self):
        content = self.EditDir.text() if self.EditDir.text() else '.'
        if not os.path.isdir(content):
            QMessageBox.warning(self, '提示', '请确认文件夹填写正确！', QMessageBox.Yes)
        else:
            self.ListDir.clear()
            filelist = os.listdir(content)
            self.dicpath = {}
            for filename in filelist:
                path = content + '/' + filename
                if os.path.isfile(path) and filename.split('.')[-1] == 'csv':
                    self.dicpath[filename.split('.csv')[0]] = path
            self.ListDir.addItems(self.dicpath)

    def dicClicked(self, item):
        self.dicnow = item.text()
        self.ListMain.clear()
        fdic = open(self.dicpath[self.dicnow], 'r', encoding='utf-8').read().split('\n')
        self.ListMain.addItems(fdic)
        self.BtnStatus.setDisabled(False)

    def statusBtnClicked(self):
        if not self.status:
            # 背词开始，清空一切
            self.BtnGo.setDisabled(False)  # 还原按钮
            self.BtnFlush.setDisabled(True)
            self.ListDir.setDisabled(True)  # 禁止更换词典
            self.BtnExportError.setDisabled(False)  # 允许错误导出
            # 模式处理 1 is 英译汉 and 0 is 汉译英(default)
            self.mode = self.CheckMode.isChecked()
            self.CheckMode.setDisabled(True)
            self.BtnStatus.setText('结束背词')
            self.status = True
            self.wrong_word_dic = []
            # 清空右栏
            self.ListCorrect.clear()
            self.ListError.clear()
            # 创建词典， 屏蔽翻译
            self.ListMain.clear()
            fdic = open(self.dicpath[self.dicnow], 'r', encoding='utf-8').read().split('\n')
            self.wordlist = {}  # 当前单词表
            for i in fdic:
                t = i.split(',')
                try:
                    if self.mode:
                        self.wordlist[t[0]] = t[1]
                    else:
                        self.wordlist[t[1]] = t[0]
                except Exception as e:
                    print(e)
            self.ListMain.addItems(self.wordlist)  # 添加至窗口
            self.ListMain.setCurrentRow(0)
            # 聚焦
            self.EditNow.setFocus()
        else:
            # 背词结束
            ret = QMessageBox.information(self, '提示', '背词结束, 是否进行错误训练？', QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                # 错误单词搬进听写界面
                self.ListMain.clear()
                self.ListError.clear()
                self.ListMain.addItems(self.wrong_word_dic)
                self.ListMain.setCurrentRow(0)
                self.wrong_word_dic = []
            else:
                self.status = False
                self.BtnGo.setDisabled(True)
                self.BtnStatus.setText('开始背词')
                self.ListDir.setDisabled(False)
                self.BtnFlush.setDisabled(False)
                self.CheckMode.setDisabled(False)

    def errorexportBtnClicked(self):
        if not self.wrong_word_dic:
            QMessageBox.information(self, '提示', '您没有错误哦，不需要导出~', QMessageBox.Yes)
            return
        name = QFileDialog.getSaveFileName(self, '保存错误单词文件', f'{self.dicnow}-Wrong', '字典文件(*.csv)')
        path = name[0]
        if not path:
            return
        with open(path, 'w', encoding='utf-8') as fp:
            for i in self.wrong_word_dic:
                if self.mode:
                    fp.write(f'{i},{self.wordlist[i]}\n')
                else:
                    fp.write(f'{self.wordlist[i]},{i}\n')
        QMessageBox.information(self, '提示', '导出成功！', QMessageBox.Yes)

    def goBtnClicked(self):
        if self.ListMain.count() == 0:
            return

        word = self.ListMain.currentItem().text()
        trans = self.wordlist[self.ListMain.currentItem().text()]
        self.ListMain.takeItem(self.ListMain.currentRow())

        # 翻译校检
        if (self.mode and self.EditNow.text() in trans) or (self.EditNow.text() == trans):
            self.ListCorrect.addItem(f'{word} -> {trans}')
            self.ListCorrect.setCurrentRow(self.ListCorrect.count() - 1)
        else:
            self.ListError.addItem(f'{word} -> {trans}')
            self.wrong_word_dic.append(word)
            self.ListError.setCurrentRow(self.ListError.count() - 1)

        # 处理剩余
        if self.ListMain.count() == 0:
            # 所有单词已背完，禁止再答，如果有错误提示是否进行错误训练
            if self.ListError.count():
                ret = QMessageBox.information(self, '提示', '背词结束, 是否进行错误训练？', QMessageBox.Yes | QMessageBox.No)
                if ret == QMessageBox.Yes:
                    # 错误单词搬进听写界面
                    self.ListError.clear()
                    self.ListMain.addItems(self.wrong_word_dic)
                    self.ListMain.setCurrentRow(0)
                    self.wrong_word_dic = []
                else:
                    self.status = False
                    self.BtnGo.setDisabled(True)
                    self.BtnStatus.setText('开始背词')
                    self.ListDir.setDisabled(False)
                    self.BtnFlush.setDisabled(False)
                    self.CheckMode.setDisabled(False)
            else:
                QMessageBox.information(self, '提示', '恭喜你已完成所有单词的背诵！现在你可选择其他词典继续开始哦^_^')
                self.BtnStatus.setText('开始背词')
                self.status = False
                self.ListDir.setDisabled(False)
                self.BtnFlush.setDisabled(False)
                self.CheckMode.setDisabled(False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = MyWidget()
    myWin.show()
    sys.exit(app.exec_())
