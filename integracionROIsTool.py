#armamos un toolbar con los recursos para dibujar las imagenes
import sys
from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QMainWindow,
    QApplication,
    QLabel,
    QToolBar,
    QAction,
    QStatusBar,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QGraphicsEllipseItem,
    QSizePolicy,
    QScrollArea
)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QBrush, QColor, QPalette
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, pyqtSlot, QPoint, QRect, QLine, QRectF, QPointF
import numpy as np
import cv2, os
#
basedir = os.path.dirname(__file__)
#
class TestImage(QLabel):
    def __init__(self):
        super().__init__()
        ######################Escala########################
        self.scaleFactor = 1
        self.scala = 1.25
        ######################Escala########################
        #punto para deteccion del click
        self.begin = QPoint()
        self.end = QPoint()
        #punto de inicio del texto para el rectangulo 1
        self.posTextRect1 = QPoint()
        self.posTextRect2 = QPoint()
        #habilitacion para dibujar ROIs rectangulares
        self.flag = True
        #registro para detectar la posicion anterior del rectangulo1 y del rectangulo2
        self.posAnteriorRect1 = QPoint()
        self.posAnteriorRect2 = QPoint()
        #utilizamos este flag para determinar si se esta moviendo la roi
        self.flagRec1VsRec2 = True
        #definimos un registro para determinar si se esta apretando el borde superior o el borde inferior
        self.umbralTopLeftRect = QPoint(5,5)
        self.umbralBottomRightRect = QPoint(5,5)
        #definimos un flag para determinar si se apreto el borde
        self.clickBordeRect = False
        self.clickBordeTopLeftRect1 = False
        self.clickBordeTopLeftRect2 = False
        self.clickBordeBottomRightRect1 = False
        self.clickBordeBottomRightRect2 = False
        
        ####################Variable para el dibujo de lineas
        self.posTextRecta1 = QPoint()
        self.posTextRecta2 = QPoint()
        #
        self.posAnteriorRecta1 = QPoint()
        self.posAnteriorRecta2 = QPoint()
        self.clickBordeRecta = False
        self.flagRecta1VsRecta2 = True
        #
        self.umbralLeftRect = QPoint(5,5)
        self.umbralRightRect = QPoint(5,5)
        #
        self.clickBordeLeftRecta1 = False
        self.clickBordeLeftRecta2 = False
        self.clickBordeRightRecta1 = False
        self.clickBordeRightRecta2 = False
        #
        self.moviendoRecta1 = False
        self.moviendoRecta2 = False
        ###################Variable para el dibujo de elipses
        self.posTextEllipse1 = QPoint()
        self.posTextEllipse2 = QPoint()
        #
        self.posAnteriorRectEllipse1 = QPoint()
        self.posAnteriorRectEllipse2 = QPoint()
        #
        self.flagRectEllipse1VsRectEllipse2 = True
        #
        self.umbralLeftEllipse = QPoint(5,5)
        self.umbralRightEllipse = QPoint(5,5)
        self.umbralTopEllipse = QPoint(5,5)
        self.umbralBottomEllipse = QPoint(5,5)
        #
        self.clickBordeEllipse = False
        #
        self.clickBordeLeftRectEllipse1 = False
        self.clickBordeLeftRectEllipse2 = False
        self.clickBordeRightRectEllipse1 = False
        self.clickBordeRightRectEllipse2 = False
        self.clickBordeTopRectEllipse1 = False
        self.clickBordeTopRectEllipse2 = False
        self.clickBordeBottomRectEllipse1 = False
        self.clickBordeBottomRectEllipse2 = False
#########################################################        
    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value() + ((factor - 1) * scrollBar.pageStep()/2)))
#########################################################
    def paintEvent(self, event):
        #sobrecargo el metodo paint de la clase label
        super().paintEvent(event)        
#########################################################
        try:
            escala = self.scaleFactor * self.pixmap().size()
            print(escala)
            self.resize(escala)
            flagEstado = True            
        except:
            print("error Image")
            flagEstado = False #si tenemos un error en la adquisicion no agregamos los objetos en la imagen
