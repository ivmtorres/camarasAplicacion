#dibujar dos rois tipo elipse
#permite ajustar su tamaño rotarlas y desplazarlas
#Nota = Tenemos problemas para girar la elipse presionando los botones flecha arriba y flecha abajo
#vamos a volver a trabajarlo mas en el futuro
#esta pruebas es parte del desarrollo de la aplicacion

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *
from PyQt5.QtGui import QPainter, QBrush, QColor
from PyQt5.QtCore import QPoint, QRect, QLine, QRectF,QPointF
import os
import sys
import time
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from cv2 import VideoCapture
import numpy as np

#tengo que crear una clase para crear objetos elipses
class TestEllipse(QLabel):
    def __init__(self):
        super().__init__()
        self.begin = QPoint()
        self.end = QPoint()
        self.posTextEllipse1 = QPoint()
        self.posTextEllipse2 = QPoint()
        self.flag = True #habilita dibujar nuevas rois
        self.posAnteriorRectEllipse1 = QPoint()
        self.posAnteriorRectEllipse2 = QPoint()
        self.flagRectEllipse1VsRectEllipse2 = True #utilizamos este flag para determinar si estamos moviendo la ellipse 1 o el 2
        self.umbralLeft = QPoint(5,5) #usamos para ajustar la parte superior de la ellipse
        self.umbralRight = QPoint(5,5) #usamos para ajustar la parte derecha de la ellipse
        self.umbralTop = QPoint(5,5)
        self.umbralBottom = QPoint(5,5)
        self.clickBorde = False
        self.clickBordeLeftRectEllipse1 = False #indicamos que queremos estirar o contraer del lado superior la ellipse 1
        self.clickBordeLeftRectEllipse2 = False #indicamos que queremos estirar o contraer del lado superior la ellipse 2
        self.clickBordeRightRectEllipse1 = False #indicamos que queremos estirar o contraer del lado lateral derecho la ellipse 1
        self.clickBordeRightRectEllipse2 = False #indicamos que queremos estirar o contraer del lado lateral derecho la ellipse 2
        self.clickBordeTopRectEllipse1 = False
        self.clickBordeTopRectEllipse2 = False
        self.clickBordeBottomRectEllipse1 = False
        self.clickBordeBottomRectEllipse2 = False
    #sobrecargo el metodo para graficar
    def paintEvent(self, event):
        super().paintEvent(event)
        #defino el color de reyeno
        qp = QPainter(self)
        br = QBrush(QColor(100, 10, 10, 40))
        qp.setBrush(br) 
        #defino el tipo de linea
        pen = QtGui.QPen()
        pen.setWidth(3)
        pen.setColor(QtGui.QColor("#00FF00"))
        qp.setPen(pen)        
        presionEnEllipse1 = (self.parent().presionTeclaEnEllipse1Flag & (self.parent().teclaUpGirarEllipse1 | self.parent().teclaDownGirarEllipse1))
        presionEnEllipse2 = (self.parent().presionTeclaEnEllipse2Flag & (self.parent().teclaUpGirarEllipse2 | self.parent().teclaDownGirarEllipse2))
        if presionEnEllipse1 | presionEnEllipse2 :
            if self.parent().presionTeclaEnEllipse1Flag:
                if self.parent().teclaUpGirarEllipse1:
                    self.parent().anguloEllipse1 = self.parent().ellipse1.rotation() + 1 * self.parent().clickEllipse1
                    print("girando derecha Ellipse 1") 
                    #roto la elipse 1                    
                    qp.rotate(self.parent().anguloEllipse1)                    
                    #dibujo las ellipses
                    qp.drawEllipse(self.parent().rectanguloEllipse1)
                    qp.drawText(self.posTextEllipse1, "Ellipse1")                  
                    #restauro
                    qp.resetTransform()
                    #dibujo las ellipses
                    qp.drawEllipse(self.parent().rectanguloEllipse2)
                    qp.drawText(self.posTextEllipse2, "Ellipse2")                                        
                  
                    print(self.parent().ellipse1.rect())
                    self.parent().teclaDownGirarEllipse1 = False
                    self.parent().teclaUpGirarEllipse2 = False
                    self.parent().teclaDownGirarEllipse2 = False                     

                elif self.parent().teclaDownGirarEllipse1:
                    self.parent().anguloEllipse1 = self.parent().ellipse1.rotation() + 1 * self.parent().clickEllipse1 
                    print("girando izquierda Ellipse 1")
                    #self.parent().ellipse1.setTransform(transform)
                    qp.drawEllipse(self.parent().rectanguloEllipse2)
                    qp.drawText(self.posTextEllipse2, "Ellipse2")
                    qp.rotate(self.parent().anguloEllipse1)
                    #dibujo las ellipses                                        
                    qp.drawEllipse(self.parent().rectanguloEllipse1)        
                    qp.drawText(self.posTextEllipse1, "Ellipse1")
                    #dibujo las ellipses
                    self.parent().teclaUpGirarEllipse1 = False                    
                    self.parent().teclaUpGirarEllipse2 = False
                    self.parent().teclaDownGirarEllipse2 = False
                else:
                    #print("aca no deberiamos estar ellips 1")        
                    pass      
            if self.parent().presionTeclaEnEllipse2Flag:
                if self.parent().teclaUpGirarEllipse2:
                    self.parent().anguloEllipse2 = self.parent().ellipse2.rotation() + 1 * self.parent().clickEllipse2
                    print("girando derecha Ellipse 2")
                    #self.parent().ellipse2.setTransform(transform)                                        
                    qp.drawEllipse(self.parent().rectanguloEllipse1)        
                    qp.drawText(self.posTextEllipse1, "Ellipse1")                                                        
                    #roto la elipse 1                    
                    qp.rotate(self.parent().anguloEllipse2)                    
                    #dibujo las ellipses
                    #dibujo las ellipses  
                    qp.drawEllipse(self.parent().rectanguloEllipse2)
                    qp.drawText(self.posTextEllipse2, "Ellipse2")                    
                    self.parent().teclaUpGirarEllipse1 = False
                    self.parent().teclaDownGirarEllipse1 = False                    
                    self.parent().teclaDownGirarEllipse2 = False
                elif self.parent().teclaDownGirarEllipse2:
                    self.parent().anguloEllipse2 = self.parent().ellipse2.rotation() + 1 * self.parent().clickEllipse2
                    print("girando izquierda Ellipse 2")
                    #self.parent().ellipse2.setTransform(transform)
                    #self.parent().ellipse1.setTransform(transform)
                    #dibujo las ellipses                    
                    qp.drawEllipse(self.parent().rectanguloEllipse1)
                    qp.drawText(self.posTextEllipse1, "Ellipse1")
                    qp.rotate(self.parent().anguloEllipse2)
                    #dibujo las ellipses                    
                    qp.drawEllipse(self.parent().rectanguloEllipse2)        
                    qp.drawText(self.posTextEllipse2, "Ellipse2")                     
                    self.parent().teclaUpGirarEllipse1 = False
                    self.parent().teclaDownGirarEllipse1 = False
                    self.parent().teclaUpGirarEllipse2 = False                    
                else:
                    #print("aca no deberiamos estar ellipse 2")
                    pass            
        else:
            #pass
            #dibujo las ellipses            
            qp.rotate(self.parent().anguloEllipse1)
            qp.drawEllipse(self.parent().rectanguloEllipse1)        
            qp.drawText(self.posTextEllipse1, "Ellipse1")                   
            qp.resetTransform()
            #dibujo las ellipses
            qp.rotate(self.parent().anguloEllipse2)                          
            qp.drawEllipse(self.parent().rectanguloEllipse2)
            qp.drawText(self.posTextEllipse2, "Ellipse2")            
            #deshabilito los flags de las teclas presionadas 
            #si se dejo de presionar sobre alguna ellipse
            self.parent().teclaUpGirarEllipse1 = False
            self.parent().teclaDownGirarEllipse1 = False
            self.parent().teclaUpGirarEllipse2 = False
            self.parent().teclaDownGirarEllipse2 = False        
    #sobrecargo el metodo de deteccion del evento click del mouse    
    def mousePressEvent(self, event):
        #detecto posicion si no aprete las teclas de girar bajar
        self.begin = event.pos()
        ptoX = self.begin.x()
        ptoY = self.begin.y()
        print(self.begin)
        #condicion de borde izquierdo - derecho
        condicionClickBordeLeftRectEllipse1 = (int(self.parent().ellipse1.rect().left()) - self.umbralLeft.x()) < self.begin.x() < (int(self.parent().ellipse1.rect().left()) + self.umbralLeft.x())
        condicionClickBordeLeftRectEllipse2 = (int(self.parent().ellipse2.rect().left()) - self.umbralLeft.x()) < self.begin.x() < (int(self.parent().ellipse2.rect().left()) + self.umbralLeft.x())
        condicionClickBordeRightRectEllipse1 = (int(self.parent().ellipse1.rect().right()) - self.umbralRight.x()) < self.begin.x() < (int(self.parent().ellipse1.rect().right()) + self.umbralRight.x())
        condicionClickBordeRightRectEllipse2 = (int(self.parent().ellipse2.rect().right()) - self.umbralRight.x()) < self.begin.x() < (int(self.parent().ellipse2.rect().right()) + self.umbralRight.x())
        #condicion de borde superior - inferior
        condicionClickBordeTopRectEllipse1 = (int(self.parent().ellipse1.rect().top()) - self.umbralTop.y()) < self.begin.y() < (int(self.parent().ellipse1.rect().top()) + self.umbralTop.y())
        condicionClickBordeTopRectEllipse2 = (int(self.parent().ellipse2.rect().top()) - self.umbralTop.y()) < self.begin.y() < (int(self.parent().ellipse2.rect().top()) + self.umbralTop.y())
        condicionClickBordeBottomRectEllipse1 = (int(self.parent().ellipse1.rect().bottom()) - self.umbralBottom.y()) < self.begin.y() < (int(self.parent().ellipse1.rect().bottom()) + self.umbralBottom.y())
        condicionClickBordeBottomRectEllipse2 = (int(self.parent().ellipse2.rect().bottom()) - self.umbralBottom.y()) < self.begin.y() < (int(self.parent().ellipse2.rect().bottom()) + self.umbralBottom.y())
        
        #verifico la condicion de click en el borde superior o derecho
        if condicionClickBordeLeftRectEllipse1 | condicionClickBordeLeftRectEllipse2 | condicionClickBordeRightRectEllipse1 | condicionClickBordeRightRectEllipse2 | condicionClickBordeTopRectEllipse1 | condicionClickBordeTopRectEllipse2 | condicionClickBordeBottomRectEllipse1 | condicionClickBordeBottomRectEllipse2:
            #si se realizo un click en el borde
            self.clickBorde = True
            #esto esta mal realizado pero por motivos de clarificar el codigo lo hacemos asi
            self.clickBordeLeftRectEllipse1 = False
            self.clickBordeLeftRectEllipse2 = False
            self.clickBordeRightRectEllipse1 = False
            self.clickBordeRightRectEllipse2 = False
            self.clickBordeTopRectEllipse1 = False
            self.clickBordeTopRectEllipse2 = False
            self.clickBordeBottomRectEllipse1 = False
            self.clickBordeBottomRectEllipse2 = False  
            if condicionClickBordeLeftRectEllipse1: #detecto el borde izquierdo ellipse 1
                print("click borde superior rect ellipse 1")
                self.clickBordeLeftRectEllipse1 = True                  
            elif condicionClickBordeLeftRectEllipse2: #detecto el borde izquierdo ellipse 2
                print("click borde superior rect ellipse 2")                
                self.clickBordeLeftRectEllipse2 = True                            
            elif condicionClickBordeRightRectEllipse1: #detecto el borde derecho ellipse 1
                print("click borde derecho rect ellipse 1")                
                self.clickBordeRightRectEllipse1 = True                
            elif condicionClickBordeRightRectEllipse2: #detecto el borde derecho ellipse 2
                print("click borde derecho rect ellipse 2")                
                self.clickBordeRightRectEllipse2 = True                
            elif condicionClickBordeTopRectEllipse1: #detecto el borde superior ellipse 1
                print("click borde top rect ellipse 1")                
                self.clickBordeTopRectEllipse1 = True                
            elif condicionClickBordeTopRectEllipse2: #detecto el borde superior ellipse 2
                print("click borde top rect ellipse 2")                
                self.clickBordeTopRectEllipse2 = True                
            elif condicionClickBordeBottomRectEllipse1: #detecto el borde inferior ellipse 1
                print("click borde bottom rect ellipse 1")                
                self.clickBordeBottomRectEllipse1 = True
            elif condicionClickBordeBottomRectEllipse2: #detecto el borde inferior ellipse 2
                print("click borde bottom rect ellipse 2")                
                self.clickBordeBottomRectEllipse2 = True            
            else:
                print("no se presiono ningun borde, no deberias estar aca!")
        #no es un click en el borde entonces hay dos opciones 
        #se esta gaficando una nueva ellipse o se esta intentando
        #desplazar la ellipse existente

        else: #click dentro de ellipse o fuera de ellipse pero no en ningun borde
            #estoy haciendo un click dentro de la ellipse 1
            if self.parent().rectanguloEllipse1.contains(ptoX,ptoY): 
                #Marco que se presiono el mouse sobre una ellipse
                self.parent().presionTeclaEnEllipse1Flag = True
                self.parent().presionTeclaEnEllipse2Flag = False
                #detecto que se esta intentando mover la elipse 1
                self.flag = False
                self.posAnteriorRectEllipse1 = self.begin #guardo la posicion anterior
                if self.parent().indice == 0:
                    print("Click Elipse 1 estoy haciendo un click para dibujar el rectangulo ellipse 1")
                else:
                    print("Click Elipse 1 estoy haciendo un click para dibujar el rectangulo ellipse 2")
                self.flagRectEllipse1VsRectEllipse2 = True
            #estoy haciendo un click dentro de la ellipse 2
            elif self.parent().rectanguloEllipse2.contains(ptoX,ptoY): 
                #Marco que se presiono el mouse sobre una ellipse
                self.parent().presionReclaEnEllipse1Flag = False
                self.parent().presionTeclaEnEllipse2Flag = True            
                self.flag = False
                self.posAnteriorRectEllipse2 = self.begin #guardo la posicion anterior 
                if self.parent().indice == 0:
                    print("Click Elipse 2 estoy haciendo un clikc para dibujar el rectangulo ellipse 1")
                else:
                    print("Click Elipse 2 estoy haciendo un clikc para dibujar el rectangulo ellipse 2")
                self.flagRectEllipse1VsRectEllipse2 = False
            else: #No estoy haciendo un click dentro de ninguna ellipse sino fuera para dibujar una nueva ellipse
                self.flag = True
                 #pongo en false tecla girar        
                self.parent().presionTeclaEnEllipse2Flag = False
                self.parent().presionTeclaEnEllipse1Flag = False

        self.update()
    def mouseMoveEvent(self, event):
        #capturo el movimiento
        self.end = event.pos()
        ptoX = self.end.x()
        ptoY = self.end.y()
        print(self.end)
        rect1TopLeft = self.parent().rectanguloEllipse1.topLeft()
        rect1BotRight = self.parent().rectanguloEllipse1.bottomRight()
        rect2TopLeft = self.parent().rectanguloEllipse2.topLeft()
        rect2BotRight = self.parent().rectanguloEllipse2.bottomRight()
        #verfico si previamente se hiso un click en el borde
        if self.clickBorde:
            print("reducir tamaño")
            if self.clickBordeLeftRectEllipse1:
                print("ajustamos left ellipse1")#************************Detectamos los bordes izquierda y derecho*************************
                self.parent().rectanguloEllipse1 = QRectF(QPointF(ptoX,rect1TopLeft.y()), rect1BotRight)
                self.parent().ellipse1 = QGraphicsEllipseItem(self.parent().rectanguloEllipse1)
                self.posTextEllipse1 = self.parent().rectanguloEllipse1.topLeft()
            elif self.clickBordeLeftRectEllipse2:
                print("ajustamos left ellipse2")
                self.parent().rectanguloEllipse2 = QRectF(QPointF(ptoX,rect2TopLeft.y()), rect2BotRight)
                self.parent().ellipse2 = QGraphicsEllipseItem(self.parent().rectanguloEllipse2)
                self.posTextEllipse2 = self.parent().rectanguloEllipse2.topLeft()
            elif self.clickBordeRightRectEllipse1:
                print("ajustamos right ellipse1")
                self.parent().rectanguloEllipse1 = QRectF(rect1TopLeft, QPointF(ptoX,rect1BotRight.y()))
                self.parent().ellipse1 = QGraphicsEllipseItem(self.parent().rectanguloEllipse1)              
            elif self.clickBordeRightRectEllipse2:
                print("ajustamos right ellipse2")
                self.parent().rectanguloEllipse2 = QRectF(rect2TopLeft, QPointF(ptoX,rect2BotRight.y()))
                self.parent().ellipse2 = QGraphicsEllipseItem(self.parent().rectanguloEllipse2)
            elif self.clickBordeTopRectEllipse1:
                print("ajustamos top ellipse1") #**************************Detectamos los bordes superior e inferior***********************
                self.parent().rectanguloEllipse1 = QRectF(QPointF(rect1TopLeft.x(),ptoY),rect1BotRight)
                self.parent().ellipse1 = QGraphicsEllipseItem(self.parent().rectanguloEllipse1)
                self.posTextEllipse1 = self.parent().rectanguloEllipse1.topLeft()
            elif self.clickBordeTopRectEllipse2:
                print("ajustamos top ellipse2")
                self.parent().rectanguloEllipse2 = QRectF(QPointF(rect2TopLeft.x(),ptoY),rect2BotRight)
                self.parent().ellipse2 = QGraphicsEllipseItem(self.parent().rectanguloEllipse2)
                self.posTextEllipse2 = self.parent().rectanguloEllipse2.topLeft()
            elif self.clickBordeBottomRectEllipse1:
                print("ajustamos bottom ellipse1")
                self.parent().rectanguloEllipse1 = QRectF(rect1TopLeft, QPointF(rect1BotRight.x(),ptoY))
                self.parent().ellipse1 = QGraphicsEllipseItem(self.parent().rectanguloEllipse1)
            elif self.clickBordeBottomRectEllipse2:
                print("ajustamos bottom ellipse2")
                self.parent().rectanguloEllipse2 = QRectF(rect2TopLeft, QPointF(rect2BotRight.x(),ptoY))
                self.parent().ellipse2 = QGraphicsEllipseItem(self.parent().rectanguloEllipse2)
            else:
                print("aca no deberiamos estar")
        else:
            if self.flag: #estoy arrastrando el mouse mientras dibujo una nueva elipse
                if self.parent().indice == 0:
                    self.parent().rectanguloEllipse1 = QRectF(self.begin, self.end)
                    self.parent().ellipse1 = QGraphicsEllipseItem(self.parent().rectanguloEllipse1)
                    self.posTextEllipse1 = self.begin
                else:
                    self.parent().rectanguloEllipse2 = QRectF(self.begin, self.end)
                    self.parent().ellipse2 = QGraphicsEllipseItem(self.parent().rectanguloEllipse2)
                    self.posTextEllipse2 = self.begin
            else:#si estoy realizando un desplazamiento de la ellipse
                if self.parent().ellipse1.contains(QPointF(ptoX,ptoY)) & self.flagRectEllipse1VsRectEllipse2:#estoy dentro de la ellipse1
                    #calculo la distancia entre el punto x-y y el punto clickeado dentro del rectangulo
                    desplazamientoXRecEllip1 = self.end.x() - self.posAnteriorRectEllipse1.x()
                    desplazamientoYRecEllip1 = self.end.y() - self.posAnteriorRectEllipse1.y()
                    self.parent().rectanguloEllipse1.translate(desplazamientoXRecEllip1, desplazamientoYRecEllip1)
                    self.parent().ellipse1.setRect(self.parent().rectanguloEllipse1)
                    self.posTextEllipse1 = self.parent().rectanguloEllipse1.topLeft()
                    self.posAnteriorRectEllipse1 = self.end
                    self.begin = self.end
                else:#estoy dentro de la ellipse2
                    desplazamientoXRecEllip2 = self.end.x() - self.posAnteriorRectEllipse2.x()
                    desplazamientoYRecEllip2 = self.end.y() - self.posAnteriorRectEllipse2.y()
                    self.parent().rectanguloEllipse2.translate(desplazamientoXRecEllip2, desplazamientoYRecEllip2)
                    self.parent().ellipse2.setRect(self.parent().rectanguloEllipse2)
                    self.posTextEllipse2 = self.parent().rectanguloEllipse2.topLeft()
                    self.posAnteriorRectEllipse2 = self.end
                    self.begin = self.end
        self.update()
    def mouseReleaseEvent(self, event):
        self.end = event.pos()
        if self.clickBorde:
            print("fin ajuste tamaño")
            self.clickBorde = False
            self.clickBordeTopRectEllipse1 = False
            self.clickBordeTopRectEllipse2 = False
            self.clickBordeRightRectEllipse1 = False
            self.clickBordeRightRectEllipse2 = False
        else:#si no es un click en el borde es que se dibujo uno nuevo o se translado uno ya existente
            print(self.begin, self.end)
            if self.flag:
                if self.parent().indice == 0:
                    self.parent().rectanguloEllipse1 = QRectF(self.begin, self.end)
                    self.parent().ellipse1 = QGraphicsEllipseItem(self.parent().rectanguloEllipse1)
                    self.posTextEllipse1 = self.begin
                    self.parent().indice = 1
                else:
                    self.parent().rectanguloEllipse2 = QRectF(self.begin, self.end)
                    self.parent().ellipse2 = QGraphicsEllipseItem(self.parent().rectanguloEllipse2)
                    self.parent().indice = 0
                    self.posTextEllipse2 = self.begin
            else:
                self.parent().presionTeclaEnEllipse1Flag = False
                self.parent().presionTeclaEnEllipse2Flag = False
        self.update()

