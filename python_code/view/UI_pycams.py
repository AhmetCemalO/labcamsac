# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI_pycams.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_PyCams(object):
    def setupUi(self, PyCams):
        PyCams.setObjectName("PyCams")
        PyCams.resize(727, 578)
        self.centralwidget = QtWidgets.QWidget(PyCams)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.mdiArea = QtWidgets.QMdiArea(self.centralwidget)
        self.mdiArea.setObjectName("mdiArea")
        self.horizontalLayout.addWidget(self.mdiArea)
        PyCams.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(PyCams)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 727, 21))
        self.menubar.setObjectName("menubar")
        self.menuView = QtWidgets.QMenu(self.menubar)
        self.menuView.setObjectName("menuView")
        PyCams.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(PyCams)
        self.statusbar.setObjectName("statusbar")
        PyCams.setStatusBar(self.statusbar)
        self.actionCascade = QtWidgets.QAction(PyCams)
        self.actionCascade.setObjectName("actionCascade")
        self.actionTiled = QtWidgets.QAction(PyCams)
        self.actionTiled.setObjectName("actionTiled")
        self.actionSubwindow = QtWidgets.QAction(PyCams)
        self.actionSubwindow.setObjectName("actionSubwindow")
        self.actionTabbed = QtWidgets.QAction(PyCams)
        self.actionTabbed.setObjectName("actionTabbed")
        self.menuView.addAction(self.actionCascade)
        self.menuView.addAction(self.actionTiled)
        self.menuView.addAction(self.actionTabbed)
        self.menuView.addAction(self.actionSubwindow)
        self.menubar.addAction(self.menuView.menuAction())

        self.retranslateUi(PyCams)
        QtCore.QMetaObject.connectSlotsByName(PyCams)

    def retranslateUi(self, PyCams):
        _translate = QtCore.QCoreApplication.translate
        PyCams.setWindowTitle(_translate("PyCams", "PyCams"))
        self.menuView.setTitle(_translate("PyCams", "View"))
        self.actionCascade.setText(_translate("PyCams", "Cascade View"))
        self.actionTiled.setText(_translate("PyCams", "Tiled View"))
        self.actionSubwindow.setText(_translate("PyCams", "Subwindow View"))
        self.actionTabbed.setText(_translate("PyCams", "Tabbed View"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    PyCams = QtWidgets.QMainWindow()
    ui = Ui_PyCams()
    ui.setupUi(PyCams)
    PyCams.show()
    sys.exit(app.exec_())
