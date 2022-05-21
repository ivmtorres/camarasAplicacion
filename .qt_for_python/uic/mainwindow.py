# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.3.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QDateTimeEdit, QDial, QDoubleSpinBox,
    QLabel, QMainWindow, QMenu, QMenuBar,
    QPushButton, QScrollBar, QSizePolicy, QSlider,
    QStatusBar, QTabWidget, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(248, 597)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setTabletTracking(False)
        self.tabWidget.setTabPosition(QTabWidget.North)
        self.tabWidget.setTabShape(QTabWidget.Rounded)
        self.tabWidget.setTabsClosable(False)
        self.tabWidget.setTabBarAutoHide(False)
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.verticalSlider = QSlider(self.tab)
        self.verticalSlider.setObjectName(u"verticalSlider")
        self.verticalSlider.setGeometry(QRect(80, 150, 16, 160))
        self.verticalSlider.setOrientation(Qt.Vertical)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.verticalScrollBar = QScrollBar(self.tab_2)
        self.verticalScrollBar.setObjectName(u"verticalScrollBar")
        self.verticalScrollBar.setGeometry(QRect(100, 120, 16, 160))
        self.verticalScrollBar.setOrientation(Qt.Vertical)
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.dateTimeEdit = QDateTimeEdit(self.tab_3)
        self.dateTimeEdit.setObjectName(u"dateTimeEdit")
        self.dateTimeEdit.setGeometry(QRect(10, 190, 194, 25))
        self.tabWidget.addTab(self.tab_3, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.doubleSpinBox = QDoubleSpinBox(self.tab_4)
        self.doubleSpinBox.setObjectName(u"doubleSpinBox")
        self.doubleSpinBox.setGeometry(QRect(50, 170, 62, 25))
        self.tabWidget.addTab(self.tab_4, "")

        self.verticalLayout.addWidget(self.tabWidget)

        self.dial = QDial(self.centralwidget)
        self.dial.setObjectName(u"dial")

        self.verticalLayout.addWidget(self.dial)

        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.pushButton = QPushButton(self.centralwidget)
        self.pushButton.setObjectName(u"pushButton")

        self.verticalLayout.addWidget(self.pushButton)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 248, 21))
        self.menuAplicacion_para_pruebas = QMenu(self.menubar)
        self.menuAplicacion_para_pruebas.setObjectName(u"menuAplicacion_para_pruebas")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuAplicacion_para_pruebas.menuAction())

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(3)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), "")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), "")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), "")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), "")
        self.label.setText(QCoreApplication.translate("MainWindow", u"Esto es otra prueba", None))
        self.pushButton.setText(QCoreApplication.translate("MainWindow", u"Presionar boton", None))
        self.menuAplicacion_para_pruebas.setTitle(QCoreApplication.translate("MainWindow", u"Aplicacion para pruebas", None))
    # retranslateUi

