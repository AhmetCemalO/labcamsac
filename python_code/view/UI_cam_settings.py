# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI_cam_settings.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Settings(object):
    def setupUi(self, Settings):
        Settings.setObjectName("Settings")
        Settings.resize(185, 104)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Settings.sizePolicy().hasHeightForWidth())
        Settings.setSizePolicy(sizePolicy)
        Settings.setMaximumSize(QtCore.QSize(16777215, 105))
        self.verticalLayout = QtWidgets.QVBoxLayout(Settings)
        self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.verticalLayout.setContentsMargins(3, 3, 3, 3)
        self.verticalLayout.setSpacing(3)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_4 = QtWidgets.QLabel(Settings)
        self.label_4.setMinimumSize(QtCore.QSize(76, 0))
        self.label_4.setMaximumSize(QtCore.QSize(16777215, 20))
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_4.addWidget(self.label_4)
        self.framerate_lineEdit = QtWidgets.QLineEdit(Settings)
        self.framerate_lineEdit.setMaximumSize(QtCore.QSize(16777215, 20))
        self.framerate_lineEdit.setObjectName("framerate_lineEdit")
        self.horizontalLayout_4.addWidget(self.framerate_lineEdit)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(Settings)
        self.label.setMinimumSize(QtCore.QSize(76, 0))
        self.label.setMaximumSize(QtCore.QSize(16777215, 20))
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.exposure_lineEdit = QtWidgets.QLineEdit(Settings)
        self.exposure_lineEdit.setMaximumSize(QtCore.QSize(16777215, 20))
        self.exposure_lineEdit.setObjectName("exposure_lineEdit")
        self.horizontalLayout.addWidget(self.exposure_lineEdit)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.autogain_checkBox = QtWidgets.QCheckBox(Settings)
        self.autogain_checkBox.setMaximumSize(QtCore.QSize(16777215, 17))
        self.autogain_checkBox.setObjectName("autogain_checkBox")
        self.horizontalLayout_3.addWidget(self.autogain_checkBox)
        self.label_2 = QtWidgets.QLabel(Settings)
        self.label_2.setMaximumSize(QtCore.QSize(16777215, 20))
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_3.addWidget(self.label_2)
        self.gain_lineEdit = QtWidgets.QLineEdit(Settings)
        self.gain_lineEdit.setMaximumSize(QtCore.QSize(16777215, 20))
        self.gain_lineEdit.setObjectName("gain_lineEdit")
        self.horizontalLayout_3.addWidget(self.gain_lineEdit)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.apply_pushButton = QtWidgets.QPushButton(Settings)
        self.apply_pushButton.setEnabled(True)
        self.apply_pushButton.setMaximumSize(QtCore.QSize(16777215, 23))
        self.apply_pushButton.setObjectName("apply_pushButton")
        self.verticalLayout.addWidget(self.apply_pushButton)

        self.retranslateUi(Settings)
        QtCore.QMetaObject.connectSlotsByName(Settings)

    def retranslateUi(self, Settings):
        _translate = QtCore.QCoreApplication.translate
        Settings.setWindowTitle(_translate("Settings", "Camera Settings"))
        Settings.setToolTip(_translate("Settings", "Allows to check/set the most commonly used camera settings"))
        self.label_4.setText(_translate("Settings", "Framerate (fps)"))
        self.label.setText(_translate("Settings", "Exposure (ms)"))
        self.autogain_checkBox.setText(_translate("Settings", "AutoGain"))
        self.label_2.setText(_translate("Settings", "Gain (dB)"))
        self.apply_pushButton.setText(_translate("Settings", "Apply"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Settings = QtWidgets.QWidget()
    ui = Ui_Settings()
    ui.setupUi(Settings)
    Settings.show()
    sys.exit(app.exec_())
