from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *
from PyQt5.QtGui import QPainter, QBrush, QColor, QPalette
from PyQt5.QtCore import QPoint, QRect
import os
import sys
import time
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QSize
import numpy as np



class TestImage(QLabel):
    
    def __init__(self):
        super().__init__()
        self.scaleFactor = 1
        self.scala = 1.25#0.8

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value() + ((factor - 1) * scrollBar.pageStep()/2)))

    def paintEvent(self, event):
        super().paintEvent(event)
        
        try:
            escala = self.scaleFactor * self.pixmap().size()
            print(escala)        
            self.resize(escala)        
        except:
            print("error image")

    def mousePressEvent(self, event):
        self.begin = event.pos()
        print("mouse click", self.scaleFactor)
        self.scaleFactor *= self.scala#1.25
        #self.scala = self.parent().zoomInOut
class VideoThread(QThread):
    
    change_pixmap_signal = pyqtSignal(np.ndarray)
    def __init__(self):
        super().__init__()
        self._run_flag = True

    def run(self):
        # capture from web cam
                
        cap = cv2.VideoCapture(0)
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret:
                self.change_pixmap_signal.emit(cv_img)
        # shut down capture system
        cap.release()

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()
 

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QT live ZOOM IN OUT")        
        #
        self.escala = QSize()
        self.display_width = 1000
        self.display_height = 800
        #
        
        self.image = TestImage()
        self.textLabel = QLabel("WebCam")
        #
        self.zoomInEscala = 1.25
        self.zoomOutEscala = 0.8
        self.zoomInOut = 1
        #
        self.image.setBackgroundRole(QPalette.Base)
        self.image.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image.setScaledContents(True)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.image)
        self.scrollArea.setVisible(True)
        #
        self.zoomInButton = QPushButton('Zoom In', self)
        self.zoomInButton.clicked.connect(self.onZoomIn)
        
                
        #
        self.zoomOutButton = QPushButton('Zoom Out', self)
        self.zoomOutButton.clicked.connect(self.onZoomOut)
       
        
        #
        hbox = QHBoxLayout()
        hbox.addWidget(self.zoomInButton)
        hbox.addWidget(self.zoomOutButton)
        #
        vbox = QVBoxLayout()
        vbox.addWidget(self.scrollArea)
        vbox.addWidget(self.textLabel)
        #
        vbox.addLayout(hbox)
        #
        self.setLayout(vbox)
        #
        self.thread = VideoThread()
        #
        self.thread.change_pixmap_signal.connect(self.update_image)
        #
        self.thread.start()

    def onZoomIn(self):
        self.image.scala = 1.25

    def onZoomOut(self):
        self.image.scala = 0.8

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        qt_img = self.convert_cv_qt(cv_img)        
        self.image.setPixmap(qt_img)
        
    def convert_cv_qt(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.display_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = App()
    a.resize(1000,800)
    a.show()
    sys.exit(app.exec())