#tengo que crear una clase para manejar el hilo de adquisicion
class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True
    #sobrecargo la funcion de arranque
    def run(self):
        #tomar imagen desde la web cam
        cap = cv2.VideoCapture(0)
        while self._run_flag:
            ret, cv_img = cap.read()
            if ret: #si la adquisicion de la imagen esta bien 
                self.change_pixmap_signal.emit(cv_img) #emito la señal
        cap.release()
    #sobrecargo la funcion de stop
    def stop(self):
        self._run_flag = False
        self.wait()

#tengo que crear una clase para manejar la UI de la aplicacion principal
class App(QWidget):
    factor = 1.5
    def __init__(self): #siempre tengo que sobrecargar el metodo __init__ para poner mi funcionalidad
        super().__init__() #con esto ya es instanciable mi clase
        self.setWindowTitle("Qt CV Show Video Camera with Ellipse")
        self.display_width = 640
        self.display_height = 480
        #lista de ellipses
        self.begin = QPoint()
        self.end = QPoint()
        #creo ellipse 1
        self.rectanguloEllipse1 = QRectF(self.begin, self.end)
        self.ellipse1 = QGraphicsEllipseItem(self.rectanguloEllipse1)#vamos a definir la ellipse1 utilizando el rectangulo1
        self.ellipse1.setTransformOriginPoint(self.rectanguloEllipse1.center())
        #creo ellipse 2
        self.rectanguloEllipse2 = QRectF(self.begin, self.end)
        self.ellipse2 = QGraphicsEllipseItem(self.rectanguloEllipse2)#vamos a definir la ellipse2 utilizando el rectangulo2
        self.ellipse2.setTransformOriginPoint(self.rectanguloEllipse2.center())
        #detecto el angulo
        self.anguloEllipse1 = self.ellipse1.rotation()
        self.anguloEllipse2 = self.ellipse2.rotation()
        #numero de click
        self.clickEllipse1 = 0
        self.clickEllipse2 = 0
        #detecto la tecla pulsada
        self.teclaUpGirarEllipse1 = False
        self.teclaDownGirarEllipse1 = False
        self.teclaUpGirarEllipse2 = False
        self.teclaDownGirarEllipse2 = False
        self.presionTeclaEnEllipse1Flag = False
        self.presionTeclaEnEllipse2Flag = False
        #indice para indicar que ellipse estoy usando
        self.indice = 0 
        #instanciamos a la clase que va a generar las elipses
        self.image = TestEllipse()
        #creamos una etiqueta
        self.textLabel = QLabel("Webcam")
        #creamos el layout vertical
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.image)
        self.vbox.addWidget(self.textLabel)
        self.setLayout(self.vbox)
        #creamos el hilo que va a realizar la captura de la imagen
        self.mithread = VideoThread()
        #conectamos el hilo con la funcion de actualizacion de imagen
        self.mithread.change_pixmap_signal.connect(self.update_image)
        #arranco el hilo
        self.mithread.start()
        
    #capturamos el evento de cierre de aplicacion
    def closeEvent(self, event):
        self.mithread.stop()
        event.accept()  
    @pyqtSlot(np.ndarray)
    def update_image(self,cv_img):
        qt_img = self.convert_cv_qt(cv_img)
        self.image.setPixmap(qt_img)
    
    def convert_cv_qt(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.display_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def keyPressEvent(self, event):
        #print(event.text())
        Key_Up = 0x01000013
        Key_Down = 0x01000015

        if event.key() == Key_Up:
            print("Tecla arriba")
            print(self.ellipse1.rotation())            
            if self.presionTeclaEnEllipse1Flag:             
                self.teclaUpGirarEllipse1 = True
                self.teclaDownGirarEllipse1 = False
                self.clickEllipse1 += 1
            elif self.presionTeclaEnEllipse2Flag:                
                self.teclaUpGirarEllipse2 = True
                self.teclaDownGirarEllipse2 = False
                self.clickEllipse2 += 1
            
        elif event.key() == Key_Down:
            print("Tecla abajo")
            if self.presionTeclaEnEllipse1Flag:
                self.teclaUpGirarEllipse1 = False
                self.teclaDownGirarEllipse1 = True                
                self.clickEllipse1 -= 1            
            if self.presionTeclaEnEllipse2Flag:
                self.teclaUpGirarEllipse2 = False
                self.teclaDownGirarEllipse2 = True
                self.clickEllipse2 -= 1
            
        else:
            print("se apreto otra tecla")
            
        
#realizo la instancia a la aplicacion principal
if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = App()   #instancio a la clase que maneja la interface grafica
    a.show()    #muestro su contenido
    sys.exit(app.exec())