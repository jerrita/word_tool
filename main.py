import os
import random
import sys

from PyQt5 import QtMultimedia
from PyQt5.QtCore import QUrl
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
        self.BtnRSort.setDisabled(True)
        self.setWindowTitle('背词小助手 build 1.1')
        self.player = QtMultimedia.QMediaPlayer()
        self.CheckSoundAuto.setChecked(True)
        self.CheckSound.setChecked(True)
        self.player.setVolume(50)

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
            self.BtnRSort.setDisabled(False)
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
            # 计数
            self.count_correct = 0
            self.count_wrong = 0
            self.Label_correct.setText('Correct')
            self.Label_wrong.setText('Wrong')
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
                self.count_wrong = 0
                self.Label_wrong.setText('Wrong')
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

    def playSound(self, item):
        self.EditNow.setFocus()
        # analyze clicked word
        # 分析箭头指向，获得单词
        txt = item.text().split(' <- ')
        if len(txt) == 1:
            txt = item.text().split(' -> ')
            word = txt[1]
        else:
            word = txt[0]
        url = f'http://dict.youdao.com/dictvoice?type={int(self.CheckSound.isChecked())}&audio={word}'
        content = QtMultimedia.QMediaContent(QUrl(url))
        self.player.setMedia(content)
        self.player.play()

    def mainSound(self, item):
        txt = item.text().split(',')
        if len(txt) == 2:
            url = f'http://dict.youdao.com/dictvoice?type={int(self.CheckSound.isChecked())}&audio={txt[0]}'
            content = QtMultimedia.QMediaContent(QUrl(url))
            self.player.setMedia(content)
            self.player.play()

    def goBtnClicked(self):
        if self.ListMain.count() == 0:
            return

        word = self.ListMain.currentItem().text()
        trans = self.wordlist[self.ListMain.currentItem().text()]
        self.ListMain.takeItem(self.ListMain.currentRow())

        # 翻译校检，使箭头指向单词，便于获取发音
        if (self.mode and self.EditNow.text() in trans and self.EditNow.text()) or (self.EditNow.text() == trans):
            self.count_correct += 1
            self.ListCorrect.addItem(word + (' <- ' if self.mode else ' -> ') + trans)
            self.ListCorrect.setCurrentRow(self.ListCorrect.count() - 1)
            self.Label_correct.setText(f'Correct: {self.count_correct}')
        else:
            self.count_wrong += 1
            self.ListError.addItem(trans + (' -> ' if self.mode else ' <- ') + word)
            self.wrong_word_dic.append(word)
            self.ListError.setCurrentRow(self.ListError.count() - 1)
            self.Label_wrong.setText(f'Wrong: {self.count_wrong}')

        # 是否自动发音
        if self.CheckSoundAuto.isChecked():
            if not self.mode:
                word = trans
            url = f'http://dict.youdao.com/dictvoice?type={int(self.CheckSound.isChecked())}&audio={word}'
            content = QtMultimedia.QMediaContent(QUrl(url))
            self.player.setMedia(content)
            self.player.play()

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
                    self.count_wrong = 0
                    self.Label_wrong.setText('Wrong')
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

    def randomSort(self):
        # 获取所有元素，打乱插入
        widgetres = []
        # 获取listwidget中条目数
        count = self.ListMain.count()
        # 遍历listwidget中的内容
        for i in range(count):
            widgetres.append(self.ListMain.item(i).text())
        # 清空，乱序后插入
        self.ListMain.clear()
        random.shuffle(widgetres)
        self.ListMain.addItems(widgetres)
        self.ListMain.setCurrentRow(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myWin = MyWidget()
    myWin.show()
    sys.exit(app.exec_())
