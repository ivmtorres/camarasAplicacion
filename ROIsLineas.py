#dibuja dos rois lineas 
#permite ajustar su tamaño rotarlas y desplazarlas
#esta prueba es parte del desarrollo de la aplicacion camaras
from asyncio.windows_events import NULL
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *
from PyQt5.QtGui import QPainter, QBrush, QColor
from PyQt5.QtCore import QPoint, QRect, QLine
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

class TestRecta(QLabel):
    #definimos la clase para dibujar las rectas
    def __init__(self):
        super().__init__()
        print("esta clase es la de recta")
        #punto de arranque
        self.begin = QPoint()
        self.end = QPoint()
        self.posTextRecta1 = QPoint()
        self.posTextRecta2 = QPoint()
        self.flag = True #habilita dibujar nuevas rois
        self.posAnteriorRecta1 = QPoint()
        self.posAnteriorRecta2 = QPoint()
        self.flagRecta1VsRecta2 = True #utilizamos este flag para determinar si estamos moviendot la recta 1 o la recta 2
        self.umbralLeft = QPoint(5,5) #uso este dato para difinir una zona donde se detecte el click sobre el vertice
        self.umbralRight = QPoint(5,5)
        self.clickBorde = False
        self.clickBordeLeftRecta1 = False
        self.clickBordeLeftRecta2 = False
        self.clickBordeRightRecta1 = False
        self.clickBordeRightRecta2 = False
        self.moviendoRecta1 = False
        self.moviendoRecta2 = False
    #sobre escribimos el metodo paint
    def paintEvent(self, event):
        super().paintEvent(event)
        #defino un objeto del tipo QPainter. Manejable a niver de graficos
        qp = QPainter(self)
        #defino un objeto del tipo QBrush. Manejable a nivel de colores
        br = QBrush(QColor(100, 10, 10, 40))
        #al objeto pintable le seteo un color definido con el objeto pintable
        qp.setBrush(br)
        #defino un ancho para la linea        
        pen = QtGui.QPen()
        #le defino un ancho de linea
        pen.setWidth(3)
        #le defino un color
        pen.setColor(QtGui.QColor("#00FF00"))
        #los atributos de antes los asigno al objeto pintable
        qp.setPen(pen)
        #dibujo las rectas
        qp.drawLine(self.parent().recta1)
        qp.drawText(self.posTextRecta1, "recta1")
        qp.drawLine(self.parent().recta2)
        qp.drawText(self.posTextRecta2, "redta2")
    
    def mousePressEvent(self, event):
        #obtengo la posicion donde se presiono el boton
        self.begin = event.pos()
        #determino si se esta presionando la esquina de la recta 1 - 2
        condicionClickBordeLeftRecta1Inf = (self.parent().recta1.p1() - self.umbralLeft).x()
        condicionClickBordeLeftRecta1Sup = (self.parent().recta1.p1() + self.umbralLeft).x()
        condicionClickBordeLeftRecta1 =  condicionClickBordeLeftRecta1Inf< self.begin.x() < condicionClickBordeLeftRecta1Sup
        condicionClickBordeLeftRecta2Inf = (self.parent().recta2.p1() - self.umbralLeft).x()
        condicionClickBordeLeftRecta2Sup = (self.parent().recta2.p1() + self.umbralLeft).x()
        condicionClickBordeLeftRecta2 =  condicionClickBordeLeftRecta2Inf< self.begin.x() <condicionClickBordeLeftRecta2Sup 
        condicionClickBordeRightRecta1Inf = (self.parent().recta1.p2() - self.umbralRight).x()
        condicionClickBordeRightRecta1Sup = (self.parent().recta1.p2() + self.umbralRight).x()
        condicionClickBordeRightRecta1 = condicionClickBordeRightRecta1Inf < self.begin.x() < condicionClickBordeRightRecta1Sup
        condicionClickBordeRightRecta2Inf = (self.parent().recta2.p2() - self.umbralRight).x()
        condicionClickBordeRightRecta2Sup= (self.parent().recta2.p2() + self.umbralRight).x()
        condicionClickBordeRightRecta2 = condicionClickBordeRightRecta2Inf < self.begin.x() < condicionClickBordeRightRecta2Sup
        #verifico si se esta haciendo un click en los bordes de las rectas
        if condicionClickBordeLeftRecta1 | condicionClickBordeLeftRecta2 |condicionClickBordeRightRecta1 | condicionClickBordeRightRecta2:
            self.clickBorde = True #indicamos que se realizo un click en uno de los bordes

            if condicionClickBordeLeftRecta1:
                print("click borde izquierdo recta 1")
                self.clickBordeLeftRecta1 = True
            elif condicionClickBordeLeftRecta2:
                print("click borde izquierdo recta 2")
                self.clickBordeLeftRecta2 = True
            elif condicionClickBordeRightRecta1:
                print("click borde derecho recta 1")
                self.clickBordeRightRecta1 = True        
            elif condicionClickBordeRightRecta2:
                print("click borde derecho recta 2")
                self.clickBordeRightRecta2 = True
            else:
                print("no se presiono ningun borde, no deberiamos estar aca")
        else: #no se presiono ningun borde y estamos dibujando una nueva recta
            #determino si el punto donde se hace click esta dentro de la recta
            if (not self.parent().recta1.isNull()) & (not self.parent().recta2.isNull()):
                
                valorInicialRecta1ZonaInf = (self.parent().recta1.p1().x() < self.begin.x() < self.parent().recta1.p2().x()) | (self.parent().recta1.p2().x()<self.begin.x()<self.parent().recta1.p1().x())
                valorFinalRecta1ZonaSup = (self.parent().recta1.p1().y() < self.begin.y() < self.parent().recta1.p2().y()) | (self.parent().recta1.p2().y()<self.begin.y()<self.parent().recta1.p1().y())
                condicionClickDentroRecta1XY =  valorInicialRecta1ZonaInf & valorFinalRecta1ZonaSup  
                pendienteRecta1 = abs(self.parent().recta1.p1().y() - self.parent().recta1.p2().y()) / abs(self.parent().recta1.p1().x() - self.parent().recta1.p2().x()) 
                pendienteRecta1PuntoClick = abs(self.parent().recta1.p1().y()-self.begin.y())/abs(self.parent().recta1.p1().x()-self.begin.x())
                condicionClickDentroRecta1Pendiente = pendienteRecta1 * 0.9 < pendienteRecta1PuntoClick < pendienteRecta1 * 1.1

                valorInicialRecta2ZonaInf = (self.parent().recta2.p1().x() < self.begin.x() < self.parent().recta2.p2().x()) | (self.parent().recta2.p2().x()<self.begin.x()<self.parent().recta2.p1().x())
                valorFinalRecta2ZonaSup = (self.parent().recta2.p1().y() < self.begin.y() < self.parent().recta2.p2().y()) | (self.parent().recta2.p2().y()<self.begin.y()<self.parent().recta2.p1().y())
                condicionClickDentroRecta2XY = valorInicialRecta2ZonaInf & valorFinalRecta2ZonaSup   
                pendienteRecta2 = abs(self.parent().recta2.p1().y() - self.parent().recta2.p2().y()) / abs(self.parent().recta2.p1().x() - self.parent().recta2.p2().x())
                pendienteRecta2PuntoClick = abs(self.parent().recta2.p1().y()-self.begin.y())/abs(self.parent().recta2.p1().x()-self.begin.x())
                condicionClickDentroRecta2Pendiente = pendienteRecta2 * 0.9 < pendienteRecta2PuntoClick < pendienteRecta2 * 1.1
                
                self.moviendoRecta1 = condicionClickDentroRecta1XY & condicionClickDentroRecta1Pendiente
                self.moviendoRecta2 = condicionClickDentroRecta2XY & condicionClickDentroRecta2Pendiente
                print(condicionClickDentroRecta2XY)
                print(condicionClickDentroRecta2Pendiente)
                if self.moviendoRecta1:
                #si estoy haciendo click entre los puntos extremos de la recta
                #pero ademas el punto esta sobre la recta va a tener la misma
                #pendiente
                #esto quiere decir que el punto es contenido por la recta
                #y vamos a mover la recta
                    self.flag = False
                    self.posAnteriorRecta1 = self.begin #guardo la posicion del click comola posicion antes de mover el mouse
                    if self.parent().indice == 0:
                        print("estoy haciendo un click para mover la recta 1")
                    else:
                        print("estoy haciendo un click para mover la recta 2")
                    self.flagRecta1VsRecta2 = True
                elif self.moviendoRecta2:
                    self.flag = False
                    self.posAnteriorRecta2 = self.begin
                    if self.parent().indice == 0:
                        print("estoy haciendo un click para mover la recta 1")
                    else:
                        print("estoy haciendo un click para mover la recta 2")
                    self.flagRecta1VsRecta2 = False
                else:
                    self.flag = True
            else:
                print("no tengo que estar aca")
        self.update()      

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        
        if self.clickBorde:
            print("reducir tamaño")
            if self.clickBordeLeftRecta1:
                self.parent().recta1.setP1(event.pos())
                self.posTextRecta1 = self.parent().recta1.p1()
            elif self.clickBordeLeftRecta2:
                self.parent().recta2.setP1(event.pos())
                self.posTextRecta2 = self.parent().recta2.p1()
            elif self.clickBordeRightRecta1:
                self.parent().recta1.setP2(event.pos())
            elif self.clickBordeRightRecta2:
                self.parent().recta2.setP2(event.pos())
            else:
                print("aca va la parte del borde inferior")
        else:
            if self.flag: #estoy arrastrando el mouse mientras dibujo una nueva recta
                if self.parent().indice == 0:
                    self.parent().recta1 = QLine(self.begin, self.end)
                    self.posTextRecta1 = self.begin
                else:
                    self.parent().recta2 = QLine(self.begin, self.end)
                    self.posTextRecta2 = self.begin
            else: #si estoy realizando un desplazamiento de la recta mientras muevo el mouse
                if self.moviendoRecta1 & self.flagRecta1VsRecta2:
                    #estoy moviendo la recta 1
                    desplazamientoXRecta1 = self.end.x() - self.posAnteriorRecta1.x()
                    desplazamientoYRecta1 = self.end.y() - self.posAnteriorRecta1.y()
                    print(desplazamientoXRecta1)
                    print(desplazamientoYRecta1)
                    self.parent().recta1.translate(desplazamientoXRecta1,desplazamientoYRecta1)
                    self.posTextRecta1 = self.parent().recta1.p1()
                    self.posAnteriorRecta1 = self.end
                    self.begin = self.end
                else: 
                    desplazamientoXRecta2 = self.end.x() - self.posAnteriorRecta2.x()
                    desplazamientoYRecta2 = self.end.y() - self.posAnteriorRecta2.y()
                    self.parent().recta2.translate(desplazamientoXRecta2, desplazamientoYRecta2)
                    self.posTextRecta2 = self.parent().recta2.p1()
                    self.posAnteriorRecta2 = self.end
                    self.begin = self.end
        self.update()
                     
    def mouseReleaseEvent(self, event):
        self.end = event.pos()
        if self.clickBorde:
            print("fin ajuste tamaño")
            self.clickBorde = False
            self.clickBordeLeftRecta1 = False
            self.clickBordeLeftRecta2 = False
            self.clickBordeRightRecta1 = False
            self.clickBordeRightRecta2 = False
        else:
            print(self.begin, self.end)
            if self.flag:
                if self.parent().indice == 0:
                    self.parent().recta1 = QLine(self.begin,self.end)
                    self.posTextRecta1 = self.begin
                    self.parent().indice = 1
                else:
                    self.parent().recta2 = QLine(self.begin,self.end)
                    self.parent().indice = 0
                    self.posTextRecta2 = self.begin
        self.update()

