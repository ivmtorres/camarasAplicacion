#dibuja dos rois rectangulares intercambiando una u otra
#permite desplazarlas y ajustar su tamaño 
#esta prueba es parte de la aplicacion para las cámaras su objetivo es agregar esta funcionalidad 
#en el toolbar de cada imagen para dibujar rectangulos
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *
from PyQt5.QtGui import QPainter,QBrush, QColor
from PyQt5.QtCore import QPoint, QRect
import os
import sys
import time
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
import numpy as np

class TestRect(QLabel):
    def __init__(self):
        super().__init__()
        self.begin = QPoint()
        self.end = QPoint()
        self.posTextRect1 = QPoint()
        self.posTextRect2 = QPoint()
        self.flag = True #habilita dibujar nuevas rois
        self.posAnteriorRect1=QPoint()
        self.posAnteriorRect2=QPoint()
        self.flagRec1VsRec2 = True #utiizamos este flag para determinar si estamos moviendo el rectangulo 1 o el 2
        self.umbralTopLeft = QPoint(5,5)
        self.umbralBottomRight = QPoint(5,5)
        self.clickBorde = False
        self.clickBordeTopLeftRec1 = False
        self.clickBordeTopLeftRec2 = False
        self.clickBordeBottomRightRect1 = False
        self.clickBordeBottomRightRect2 = False

    def paintEvent(self,event):
        super().paintEvent(event)
        qp = QPainter(self)
        br = QBrush(QColor(100, 10, 10, 40))
        qp.setBrush(br)
        pen  = QtGui.QPen()
        pen.setWidth(3)
        pen.setColor(QtGui.QColor("#00FF00")) #"#EB5160"
        qp.setPen(pen)
        
        #qp.drawRect(QRect(self.begin, self.end))
        qp.drawRect(self.parent().rectangulo1)
        qp.drawText(self.posTextRect1,"rect1")
        qp.drawRect(self.parent().rectangulo2)
        qp.drawText(self.posTextRect2,"rect2")
        
    def mousePressEvent(self, event):
        self.begin = event.pos()
        detectoCondicionClickBordeTopLeftRect1Inf = (self.parent().rectangulo1.topLeft() - self.umbralTopLeft).x() 
        detectoCondicionClickBordeTopLeftRect1Sup = (self.parent().rectangulo1.topLeft() + self.umbralTopLeft).x()
        condicionClickBordeTopLeftRect1 = detectoCondicionClickBordeTopLeftRect1Inf < self.begin.x() < detectoCondicionClickBordeTopLeftRect1Sup 
        
        detectoCondicionClickBordeTopLeftRect2Inf = (self.parent().rectangulo2.topLeft() - self.umbralTopLeft).x()
        detectoCondicionClickBordeTopLeftRect2Sup = (self.parent().rectangulo2.topLeft() + self.umbralTopLeft).x()
        condicionClickBordeTopLeftRect2 = detectoCondicionClickBordeTopLeftRect2Inf < self.begin.x() < detectoCondicionClickBordeTopLeftRect2Sup

        detectoCondicionClickBordeBottomRightRect1Inf = (self.parent().rectangulo1.bottomRight() - self.umbralBottomRight).x()
        detectoCondicionClickBordeBottomRightRect1Sup = (self.parent().rectangulo1.bottomRight() + self.umbralBottomRight).x()
        condicionClickBordeBottomRightRect1 = detectoCondicionClickBordeBottomRightRect1Inf < self.begin.x() < detectoCondicionClickBordeBottomRightRect1Sup
        
        detectoCondicionClickBordeBottomRightRect2Inf = (self.parent().rectangulo2.bottomRight() - self.umbralBottomRight).x()
        detectoCondicionClickBordeBottomRightRect2Sup = (self.parent().rectangulo2.bottomRight() + self.umbralBottomRight).x()
        condicionClickBordeBottomRightRect2 = detectoCondicionClickBordeBottomRightRect2Inf < self.begin.x() < detectoCondicionClickBordeBottomRightRect2Sup
        
        if condicionClickBordeTopLeftRect1 | condicionClickBordeTopLeftRect2 | condicionClickBordeBottomRightRect1 | condicionClickBordeBottomRightRect2:
            self.clickBorde = True
            
            if condicionClickBordeTopLeftRect1:
                print( "click borde superior rect 1")
                self.clickBordeTopLeftRec1 = True
                self.clickBordeTopLeftRec2 = False
            elif condicionClickBordeTopLeftRect2:
                print("click borde superior rect 2")
                self.clickBordeTopLeftRec1 = False
                self.clickBordeTopLeftRec2 = True
            elif condicionClickBordeBottomRightRect1:
                print("click borde inferior rect 1")
                self.clickBordeBottomRightRect1 = True
                self.clickBordeBottomRightRect2 = False
            elif condicionClickBordeBottomRightRect2:
                print("click borde inferior rect 2")
                self.clickBordeBottomRightRect1 = False
                self.clickBordeBottomRightRect2 = True
            else:
                print("no se presiono ningun borde, no deberias estar aca!")
        else:
            if self.parent().rectangulo1.contains(self.begin,False):
                self.flag = False
                self.posAnteriorRect1 = self.begin #guardo la posicion del click como la posicion antes de mover el mouse
                if self.parent().indice == 0: 
                   print("estoy haciendo un click para dibujar el rectangulo 1")
                else:
                    print("estoy haciendo un click para dibujar el rectangulo 2")
                self.flagRec1VsRec2 = True
            elif self.parent().rectangulo2.contains(self.begin,False):
                self.flag = False
                self.posAnteriorRect2 = self.begin #guardo la posicion del click como la posicion antes de mover el mouse
                if self.parent().indice == 0: 
                    print("estoy haciendo un click para dibujar el rectangulo 1")
                else:
                    print("estoy haciendo un click para dibujar el rectangulo 2")
                self.flagRec1VsRec2 = False
            else:
                self.flag = True



        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        print(self.end)
        if self.clickBorde:
            print("reducir tama;o")
            if self.clickBordeTopLeftRec1:
                self.parent().rectangulo1.setTopLeft(event.pos())
                self.posTextRect1 = self.parent().rectangulo1.topLeft()
            elif self.clickBordeTopLeftRec2:
                self.parent().rectangulo2.setTopLeft(event.pos())
                self.posTextRect2 = self.parent().rectangulo2.topLeft()
            elif self.clickBordeBottomRightRect1:
                self.parent().rectangulo1.setBottomRight(event.pos())
            elif self.clickBordeBottomRightRect2:
                self.parent().rectangulo2.setBottomRight(event.pos())
            else:
                print("aca va la parte del borde inferior")
                
        else:            
            if self.flag:#estoy arrastando el mouse mientras dibujo una nueva roi
                if self.parent().indice == 0:
                    self.parent().rectangulo1 = QRect(self.begin, self.end)
                    self.posTextRect1 = self.begin
                else:
                    self.parent().rectangulo2 = QRect(self.begin, self.end)
                    self.posTextRect2 = self.begin
            else:#si estoy realizando un desplazamiento del rectangulo mientras muevo el mouse
                if self.parent().rectangulo1.contains(self.begin,False) & self.flagRec1VsRec2: #estoy dentro del rectangulo 1
                    #calculo la distancia entre el punto x-y y el punto clickeado dentro del rectangulo
                    #print(self.end.x(),self.end.y())
                    desplazamientoXRect1 = self.end.x() - self.posAnteriorRect1.x()
                    desplazamientoYRect1 = self.end.y() - self.posAnteriorRect1.y()                
                    self.parent().rectangulo1.translate(desplazamientoXRect1,desplazamientoYRect1)
                    self.posTextRect1 = self.parent().rectangulo1.topLeft()
                    self.posAnteriorRect1 = self.end
                    self.begin = self.end
                else:
                    desplazamientoXRect2 = self.end.x() - self.posAnteriorRect2.x()
                    desplazamientoYRect2 = self.end.y() - self.posAnteriorRect2.y()
                    self.parent().rectangulo2.translate(desplazamientoXRect2,desplazamientoYRect2)
                    self.posTextRect2 = self.parent().rectangulo2.topLeft()
                    self.posAnteriorRect2 = self.end
                    self.begin = self.end
                
        self.update()

    def mouseReleaseEvent(self, event):
        self.end = event.pos()
        if self.clickBorde:
            print("fin ajuste tama;o")
            self.clickBorde = False
            self.clickBordeTopLeftRec1 = False
            self.clickBordeTopLeftRec2 = False
            self.clickBordeBottomRightRect1 = False
            self.clickBordeBottomRightRect2 = False
        else:
            print(self.begin,self.end)
            if self.flag:
                if self.parent().indice == 0:
                    self.parent().rectangulo1 = QRect(self.begin, self.end)
                    self.posTextRect1=self.begin
                    self.parent().indice = 1
                else:
                    self.parent().rectangulo2 = QRect(self.begin, self.end)
                    self.parent().indice = 0
                    self.posTextRect2=self.begin

        self.update()



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
        self.setWindowTitle("Qt live label demo")
        self.disply_width = 640
        self.display_height = 480
        #lista de rectangulos
        self.begin = QPoint()
        self.end = QPoint()
        self.rectangulo1 = QRect(self.begin,self.end)
        self.rectangulo2 = QRect(self.begin,self.end)
        self.listaRect = [self.rectangulo1,self.rectangulo2]
        self.indice = 0
        # create the label that holds the image
        #self.image_label = QLabel(self)
        #self.image_label.resize(self.disply_width, self.display_height)
        self.image = TestRect()
        # create a text label
        self.textLabel = QLabel('Webcam')

        # create a vertical box layout and add the two labels
        vbox = QVBoxLayout()
        #vbox.addWidget(self.image_label)
        vbox.addWidget(self.image)
        vbox.addWidget(self.textLabel)
        # set the vbox layout as the widgets layout
        self.setLayout(vbox)

        # create the video capture thread
        self.thread = VideoThread()
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()



    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        #self.image_label.setPixmap(qt_img)
        self.image.setPixmap(qt_img)
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)
    
if __name__=="__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec_())