# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI_cam.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Cam(object):
    def setupUi(self, Cam):
        Cam.setObjectName("Cam")
        Cam.resize(310, 235)
        self.verticalLayout = QtWidgets.QVBoxLayout(Cam)
        self.verticalLayout.setContentsMargins(3, 3, 3, 3)
        self.verticalLayout.setSpacing(3)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.save_location_pushButton = QtWidgets.QPushButton(Cam)
        self.save_location_pushButton.setMaximumSize(QtCore.QSize(100, 16777215))
        self.save_location_pushButton.setObjectName("save_location_pushButton")
        self.horizontalLayout.addWidget(self.save_location_pushButton)
        self.save_location_label = QtWidgets.QLabel(Cam)
        self.save_location_label.setObjectName("save_location_label")
        self.horizontalLayout.addWidget(self.save_location_label)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.start_stop_pushButton = QtWidgets.QPushButton(Cam)
        self.start_stop_pushButton.setMinimumSize(QtCore.QSize(100, 0))
        self.start_stop_pushButton.setObjectName("start_stop_pushButton")
        self.horizontalLayout_2.addWidget(self.start_stop_pushButton)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.record_checkBox = QtWidgets.QCheckBox(Cam)
        self.record_checkBox.setObjectName("record_checkBox")
        self.horizontalLayout_2.addWidget(self.record_checkBox)
        self.trigger_checkBox = QtWidgets.QCheckBox(Cam)
        self.trigger_checkBox.setObjectName("trigger_checkBox")
        self.horizontalLayout_2.addWidget(self.trigger_checkBox)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.img_label = QtWidgets.QLabel(Cam)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.img_label.sizePolicy().hasHeightForWidth())
        self.img_label.setSizePolicy(sizePolicy)
        self.img_label.setText("")
        self.img_label.setObjectName("img_label")
        self.verticalLayout.addWidget(self.img_label)

        self.retranslateUi(Cam)
        QtCore.QMetaObject.connectSlotsByName(Cam)

    def retranslateUi(self, Cam):
        _translate = QtCore.QCoreApplication.translate
        Cam.setWindowTitle(_translate("Cam", "Cam"))
        self.save_location_pushButton.setText(_translate("Cam", "Save Location"))
        self.save_location_label.setText(_translate("Cam", "TextLabel"))
        self.start_stop_pushButton.setText(_translate("Cam", "Start"))
        self.record_checkBox.setText(_translate("Cam", "Record"))
        self.trigger_checkBox.setText(_translate("Cam", "Receive trigger"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Cam = QtWidgets.QWidget()
    ui = Ui_Cam()
    ui.setupUi(Cam)
    Cam.show()
    sys.exit(app.exec_())