class VideoThread(QThread):
    #este hilo maneja la adquisicion desde la camara
    change_pixmap_signal = pyqtSignal(np.ndarray)
    def __init__(self):
        #usamos un flag para determinar si debe seguir
        #adquiriendo desde la camara o no
        super().__init__()
        self._run_flag = True
    def run(self):
        #capturamos desde la webcam
        cap = cv2.VideoCapture(0)
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret: #si se retorna una imagen sin error emitimos un evento para la carga del hilo
                self.change_pixmap_signal.emit(cv_img)
        #si salimos del while entonces liberamos el recurso
        cap.release()
    def stop(self):
        #indicamos poniendo a false el flag para detener la adquisicion
        self._run_flag = False
        self.wait()

class App(QWidget):
    #creo la clase para manejar la adquisicion
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt CV Show Video Camera with Rules")
        self.display_width = 640
        self.display_height = 480
        #lista de rectas
        self.begin = QPoint()
        self.end = QPoint()
        self.recta1 = QLine(self.begin, self.end)
        self.recta2 = QLine(self.begin, self.end)
        self.listaRecta = [self.recta1, self.recta2]
        self.indice = 0
        #creamos el label donde vamos a representar la imagne y las rois
        self.image = TestRecta()

        #creamos una etiqueta para el nombre de la imagen
        self.textLabel = QLabel("Web Cam")

        #creamos un layout vertical
        vbox = QVBoxLayout()
        #agregamos el widget
        vbox.addWidget(self.image)
        vbox.addWidget(self.textLabel)
        #asiganmos el layout al cuerpo del objeto
        self.setLayout(vbox)

        #tenemos que crear un hilo para que la navegacion no interrumpa la adquisicion
        self.thread = VideoThread()
        #conectamos el hilo con la funcion que actualiza la imagen utilizando emmit
        self.thread.change_pixmap_signal.connect(self.update_image)
        #arrancamos el procesamiento en el hilo
        self.thread.start()
    
    def closeEvent(self, event):
        self.thread.stop()
        event.accept()
    #le indico que va a manejar un slot de hilo    
    @pyqtSlot(np.ndarray) 
    def update_image(self, cv_img):
        #convierto el dato emitido en formato opencv
        #a formato qt
        qt_img = self.convert_cv_qt(cv_img)
        #asigno la imagen convertida al label del tipo recta
        self.image.setPixmap(qt_img)
    
    def convert_cv_qt(self, cv_img):
        #convertimos la imagen de openCV BGR a RGB
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        #convertimos al formato de Qt
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.display_width,self.display_height,Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec_())