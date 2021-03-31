# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI_labcams.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_LabCams(object):
    def setupUi(self, LabCams):
        LabCams.setObjectName("LabCams")
        LabCams.resize(727, 578)
        self.centralwidget = QtWidgets.QWidget(LabCams)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.mdiArea = QtWidgets.QMdiArea(self.centralwidget)
        self.mdiArea.setObjectName("mdiArea")
        self.horizontalLayout.addWidget(self.mdiArea)
        LabCams.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(LabCams)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 727, 21))
        self.menubar.setObjectName("menubar")
        self.menuView = QtWidgets.QMenu(self.menubar)
        self.menuView.setObjectName("menuView")
        LabCams.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(LabCams)
        self.statusbar.setObjectName("statusbar")
        LabCams.setStatusBar(self.statusbar)
        self.actionCascade = QtWidgets.QAction(LabCams)
        self.actionCascade.setObjectName("actionCascade")
        self.actionTiled = QtWidgets.QAction(LabCams)
        self.actionTiled.setObjectName("actionTiled")
        self.actionSubwindow = QtWidgets.QAction(LabCams)
        self.actionSubwindow.setObjectName("actionSubwindow")
        self.actionTabbed = QtWidgets.QAction(LabCams)
        self.actionTabbed.setObjectName("actionTabbed")
        self.menuView.addAction(self.actionCascade)
        self.menuView.addAction(self.actionTiled)
        self.menuView.addAction(self.actionTabbed)
        self.menuView.addAction(self.actionSubwindow)
        self.menubar.addAction(self.menuView.menuAction())

        self.retranslateUi(LabCams)
        QtCore.QMetaObject.connectSlotsByName(LabCams)

    def retranslateUi(self, LabCams):
        _translate = QtCore.QCoreApplication.translate
        LabCams.setWindowTitle(_translate("LabCams", "LabCams"))
        self.menuView.setTitle(_translate("LabCams", "View"))
        self.actionCascade.setText(_translate("LabCams", "Cascade View"))
        self.actionTiled.setText(_translate("LabCams", "Tiled View"))
        self.actionSubwindow.setText(_translate("LabCams", "Subwindow View"))
        self.actionTabbed.setText(_translate("LabCams", "Tabbed View"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    LabCams = QtWidgets.QMainWindow()
    ui = Ui_LabCams()
    ui.setupUi(LabCams)
    LabCams.show()
    sys.exit(app.exec_())