#########################################################
        if flagEstado:
            #instancio a la clase QPainter
            qp = QPainter(self)
            #defino un color para el objeto instanciado
            br = QBrush(QColor(100,10,10,40))
            #pinto el objeto 
            qp.setBrush(br)
            #defino un borde para los objetos
            pen = QtGui.QPen()
            pen.setWidth(3)
            pen.setColor(QtGui.QColor("#00FF00"))
            #asigno este objeto al objeto painter instanciado
            qp.setPen(pen)
            #dibujo dos rectangulos llevo la posicion en dos variables del programa principal
            qp.drawRect(self.parent().parent().rectangulo1)
            qp.drawText(self.posTextRect1,"rect1")
            qp.drawRect(self.parent().parent().rectangulo2)
            qp.drawText(self.posTextRect2,"rect2")
            #dibujo dos lineas
            qp.drawLine(self.parent().parent().recta1)
            qp.drawText(self.posTextRecta1, "recta1")
            qp.drawLine(self.parent().parent().recta2)
            qp.drawText(self.posTextRecta2, "recta2")
            #dibujo dos ellipses
            #deteccion de giro de ellipse
            presionEnEllipse1 = (self.parent().parent().presionTeclaEnEllipse1Flag & (self.parent().parent().teclaUpGirarEllipse1 | self.parent().parent().teclaDownGirarEllipse1))
            presionEnEllipse2 = (self.parent().parent().presionTeclaEnEllipse2Flag & (self.parent().parent().teclaUpGirarEllipse2 | self.parent().parent().teclaDownGirarEllipse2))
            if presionEnEllipse1 | presionEnEllipse2 :
                if self.parent().parent().presionTeclaEnEllipse1Flag:
                    if self.parent().parent().teclaUpGirarEllipse1:
                        self.parent().parent().anguloEllipse1 = self.parent().parent().ellipse1.rotation() + 1 * self.parent().parent().clickEllipse1
                        #roto la elipse 1
                        qp.rotate(self.parent().parent().anguloEllipse1)
                        #dibujo las ellipses
                        qp.drawEllipse(self.parent().parent().rectanguloEllipse1)
                        qp.drawText(self.posTextEllipse1, "Ellipse1")
                        #restauro
                        qp.resetTransform()
                        #dibujo las ellipses
                        qp.drawEllipse(self.parent().parent().rectanguloEllipse2)
                        qp.drawText(self.posTextEllipse2, "Ellipse2")
                        #reseteo los flags de deteccion de giro
                        self.parent().parent().teclaDownGirarEllipse1 = False
                        self.parent().parent().teclaUpGirarEllipse2 = False
                        self.parent().parent().teclaDownGirarEllipse2 = False

                    elif self.parent().parent().teclaDownGirarEllipse1:
                        self.parent().parent().anguloEllipse1 = self.parent().parent().ellipse1.rotation() + 1 * self.parent().parent().clickEllipse1
                        qp.drawEllipse(self.parent().parent().rectanguloEllipse2)
                        qp.drawText(self.posTextEllipse2, "Ellipse2")
                        qp.rotate(self.parent().parent().anguloEllipse1)
                        #dibujo las ellipses
                        qp.drawEllipse(self.parent().parent().rectanguloElipse1)
                        qp.drawText(self.posTextEllipse1, "Ellipse1")
                        #reseteo los flags de deteccion de giro
                        self.parent().parent().teclaUpGirarEllipse1 = False
                        self.parent().parent().teclaUpGirarEllipse2 = False
                        self.parent().parent().teclaDownGirarEllipse2 = False
                    else:
                        pass
                if self.parent().parent().presionTeclaEnEllipse2Flag:
                    if self.parent().parent().teclaUpGirarEllipse2:
                        self.parent().parent().anguloEllipse2 = self.parent().parent().ellipse2.rotation() + 1 * self.parent().parent().clickEllipse2
                        qp.drawEllipse(self.parent().parent().rectanguloEllipse1)
                        qp.drawText(self.posTextEllipse1, "Ellipse1")
                        #roto la elipse 1
                        qp.rotate(self.parent().parent().anguloEllipse2)
                        #dibujo las ellipses
                        qp.drawEllipse(self.parent().parent().rectanguloEllipse2)
                        qp.drawText(self.posTextEllipse2, "Ellipse2")
                        #reseteo los flag de giro
                        self.parent().parent().teclaUpGirarEllipse1 = False
                        self.parent().parent().teclaDownGirarEllipse1 = False
                        self.parent().parent().teclaDownGirarEllipse2 = False
                    elif self.parent().parent().teclaDownGirarEllipse2:
                        self.parent().parent().anguloEllipse2 = self.parent().parent().ellipse2.rotation() + 1 * self.parent().parent().clickEllipse2
                        #dibjo las ellipses
                        qp.drawEllipse(self.parent().parent().rectanguloEllipse1)
                        qp.drawText(self.posTextEllipse1, "Ellipse1")
                        qp.rotate(self.parent().parent().anguloEllipse2)
                        #dibujo las ellipses
                        qp.drawEllipse(self.parent().parent().rectanguloEllipse2)
                        qp.drawText(self.posTextEllipse2, "Ellipse2")
                        #reseteo los flags
                        self.parent().parent().teclaUpGirarEllipse1 = False
                        self.parent().parent().teclaDownGirarEllipse1 = False
                        self.parent().parent().teclaUpGirarEllipse2 = False
                    else:
                        pass
            else:
                #dibujo las ellipses sin rotar
                qp.rotate(self.parent().parent().anguloEllipse1)
                qp.drawEllipse(self.parent().parent().rectanguloEllipse1)
                qp.drawText(self.posTextEllipse1, "Ellipse1")
                qp.resetTransform()
                #dibujo las ellipses sin rotar
                qp.rotate(self.parent().parent().anguloEllipse2)
                qp.drawEllipse(self.parent().parent().rectanguloEllipse2)
                qp.drawText(self.posTextEllipse2, "Ellipse2")
                #reseteo los flags
                self.parent().parent().teclaUpGirarEllipse1 = False
                self.parent().parent().teclaDownGirarEllipse1 = False
                self.parent().parent().teclaUpGirarEllipse2 = False
                self.parent().parent().teclaDownGirarEllipse2 = False

    def mousePressEvent(self, event):
        #detecto la posicion del ultimo movimiento
        self.begin = event.pos()
        #####################################################
        print("mouse click", self.scaleFactor)
        if  self.parent().parent().zoomInButton == True:
            self.scala = 1.25
        elif self.parent().parent().zoomOutButton == True:
            self.scala = 0.8
        else:
            self.scala = 1
        self.scaleFactor *= self.scala
        #####################################################
        #detecto si se estan dibujando los rectangulos
        if self.parent().parent().toolROIs == 0:
            #defino las condiciones de borde, si es que estoy tocando el borde o no
            detectoCondicionClickBordeTopLeftRect1Inf = (self.parent().parent().rectangulo1.topLeft() - self.umbralTopLeftRect).x() 
            detectoCondicionClickBordeTopLeftRect1Sup = (self.parent().parent().rectangulo1.topLeft() + self.umbralTopLeftRect).x()
            condicionClickBordeTopLeftRect1 = detectoCondicionClickBordeTopLeftRect1Inf < self.begin.x() < detectoCondicionClickBordeTopLeftRect1Sup 
            
            detectoCondicionClickBordeTopLeftRect2Inf = (self.parent().parent().rectangulo2.topLeft() - self.umbralTopLeftRect).x()
            detectoCondicionClickBordeTopLeftRect2Sup = (self.parent().parent().rectangulo2.topLeft() + self.umbralTopLeftRect).x()
            condicionClickBordeTopLeftRect2 = detectoCondicionClickBordeTopLeftRect2Inf < self.begin.x() < detectoCondicionClickBordeTopLeftRect2Sup

            detectoCondicionClickBordeBottomRightRect1Inf = (self.parent().parent().rectangulo1.bottomRight() - self.umbralBottomRightRect).x()
            detectoCondicionClickBordeBottomRightRect1Sup = (self.parent().parent().rectangulo1.bottomRight() + self.umbralBottomRightRect).x()
            condicionClickBordeBottomRightRect1 = detectoCondicionClickBordeBottomRightRect1Inf < self.begin.x() < detectoCondicionClickBordeBottomRightRect1Sup
            
            detectoCondicionClickBordeBottomRightRect2Inf = (self.parent().parent().rectangulo2.bottomRight() - self.umbralBottomRightRect).x()
            detectoCondicionClickBordeBottomRightRect2Sup = (self.parent().parent().rectangulo2.bottomRight() + self.umbralBottomRightRect).x()
            condicionClickBordeBottomRightRect2 = detectoCondicionClickBordeBottomRightRect2Inf < self.begin.x() < detectoCondicionClickBordeBottomRightRect2Sup
            
            if condicionClickBordeTopLeftRect1 | condicionClickBordeTopLeftRect2 | condicionClickBordeBottomRightRect1 | condicionClickBordeBottomRightRect2:
                #se detecto un borde
                self.clickBordeRect = True
                #se detecto el borde 1
                if condicionClickBordeTopLeftRect1:
                    print("click borde superior rect 1")
                    self.clickBordeTopLeftRect1 = True
                    self.clickBordeTopLeftRect2 = False                
                elif condicionClickBordeTopLeftRect2:
                    print("click borde superior rect 2")
                    self.clickBordeTopLeftRect1 = False
                    self.clickBordeTopLeftRect2 = True            
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
                #verifico si el click fue dentro del rectangulo 1
                if self.parent().parent().rectangulo1.contains(self.begin, False):
                    self.flag = False
                    #guardo la posicion del click como la posicion anterior
                    self.posAnteriorRect1 = self.begin
                    if self.parent().parent().indiceRect == 0:
                        print("estoy haciendo un click para dibujar el rectangulo 1")
                    else:
                        print("estoy haciendo un click para dibujar el rectangulo 2")
                    self.flagRec1VsRec2 = True
                #verifico si el click fue dentro del rectangulo 2
                elif self.parent().parent().rectangulo2.contains(self.begin, False):
                    self.flag = False
                    #guardo la posicion del click como la posicion anterior
                    self.posAnteriorRect2 = self.begin
                    if self.parent().parent().indiceRect == 0:
                        print("estoy haciendo un clikc para dibujar el rectangulo 1")
                    else:
                        print("estoy haciendo un click para dibujar el rectangulo 2")
                    self.flagRec1VsRec2 = False
                else:
                    #estoy dibujando un nuevo rectangulo
                    self.flag = True
        #detecto se se estan dibujando las rectas
        if self.parent().parent().toolROIs == 1:
            #determino si se esta presionando la esquina de la recta 1 - 2
            #determino si se esta presionando la esquina de la recta 1 - 2
            condicionClickBordeLeftRecta1Inf = (self.parent().parent().recta1.p1() - self.umbralLeftRect).x()
            condicionClickBordeLeftRecta1Sup = (self.parent().parent().recta1.p1() + self.umbralLeftRect).x()
            condicionClickBordeLeftRecta1 =  condicionClickBordeLeftRecta1Inf< self.begin.x() < condicionClickBordeLeftRecta1Sup
            condicionClickBordeLeftRecta2Inf = (self.parent().parent().recta2.p1() - self.umbralLeftRect).x()
            condicionClickBordeLeftRecta2Sup = (self.parent().parent().recta2.p1() + self.umbralLeftRect).x()
            condicionClickBordeLeftRecta2 =  condicionClickBordeLeftRecta2Inf< self.begin.x() <condicionClickBordeLeftRecta2Sup 
            condicionClickBordeRightRecta1Inf = (self.parent().parent().recta1.p2() - self.umbralRightRect).x()
            condicionClickBordeRightRecta1Sup = (self.parent().parent().recta1.p2() + self.umbralRightRect).x()
            condicionClickBordeRightRecta1 = condicionClickBordeRightRecta1Inf < self.begin.x() < condicionClickBordeRightRecta1Sup
            condicionClickBordeRightRecta2Inf = (self.parent().parent().recta2.p2() - self.umbralRightRect).x()
            condicionClickBordeRightRecta2Sup= (self.parent().parent().recta2.p2() + self.umbralRightRect).x()
            condicionClickBordeRightRecta2 = condicionClickBordeRightRecta2Inf < self.begin.x() < condicionClickBordeRightRecta2Sup
            #verifico si se esta haciendo un click en los bordes de las rectas
            if condicionClickBordeLeftRecta1 | condicionClickBordeLeftRecta2 | condicionClickBordeRightRecta1 | condicionClickBordeRightRecta2:
                #indicamos que se realizo un click en uno de los bordes
                self.clickBordeRecta = True 
                #condicion click en el extremo izquierdo recta 1
                if condicionClickBordeLeftRecta1:
                    print("click borde izquierdo recta 1")
                    self.clickBordeLeftRecta1 = True
                #condicion click en el extremo izquierdo recta 2
                elif condicionClickBordeLeftRecta2:
                    print("click borde izquierdo recta 2")
                    self.clickBordeLeftRecta2 = True
                #condicion click en el extremo derecho recta 1
                elif condicionClickBordeRightRecta1:
                    print("click borde derecho recta 1")
                    self.clickBordeRightRecta1 = True
                #condicion click en el extremo derecho recta 2        
                elif condicionClickBordeRightRecta2:
                    print("click borde derecho recta 2")
                    self.clickBordeRightRecta2 = True
                else:
                    print("no se presiono ningun borde, no deberiamos estar aca")
            #no se presiono ningun borde y estamos dibujando una nueva recta
            #o bien estamos desplazando la recta dibujada
            else:
                #determino si el punto donde se hace click esta dentro de la recta
                if(not self.parent().parent().recta1.isNull()) & (not self.parent().parent().recta2.isNull()):
                    valorInicialRecta1ZonaInf = (self.parent().parent().recta1.p1().x() < self.begin.x() < self.parent().parent().recta1.p2().x()) | (self.parent().parent().recta1.p2().x()<self.begin.x()<self.parent().parent().recta1.p1().x())
                    valorFinalRecta1ZonaSup = (self.parent().parent().recta1.p1().y() < self.begin.y() < self.parent().parent().recta1.p2().y()) | (self.parent().parent().recta1.p2().y()<self.begin.y()<self.parent().parent().recta1.p1().y())
                    condicionClickDentroRecta1XY =  valorInicialRecta1ZonaInf & valorFinalRecta1ZonaSup  
                    pendienteRecta1 = abs(self.parent().parent().recta1.p1().y() - self.parent().parent().recta1.p2().y()) / abs(self.parent().parent().recta1.p1().x() - self.parent().parent().recta1.p2().x()) 
                    pendienteRecta1PuntoClick = abs(self.parent().parent().recta1.p1().y()-self.begin.y())/abs(self.parent().parent().recta1.p1().x()-self.begin.x())
                    condicionClickDentroRecta1Pendiente = pendienteRecta1 * 0.9 < pendienteRecta1PuntoClick < pendienteRecta1 * 1.1

                    valorInicialRecta2ZonaInf = (self.parent().parent().recta2.p1().x() < self.begin.x() < self.parent().parent().recta2.p2().x()) | (self.parent().parent().recta2.p2().x()<self.begin.x()<self.parent().parent().recta2.p1().x())
                    valorFinalRecta2ZonaSup = (self.parent().parent().recta2.p1().y() < self.begin.y() < self.parent().parent().recta2.p2().y()) | (self.parent().parent().recta2.p2().y()<self.begin.y()<self.parent().parent().recta2.p1().y())
                    condicionClickDentroRecta2XY = valorInicialRecta2ZonaInf & valorFinalRecta2ZonaSup   
                    pendienteRecta2 = abs(self.parent().parent().recta2.p1().y() - self.parent().parent().recta2.p2().y()) / abs(self.parent().parent().recta2.p1().x() - self.parent().parent().recta2.p2().x())
                    pendienteRecta2PuntoClick = abs(self.parent().parent().recta2.p1().y()-self.begin.y())/abs(self.parent().parent().recta2.p1().x()-self.begin.x())
                    condicionClickDentroRecta2Pendiente = pendienteRecta2 * 0.9 < pendienteRecta2PuntoClick < pendienteRecta2 * 1.1
                    
                    self.moviendoRecta1 = condicionClickDentroRecta1XY & condicionClickDentroRecta1Pendiente
                    self.moviendoRecta2 = condicionClickDentroRecta2XY & condicionClickDentroRecta2Pendiente
                    #movemos la recta
                    if self.moviendoRecta1:
                        self.flag = False
                        self.posAnteriorRecta1 = self.begin #guardo la posicion del click comola posicion antes de mover el mouse
                        if self.parent().parent().indiceRect == 0:
                            print("estoy haciendo un click para mover la recta 1")
                        else:
                            print("estoy haciendo un click para mover la recta 2")
                        self.flagRecta1VsRecta2 = True
                    elif self.moviendoRecta2:
                        self.flag = False
                        self.posAnteriorRecta2 = self.begin
                        if self.parent().parent().indiceRect == 0:
                            print("estoy haciendo un click para mover la recta 1")
                        else:
                            print("estoy haciendo un click para mover la recta 2")
                        self.flagRecta1VsRecta2 = False
                    else:
                        self.flag = True
                else:
                    print("no tengo que estar aca")
        #detecto si se estan dibujando las ellipses
        if self.parent().parent().toolROIs == 2:
            ptoXEllipse = self.begin.x()
            ptoYEllipse = self.begin.y()
            #condicion de borde izquierdo - derecho para ellipse1-2
            condicionClickBordeLeftRectEllipse1Inf = (int(self.parent().parent().ellipse1.rect().left()) - self.umbralLeftEllipse.x())
            condicionClickBordeLeftRectEllipse1Sup = (int(self.parent().parent().ellipse1.rect().left()) + self.umbralLeftEllipse.x())
            condicionClickBordeLeftRectEllipse1 = condicionClickBordeLeftRectEllipse1Inf < self.begin.x() < condicionClickBordeLeftRectEllipse1Sup
            #
            condicionClickBordeLeftRectEllipse2Inf = (int(self.parent().parent().ellipse2.rect().left()) - self.umbralLeftEllipse.x())
            condicionClickBordeLeftRectEllipse2Sup = (int(self.parent().parent().ellipse2.rect().left()) + self.umbralLeftEllipse.x())
            condicionClickBordeLeftRectEllipse2 = condicionClickBordeLeftRectEllipse2Inf < self.begin.x() < condicionClickBordeLeftRectEllipse2Sup
            #
            condicionClickBordeRightRectEllipse1Inf = (int(self.parent().parent().ellipse1.rect().right()) - self.umbralRightEllipse.x())
            condicionClickBordeRightRectEllipse1Sup = (int(self.parent().parent().ellipse1.rect().right()) + self.umbralRightEllipse.x())
            condicionClickBordeRightRectEllipse1 = condicionClickBordeRightRectEllipse1Inf < self.begin.x() < condicionClickBordeRightRectEllipse1Sup
            #
            condicionClickBordeRightRectEllipse2Inf = (int(self.parent().parent().ellipse2.rect().right()) - self.umbralRightEllipse.x())
            condicionClickBordeRightRectEllipse2Sup = (int(self.parent().parent().ellipse2.rect().right()) + self.umbralRightEllipse.x())
            condicionClickBordeRightRectEllipse2 = condicionClickBordeRightRectEllipse2Inf < self.begin.x() < condicionClickBordeRightRectEllipse2Sup
            #condicion de borde superior - inferior para ellise1-2
            condicionClickBordeTopRectEllipse1Inf = (int(self.parent().parent().ellipse1.rect().top()) - self.umbralTopEllipse.y())
            condicionClickBordeTopRectEllipse1Sup = (int(self.parent().parent().ellipse1.rect().top()) + self.umbralTopEllipse.y())
            condicionClickBordeTopRectEllipse1 = condicionClickBordeTopRectEllipse1Inf < self.begin.y() < condicionClickBordeTopRectEllipse1Sup
            #
            condicionClickBordeTopRectEllipse2Inf = (int(self.parent().parent().ellipse2.rect().top()) - self.umbralTopEllipse.y())
            condicionClickBordeTopRectEllipse2Sup = (int(self.parent().parent().ellipse2.rect().top()) + self.umbralTopEllipse.y())
            condicionClickBordeTopRectEllipse2 = condicionClickBordeTopRectEllipse2Inf < self.begin.y() < condicionClickBordeTopRectEllipse2Sup
            #
            condicionClickBordeBottomRectEllipse1Inf = (int(self.parent().parent().ellipse1.rect().bottom()) - self.umbralBottomEllipse.y()) 
            condicionClickBordeBottomRectEllipse1Sup = (int(self.parent().parent().ellipse1.rect().bottom()) + self.umbralBottomEllipse.y())
            condicionClickBordeBottomRectEllipse1 = condicionClickBordeBottomRectEllipse1Inf < self.begin.y() < condicionClickBordeBottomRectEllipse1Sup
            #
            condicionClickBordeBottomRectEllipse2Inf = (int(self.parent().parent().ellipse2.rect().bottom()) - self.umbralBottomEllipse.y())
            condicionClickBordeBottomRectEllipse2Sup = (int(self.parent().parent().ellipse2.rect().bottom()) + self.umbralBottomEllipse.y())
            condicionClickBordeBottomRectEllipse2 = condicionClickBordeBottomRectEllipse2Inf < self.begin.y() < condicionClickBordeBottomRectEllipse2Sup
            #verifico la condicion de click en el borde superior o derecho
            if condicionClickBordeLeftRectEllipse1 | condicionClickBordeLeftRectEllipse2 | condicionClickBordeRightRectEllipse1 | condicionClickBordeRightRectEllipse2 | condicionClickBordeTopRectEllipse1 | condicionClickBordeTopRectEllipse2 | condicionClickBordeBottomRectEllipse1 | condicionClickBordeBottomRectEllipse2:
                #si se realiza un click en el borde
                self.clickBordeEllipse = True
                #esto esta mal realizado pero por motivos de clarificar el codigo lo hacemos asi
                self.clickBordeLeftRectEllipse1 = False
                self.clickBordeLeftRectEllipse2 = False
                self.clickBordeRightRectEllipse1 = False
                self.clickBordeRightRectEllipse2 = False
                self.clickBordeTopRectEllipse1 = False
                self.clickBordeTopRectEllipse2 = False
                self.clickBordeBottomRectEllipse1 = False
                self.clickBordeBottomRectEllipse2 = False
                #verifico las condiciones
                #detecto el borde izquierdo ellipse 1
                if condicionClickBordeLeftRectEllipse1:
                    print("click borde superior rect ellipse 1")
                    self.clickBordeLeftRectEllipse1 = True
                #detecto el borde izquierdo ellipse 2
                elif condicionClickBordeLeftRectEllipse2:
                    print("click bordesuperior rect ellipse 2")
                    self.clickBordeLeftRectEllipse2 = True
                #detecto el borde derecho ellipse 1
                elif condicionClickBordeRightRectEllipse1:
                    print("click borde derecho rect ellipse 1")
                    self.clickBordeRightRectEllipse1 = True
                #detecto el borde derecho ellipse 2
                elif condicionClickBordeRightRectEllipse2:
                    print("click borde derecho rect ellipse 2")
                    self.clickBordeRightRectEllipse2 = True
                #detecto el borde superio ellipse 1
                elif condicionClickBordeTopRectEllipse1:
                    print("click borde top rect ellipse 1")
                    self.clickBordeTopRectEllipse1 = True
                #detecto el borde superior ellipse 2
                elif condicionClickBordeTopRectEllipse2:
                    print("click borde top rect ellipse 2")
                    self.clickBordeTopRectEllipse2 = True
                #detecto el borde inferior ellipse 1
                elif condicionClickBordeBottomRectEllipse1:
                    print("click borde bottom rect ellipse 1")
                    self.clickBordeBottomRectEllipse1 = True
                #detecto el borde inferior ellipse 2
                elif condicionClickBordeBottomRectEllipse2:
                    print("click borde bottom rect ellipse 2")
                    self.clickBordeBottomRectEllipse2 = True
                else:
                    print("no se presiono ningun borde, no deberias estas aca!")
            #no es un click en el borde entonces hay dos opciones
            #se esta graficando una nueva ellipse o se esta intentando
            #desplazar la ellipse existente
            #click dentro de ellipse o fuera de ellipse pero no en ningun borde
            else:
                #estoy haciendo un click dentro de la ellipse 1
                if self.parent().parent().rectanguloEllipse1.contains(ptoXEllipse,ptoYEllipse):
                    #marco que se presiono el mouse sobre una elipse
                    self.parent().parent().presionTeclaEnEllipse1Flag = True
                    self.parent().parent().presionTeclaEnEllipse2Flag = False
                    #detecto que se esta intentando mover la elipse 1
                    self.flag = False
                    #guardo la posicion anterior
                    self.posAnteriorRectEllipse1 = self.begin     
                    if self.parent().parent().indiceEllipse == 0:
                        print("click ellipse 1 estoy haciendo un click para dibujar el rectangulo ellipse 1")
                    else:
                        print("click elipse 1 estoy haciendo un clikc para dibujar el rectantulo ellipse 2 ")  
                    self.flagRectEllipse1VsRectEllipse2 = True
                elif self.parent().parent().rectanguloEllipse2.contains(ptoXEllipse, ptoYEllipse):
                    #marco que se presiono el mouse sobre una ellipse
                    self.parent().parent().presionReclaEnEllipse1Flag = False
                    self.parent().parent().presionTeclaEnEllipse2Flag = True
                    self.flag = False
                    #guardo la posicion anterior
                    self.posAnteriorRectEllipse2 = self.begin
                    if self.parent().parent().indiceEllipse == 0 :
                        print("click elipse 2 estoy haciendo un click para dibujar el rectangulo ellipse 1")
                    else:
                        print("click elipse 2 estoy haciendo un click para dibujar el rectangulo ellipse 2")
                    self.flagRectEllipse1VsRectEllipse2 = False
                #no estoy haciendo un click dentro de ninguna elipse sino fuera para dibujar una nueva elipse 
                else:
                    self.flag = True
                    #pongo en false tecla girar
                    self.parent().parent().presionTeclaEnEllipse2Flag = False
                    self.parent().parent().presionTeclaEnEllipse1Flag = False
        ####
        self.update()
    def mouseMoveEvent(self, event):
        #detecto la posiocion del mouse
        self.end = event.pos()
        print(self.end)
        #rectangulo
        if self.parent().parent().toolROIs == 0:
            #determino si estoy en un borde
            if self.clickBordeRect:
                print("reducir tama;o")
                if self.clickBordeTopLeftRect1:
                    self.parent().parent().rectangulo1.setTopLeft(event.pos())
                    self.posTextRect1 = self.parent().parent().rectangulo1.topLeft()
                elif self.clickBordeTopLeftRect2:
                    self.parent().parent().rectangulo2.setTopLeft(event.pos())
                    self.posTextRect2 = self.parent().parent().rectangulo2.topLeft()
                elif self.clickBordeBottomRightRect1:
                    self.parent().parent().rectangulo1.setBottomRight(event.pos())
                elif self.clickBordeBottomRightRect2:
                    self.parent().parent().rectangulo2.setBottomRight(event.pos())
                else:
                    print("aca va la parte del borde inferior")
            #no estoy en un borde
            else:
                #estoy arrastrando el mouse mientras dibujo una nueva roi
                if self.flag:
                    if self.parent().parent().indiceRect == 0:
                        self.parent().parent().rectangulo1 = QRect(self.begin, self.end)
                        self.posTextRect1 = self.begin
                    else:
                        self.parent().parent().rectangulo2 = QRect(self.begin, self.end)
                        self.posTextRect2 = self.begin
                #estoy realizando un desplazamiento del rectangulo mientras muevo el mouse
                else:
                    if self.parent().parent().rectangulo1.contains(self.begin, False) & self.flagRec1VsRec2:
                        #calculo la distancia entre el punto x-y y el punto clickeado dentro del rectangulo
                        desplazamientoXRect1 = self.end.x() - self.posAnteriorRect1.x()
                        desplazamientoYRect1 = self.end.y() - self.posAnteriorRect1.y()
                        self.parent().parent().rectangulo1.translate(desplazamientoXRect1, desplazamientoYRect1)
                        self.posTextRect1 = self.parent().parent().rectangulo1.topLeft()
                        self.posAnteriorRect1 = self.end
                        self.begin = self.end
                    else:
                        desplazamientoXRect2 = self.end.x() - self.posAnteriorRect2.x()
                        desplazamientoYRect2 = self.end.y() - self.posAnteriorRect2.y()
                        self.parent().parent().rectangulo2.translate(desplazamientoXRect2, desplazamientoYRect2)
                        self.posTextRect2 = self.parent().parent().rectangulo2.topLeft()
                        self.posAnteriorRect2 = self.end
                        self.begin = self.end
        #recta
        if self.parent().parent().toolROIs == 1:
            #determina el borde
            if self.clickBordeRecta:
                print("reducir tamaño")
                if self.clickBordeLeftRecta1:
                    self.parent().parent().recta1.setP1(event.pos())
                    self.posTextRecta1 = self.parent().parent().recta1.p1()
                elif self.clickBordeLeftRecta2:
                    self.parent().parent().recta2.setP1(event.pos())
                    self.posTextRecta2 = self.parent().parent().recta2.p1()
                elif self.clickBordeRightRecta1:
                    self.parent().parent().recta1.setP2(event.pos())
                elif self.clickBordeRightRecta2:
                    self.parent().parent().recta2.setP2(event.pos())
                else:
                    print("aca va la parte del borde inferior")
            #estoy arrastrando el mouse mientras dibujo una nueva recta
            else:
                if self.flag: 
                    if self.parent().parent().indiceRect == 0:
                        self.parent().parent().recta1 = QLine(self.begin, self.end)
                        self.posTextRecta1 = self.begin
                    else:
                        self.parent().parent().recta2 = QLine(self.begin, self.end)
                        self.posTextRecta2 = self.begin
                else: #si estoy realizando un desplazamiento de la recta mientras muevo el mouse
                    if self.moviendoRecta1 & self.flagRecta1VsRecta2:
                        #estoy moviendo la recta 1
                        desplazamientoXRecta1 = self.end.x() - self.posAnteriorRecta1.x()
                        desplazamientoYRecta1 = self.end.y() - self.posAnteriorRecta1.y()
                        print(desplazamientoXRecta1)
                        print(desplazamientoYRecta1)
                        self.parent().parent().recta1.translate(desplazamientoXRecta1,desplazamientoYRecta1)
                        self.posTextRecta1 = self.parent().parent().recta1.p1()
                        self.posAnteriorRecta1 = self.end
                        self.begin = self.end
                    else: 
                        desplazamientoXRecta2 = self.end.x() - self.posAnteriorRecta2.x()
                        desplazamientoYRecta2 = self.end.y() - self.posAnteriorRecta2.y()
                        self.parent().parent().recta2.translate(desplazamientoXRecta2, desplazamientoYRecta2)
                        self.posTextRecta2 = self.parent().parent().recta2.p1()
                        self.posAnteriorRecta2 = self.end
                        self.begin = self.end
        #elipse
        if self.parent().parent().toolROIs == 2:
            ptoXEllipse = self.end.x()
            ptoYEllipse = self.end.y()
            rect1TopLeftEllipse = self.parent().parent().rectanguloEllipse1.topLeft()
            rect1BotRightEllipse = self.parent().parent().rectanguloEllipse1.bottomRight()
            rect2TopLeftEllipse = self.parent().parent().rectanguloEllipse2.topLeft()
            rect2BotRightEllipse = self.parent().parent().rectanguloEllipse2.bottomRight()
            #verifico si previamente se hiso un click en el borde
            if self.clickBordeEllipse:
                if self.clickBordeLeftRectEllipse1:
                    self.parent().parent().rectanguloEllipse1 = QRectF(QPointF(ptoXEllipse, rect1TopLeftEllipse.y()), rect1BotRightEllipse)
                    self.parent().parent().ellipse1 = QGraphicsEllipseItem(self.parent().parent().rectanguloEllipse1)
                    self.posTextEllipse1 = self.parent().parent().rectanguloEllipse1.topLeft()
                elif self.clickBordeLeftRectEllipse2:
                    self.parent().parent().rectanguloEllipse2 = QRectF(QPointF(ptoXEllipse, rect2TopLeftEllipse.y()), rect2BotRightEllipse)
                    self.parent().parent().ellipse2 = QGraphicsEllipseItem(self.parent().parent().rectanguloEllipse2)
                    self.posTextEllipse2 = self.parent().parent().rectanguloEllipse2.topLeft()
                elif self.clickBordeRightRectEllipse1:
                    self.parent().parent().rectanguloEllipse1 = QRectF(rect1TopLeftEllipse, QPointF(ptoXEllipse, rect1BotRightEllipse.y()))
                    self.parent().parent().ellipse1 = QGraphicsEllipseItem(self.parent().parent().rectanguloEllipse1)
                elif self.clickBordeRightRectEllipse2:
                    self.parent().parent().rectanguloEllipse2 = QRectF(rect2TopLeftEllipse, QPointF(ptoXEllipse, rect2BotRightEllipse.y()))
                    self.parent().parent().ellipse2 = QGraphicsEllipseItem(self.parent().parent().rectanguloEllipse2)
                elif self.clickBordeTopRectEllipse1:
                    self.parent().parent().rectanguloEllipse1 = QRectF(QPointF(rect1TopLeftEllipse.x(),ptoYEllipse), rect1BotRightEllipse)
                    self.parent().parent().ellipse1 = QGraphicsEllipseItem(self.parent().parent().rectanguloEllipse1)
                    self.posTextEllipse1 = self.parent().parent().rectanguloEllipse1.topLeft()
                elif self.clickBordeTopRectEllipse2:
                    self.parent().parent().rectanguloEllipse2 = QRectF(QPointF(rect2TopLeftEllipse.x(), ptoYEllipse), rect2BotRightEllipse)
                    self.parent().parent().ellipse2 = QGraphicsEllipseItem(self.parent().parent().rectanguloEllipse2)
                    self.posTextEllipse2 = self.parent().parent().rectanguloEllipse2.topLeft()
                elif self.clickBordeBottomRectEllipse1:
                    self.parent().parent().rectanguloEllipse1 = QRectF(rect1TopLeftEllipse, QPointF(rect1BotRightEllipse.x(), ptoYEllipse))
                    self.parent().parent().ellipse1 = QGraphicsEllipseItem(self.parent().parent().rectanguloEllipse1)
                elif self.clickBordeBottomRectEllipse2:
                    self.parent().parent().rectanguloEllipse2 = QRectF(rect2TopLeftEllipse, QPointF(rect2BotRightEllipse.x(), ptoYEllipse))
                    self.parent().parent().ellipse2 = QGraphicsEllipseItem(self.parent().parent().rectanguloEllipse2)
                else:
                    print("aca no deberiamos estar")
            else:
                #estoy arrastrando el mouse mientras dibujo una nueva elipse
                if self.flag:
                    if self.parent().parent().indiceEllipse == 0:
                        self.parent().parent().rectanguloEllipse1 = QRectF(self.begin, self.end)
                        self.parent().parent().ellipse1 = QGraphicsEllipseItem(self.parent().parent().rectanguloEllipse1)
                        self.posTextEllipse1 = self.begin
                    else:
                        self.parent().parent().rectanguloEllipse2 = QRectF(self.begin, self.end)
                        self.parent().parent().ellipse2 = QGraphicsEllipseItem(self.parent().parent().rectanguloEllipse2)
                        self.posTextEllipse2 = self.begin
                #si estoy realizando un desplazaimiento de la elipse
                else:
                    #estoy dentro de la elipse 1
                    if self.parent().parent().ellipse1.contains(QPointF(ptoXEllipse, ptoYEllipse)) & self.flagRectEllipse1VsRectEllipse2:
                        #calculo la distrancia entre el punto x-y y el punto clickeado dentro del rectangulo
                        desplazamientoXRecEllip1 = self.end.x() - self.posAnteriorRectEllipse1.x()
                        desplazamientoYRecEllip1 = self.end.y() - self.posAnteriorRectEllipse1.y()
                        self.parent().parent().rectanguloEllipse1.translate(desplazamientoXRecEllip1, desplazamientoYRecEllip1)
                        self.parent().parent().ellipse1.setRect(self.parent().parent().rectanguloEllipse1)
                        self.posTextEllipse1 = self.parent().parent().rectanguloEllipse1.topLeft()
                        self.posAnteriorRectEllipse1 = self.end
                        self.begin = self.end
                    #estoy dentro de la elipse 2
                    else:
                        desplazamientoXRecEllip2 = self.end.x() - self.posAnteriorRectEllipse2.x()
                        desplazamientoYRecEllip2 = self.end.y() - self.posAnteriorRectEllipse2.y()
                        self.parent().parent().rectanguloEllipse2.translate(desplazamientoXRecEllip2, desplazamientoYRecEllip2)
                        self.parent().parent().ellipse2.setRect(self.parent().parent().rectanguloEllipse2)
                        self.posTextEllipse2 = self.parent().parent().rectanguloEllipse2.topLeft()
                        self.posAnteriorRectEllipse2 = self.end
                        self.begin = self.end
        ####
        self.update()
    def mouseReleaseEvent(self, event):
        #detecto la posicion en la que se solto el mouse
        self.end = event.pos()
        #rectangulo
        if self.parent().parent().toolROIs == 0:    
            #determino si estoy soltando el borde
            if self.clickBordeRect:
                print("fin ajuste tama;o")
                self.clickBordeRect = False
                self.clickBordeTopLeftRect1 = False
                self.clickBordeTopLeftRect2 = False
                self.clickBordeBottomRightRect1 = False
                self.clickBordeBottomRightRect2 = False
            #estoy soltando una nueva roi
            else:
                if self.flag:
                    if self.parent().parent().indiceRect == 0:
                        self.parent().parent().rectangulo1 = QRect(self.begin, self.end)
                        self.posTextRect1 = self.begin
                        self.parent().parent().indiceRect = 1
                    else:
                        self.parent().parent().rectangulo2 = QRect(self.begin, self.end)
                        self.parent().parent().indiceRect = 0
                        self.posTextRect2 = self.begin
        #recta
        if self.parent().parent().toolROIs == 1:
            if self.clickBordeRecta:
                print("fin ajuste tamaño")
                self.clickBordeRecta = False
                self.clickBordeLeftRecta1 = False
                self.clickBordeLeftRecta2 = False
                self.clickBordeRightRecta1 = False
                self.clickBordeRightRecta2 = False
            else:
                print(self.begin, self.end)
                if self.flag:
                    if self.parent().parent().indiceRect == 0:
                        self.parent().parent().recta1 = QLine(self.begin,self.end)
                        self.posTextRecta1 = self.begin
                        self.parent().parent().indiceRect = 1
                    else:
                        self.parent().parent().recta2 = QLine(self.begin,self.end)
                        self.parent().parent().indiceRect = 0
                        self.posTextRecta2 = self.begin
        #elipse
        if self.parent().parent().toolROIs == 2:
            if self.clickBordeEllipse:
                self.clickBordeEllipse = False
                self.clickBordeTopRectEllipse1 = False
                self.clickBordeTopRectEllipse2 = False
                self.clickBordeRightRectEllipse1 = False
                self.clickBordeRightRectEllipse2 = False
            #si no es un click en el borde es que se dibujo uno nuevo o se translado uno ya existente
            else:
                if self.flag:
                    if self.parent().parent().indiceEllipse == 0:
                        self.parent().parent().rectanguloEllipse1 = QRectF(self.begin, self.end)
                        self.parent().parent().ellipse1 = QGraphicsEllipseItem(self.parent().parent().rectanguloEllipse1)
                        self.posTextEllipse1 = self.begin
                        self.parent().parent().indiceEllipse = 1
                    else:
                        self.parent().parent().rectanguloEllipse2 = QRectF(self.begin, self.end)
                        self.parent().parent().ellipse2 = QGraphicsEllipseItem(self.parent().parent().rectanguloEllipse2)
                        self.parent().parent().indiceEllipse = 0
                        self.posTextEllipse2 = self.begin
                else:
                    self.parent().parent().presionTeclaEnEllipse1Flag = False
                    self.parent().parent().presionTeclaEnEllipse2Flag = False
        ####
        self.update()
    
#
class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True
    
    def run(self):
        cap = cv2.VideoCapture(0)
        while self._run_flag:
            ret, cv_img = cap.read()
            print(ret)
            if ret:
                self.change_pixmap_signal.emit(cv_img)
        cap.release()
    
    def stop(self):
        self._run_flag = False
        self.wait()


class App(QWidget):
    def __init__(self):
        super().__init__()
        #widget contenedor para toolbar, para imagen y para label
        self.subwindow = QWidget()
        #
        self.display_width = 640
        self.display_height = 480
        self.setWindowTitle("Probamos Agregar Toolbar")
        #Defino los rectangulos
        self.beginRect = QPoint()
        self.endRect = QPoint()
        
        #configuro los objetos para visualizar la imagen
        self.image = TestImage()
        #configuro una iamgen
        self.textLabel = QLabel("WebCam")       
        #########################Escala##################
        self.zoomInEscala = 1.25
        self.zoomOutEscala = 0.8
        self.zoomInOut = 1
        #
        self.image.setBackgroundRole(QPalette.Base)
        self.image.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image.setScaledContents(True)
        #
        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.image)
        self.scrollArea.setVisible(True)
        #
        self.scrollArea.zoomInButton = False
        self.scrollArea.zoomOutButton = False
        #########################Escala###################
        #
        self.scrollArea.indiceRect = 0
        #       
        #defino los rectangulos
        self.scrollArea.rectangulo1 = QRect(self.beginRect, self.endRect)
        self.scrollArea.rectangulo2 = QRect(self.beginRect, self.endRect)
        self.scrollArea.listaRects = [self.scrollArea.rectangulo1, self.scrollArea.rectangulo2]
        #defino las lineas
        self.beginLinea = QPoint()
        self.endLinea = QPoint()
        self.scrollArea.recta1 = QLine(self.beginLinea, self.endLinea)
        self.scrollArea.recta2 = QLine(self.beginLinea, self.endLinea)
        self.scrollArea.indiceRecta = 0
        #defino las elipses o circulos
        self.beginEllipse = QPoint()
        self.endEllipse = QPoint()
        #definimos la elipse 1
        self.scrollArea.rectanguloEllipse1 = QRectF(self.beginEllipse, self.endEllipse)
        self.scrollArea.ellipse1 = QGraphicsEllipseItem(self.scrollArea.rectanguloEllipse1)
        #definimos la elipse 2
        self.scrollArea.rectanguloEllipse2 = QRectF(self.beginEllipse, self.endEllipse)
        self.scrollArea.ellipse2 = QGraphicsEllipseItem(self.scrollArea.rectanguloEllipse2)
        #detecto el angulo
        self.scrollArea.anguloEllipse1 = self.scrollArea.ellipse1.rotation()
        self.scrollArea.anguloEllipse2 = self.scrollArea.ellipse2.rotation()
        #numero de clicks
        self.scrollArea.clickEllipse1 = 0
        self.scrollArea.clickEllipse2 = 0
        #detecto la tecla presionada
        self.scrollArea.teclaUpGirarEllipse1 = False
        self.scrollArea.teclaDownGirarEllipse1 = False
        self.scrollArea.teclaUpGirarEllipse2 = False
        self.scrollArea.teclaDownGirarEllipse2 = False
        self.scrollArea.presionTeclaEnEllipse1Flag = False
        self.scrollArea.presionTeclaEnEllipse2Flag = False
        #indice para indicar que ellipse estoy usando
        self.scrollArea.indiceEllipse = 0
        #
        self.scrollArea.toolROIs = 0
        #
        self.thread = VideoThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()
        #
        toolbar = QToolBar("Mi toolbar")
        toolbar.setIconSize(QSize(16,16))
        #self.addToolBar(toolbar)
        #creamos un boton en el toolbar para dibujar una roi rectangular
        self.button_actionRect = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape.png")),"ROI Rect", self)
        self.button_actionRect.setStatusTip("Draw a rectangle")
        self.button_actionRect.triggered.connect(self.drawROIRectangle)
        self.button_actionRect.setCheckable(True)
        #agregamos este buttonAction dibujar rectangulo al toolbar
        toolbar.addAction(self.button_actionRect)
        #creamos un boton en el toolbar para dibujar una roi lineal
        self.button_actionLine = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape-line.png")), "ROI Line", self)
        self.button_actionLine.setStatusTip("Draw a line")
        self.button_actionLine.triggered.connect(self.drawROILine)
        self.button_actionLine.setCheckable(True)
        #agregamos este buttonAction dibujar linea al toolbar
        toolbar.addAction(self.button_actionLine)
        #creamos un boton en el toolbar para dibujar una roi circulo o ellipse
        self.button_actionCircle = QAction(QIcon(os.path.join(basedir,"appIcons", "layer-shape-ellipse.png")), "ROI Circle", self)
        self.button_actionCircle.setStatusTip("Draw a circle")
        self.button_actionCircle.triggered.connect(self.drawROICircle)
        self.button_actionCircle.setCheckable(True)
        #agregamos este buttonAction dibujar circulo al toolbar
        toolbar.addAction(self.button_actionCircle)

        self.button_actionZoomIn = QAction(QIcon(os.path.join(basedir, "appIcons", "magnifier-zoom-in.png")), "ROI ZoomIn", self)
        self.button_actionZoomIn.setStatusTip("ZoomIn on Image")
        self.button_actionZoomIn.triggered.connect(self.makeZoomIn)
        self.button_actionZoomIn.setCheckable(True)

        toolbar.addAction(self.button_actionZoomIn)

        self.button_actionZoomOut = QAction(QIcon(os.path.join(basedir, "appIcons", "magnifier-zoom-out.png")), "ROI ZoomOut", self)
        self.button_actionZoomOut.setStatusTip("ZoomOut on Image")
        self.button_actionZoomOut.triggered.connect(self.makeZoomOut)
        self.button_actionZoomOut.setCheckable(True)

        toolbar.addAction(self.button_actionZoomOut)

        #
        vbox = QVBoxLayout()  
        vbox.addWidget(toolbar)      
        vbox.addWidget(self.scrollArea)#image)        
        self.subwindow.setLayout(vbox)
        #
        hbox = QHBoxLayout()
        hbox.addWidget(self.subwindow)
        #hbox.addWidget(self.image)
        hbox.addWidget(self.textLabel)
        self.setLayout(hbox)

        #self.setStatusBar(QStatusBar(self))
    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        #print(cv_img)
        qt_img = self.convert_cv_qt(cv_img)
        self.image.setPixmap(qt_img)
    
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.display_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()
    
    def drawROIRectangle(self, statusButton):
        print("click make a ROI Rectangle", statusButton)
        #logica para dibujar un rectangulo
        self.scrollArea.toolROIs = 0
        self.scrollArea.zoomInButton = False
        self.scrollArea.zoomOutButton = False
        if statusButton:
            self.button_actionLine.setChecked(False)
            self.button_actionCircle.setChecked(False)
            self.button_actionZoomIn.setChecked(False)
            self.button_actionZoomOut.setChecked(False)
            
    def drawROILine(self, statusButton):
        print("click make a ROI Line", statusButton)
        statusTip = self.parent().statusTip()
        print("status tip", statusTip)
        #logica para dibujar una linea
        self.scrollArea.toolROIs = 1
        self.scrollArea.zoomInButton = False
        self.scrollArea.zoomOutButton = False
        if statusButton:
            self.button_actionRect.setChecked(False)
            self.button_actionCircle.setChecked(False)
            self.button_actionZoomIn.setChecked(False)
            self.button_actionZoomOut.setChecked(False)

    def drawROICircle(self, statusButton):
        print("click make a ROI Circle", statusButton)
        #logica para dibujar un circulo
        self.scrollArea.toolROIs = 2
        self.scrollArea.zoomInButton = False
        self.scrollArea.zoomOutButton = False
        if statusButton:
            self.button_actionRect.setChecked(False)
            self.button_actionLine.setChecked(False)
            self.button_actionZoomIn.setChecked(False)
            self.button_actionZoomOut.setChecked(False)

    def makeZoomIn(self, statusButton):
        print("click on Zoom IN", statusButton)
        #logica para hacer zoomIn
        self.scrollArea.toolROIs = 3 #ningun herramienta roi
        self.scrollArea.zoomInButton = True
        self.scrollArea.zoomOutButton = False
        if statusButton:
            self.button_actionRect.setChecked(False)
            self.button_actionLine.setChecked(False)
            self.button_actionCircle.setChecked(False)
            self.button_actionZoomOut.setChecked(False)

    def makeZoomOut(self, statusButton):
        print("click on Zoom OUT", statusButton)
        #logica para hacer zoomOut
        self.scrollArea.toolROIs = 3 #ningun herramienta roi
        self.scrollArea.zoomInButton = False
        self.scrollArea.zoomOutButton = True
        if statusButton:
            self.button_actionRect.setChecked(False)
            self.button_actionLine.setChecked(False)
            self.button_actionCircle.setChecked(False)
            self.button_actionZoomIn.setChecked(False)

app = QApplication(sys.argv)
w = App()
w.show()
sys.exit(app.exec())