
from functools import partial
from PyQt5 import QtGui, QtCore,QtWidgets
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QPen, QPalette
from PyQt5.QtCore import QDateTime, Qt, QTimer, pyqtSignal, QSize, QPoint, QPointF, QRect, QLine, QRectF, QEasingCurve, QPropertyAnimation, QSequentialAnimationGroup, pyqtSlot, pyqtProperty, QThread
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDial,
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollBar,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QStyleFactory,
    QTableWidget,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QGraphicsScene,
    QGraphicsView,
    QToolBar,
    QAction,
    QGraphicsEllipseItem,
    QScrollArea   
)
from PyQt5.QtGui import QIcon, QPaintEvent
from cv2 import ellipse
import matplotlib
from matplotlib.widgets import Widget
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import pandas as pd
import sys, os
import numpy as np
import ctypes as ct
import cv2
import os
import random
from matplotlib import pyplot as plt
#direccion base para los archivos de imagen
basedir = os.path.dirname(__file__)
#detecto si se cargo la imagen
try:
    from ctypes import winddl
    myappid = "ar.com.tgs.cameraApp.00"
    winddl.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass
#***************************************************
#clase para herramientas de imagen
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
    #barras de scroll bar a lado derecho e inferior  
    def adjustScrollBar(self, scrollBar, factor):
    #capturo el redibujo de la imagen en el textlabel
        scrollBar.setValue(int(factor * scrollBar.value() + ((factor - 1) * scrollBar.pageStep()/2)))
    #sobrecargamos el evento de imagen en textlabel
    def paintEvent(self, event):
    #sobrecargo el metodo paint de la clase label
        super().paintEvent(event)
        try:
            escala = self.scaleFactor * self.pixmap().size()
            #print(escala)
            self.resize(escala)
            flagEstado = True            
        except:
            print("error Image")
            flagEstado = False #si tenemos un error en la adquisicion no agregamos los objetos en la imagen
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
            qp.drawRect(self.parent().parent().rectangulo1) #
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
            #actualizo la lista con los valores de posicion QPoint para cada Roi
            self.parent().parent().listaRects=[self.parent().parent().rectangulo1,self.parent().parent().rectangulo2]
            self.parent().parent().listaLineas=[self.parent().parent().recta1,self.parent().parent().recta2]
            self.parent().parent().listaElipses=[self.parent().parent().rectanguloEllipse1,self.parent().parent().rectanguloEllipse2]
            #mostramos la lista de cada uno de los rois
            #print(self.parent().parent().listaRects)
            #print(self.parent().parent().listaLineas)
            #print(self.parent().parent().listaElipses)
    #sobrecargamos el evento de presion de mouse
    def mousePressEvent(self, event):
        #detecto la posicion del ultimo movimiento
        self.begin = event.pos()
        #####################################################
        #print("mouse click", self.scaleFactor)
        if  self.parent().parent().zoomInButton == True:
            self.scala = 1.25
        elif self.parent().parent().zoomOutButton == True:
            self.scala = 0.8
        else:
            self.scala = 1
        #calculamos el factor de escala
        self.scaleFactor *= self.scala
        #detectamos si se esta dibujando los rectangulos
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
            #comparamos si se esta haciendo un click
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
        #detecto si se estan dibujando las rectas
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
                    #print("click borde superior rect ellipse 1")
                    self.clickBordeLeftRectEllipse1 = True
                #detecto el borde izquierdo ellipse 2
                elif condicionClickBordeLeftRectEllipse2:
                    #print("click bordesuperior rect ellipse 2")
                    self.clickBordeLeftRectEllipse2 = True
                #detecto el borde derecho ellipse 1
                elif condicionClickBordeRightRectEllipse1:
                    #print("click borde derecho rect ellipse 1")
                    self.clickBordeRightRectEllipse1 = True
                #detecto el borde derecho ellipse 2
                elif condicionClickBordeRightRectEllipse2:
                    #print("click borde derecho rect ellipse 2")
                    self.clickBordeRightRectEllipse2 = True
                #detecto el borde superio ellipse 1
                elif condicionClickBordeTopRectEllipse1:
                    #print("click borde top rect ellipse 1")
                    self.clickBordeTopRectEllipse1 = True
                #detecto el borde superior ellipse 2
                elif condicionClickBordeTopRectEllipse2:
                    #print("click borde top rect ellipse 2")
                    self.clickBordeTopRectEllipse2 = True
                #detecto el borde inferior ellipse 1
                elif condicionClickBordeBottomRectEllipse1:
                    #print("click borde bottom rect ellipse 1")
                    self.clickBordeBottomRectEllipse1 = True
                #detecto el borde inferior ellipse 2
                elif condicionClickBordeBottomRectEllipse2:
                    #print("click borde bottom rect ellipse 2")
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
    #sobrecargamos el evento de move del mouse
    def mouseMoveEvent(self, event):
        #detecto la posiocion del mouse
        self.end = event.pos()
        #print(self.end)
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
                        #print(desplazamientoXRecta1)
                        #print(desplazamientoYRecta1)
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
    #sobrecargamos el evento de soltar el mouse
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
                #print(self.begin, self.end)
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
#***************************************************
#Clase para comunicacion con camara optris
class EvoIRFrameMetadata(ct.Structure):
     _fields_ = [("counter", ct.c_uint),
                 ("counterHW", ct.c_uint),
                 ("timestamp", ct.c_longlong),
                 ("timestampMedia", ct.c_longlong),
                 ("flagState", ct.c_int),
                 ("tempChip", ct.c_float),
                 ("tempFlag", ct.c_float),
                 ("tempBox", ct.c_float),
                 ]
class VideoThread(QThread): #creo el hilo para manejar la adquisicion de imagen
    change_pixmap_signal = pyqtSignal(np.ndarray)
    change_thermal_signal = pyqtSignal(np.ndarray)
    def __init__(self): #sobre escribimos la clase
        super().__init__()
        self._run_flag = True #utilizamos este flag para indicar al hilo que termine la adquisicion

    def run(self):  #funcion que sobre escribimos de run del hilo
        # capture from thermal cam
        # load library
        if os.name == 'nt':
                #windows:
                libir = ct.CDLL("c:\\irDirectSDK\\sdk\\x64\\libirimager.dll") 
        else:
                #linux:
                libir = ct.cdll.LoadLibrary(ct.util.find_library("irdirectsdk"))

        #path to config xml file ---> ../config/generic.xml 
        pathXml = ct.c_char_p(b'C:\Users\lupus\OneDrive\Documentos\ProcesamientoDeImagenes\config\generic.xml')

        # init vars
        pathFormat = ct.c_char_p()      #tipo de formato que usamos para el path a la libreria
        
        
        pathLog = ct.c_char_p(b'logfilename')   #tipo de formato que usamos par ael path al archivo de log

        palette_width = ct.c_int() #dimension de la paleta ..ancho
        palette_height = ct.c_int()  #dimension de la paleta ..alto

        thermal_width = ct.c_int() #dimension de la paleta termica ..ancho
        thermal_height = ct.c_int() #dimension de la paleta termica ..alto

        serial = ct.c_ulong() #numero serial de la camara
        # init EvoIRFrameMetadata structure
        metadata = EvoIRFrameMetadata() #instanciamos a la clase de EVO cortex la estructura

        # init lib
        ret = libir.evo_irimager_usb_init(pathXml, pathFormat, pathLog) #instancio a la libreria de evo para
        if ret != 0:                                                    #conectar con camara usb de optris
                print("error at init")                                  #si hay error salgo y retorno el error
                exit(ret)                                               #de la camara

        # get the serial number
        ret = libir.evo_irimager_get_serial(ct.byref(serial))           #si la conexxion salio bien retorno el 
        print('serial: ' + str(serial.value))                           #numero serie de la camara

        # get thermal image size
        libir.evo_irimager_get_thermal_image_size(ct.byref(thermal_width), ct.byref(thermal_height))
        print('thermal width: ' + str(thermal_width.value))     #utilizamos el metodo de la libreria para determinar
        print('thermal height: ' + str(thermal_height.value))   #el tama;o de la imagen. El ancho y el alto
        
        # init thermal data container
        np_thermal = np.zeros([thermal_width.value * thermal_height.value], dtype=np.uint16)
        npThermalPointer = np_thermal.ctypes.data_as(ct.POINTER(ct.c_ushort)) #utilizo la libreria ctypes para manipular datos de C
                                                                              #en python

        # get palette image size, width is different to thermal image width duo to stride alignment!!!
        libir.evo_irimager_get_palette_image_size(ct.byref(palette_width), ct.byref(palette_height))
        print('palette width: ' + str(palette_width.value)) #con la libreria de evo obtengo la imagen y cargo los datos
        print('palette height: ' + str(palette_height.value)) #de ancho y alto para la paleta 

        # init image container
        np_img = np.zeros([palette_width.value * palette_height.value * 3], dtype=np.uint8)
        npImagePointer = np_img.ctypes.data_as(ct.POINTER(ct.c_ubyte))

        #a partir de aca comenzamos a obtener la imagen        
        while self._run_flag == True: #capturo la imagen mientras no este activa el flag de detener
                #get thermal and palette image with metadat
                ret = libir.evo_irimager_get_thermal_palette_image_metadata(thermal_width, thermal_height, npThermalPointer, palette_width, palette_height, npImagePointer, ct.byref(metadata))
                #obtenemos de evo la imagen, ademas los datos de ancho y algo termico. los datos de imagen ancho y alto. el dato np termico y el dato np de imagen
                #le tenemos que pasar como dato la estructura evo que definimos antes
                if ret != 0:
                        print('error on evo_irimager_get_thermal_palette_image ' + str(ret))
                        continue
                #si llega a responder con un error lo indicamos 
                #calculate total mean value
                mean_temp = np_thermal.mean() #sobre el contenido de la imagen que retorna calculo una media.
                mean_temp = mean_temp / 10. - 100 #le saco un cero y le resto 100
                #print('Mean Temp: ' + str(mean_temp)) #mostramos el promedio

                #display palette image
                #cv2.imshow('Optris Image Test',np_img.reshape(palette_height.value, palette_width.value, 3)[:,:,::-1])
                frame = np_img.reshape(palette_height.value, palette_width.value, 3)[:,:,::-1]
                self.change_pixmap_signal.emit(frame) #convierto el dato en formato numpy a un formato de qt5
                np_thermalEscalado = np_thermal / 10. - 100
                frameThermal = np_thermalEscalado.reshape( thermal_height.value, thermal_width.value)
                self.change_thermal_signal.emit(frameThermal)
        # clean shutdown
        libir.evo_irimager_terminate()   #si se detiene el hilo de adquisicion termino el hilo de ejecucion

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False #cuando el hilo se termina indicamos con el flag que salga del while
        self.wait()
#***************************************************
#***************************************************
#Clase barra de niveles
class _Bar(QtWidgets.QWidget):
    clickedValue = QtCore.pyqtSignal(int)

    def __init__(self, steps, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding,
            QtWidgets.QSizePolicy.MinimumExpanding
        )
        if isinstance(steps, list):
            #lista de colores
            self.n_steps = len(steps)
            self.steps = steps
        elif isinstance(steps, int):
            #int tiene el numero de barras, el color es rojo
            self.n_steps = steps
            self.steps = ['red'] * steps
        else:
            raise TypeError('steps debe ser una lista o un int')
        
        self._bar_solid_percent = 0.8
        self._background_color = QtGui.QColor('black')
        self._padding = 4.0
    def sizeHint(self):
        return QtCore.QSize(40,120)

    def paintEvent(self, e):
        painter = QtGui.QPainter(self)
        brush = QtGui.QBrush()
        brush.setColor(self._background_color)
        brush.setStyle(Qt.SolidPattern)
        rect = QtCore.QRect(0,0,painter.device().width(),painter.device().height())
        painter.fillRect(rect, brush)
        #obtenemos el estado actual
        dial = self.parent()._dial        
        vmin, vmax = dial.minimum(), dial.maximum()
        value = dial.value()
        #print(value)
        labelValue = self.parent().valorQDial
        labelValue.setText(str(value))
        #definimos nuestro canvas
        d_height = painter.device().height() - (self._padding * 2)
        d_width = painter.device().width() - (self._padding * 2)
        #dibujo las barras
        step_size = d_height / self.n_steps
        bar_height = step_size * self._bar_solid_percent
        bar_spacer = step_size * (1 - self._bar_solid_percent) / 2
        #calculamos el y-stop position, usando el valor dentro del rango
        pc = (value - vmin) / (vmax - vmin)
        n_steps_to_draw = int(pc * self.n_steps)

        for n in range(n_steps_to_draw):
            brush.setColor(QtGui.QColor(self.steps[n]))
            rect = QtCore.QRect(
                self._padding,
                self._padding + d_height - ((1+n) * step_size) + bar_spacer,
                d_width,
                bar_height
            )
            painter.fillRect(rect, brush)
            
        
        painter.end()
    def _trigger_refresh(self,i):
        #print("valor actual: ",i)
        self.update()
#Clase para mostrar la Powerbar 
class PowerBar(QtWidgets.QWidget):    
    def __init__(self, steps=5, *args, **kwargs):    
        super().__init__(*args, **kwargs)
        #creo el layout horizontal para mostrar las barras y el dial
        layout = QHBoxLayout()
        #creo una instancia a las barras y la agrego al layout
        self._bar = _Bar(steps)
        layout.addWidget(self._bar)
        #creo el dial
        self._dial = QtWidgets.QDial()
        #seteo los valores maximos y minimos
        self._dial.setMinimum(0)
        self._dial.setMaximum(100)
        self._dial.setSingleStep(10)
        self._dial.setNotchesVisible(True)
        #agrego el dial al layout
        layout.addWidget(self._dial)
        #indicador
        self.valorQDial = QLabel()
        self.valorQDial.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.valorQDial.setFixedSize(QSize(40,23))
        layout.addWidget(self.valorQDial)
        #asocio la powerbar a la funcion de trigger de la clase _bar
        self._dial.valueChanged.connect(self._bar._trigger_refresh)
        #seteo el alyout 
        self.setLayout(layout)
#Clase boton para checkear
class AnimatedToggle(QCheckBox):

    _transparent_pen = QPen(Qt.transparent)
    _light_grey_pen = QPen(Qt.lightGray)

    def __init__(
        self,
        parent =None,
        bar_color = Qt.gray,
        checked_color = "#00B0FF",
        handle_color = Qt.white,
        pulse_unchecked_color = "#44999999",
        pulse_checked_color = "#4400B0EE"
        ):
        super().__init__(parent)

        self._bar_brush = QBrush(bar_color)
        self._bar_checked_brush = QBrush(QColor(checked_color).lighter())

        self._handle_brush = QBrush(handle_color)
        self._handle_checked_brush = QBrush(QColor(checked_color))

        self._pulse_unchecked_animation = QBrush(QColor(pulse_unchecked_color))
        self._pulse_checked_animation = QBrush(QColor(pulse_checked_color))

        self.setContentsMargins(8, 0, 8, 0)
        self._handle_position = 0
        
        self._pulse_radius = 0

        self.animation = QPropertyAnimation(self, b"handle_position", self)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.setDuration(200)

        self.pulse_anim = QPropertyAnimation(self, b"pulse_radius", self)
        self.pulse_anim.setDuration(350)
        self.pulse_anim.setStartValue(10)
        self.pulse_anim.setEndValue(20)

        self.animations_group = QSequentialAnimationGroup()
        self.animations_group.addAnimation(self.animation)
        self.animations_group.addAnimation(self.pulse_anim)

        self.stateChanged.connect(self.setup_animation)

    def sizeHint(self):
        return QSize(58,45)
    
    def hitButton(self, pos:QPoint):
        return self.contentsRect().contains(pos)
    
    @pyqtSlot(int)
    def setup_animation(self, value):
        self.animations_group.stop()
        if value:
            self.animation.setEndValue(1)
        else:
            self.animation.setEndValue(0)
        self.animations_group.start()
    
    def paintEvent(self, e:QPaintEvent):
        contRect = self.contentsRect()
        handleRadius = round(0.24 * contRect.height())

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setPen(self._transparent_pen)
        barRect = QRectF(
            0,
            0,
            contRect.width() - handleRadius,
            0.4 * contRect.height()
        )
        barRect.moveCenter(contRect.center())
        rounding = barRect.height() / 2

        trailLength = contRect.width() -2 * handleRadius

        xPos = contRect.x() + handleRadius + trailLength * self._handle_position

        if self.pulse_anim.state() == QPropertyAnimation.Running:
            p.setBrush(self._bar_checked_brush)
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setBrush(self._handle_checked_brush)
        else:
            p.setBrush(self._bar_brush)
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setBrush(self._handle_checked_brush)
        
        p.drawEllipse(
            QPointF(xPos, 
            barRect.center().y()),
            handleRadius,
            handleRadius
        )
        p.end()

    @pyqtProperty(float)
    def handle_position(self):
        return self._handle_position
    
    @handle_position.setter
    def handle_position(self,pos):
        self._handle_position = pos
        self.update()
    
    @pyqtProperty(float)
    def pulse_radius(self):
        return self._pulse_radius
    
    @pulse_radius.setter
    def pulse_radius(self, pos):
        self._pulse_radius = pos
        self.update()
#Clase para graficar curvas
class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width,height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas,self).__init__(fig)
#Clase modelo generico de seleccion de fecha
class PopUpDateSelected(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Request initial date and final date")
        layoutV = QVBoxLayout()
        self.inputInitialDate = QLabel("Initial Date")        
        self.dateTimeStart = QDateTimeEdit()
        self.dateTimeStart.setDateTime(QDateTime.currentDateTime())
        self.inputInitialDate.setBuddy(self.dateTimeStart)
        self.dateTimeStart.setCalendarPopup(True)
        self.inputFinalDate = QLabel("Final Date")
        self.dateTimeEnd = QDateTimeEdit()
        self.dateTimeEnd.setDateTime(QDateTime.currentDateTime())
        self.inputFinalDate.setBuddy(self.dateTimeEnd)
        self.dateTimeEnd.setCalendarPopup(True)
        layoutV = QVBoxLayout()
        layoutV.addWidget(self.inputInitialDate)
        layoutV.addWidget(self.dateTimeStart)
        layoutV.addWidget(self.inputFinalDate)
        layoutV.addWidget(self.dateTimeEnd)

        self.okSearchButton = QPushButton("Search")
        self.okSearchButton.clicked.connect(self.realizarBusquedaOk)
        self.okSearchButton.setIcon(QIcon(os.path.join(basedir,"appIcons","magnifier.png")))
        self.cancelSearchButton = QPushButton("Cancel")
        self.cancelSearchButton.clicked.connect(self.realizarBusquedaCancel)
        self.cancelSearchButton.setIcon(QIcon(os.path.join(basedir,"appIcons","cross-circle-frame.png")))
        layoutH = QHBoxLayout()
        layoutH.addWidget(self.okSearchButton)
        layoutH.addWidget(self.cancelSearchButton)

        layoutV.addLayout(layoutH)
        self.setLayout(layoutV)
        self.resize(400,20)
        self.dateTimeStart.setFocus(Qt.NoFocusReason)
    def realizarBusquedaOk(self):
        print("Buscando ...")
    def realizarBusquedaCancel(self):
        print("Cancelar busqueda")
        self.close()
#Clase modelo generico de reset preset control
#usamos esta clase para ajustar los valores de control para cada
#funcionalidad que tenga la pantalla (tab)
class PopUpResetPresetTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reset Preset of Control")
        #aca va la funcionalidad del graficador con el control
        layoutPresetCurrentResetTab = QVBoxLayout()
        #valor de preset actual
        self.labelCurrentPresetTab = QLabel("Current Control Tab")
        self.valueCurrentPresetTab = QLineEdit("124.15")
        self.valueCurrentPresetTab.setStyleSheet("border: 2px solid black; background-color : lightgray;")        
        self.labelCurrentPresetTab.setBuddy(self.valueCurrentPresetTab)
        #valor de preset a cambiar
        self.labelDefaultPresetTab = QLabel("Default Control Tab")
        self.valueDefaultPresetTab = QLineEdit("124.15")
        self.valueDefaultPresetTab.setStyleSheet("border: 2px solid black;background-color:lightgreen;")
        self.labelDefaultPresetTab.setBuddy(self.valueDefaultPresetTab)
        #agrego los dos widgets al layout
        layoutPresetCurrentResetTab.addWidget(self.labelCurrentPresetTab)
        layoutPresetCurrentResetTab.addWidget(self.valueCurrentPresetTab)
        layoutPresetCurrentResetTab.addWidget(self.labelDefaultPresetTab)
        layoutPresetCurrentResetTab.addWidget(self.valueDefaultPresetTab)
        #layout horizontal para los controles de los botones
        layoutPresetCurrentDefaultBotones = QHBoxLayout()
        #agrego los botones de control aceptar
        self.okDefaulPresetTab = QPushButton("Reset Control")
        self.okDefaulPresetTab.clicked.connect(self.okUpDatePresetTab)
        self.okDefaulPresetTab.setIcon(QIcon(os.path.join(basedir,"appIcons","arrow-curve-270.png")))
        #agrego el boton de control cancel
        self.cancelDefaultPresetTab = QPushButton("Cancel Change")
        self.cancelDefaultPresetTab.clicked.connect(self.cancelUpDatePresetTab)
        self.cancelDefaultPresetTab.setIcon(QIcon(os.path.join(basedir,"appIcons","cross-circle-frame.png")))
        #agrego el layout horizontal
        layoutPresetCurrentDefaultBotones.addWidget(self.okDefaulPresetTab)
        layoutPresetCurrentDefaultBotones.addWidget(self.cancelDefaultPresetTab)
        #agrego al layout vertical el horizontal
        layoutPresetCurrentResetTab.addLayout(layoutPresetCurrentDefaultBotones)
        self.setLayout(layoutPresetCurrentResetTab)
        self.resize(400,20)
        self.labelDefaultPresetTab.setFocus(Qt.NoFocusReason)
    def okUpDatePresetTab(self):
        print("Bajando default value al control")
    def cancelUpDatePresetTab(self):
        print("Cancelar default value al control")
        self.close()
#Clase modelo generico de preset control 
class PopUpWritePresetTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Write Preset of Control")
        layoutPresetCurrentNew = QVBoxLayout()
        #grafico powerbar
        volumenCtrl = PowerBar(["#5e4fa2","#3288bd","#66c2a5","#abdda4","#e6f598"])
        #
        layoutPresetCurrentNew.addWidget(volumenCtrl)
        #agrego el layout horizontal
        layoutPresetCurrentNewBotones = QHBoxLayout()
        #agrego los botones de control aceptar
        self.okNewPreset = QPushButton("Update")
        self.okNewPreset.clicked.connect(self.okUpDatePresetCtrl)
        self.okNewPreset.setIcon(QIcon(os.path.join(basedir,"appIcons", "arrow-curve-270.png")))
        #agreg el boton de control cancel
        self.cancelNewPreset = QPushButton("Cancel")
        self.cancelNewPreset.clicked.connect(self.cancelUpDatePresetCtrl)
        self.cancelNewPreset.setIcon(QIcon(os.path.join(basedir,"appICons","cross-circle-frame.png")))
        #agrego el layout horizontal
        layoutPresetCurrentNewBotones.addWidget(self.okNewPreset)
        layoutPresetCurrentNewBotones.addWidget(self.cancelNewPreset)
        #agrego al layout vertical el horizontal
        layoutPresetCurrentNew.addLayout(layoutPresetCurrentNewBotones)
        self.setLayout(layoutPresetCurrentNew)
        self.resize(400,20)
        self.okNewPreset.setFocus(Qt.NoFocusReason)
    def okUpDatePresetCtrl(self):
        print("Bajando preset a camara")
    def cancelUpDatePresetCtrl(self):
        print("Cancelar preset a camara")
        self.close()
#Clase modelo generico de reset preset camara
class PopUpResetPresetCam(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reset Preset Of Camera")
        layoutPresetCurrentReset = QVBoxLayout()
        #valor de preset actual
        self.labelCurrentPreset = QLabel("Current Preset")
        self.valueCurrentPreset = QLineEdit("124.15")
        self.valueCurrentPreset.setStyleSheet("border: 2px solid black; background-color : lightgray;")        
        self.labelCurrentPreset.setBuddy(self.valueCurrentPreset)
        #valor de preset a cambiar
        self.labelDefaultPreset = QLabel("Default Preset")
        self.valueDefaultPreset = QLineEdit("124.15")
        self.valueDefaultPreset.setStyleSheet("border: 2px solid black; background-color:lightgreen;")
        self.labelDefaultPreset.setBuddy(self.valueDefaultPreset)
        #agrego los dos widgets al layout
        layoutPresetCurrentReset.addWidget(self.labelCurrentPreset)
        layoutPresetCurrentReset.addWidget(self.valueCurrentPreset)
        layoutPresetCurrentReset.addWidget(self.labelDefaultPreset)
        layoutPresetCurrentReset.addWidget(self.valueDefaultPreset)
        #layout horizontal para los botones de aceptar rechazar
        layoutPresetCurrentDefaultBotones = QHBoxLayout()
        #agrego los botones de control aceptar
        self.okDefaultPreset = QPushButton("Reset")
        self.okDefaultPreset.clicked.connect(self.okUpDatePresetCam)
        self.okDefaultPreset.setIcon(QIcon(os.path.join(basedir,"appIcons","arrow-curve-270.png")))
        #agrego el boton de control cancel
        self.cancelDefaultPreset = QPushButton("Cancel")
        self.cancelDefaultPreset.clicked.connect(self.cancelUpDatePresetCam)
        self.cancelDefaultPreset.setIcon(QIcon(os.path.join(basedir,"appIcons","cross-circle-frame.png")))
        #agrego al layout horizontal
        layoutPresetCurrentDefaultBotones.addWidget(self.okDefaultPreset)
        layoutPresetCurrentDefaultBotones.addWidget(self.cancelDefaultPreset)
        #agrego al layout vertical el horizontal
        layoutPresetCurrentReset.addLayout(layoutPresetCurrentDefaultBotones)
        self.setLayout(layoutPresetCurrentReset)
        self.resize(400,20)
        self.labelDefaultPreset.setFocus(Qt.NoFocusReason)
    def okUpDatePresetCam(self):
        print("Bajando default value a camara")
    
    def cancelUpDatePresetCam(self):
        print("Cancelar default value a camara")
        self.close()
#Clase modelo generico de cambio preset camara
class PopUPWritePresetCam(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Write Preset Of Camera")
        layoutPresetCurrentNew = QVBoxLayout()
        #valor de preset actual
        self.labelCurrentPreset = QLabel("Current Preset")
        self.valueCurrentPreset = QLineEdit("124.15")
        self.valueCurrentPreset.setStyleSheet("border: 2px solid black; background-color : lightgray;")        
        self.labelCurrentPreset.setBuddy(self.valueCurrentPreset)
        #valor de preset a cambiar
        self.labelNewPreset = QLabel("New Preset")
        self.valueNewPreset = QLineEdit("....")
        self.valueNewPreset.setStyleSheet("border: 2px solid black;")
        self.labelNewPreset.setBuddy(self.valueNewPreset)
        #agrego los dos widgets al layout
        layoutPresetCurrentNew.addWidget(self.labelCurrentPreset)
        layoutPresetCurrentNew.addWidget(self.valueCurrentPreset)
        layoutPresetCurrentNew.addWidget(self.labelNewPreset)
        layoutPresetCurrentNew.addWidget(self.valueNewPreset)
        #layout horizontal para los botones de aceptar rechazar
        layoutPresetCurrentNewBotones = QHBoxLayout()
        #agrego los botones de control aceptar
        self.okNewPreset = QPushButton("Update")
        self.okNewPreset.clicked.connect(self.okUpDatePresetCam)
        self.okNewPreset.setIcon(QIcon(os.path.join(basedir,"appIcons","arrow-curve-270.png")))
        #agrego el boton de control cancel
        self.cancelNewPreset = QPushButton("Cancel")
        self.cancelNewPreset.clicked.connect(self.cancelUpDatePresetCam)
        self.cancelNewPreset.setIcon(QIcon(os.path.join(basedir,"appIcons","cross-circle-frame.png")))
        #agrego al layout horizontal
        layoutPresetCurrentNewBotones.addWidget(self.okNewPreset)
        layoutPresetCurrentNewBotones.addWidget(self.cancelNewPreset)
        #agrego al layout vertical el horizontal
        layoutPresetCurrentNew.addLayout(layoutPresetCurrentNewBotones)
        self.setLayout(layoutPresetCurrentNew)
        self.resize(400,20)
        self.labelNewPreset.setFocus(Qt.NoFocusReason)
    def okUpDatePresetCam(self):
        print("Bajando preset a camara")
    
    def cancelUpDatePresetCam(self):
        print("Cancelar preset a camara")
        self.close()
#Clase modelo generico de loggin 
class PopUpLoggin(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Request User Credential")
        layoutV = QVBoxLayout()
        self.inputUser = QLineEdit()
        self.inputUser.setText("User name input")
        #defino una paleta         
        self.inputUser.setStyleSheet('color:#888;''font:italic;')
        self.inputPassword = QLineEdit()
        self.inputPassword.setText("User password input")
        self.inputPassword.setEchoMode(QLineEdit.Password)  
              
        layoutH = QHBoxLayout()
        self.okLogButton = QPushButton("Loggin")
        self.okLogButton.clicked.connect(self.connectDB)
        self.okLogButton.setIcon(QIcon(os.path.join(basedir,"appIcons","key-solid.png")))
        self.cancelLogButton = QPushButton("Cancel")
        self.cancelLogButton.clicked.connect(self.cancelConnectDB)
        self.cancelLogButton.setIcon(QIcon(os.path.join(basedir,"appIcons","cross-circle-frame.png")))
        #armamos el layout horizontal con los botones
        layoutH.addWidget(self.okLogButton)
        layoutH.addWidget(self.cancelLogButton)
        #armamos el layout vertical usuario password y el horizontal
        layoutV.addWidget(self.inputUser)
        layoutV.addWidget(self.inputPassword)
        layoutV.addLayout(layoutH)
        self.setLayout(layoutV)
        self.resize(400,20)
        self.inputUser.setFocus(Qt.NoFocusReason)
        

    #funcion para conectarse con la base de datos
    def connectDB(self):
        print("Conectando")
    #funcion salir de la ventana
    def cancelConnectDB(self):
        print("Cancelar")
        self.close()
#clase modelo generico de combo box
class UserComboBox(QComboBox):
    popupAboutToBeShown = pyqtSignal()
    def showPopup(self):
        self.popupAboutToBeShown.emit()
        super(UserComboBox,self).showPopup()
class CamComboBox(QComboBox):
    popupAboutToBeShown = pyqtSignal()
    def showPopup(self):
        self.popupAboutToBeShown.emit()
        super(CamComboBox,self).showPopup()
class ROIComboBox(QComboBox):
    popupAboutToBeShown = pyqtSignal()
    def showPopup(self):
        self.popupAboutToBeShown.emit()
        super(ROIComboBox, self).showPopup()
class ProfileComboBox(QComboBox):
    popupAboutToBeShown = pyqtSignal()
    def showPopup(self):
        self.popupAboutToBeShown.emit()
        super(ProfileComboBox, self).showPopup()        
#Clase principal
class MainWindow(QDialog):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        #*****cargo la clase asociada a la comunicacion con la camara
        #*****optris
        #
        self.cam1Width = 0
        self.cam1Height = 0
        #
        #hago una instancia a mi combobox ==> userComboBox
        self.userCombo = UserComboBox(self) #combo box de usuarios
        self.userCombo.popupAboutToBeShown.connect(self.populateUserCombo)
        #
        self.roiSelComboIzq = ROIComboBox(self)
        self.roiSelComboIzq.popupAboutToBeShown.connect(self.populateRoiCombo1)
        #
        self.profileSelComboIzq = ProfileComboBox(self)
        self.profileSelComboIzq.popupAboutToBeShown.connect(self.profileRoiCombo1)
        #
        self.roiSelComboDer = ROIComboBox(self)
        self.roiSelComboDer.popupAboutToBeShown.connect(self.populateRoiCombo2)
        #
        self.camCombo1 = CamComboBox(self) #combo box de camaras para los historicos de la izquierda
        self.camCombo1.popupAboutToBeShown.connect(self.populateCamCombo1)

        self.dateCam1Image = QPushButton("Date Select") #apertura de popup para la seleccion con fecha inicial y final 
                                                        #para los historicos de la izquierda 
        self.dateCam1Image.setToolTip("Select the dates range of images to show")
        self.dateCam1Image.clicked.connect(self.popUpSearchDateToHistory)
        self.dateCam1Image.setIcon(QIcon(os.path.join(basedir, "appIcons","calendar-day.png")))
        
        self.img1ComboBoxReading = QComboBox(self)
        self.imag1_icon = QIcon(os.path.join(basedir,"appIcons","image.png"))
        self.img1ComboBoxReading.addItem(self.imag1_icon,"image_1") #despues de realizar la consulta a los registros
        self.img1ComboBoxReading.addItem(self.imag1_icon,"image_2") #de imagenes vamos a llenar estos datos con las 
        self.img1ComboBoxReading.addItem(self.imag1_icon,"image_3") #imagenes que nos devuelva la busqueda.
        self.img1ComboBoxReading.addItem(self.imag1_icon,"image_4") #por ahora lo dejamos hardcodeado
        self.img1ComboBoxReading.setToolTip("Push for select the image to show")
        
        self.camCombo2 = CamComboBox(self) #combo box de camaras para los historicos de la derecha
        self.camCombo2.popupAboutToBeShown.connect(self.populateCamCombo2)

        self.dateCam2Image = QPushButton("Date Select") #apertura de popup para la seleccion con fecha incial y final
        self.dateCam2Image.setToolTip("Select the dates range of images to show")
        self.dateCam2Image.clicked.connect(self.popUpSearchDateToHistory)                                                #para los historicos de la derecha
        self.dateCam2Image.setIcon(QIcon(os.path.join(basedir,"appIcons","calendar-day.png")))
        
        #agrego el combobox de las imagenes cargadas despues de la busqueda
        self.img2ComboBoxReading = QComboBox(self)
        self.imag2_icon = QIcon(os.path.join(basedir,"appIcons","image.png"))
        self.img2ComboBoxReading.addItem(self.imag2_icon,"image_1") #despues de realizar la consulta a los registros
        self.img2ComboBoxReading.addItem(self.imag2_icon,"image_2") #de imagenes vamos a llenar estos datos con las 
        self.img2ComboBoxReading.addItem(self.imag2_icon,"image_3") #imagenes que nos devuelva la busqueda.
        self.img2ComboBoxReading.addItem(self.imag2_icon,"image_4") #por ahora lo dejamos hardcodeado
        self.img2ComboBoxReading.setToolTip("Push for select the image to show")
        
        self.setWindowTitle("Camera Applications")
        #***********************************************
        #***********************************************
        #***********************************************
        #*****************Definimos paleta de la interfaz grafica***************************************************
        self.originalPalette = QApplication.palette()   #cargo la paleta de estilos que tenga el SO
        #*****************Creamos el objeto para seleccionar usuario************************************************
        #self.comboBoxUsers = QComboBox() #creamos el combo con los usuario para al seleccionar solicite el loggin
        #self.comboBoxUsers.addItems(["Martin", "Polaco", "Iñaki"]) #lista hardcodeada con los usuarios de la aplicacion
                                    #en el futuro al cambiar este objeto debe realizar una consutla a la base local 
                                    #de usuarios
        #self.comboBoxUsers.setToolTip("Select Current User")
        self.userCombo.setToolTip("Select Current User")
        self.labelComboBoxUsers = QLabel("&Users: ") #Con el & estamos indicando un shortcut al presionar alt + u 
                                                #Va a realizar el foco en el combo box para que seleccionemos 
                                                #un usuario        
        self.labelComboBoxUsers.setBuddy(self.userCombo)
        #        
        #******************Creamos la etiqueta para indicar pantalla funcional seleccionada**************************
        self.labelFunctionalWindowSelected = QLabel("Functional Window Cam 1") #El contenido de esta etiqueta va a cambiar en
                                                                      #funcion de que botón de ventana se seleccione
        self.labelFunctionalWindowSelected.setStyleSheet("font-weight:bold; font-size: 15pt; color:green")                                                              #
                                                                      #
        #******************Creamos un checkbox para indicar el estado de la conexión*********************************
        self.statusCameraConnectedCheckBox = QCheckBox("&Connected Cameras Status")#Mostramos un resumen del estado de
        self.statusCameraConnectedCheckBox.setChecked(True)                        #las cámaras si están todas bien

                                                                      #se mostrara un tilde
        topLayout = QHBoxLayout()                               #se configura para el header un layout horizontal
        topLayout.addWidget(self.labelComboBoxUsers)                 #vamos a poner en este layout el combobox de usuario
        #topLayout.addWidget(self.comboBoxUsers)                      #la etiqueta del combobox de usuarios
        topLayout.addWidget(self.userCombo)
        topLayout.addStretch(50)                                 #Un espacio
        topLayout.addWidget(self.labelFunctionalWindowSelected)      #la etiqueta de la ventana de operacion que se esta mostrando
        topLayout.addStretch(50)
        topLayout.addWidget(self.statusCameraConnectedCheckBox) #la etiqueta del estado de las cámaras

        #***********************************************
        #***********************************************
        #***********************************************
        #***********************************************
        self.bodyTabWidget = QTabWidget() #defino la tabla donde mostrar las ventanas asociadas a cada botón
        self.bodyTabWidget.setSizePolicy(
            QSizePolicy.Preferred,
            QSizePolicy.Ignored
        )
        self.bodyTabWidget.setFixedSize(1900,920)#700,500)
        #***************************************
        #Creo el contenido de la primer pestaña
        #***************************************
        #creo el contenido de la imagen
        #agrego las dimensiones
        self.disply_width = 390
        self.display_height = 290
        # create the label that holds the image
        #self.image_label = QLabel(self)
        #self.image_label.resize(self.disply_width, self.display_height)
        # create a text label
        self.textLabel = QLabel('ThermalCam')
        #**************************************
        #widget contenedor para toolbar, para imagen y para label
        self.subwindow = QWidget()
        #defino los rectangulos
        self.beginRect = QPoint()
        self.endRect = QPoint()
        #configuro los objetos para visualizar la imagen
        self.image_label = TestImage()
        self.image_label.resize(self.disply_width, self.display_height)
        #configuro una imagen
        #escala
        self.zoomInEscala = 1.25
        self.zoomOutEscala = 0.8
        self.zoomInOut = 1
        #
        self.image_label.setBackgroundRole(QPalette.Base)
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setScaledContents(True)
        #
        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.image_label)
        self.scrollArea.setVisible(True)
        self.scrollArea.resize(self.scrollArea.sizeHint())
        #
        self.scrollArea.zoomInButton = False
        self.scrollArea.zoomOutButton = False
        ############Escala####################
        #
        self.scrollArea.indiceRect = 0
        #
        #defino los rectangulos
        self.scrollArea.rectangulo1 = QRect(self.beginRect, self.endRect)
        self.scrollArea.rectangulo2 = QRect(self.beginRect, self.endRect)
        self.scrollArea.listaRects = [self.scrollArea.rectangulo1, self.scrollArea.rectangulo2] #llevo la lista de rectangulos
        #defino las lineas
        self.beginLinea = QPoint()
        self.endLinea = QPoint()
        self.scrollArea.recta1 = QLine(self.beginLinea, self.endLinea)
        self.scrollArea.recta2 = QLine(self.beginLinea, self.endLinea)
        self.scrollArea.indiceRecta = 0
        self.scrollArea.listaLineas = [self.scrollArea.recta1, self.scrollArea.recta2] #llevo la lista de rectas
        #defino las elipses o circulos
        self.beginEllipse = QPoint()
        self.endEllipse = QPoint()
        #definimos la elipse 1
        self.scrollArea.rectanguloEllipse1 = QRectF(self.beginEllipse, self.endEllipse)
        self.scrollArea.ellipse1 = QGraphicsEllipseItem(self.scrollArea.rectanguloEllipse1)
        #definimos la elipse 2
        self.scrollArea.rectanguloEllipse2 = QRectF(self.beginEllipse, self.endEllipse)
        self.scrollArea.ellipse2 = QGraphicsEllipseItem(self.scrollArea.rectanguloEllipse2)
        #        
        self.scrollArea.listaElipses = [self.scrollArea.rectanguloEllipse1, self.scrollArea.rectanguloEllipse2] #llevo la lista de elipses
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
        #**************************************
        # create the video capture thread
        self.thread = VideoThread()
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        #
        self.thread.change_thermal_signal.connect(self.thermal_image)
        # start the thread
        self.thread.start()
        #***************************************
        #
        tab1Boton = QWidget() #defino la pestaña de la tabla asociada al boton 1
        textEditTab1Boton = QLineEdit() #cargo el texto en el label, esto es de ejemplo vamos a reemplazarlo por la imagen
        textEditTab1Boton.setText("Status: Camara conectando ....") #este texto lo vamos a 
        #vamos a agregar la barra de conexion para la camara 1
        self.pbarTab1 = QProgressBar(self)      #creo una instancia al modelo barras y le doy un nombre
        self.pbarTab1.setGeometry(30,40,200,25) #defino una dimension para la barra creada
        self.pbarTab1.setValue(0)               #inicializo en un valor

        self.timerPbar1 = QTimer()              #arranco un temporizador para la conexion de la barra de la camara 1
        self.timerPbar1.timeout.connect(self.handleTimer1) #defino la funcion que maneja el temporizador
        self.timerPbar1.start(1000)             #le doy una determinada cantidad de tiempo
 
        sub1WindowTab1Boton = QWidget() #creo una subventana para mostrar la camara1 la curvas de la izquierda y la curva de la derecha
        #creo un contenedor para la imagen y para el toolbar
        contenedorImageToolbarCentralTab1 = QWidget()        
        #creo el layout vertical para el tollbar y la imagen 
        contenedorImageToolbarCentralTab1layout = QVBoxLayout()
        #creo el toolbar
        toolBarImageTab1 = QToolBar("Toolbar Image Tab1")
        toolBarImageTab1.setIconSize(QSize(16,16))
        #cargo los iconos en la barra del toolbar
        #button in
        self.buttonZoomInActionImageTab1 = QAction(QIcon(os.path.join(basedir,"appIcons","magnifier-zoom-in.png")),"zoom in", self)
        self.buttonZoomInActionImageTab1.setStatusTip("Zoom In")
        self.buttonZoomInActionImageTab1.nombreBoton = "zoomInTab1"
        self.buttonZoomInActionImageTab1.triggered.connect(self.makeZoomIn)
        self.buttonZoomInActionImageTab1.setCheckable(True)
        #button out
        self.buttonZoomOutActionImageTab1 = QAction(QIcon(os.path.join(basedir,"appIcons","magnifier-zoom-out.png")),"zoom out",self)
        self.buttonZoomOutActionImageTab1.setStatusTip("Zoom Out")
        self.buttonZoomOutActionImageTab1.nombreBoton = "zoomOutTab1"
        self.buttonZoomOutActionImageTab1.triggered.connect(self.makeZoomOut)
        self.buttonZoomOutActionImageTab1.setCheckable(True)
        #button roi rectangle
        self.buttonRectRoiActionImageTab1 = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape.png")),"Roi Rect", self)
        self.buttonRectRoiActionImageTab1.setStatusTip("Rectangle Roi")
        self.buttonRectRoiActionImageTab1.nombreBoton = "roiRectanguloTab1"
        self.buttonRectRoiActionImageTab1.triggered.connect(self.drawROIRectangle)
        self.buttonRectRoiActionImageTab1.setCheckable(True)
        #button roi ellipse
        self.buttonEllipRoiActionImageTab1 = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape-ellipse.png")),"Roi Ellipse", self)
        self.buttonEllipRoiActionImageTab1.setStatusTip("Ellipse Roi")
        self.buttonEllipRoiActionImageTab1.nombreBoton = "roiEllipseTab1"
        self.buttonEllipRoiActionImageTab1.triggered.connect(self.drawROICircle)
        self.buttonEllipRoiActionImageTab1.setCheckable(True)
        #button roi line
        self.buttonLineRoiActionImageTab1 = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape-line.png")),"Roi Line", self)
        self.buttonLineRoiActionImageTab1.setStatusTip("Line Roi")
        self.buttonLineRoiActionImageTab1.nombreBoton = "roiLineTab1"
        self.buttonLineRoiActionImageTab1.triggered.connect(self.drawROILine)
        self.buttonLineRoiActionImageTab1.setCheckable(True)
        #agrego los botones al toolbar
        toolBarImageTab1.addAction(self.buttonZoomInActionImageTab1)
        toolBarImageTab1.addAction(self.buttonZoomOutActionImageTab1)
        toolBarImageTab1.addAction(self.buttonRectRoiActionImageTab1)
        toolBarImageTab1.addAction(self.buttonEllipRoiActionImageTab1)
        toolBarImageTab1.addAction(self.buttonLineRoiActionImageTab1)
        #
        toolBarImageTab1.resize(toolBarImageTab1.sizeHint())
        #*******
        self.scene = QGraphicsScene(0, 0, 0, 0)
        self.pixmap = QPixmap("imageCam1.jpg") #a reemplazar por la imagen
        pixmapitem = self.scene.addPixmap(self.pixmap)
        viewPixMapItem = QGraphicsView(self.scene)
        viewPixMapItem.setRenderHint(QPainter.Antialiasing)
        #*******
        contenedorImageToolbarCentralTab1layout.addWidget(toolBarImageTab1)
        contenedorImageToolbarCentralTab1layout.addWidget(self.scrollArea)#)viewPixMapItem) 
        contenedorImageToolbarCentralTab1.setLayout(contenedorImageToolbarCentralTab1layout)
        #*******
        #
        contenedorImageToolbarCentralTab1.resize(824,768)
        #
        #Agrego comboBox para seleccionar el trending que vamos a mostrar en dfTab1Izq
        #
        textEditTab1BotonSelROI = QLabel()
        textEditTab1BotonSelROI.setText("Selected ROI: ")
        textEditTab1BotonSelROI.setBuddy(self.roiSelComboIzq)
        self.roiSelComboIzq.setToolTip("selected the roi to show min-avg-max value")
        #
        #Agrego comoboBox para seleccion el perfil que vamos a mostrar en dfTab11Izq
        textEditTab1BotonSelProfile = QLabel()
        textEditTab1BotonSelProfile.setText("Selected Profile:")
        textEditTab1BotonSelProfile.setBuddy(self.profileSelComboIzq)
        self.profileSelComboIzq.setToolTip("selected the profile to show Rois")
        #agrego grafico izquierda para la camara 1
        #
        self.dfTab1Izq = MplCanvas(self, width=5, height=4, dpi=100)

        n_data = 50
        self.xdataIzq = list(range(n_data))
        self.ydataIzq = [random.randint(0,100) for i in range(n_data)]

        self._plot_refIzq = None
        self.update_plot_dfTab1Izq()

        self.timerIzq = QtCore.QTimer()
        self.timerIzq.setInterval(100)
        self.timerIzq.timeout.connect(self.update_plot_dfTab1Izq)
        self.timerIzq.start()
        #
        #agrego grafico sub izquierda para la camara 1
        #
        self.dfTab1Izq1 = MplCanvas(self, width=5, height=4, dpi=100)
        #defino los datos para el grafico de perfiles a izquierda de la imagen
        n_data1 = 50
        self.xdataIzq1 = list(range(n_data1))
        self.ydataIzq1 = [random.randint(0,100) for i in range(n_data1)]
        #defino los datos para llevar los perfiles de cada roi
        #roi rectangulo horizontal
        self.xdataIzq1RectHor = list(range(n_data1))
        self.ydataIzq1RectHor = [random.randint(0,10) for i in range(n_data1)]
        #roi rectangulo vertical
        self.xdataIzq1RectVert = list(range(n_data1))
        self.ydataIzq1RectVert = [random.randint(0,10) for i in range(n_data1)]
        #roi elipse horizontal
        self.xdataIzq1ElipHor = list(range(n_data1))
        self.ydataIzq1ElipHor = [random.randint(0,10) for i in range(n_data1)]
        #roi elipse vertical
        self.xdataIzq1ElipVer = list(range(n_data1))
        self.ydataIzq1ElipVer = [random.randint(0,10) for i in range(n_data1)]
        #roi linea
        self.xdataIzq1Line = list(range(n_data1))
        self.ydataIzq1Line = [random.randint(0,10) for i in range(n_data1)]
        #dibujo el perfil
        self._plot_refIzq1 = None
        self.update_plot_dfTab1Izq1()
        # No actualizo el grafico lo dejo estatico
        # Ya que voy a mostrar el dato cuando se
        # actualice la medicion con el eje X en pixel
        self.timerIzq1 = QtCore.QTimer()
        self.timerIzq1.setInterval(1000)
        self.timerIzq1.timeout.connect(self.update_plot_dfTab1Izq1)
        self.timerIzq1.start()
        #
        #
        #Agrego comboBox para seleccionar el trending que vamos a mostrar en dfTab1Der
        #
        textEditTab1BotonSelROIDer = QLabel()
        textEditTab1BotonSelROIDer.setText("Sel ROI: ")
        textEditTab1BotonSelROIDer.setBuddy(self.roiSelComboDer)
        self.roiSelComboDer.setToolTip("selected the roi to show min-avg-max value")
        #
        #agrego grafico derecha
        #genero un dataframe de prueba
        self.dfTab1Der = MplCanvas(self, width=5, height=4, dpi=100)

        n_data = 50
        self.xdata = list(range(n_data))
        self.ydata = [random.randint(0,10) for i in range(n_data)]

        self._plot_ref = None
        self.update_plot_dfTab1Der() 

        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_plot_dfTab1Der)
        self.timer.start()
        #
        #
        #agrego grafico derecha 1
        #genero un dataframe de prueba
        self.dfTab1Der1 = MplCanvas(self, width=5, height=4, dpi=100)

        n_data2 = 50
        self.xdataDer1 = list(range(n_data2))
        self.ydataDer1 = [random.randint(0,100) for i in range(n_data2)]
        #defino los datos para llevar los perfiles de cada roi
        #roi rectangulo horizontal
        self.xdataDer1RectHor = list(range(n_data2))
        self.ydataDer1RectHor = [random.randint(0,10) for i in range(n_data2)]
        #roi rectangulo vertical
        self.xdataDer1RectVert = list(range(n_data2))
        self.ydataDer1RectVert = [random.randint(0,10) for i in range(n_data2)]
        #roi elipse horizontal
        self.xdataDer1ElipHor = list(range(n_data2))
        self.ydataDer1ElipHor = [random.randint(0,10) for i in range(n_data2)]
        #roi elipse vertical
        self.xdataDer1ElipVer = list(range(n_data2))
        self.ydataDer1ElipVer = [random.randint(0,10) for i in range(n_data2)]
        #roi linea
        self.xdataDer1Line = list(range(n_data2))
        self.ydataDer1Line = [random.randint(0,10) for i in range(n_data2)]
           


        self._plot_refDer1 = None
        self.update_plot_dfTab1Der1() 
        # No actualizo el grafico lo dejo estatico
        # Ya que voy a mostrar el dato cuando se
        # actualice la medicion con el eje X en pixel
        # self.timerDer1 = QtCore.QTimer()
        # self.timerDer1.setInterval(10)
        # self.timerDer1.timeout.connect(self.update_plot_dfTab1Der1)
        # self.timerDer1.start()
        #
        #agrego contenedor a la izquierda para curva
        #para label1 y boton1
        #para label2 y boton2
        contenedorIzqTab1 = QWidget()        
        contenedorIzqTab1Layout = QVBoxLayout()
        #creo label 1
        label1Tab1 = QLabel("Min")
        label1Tab1.setFixedSize(QSize(16,16))
        label1Tab1.setStyleSheet("border-style: none;")
        #creo boton 1
        boton1Tab1 = AnimatedToggle()
        boton1Tab1.setFixedSize(boton1Tab1.sizeHint())
        boton1Tab1.setToolTip("Toggle to change preset 1")
        #definimos la funcion asociada al preset1 del tab1
        enableBoton1Tab1 = partial(self.popUpSetBotonTab1, boton1Tab1 )
        disableBoton1Tab1 = partial(self.popUpResetBotonTab1, boton1Tab1)
        boton1Tab1.stateChanged.connect(lambda x: enableBoton1Tab1() if x else disableBoton1Tab1())        
        #agregamos el indicador 1 de medicion
        valor1Tab1MinRoi1Rect = "105.2" #minimo roi rect
        self.valor1IndTab1MinRoi1Rect = QLabel(valor1Tab1MinRoi1Rect)
        self.valor1IndTab1MinRoi1Rect.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.valor1IndTab1MinRoi1Rect.setFixedSize(QSize(40,23))
        #creo label 11
        label11Tab1 = QLabel("Min")
        label11Tab1.setFixedSize(QSize(16,16))
        label11Tab1.setStyleSheet("border-style: none;")
        #creo boton 11
        boton11Tab1 = AnimatedToggle()
        boton11Tab1.setFixedSize(boton11Tab1.sizeHint())
        boton11Tab1.setToolTip("Toggle to change preset 1")
        #definimos la funcion asociada al preset11 del tab1
        enableBoton11Tab1 = partial(self.popUpSetBotonTab1, boton11Tab1 )
        disableBoton11Tab1 = partial(self.popUpResetBotonTab1, boton11Tab1)
        boton11Tab1.stateChanged.connect(lambda x: enableBoton11Tab1() if x else disableBoton11Tab1())        
        #agregamos el indicador 11 de medicion
        valor11Tab1MinRoi1Line = "105.2" #minimo roi line
        self.valor11IndTab1MinRoi1Line = QLabel(valor11Tab1MinRoi1Line)
        self.valor11IndTab1MinRoi1Line.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.valor11IndTab1MinRoi1Line.setFixedSize(QSize(40,23))
        #creo label 12
        label12Tab1 = QLabel("Min")
        label12Tab1.setFixedSize(QSize(16,16))
        label12Tab1.setStyleSheet("border-style: none;")
        #creo boton 12
        boton12Tab1 = AnimatedToggle()
        boton12Tab1.setFixedSize(boton12Tab1.sizeHint())
        boton12Tab1.setToolTip("Toggle to change preset 1")
        #definimos la funcion asociada al preset12 del tab1
        enableBoton12Tab1 = partial(self.popUpSetBotonTab1, boton12Tab1 )
        disableBoton12Tab1 = partial(self.popUpResetBotonTab1, boton12Tab1)
        boton12Tab1.stateChanged.connect(lambda x: enableBoton12Tab1() if x else disableBoton12Tab1())        
        #agregamos el indicador 12 de medicion
        valor12Tab1MinRoi1Ellipse = "105.2" #minimo roi elipse
        self.valor12IndTab1MinRoi1Ellipse = QLabel(valor12Tab1MinRoi1Ellipse)
        self.valor12IndTab1MinRoi1Ellipse.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.valor12IndTab1MinRoi1Ellipse.setFixedSize(QSize(40,23))
        #creo label 2
        label2Tab1 = QLabel("Avg")
        label2Tab1.setFixedSize(QSize(16,16))
        label2Tab1.setStyleSheet("border-style: none;")
        #creo el boton 2
        boton2Tab1 = AnimatedToggle()
        boton2Tab1.setFixedSize(boton2Tab1.sizeHint())
        boton2Tab1.setToolTip("Toggle to change preset 2")       
        #agregamos el indicador 2 de medicion
        valor2Tab1AvgRoi1Rect = "115.2" #avg roi rect
        self.valor2IndTab1AvgRoi1Rect = QLabel(valor2Tab1AvgRoi1Rect)
        self.valor2IndTab1AvgRoi1Rect.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.valor2IndTab1AvgRoi1Rect.setFixedSize(QSize(40,23))
        #definimos la funcion asociada al preset 2 del tab1
        enableBoton2Tab1 = partial(self.popUpSetBotonTab1, boton2Tab1)
        disableBoton2Tab1 = partial(self.popUpResetBotonTab1, boton2Tab1)
        boton2Tab1.stateChanged.connect(lambda x: enableBoton2Tab1() if x else disableBoton2Tab1())
        #creo label 21
        label21Tab1 = QLabel("Avg")
        label21Tab1.setFixedSize(QSize(16,16))
        label21Tab1.setStyleSheet("border-style: none;")
        #creo el boton 21
        boton21Tab1 = AnimatedToggle()
        boton21Tab1.setFixedSize(boton21Tab1.sizeHint())
        boton21Tab1.setToolTip("Toggle to change preset 2")       
        #agregamos el indicador 21 de medicion
        valor21Tab1AvgRoi1Line = "115.2" #avg roi line
        self.valor21IndTab1AvgRoi1Line = QLabel(valor21Tab1AvgRoi1Line)
        self.valor21IndTab1AvgRoi1Line.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.valor21IndTab1AvgRoi1Line.setFixedSize(QSize(40,23))
        #definimos la funcion asociada al preset 21 del tab1
        enableBoton21Tab1 = partial(self.popUpSetBotonTab1, boton21Tab1)
        disableBoton21Tab1 = partial(self.popUpResetBotonTab1, boton21Tab1)
        boton21Tab1.stateChanged.connect(lambda x: enableBoton21Tab1() if x else disableBoton21Tab1())
         #creo label 22
        label22Tab1 = QLabel("Avg")
        label22Tab1.setFixedSize(QSize(16,16))
        label22Tab1.setStyleSheet("border-style: none;")
        #creo el boton 22
        boton22Tab1 = AnimatedToggle()
        boton22Tab1.setFixedSize(boton22Tab1.sizeHint())
        boton22Tab1.setToolTip("Toggle to change preset 2")       
        #agregamos el indicador 22 de medicion
        valor22Tab1AvgRoi1Ellipse = "115.2" #avg roi elipse
        self.valor22IndTab1AvgRoi1Ellipse = QLabel(valor22Tab1AvgRoi1Ellipse)
        self.valor22IndTab1AvgRoi1Ellipse.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.valor22IndTab1AvgRoi1Ellipse.setFixedSize(QSize(40,23))
        #definimos la funcion asociada al preset 22 del tab1
        enableBoton22Tab1 = partial(self.popUpSetBotonTab1, boton22Tab1)
        disableBoton22Tab1 = partial(self.popUpResetBotonTab1, boton22Tab1)
        boton22Tab1.stateChanged.connect(lambda x: enableBoton22Tab1() if x else disableBoton22Tab1())
        #creo label 3
        label3Tab1 = QLabel("Max")
        label3Tab1.setFixedSize(QSize(16,16))
        label3Tab1.setStyleSheet("border-style: none;")
        #creo el boton 3
        boton3Tab1 = AnimatedToggle()
        boton3Tab1.setFixedSize(boton3Tab1.sizeHint())
        boton3Tab1.setToolTip("Toggle to change preset 2")       
        #agregamos el indicador 3 de medicion
        valor3Tab1MaxRoi1Rect = "115.2" #max roi rect
        self.valor3IndTab1MaxRoi1Rect = QLabel(valor3Tab1MaxRoi1Rect)
        self.valor3IndTab1MaxRoi1Rect.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.valor3IndTab1MaxRoi1Rect.setFixedSize(QSize(40,23))
        #definimos la funcion asociada al preset 3 del tab1
        enableBoton3Tab1 = partial(self.popUpSetBotonTab1, boton3Tab1)
        disableBoton3Tab1 = partial(self.popUpResetBotonTab1, boton3Tab1)
        boton3Tab1.stateChanged.connect(lambda x: enableBoton3Tab1() if x else disableBoton3Tab1())
        #creo label 31
        label31Tab1 = QLabel("Max")
        label31Tab1.setFixedSize(QSize(16,16))
        label31Tab1.setStyleSheet("border-style: none;")
        #creo el boton 31
        boton31Tab1 = AnimatedToggle()
        boton31Tab1.setFixedSize(boton31Tab1.sizeHint())
        boton31Tab1.setToolTip("Toggle to change preset 3")       
        #agregamos el indicador 31 de medicion
        valor31Tab1MaxRoi1Line = "115.2" #max roi Line
        self.valor31IndTab1MaxRoi1Line = QLabel(valor31Tab1MaxRoi1Line)
        self.valor31IndTab1MaxRoi1Line.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.valor31IndTab1MaxRoi1Line.setFixedSize(QSize(40,23))
        #definimos la funcion asociada al preset 21 del tab1
        enableBoton31Tab1 = partial(self.popUpSetBotonTab1, boton31Tab1)
        disableBoton31Tab1 = partial(self.popUpResetBotonTab1, boton31Tab1)
        boton31Tab1.stateChanged.connect(lambda x: enableBoton31Tab1() if x else disableBoton31Tab1())
         #creo label 32
        label32Tab1 = QLabel("Max")
        label32Tab1.setFixedSize(QSize(16,16))
        label32Tab1.setStyleSheet("border-style: none;")
        #creo el boton 32
        boton32Tab1 = AnimatedToggle()
        boton32Tab1.setFixedSize(boton32Tab1.sizeHint())
        boton32Tab1.setToolTip("Toggle to change preset 2")       
        #agregamos el indicador 22 de medicion
        valor32Tab1MaxRoi1Ellipse = "115.2" #max roi ellipse
        self.valor32IndTab1MaxRoi1Ellipse = QLabel(valor32Tab1MaxRoi1Ellipse)
        self.valor32IndTab1MaxRoi1Ellipse.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.valor32IndTab1MaxRoi1Ellipse.setFixedSize(QSize(40,23))
        #definimos la funcion asociada al preset 22 del tab1
        enableBoton32Tab1 = partial(self.popUpSetBotonTab1, boton32Tab1)
        disableBoton32Tab1 = partial(self.popUpResetBotonTab1, boton32Tab1)
        boton32Tab1.stateChanged.connect(lambda x: enableBoton32Tab1() if x else disableBoton32Tab1())
        #agrego el layout
        contenedorIzqTab1LayoutSub0 = QVBoxLayout()
        contenedorIzqTab1WidgetSub0 = QWidget()
        contenedorIzqTab1LayoutSub01 = QHBoxLayout()
        contenedorIzqTab1WidgetSub01 = QWidget()
        contenedorIzqTab1LayoutSub01.addWidget(textEditTab1BotonSelROI)
        contenedorIzqTab1LayoutSub01.addWidget(self.roiSelComboIzq)
        contenedorIzqTab1LayoutSub01.addWidget(textEditTab1BotonSelProfile)
        contenedorIzqTab1LayoutSub01.addWidget(self.profileSelComboIzq)
        contenedorIzqTab1WidgetSub01.setLayout(contenedorIzqTab1LayoutSub01)        
        contenedorIzqTab1LayoutSub0.addWidget(contenedorIzqTab1WidgetSub01)
        contenedorIzqTab1LayoutSub0.addWidget(self.dfTab1Izq)
        contenedorIzqTab1LayoutSub0.addWidget(self.dfTab1Izq1)
        contenedorIzqTab1WidgetSub0.setLayout(contenedorIzqTab1LayoutSub0)
        contenedorIzqTab1WidgetSub0.resize(300,668)
        contenedorIzqTab1LayoutSub10 = QHBoxLayout()
        contenedorIzqTab1WidgetSub10 = QWidget()                
        contenedorIzqTab1LayoutSub10.addWidget(label1Tab1)
        contenedorIzqTab1LayoutSub10.addWidget(boton1Tab1)        
        contenedorIzqTab1LayoutSub10.addWidget(self.valor1IndTab1MinRoi1Rect)
        contenedorIzqTab1LayoutSub10.addWidget(label11Tab1)
        contenedorIzqTab1LayoutSub10.addWidget(boton11Tab1)        
        contenedorIzqTab1LayoutSub10.addWidget(self.valor11IndTab1MinRoi1Line)
        contenedorIzqTab1LayoutSub10.addWidget(label12Tab1)
        contenedorIzqTab1LayoutSub10.addWidget(boton12Tab1)        
        contenedorIzqTab1LayoutSub10.addWidget(self.valor12IndTab1MinRoi1Ellipse)
        contenedorIzqTab1WidgetSub10.setLayout(contenedorIzqTab1LayoutSub10)
        contenedorIzqTab1WidgetSub10.resize(300,50)
        contenedorIzqTab1LayoutSub20 = QHBoxLayout()
        contenedorIzqTab1WidgetSub20 = QWidget()        
        contenedorIzqTab1LayoutSub20.addWidget(label2Tab1)
        contenedorIzqTab1LayoutSub20.addWidget(boton2Tab1)        
        contenedorIzqTab1LayoutSub20.addWidget(self.valor2IndTab1AvgRoi1Rect)
        contenedorIzqTab1LayoutSub20.addWidget(label21Tab1)
        contenedorIzqTab1LayoutSub20.addWidget(boton21Tab1)        
        contenedorIzqTab1LayoutSub20.addWidget(self.valor21IndTab1AvgRoi1Line)
        contenedorIzqTab1LayoutSub20.addWidget(label22Tab1)
        contenedorIzqTab1LayoutSub20.addWidget(boton22Tab1)        
        contenedorIzqTab1LayoutSub20.addWidget(self.valor22IndTab1AvgRoi1Ellipse)
        contenedorIzqTab1WidgetSub20.setLayout(contenedorIzqTab1LayoutSub20)
        contenedorIzqTab1WidgetSub20.resize(300,50)
        contenedorIzqTab1LayoutSub30 = QHBoxLayout()
        contenedorIzqTab1WidgetSub30 = QWidget()
        contenedorIzqTab1LayoutSub30.addWidget(label3Tab1)
        contenedorIzqTab1LayoutSub30.addWidget(boton3Tab1)        
        contenedorIzqTab1LayoutSub30.addWidget(self.valor3IndTab1MaxRoi1Rect)
        contenedorIzqTab1LayoutSub30.addWidget(label31Tab1)
        contenedorIzqTab1LayoutSub30.addWidget(boton31Tab1)        
        contenedorIzqTab1LayoutSub30.addWidget(self.valor31IndTab1MaxRoi1Line)
        contenedorIzqTab1LayoutSub30.addWidget(label32Tab1)
        contenedorIzqTab1LayoutSub30.addWidget(boton32Tab1)        
        contenedorIzqTab1LayoutSub30.addWidget(self.valor32IndTab1MaxRoi1Ellipse)
        contenedorIzqTab1WidgetSub30.setLayout(contenedorIzqTab1LayoutSub30)
        contenedorIzqTab1LayoutSub1=QVBoxLayout()
        contenedorIzqTab1WidgetSub1=QWidget()
        contenedorIzqTab1LayoutSub1.addWidget(contenedorIzqTab1WidgetSub10)
        contenedorIzqTab1LayoutSub1.addWidget(contenedorIzqTab1WidgetSub20)
        contenedorIzqTab1LayoutSub1.addWidget(contenedorIzqTab1WidgetSub30)        
        contenedorIzqTab1WidgetSub1.setLayout(contenedorIzqTab1LayoutSub1)
        contenedorIzqTab1WidgetSub1.resize(300,100)
        contenedorIzqTab1Layout.addWidget(contenedorIzqTab1WidgetSub0)
        contenedorIzqTab1Layout.addWidget(contenedorIzqTab1WidgetSub1)
        #cargo el layout
        contenedorIzqTab1.setLayout(contenedorIzqTab1Layout)
        #
        anchoContendor = QSize(300,768)
        contenedorIzqTab1.resize(anchoContendor)
        #
        #agrego contenedor a la derecha para curva
        #para label4 y boton4
        #para label5 y boton5
        #para label6 y boton6        
        contenedorDerTab1 = QWidget()
        contenedorDerTab1Layout = QVBoxLayout()
        #creo label 4
        label4Tab1 = QLabel("Min")
        label4Tab1.setFixedSize(QSize(16,16))
        label4Tab1.setStyleSheet("border-style: none;")
        #creo boton 3
        boton4Tab1 = AnimatedToggle()
        boton4Tab1.setFixedSize(boton4Tab1.sizeHint())
        boton4Tab1.setToolTip("Toggle to change preset 4")
        #agregamos el indicador 4 de medicion
        valor4Tab1MinRoi2Rect = "115.2"
        self.valor4IndTab1MinRoi2Rect = QLabel(valor4Tab1MinRoi2Rect)
        self.valor4IndTab1MinRoi2Rect.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.valor4IndTab1MinRoi2Rect.setFixedSize(QSize(40,23))
        #definimos la funcion asociada al preset 4 del tab1
        enableBoton4Tab1 = partial(self.popUpSetBotonTab1, boton4Tab1)
        disableBoton4Tab1 = partial(self.popUpResetBotonTab1, boton4Tab1)
        boton4Tab1.stateChanged.connect(lambda x: enableBoton4Tab1() if x else disableBoton4Tab1())
        #creo label 41
        label41Tab1 = QLabel("Min")
        label41Tab1.setFixedSize(QSize(16,16))
        label41Tab1.setStyleSheet("border-style: none;")
        #creo boton 41
        boton41Tab1 = AnimatedToggle()
        boton41Tab1.setFixedSize(boton41Tab1.sizeHint())
        boton41Tab1.setToolTip("Toggle to change preset 4")
        #agregamos el indicador 31 de medicion
        valor41Tab1MinRoi2Line = "115.2"
        self.valor41IndTab1MinRoi2Line = QLabel(valor41Tab1MinRoi2Line)
        self.valor41IndTab1MinRoi2Line.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.valor41IndTab1MinRoi2Line.setFixedSize(QSize(40,23))
        #definimos la funcion asociada al preset 4 del tab1
        enableBoton41Tab1 = partial(self.popUpSetBotonTab1, boton41Tab1)
        disableBoton41Tab1 = partial(self.popUpResetBotonTab1, boton41Tab1)
        boton41Tab1.stateChanged.connect(lambda x: enableBoton41Tab1() if x else disableBoton41Tab1())
        #creo label 42
        label42Tab1 = QLabel("Min")
        label42Tab1.setFixedSize(QSize(16,16))
        label42Tab1.setStyleSheet("border-style: none;")
        #creo boton 42
        boton42Tab1 = AnimatedToggle()
        boton42Tab1.setFixedSize(boton42Tab1.sizeHint())
        boton42Tab1.setToolTip("Toggle to change preset 3")
        #agregamos el indicador 42 de medicion
        valor42Tab1MinRoi2Ellipse = "115.2"
        self.valor42IndTab1MinRoi2Ellipse = QLabel(valor42Tab1MinRoi2Ellipse)
        self.valor42IndTab1MinRoi2Ellipse.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.valor42IndTab1MinRoi2Ellipse.setFixedSize(QSize(40,23))
        #definimos la funcion asociada al preset 3 del tab1
        enableBoton42Tab1 = partial(self.popUpSetBotonTab1, boton42Tab1)
        disableBoton42Tab1 = partial(self.popUpResetBotonTab1, boton42Tab1)
        boton42Tab1.stateChanged.connect(lambda x: enableBoton42Tab1() if x else disableBoton42Tab1())
        #creo label 5
        label5Tab1 = QLabel("Avg")
        label5Tab1.setFixedSize(QSize(16,16))
        label5Tab1.setStyleSheet("border-style: none;")
        #creo boton 4
        boton5Tab1 = AnimatedToggle()
        boton5Tab1.setFixedSize(boton5Tab1.sizeHint())
        boton5Tab1.setToolTip("Toggle to change preset 4")
         #agregamos el indicador 4 de medicion
        valor5Tab1AvgRoi2Rect = "115.2"
        self.valor5IndTab1AvgRoi2Rect = QLabel(valor5Tab1AvgRoi2Rect)
        self.valor5IndTab1AvgRoi2Rect.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.valor5IndTab1AvgRoi2Rect.setFixedSize(QSize(40,23))
        #definimos la funcion asociada al preset4 del tab1
        enableBoton5Tab1 = partial(self.popUpSetBotonTab1, boton5Tab1)
        disableBoton5Tab1 = partial(self.popUpResetBotonTab1, boton5Tab1)
        boton5Tab1.stateChanged.connect(lambda x: enableBoton5Tab1() if x else disableBoton5Tab1())
        #creo label 5
        label51Tab1 = QLabel("Avg")
        label51Tab1.setFixedSize(QSize(16,16))
        label51Tab1.setStyleSheet("border-style: none;")
        #creo boton 4
        boton51Tab1 = AnimatedToggle()
        boton51Tab1.setFixedSize(boton51Tab1.sizeHint())
        boton51Tab1.setToolTip("Toggle to change preset 4")
         #agregamos el indicador 4 de medicion
        valor51Tab1AvgRoi2Line = "115.2"
        self.valor51IndTab1AvgRoi2Line = QLabel(valor51Tab1AvgRoi2Line)
        self.valor51IndTab1AvgRoi2Line.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.valor51IndTab1AvgRoi2Line.setFixedSize(QSize(40,23))
        #definimos la funcion asociada al preset4 del tab1
        enableBoton51Tab1 = partial(self.popUpSetBotonTab1, boton51Tab1)
        disableBoton51Tab1 = partial(self.popUpResetBotonTab1, boton51Tab1)
        boton51Tab1.stateChanged.connect(lambda x: enableBoton51Tab1() if x else disableBoton51Tab1())        
        #creo label 52
        label52Tab1 = QLabel("Avg")
        label52Tab1.setFixedSize(QSize(16,16))
        label52Tab1.setStyleSheet("border-style: none;")
        #creo boton 4
        boton52Tab1 = AnimatedToggle()
        boton52Tab1.setFixedSize(boton52Tab1.sizeHint())
        boton52Tab1.setToolTip("Toggle to change preset 4")
         #agregamos el indicador 5 de medicion
        valor52Tab1AvgRoi2Ellipse = "115.2"
        self.valor52IndTab1AvgRoi2Ellipse = QLabel(valor52Tab1AvgRoi2Ellipse)
        self.valor52IndTab1AvgRoi2Ellipse.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.valor52IndTab1AvgRoi2Ellipse.setFixedSize(QSize(40,23))
        #definimos la funcion asociada al preset5 del tab1
        enableBoton52Tab1 = partial(self.popUpSetBotonTab1, boton52Tab1)
        disableBoton52Tab1 = partial(self.popUpResetBotonTab1, boton52Tab1)
        boton52Tab1.stateChanged.connect(lambda x: enableBoton52Tab1() if x else disableBoton52Tab1())        
        #creo label 6
        label6Tab1 = QLabel("Max")
        label6Tab1.setFixedSize(QSize(16,16))
        label6Tab1.setStyleSheet("border-style: none;")
        #creo boton 6
        boton6Tab1 = AnimatedToggle()
        boton6Tab1.setFixedSize(boton6Tab1.sizeHint())
        boton6Tab1.setToolTip("Toggle to change preset 4")
        #agregamos el indicador 6 de medicion
        valor6Tab1MaxRoi2Rect = "115.2"
        self.valor6IndTab1MaxRoi2Rect = QLabel(valor6Tab1MaxRoi2Rect)
        self.valor6IndTab1MaxRoi2Rect.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.valor6IndTab1MaxRoi2Rect.setFixedSize(QSize(40,23))
        #definimos la funcion asociada al preset 6 del tab1
        enableBoton6Tab1 = partial(self.popUpSetBotonTab1, boton6Tab1)
        disableBoton6Tab1 = partial(self.popUpResetBotonTab1, boton6Tab1)
        boton6Tab1.stateChanged.connect(lambda x: enableBoton6Tab1() if x else disableBoton6Tab1())
        #creo label 61
        label61Tab1 = QLabel("Max")
        label61Tab1.setFixedSize(QSize(16,16))
        label61Tab1.setStyleSheet("border-style: none;")
        #creo boton 6
        boton61Tab1 = AnimatedToggle()
        boton61Tab1.setFixedSize(boton61Tab1.sizeHint())
        boton61Tab1.setToolTip("Toggle to change preset 4")
        #agregamos el indicador 6 de medicion
        valor61Tab1MaxRoi2Line = "115.2"
        self.valor61IndTab1MaxRoi2Line = QLabel(valor61Tab1MaxRoi2Line)
        self.valor61IndTab1MaxRoi2Line.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.valor61IndTab1MaxRoi2Line.setFixedSize(QSize(40,23))
        #definimos la funcion asociada al preset 6 del tab1
        enableBoton61Tab1 = partial(self.popUpSetBotonTab1, boton61Tab1)
        disableBoton61Tab1 = partial(self.popUpResetBotonTab1, boton61Tab1)
        boton61Tab1.stateChanged.connect(lambda x: enableBoton61Tab1() if x else disableBoton61Tab1())
        #creo label 62
        label62Tab1 = QLabel("Max")
        label62Tab1.setFixedSize(QSize(16,16))
        label62Tab1.setStyleSheet("border-style: none;")
        #creo boton 6
        boton62Tab1 = AnimatedToggle()
        boton62Tab1.setFixedSize(boton62Tab1.sizeHint())
        boton62Tab1.setToolTip("Toggle to change preset 4")
        #agregamos el indicador 6 de medicion
        valor62Tab1MaxRoi2Ellipse = "115.2"
        self.valor62IndTab1MaxRoi2Ellipse = QLabel(valor62Tab1MaxRoi2Ellipse)
        self.valor62IndTab1MaxRoi2Ellipse.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.valor62IndTab1MaxRoi2Ellipse.setFixedSize(QSize(40,23))
        #definimos la funcion asociada al preset 6 del tab1
        enableBoton62Tab1 = partial(self.popUpSetBotonTab1, boton62Tab1)
        disableBoton62Tab1 = partial(self.popUpResetBotonTab1, boton62Tab1)
        boton62Tab1.stateChanged.connect(lambda x: enableBoton62Tab1() if x else disableBoton62Tab1())
        #agrego el layout
        contenedorDerTab1LayoutSub0 = QVBoxLayout()
        contenedorDerTab1WidgetSub0 = QWidget()
        contenedorDerTab1LayoutSub01 = QHBoxLayout()
        contenedorDerTab1WidgetSub01 = QWidget()
        contenedorDerTab1LayoutSub01.addWidget(textEditTab1BotonSelROIDer)
        contenedorDerTab1LayoutSub01.addWidget(self.roiSelComboDer)
        contenedorDerTab1WidgetSub01.setLayout(contenedorDerTab1LayoutSub01)                
        contenedorDerTab1LayoutSub0.addWidget(contenedorDerTab1WidgetSub01)
        contenedorDerTab1LayoutSub0.addWidget(self.dfTab1Der)
        contenedorDerTab1LayoutSub0.addWidget(self.dfTab1Der1)
        contenedorDerTab1WidgetSub0.setLayout(contenedorDerTab1LayoutSub0)
        contenedorDerTab1WidgetSub0.resize(300,668)
        contenedorDerTab1LayoutSub10 = QHBoxLayout()
        contenedorDerTab1WidgetSub10 = QWidget()                
        contenedorDerTab1LayoutSub10.addWidget(label4Tab1)
        contenedorDerTab1LayoutSub10.addWidget(boton4Tab1)        
        contenedorDerTab1LayoutSub10.addWidget(self.valor4IndTab1MinRoi2Rect)
        contenedorDerTab1LayoutSub10.addWidget(label41Tab1)
        contenedorDerTab1LayoutSub10.addWidget(boton41Tab1)        
        contenedorDerTab1LayoutSub10.addWidget(self.valor41IndTab1MinRoi2Line)
        contenedorDerTab1LayoutSub10.addWidget(label42Tab1)
        contenedorDerTab1LayoutSub10.addWidget(boton42Tab1)        
        contenedorDerTab1LayoutSub10.addWidget(self.valor42IndTab1MinRoi2Ellipse)
        contenedorDerTab1WidgetSub10.setLayout(contenedorDerTab1LayoutSub10)
        contenedorDerTab1WidgetSub10.resize(300,50)
        contenedorDerTab1LayoutSub20 = QHBoxLayout()
        contenedorDerTab1WidgetSub20 = QWidget()        
        contenedorDerTab1LayoutSub20.addWidget(label5Tab1)
        contenedorDerTab1LayoutSub20.addWidget(boton5Tab1)        
        contenedorDerTab1LayoutSub20.addWidget(self.valor5IndTab1AvgRoi2Rect)
        contenedorDerTab1LayoutSub20.addWidget(label51Tab1)
        contenedorDerTab1LayoutSub20.addWidget(boton51Tab1)        
        contenedorDerTab1LayoutSub20.addWidget(self.valor51IndTab1AvgRoi2Line)
        contenedorDerTab1LayoutSub20.addWidget(label52Tab1)
        contenedorDerTab1LayoutSub20.addWidget(boton52Tab1)        
        contenedorDerTab1LayoutSub20.addWidget(self.valor52IndTab1AvgRoi2Ellipse)
        contenedorDerTab1WidgetSub20.setLayout(contenedorDerTab1LayoutSub20)
        contenedorDerTab1WidgetSub20.resize(300,50)
        contenedorDerTab1LayoutSub30 = QHBoxLayout()
        contenedorDerTab1WidgetSub30 = QWidget()
        contenedorDerTab1LayoutSub30.addWidget(label6Tab1)
        contenedorDerTab1LayoutSub30.addWidget(boton6Tab1)        
        contenedorDerTab1LayoutSub30.addWidget(self.valor6IndTab1MaxRoi2Rect)
        contenedorDerTab1LayoutSub30.addWidget(label61Tab1)
        contenedorDerTab1LayoutSub30.addWidget(boton61Tab1)        
        contenedorDerTab1LayoutSub30.addWidget(self.valor61IndTab1MaxRoi2Line)
        contenedorDerTab1LayoutSub30.addWidget(label62Tab1)
        contenedorDerTab1LayoutSub30.addWidget(boton62Tab1)        
        contenedorDerTab1LayoutSub30.addWidget(self.valor62IndTab1MaxRoi2Ellipse)
        contenedorDerTab1WidgetSub30.setLayout(contenedorDerTab1LayoutSub30)
        contenedorDerTab1WidgetSub30.resize(300,50)        
        contenedorDerTab1LayoutSub1=QVBoxLayout()
        contenedorDerTab1WidgetSub1=QWidget()
        contenedorDerTab1LayoutSub1.addWidget(contenedorDerTab1WidgetSub10)
        contenedorDerTab1LayoutSub1.addWidget(contenedorDerTab1WidgetSub20)
        contenedorDerTab1LayoutSub1.addWidget(contenedorDerTab1WidgetSub30)
        contenedorDerTab1WidgetSub1.setLayout(contenedorDerTab1LayoutSub1)
        contenedorDerTab1WidgetSub1.resize(300,100)
        contenedorDerTab1Layout.addWidget(contenedorDerTab1WidgetSub0)
        contenedorDerTab1Layout.addWidget(contenedorDerTab1WidgetSub1)
        #cargo el layout
        contenedorDerTab1.setLayout(contenedorDerTab1Layout)
        #
        contenedorDerTab1.resize(anchoContendor)
        #
        tab1BotonHboxSub1 = QHBoxLayout()
        tab1BotonHboxSub1.addWidget(contenedorIzqTab1)
        tab1BotonHboxSub1.addWidget(contenedorImageToolbarCentralTab1)#viewPixMapItem)
        tab1BotonHboxSub1.addWidget(contenedorDerTab1)
        sub1WindowTab1Boton.setLayout(tab1BotonHboxSub1)
        #
        #agrego el texto q representa la barra de conexion y la ventana de trending e imagen                                                                               #
        tab1BotonVbox = QVBoxLayout()
        tab1BotonVbox.setContentsMargins(5,5,5,5)
        tab1BotonVbox.addWidget(textEditTab1Boton)
        tab1BotonVbox.addWidget(self.pbarTab1)
        tab1BotonVbox.addWidget(sub1WindowTab1Boton)
        tab1Boton.setLayout(tab1BotonVbox)
        #******************************************
        #creo el contenido de la segunda pestaña
        #******************************************
        tab2Boton = QWidget() #defino la pestaña de la 2 camara
        textEditTab2Boton = QLineEdit()
        textEditTab2Boton.setText("Status: Camaras conectando ....")
        self.pbarTab2 = QProgressBar(self)
        self.pbarTab2.setGeometry(30,40,200,25)
        self.pbarTab2.setValue(0)

        self.timerPbar2 = QTimer()
        self.timerPbar2.timeout.connect(self.handleTimer2)
        self.timerPbar2.start(1000)

        sub1WindowTab2Boton = QWidget() #creo una subventana para mostrar la camara2 y las curvas2        
        sub2WindowTab2Boton = QWidget() #creo una subventana para mostrar las 2 curvas verticales
        scene2 = QGraphicsScene(0,0,0,0)
        pixmap2 = QPixmap("imageCam2.jpg")
        pixmapitem2 = scene2.addPixmap(pixmap2)
        viewPixMapItem2 = QGraphicsView(scene2)
        viewPixMapItem2.setRenderHint(QPainter.Antialiasing)
        #creo un contenedor para la imagen del tab2 y para el toolbar
        contenedorImageToolbarCentralTab2 = QWidget()
        #creo un layout vertical para el toolbar y la imagen
        contenedorImageToolbarCentralTab2layout = QVBoxLayout()
        #agrego el toolbar para la imagen del tab2
        toolBarImageTab2 = QToolBar("Toolbar Image Tab2")
        toolBarImageTab2.setIconSize(QSize(16,16))
        #cargo los iconos en la barra del toolbar
        #button in
        self.buttonZoomInActionImageTab2 = QAction(QIcon(os.path.join(basedir,"appIcons","magnifier-zoom-in.png")),"zoom in", self)
        self.buttonZoomInActionImageTab2.setStatusTip("Zoom In")
        self.buttonZoomInActionImageTab2.nombreBoton = "zoomInTab2"
        self.buttonZoomInActionImageTab2.triggered.connect(self.makeZoomIn)
        self.buttonZoomInActionImageTab2.setCheckable(True)
        #button out
        self.buttonZoomOutActionImageTab2 = QAction(QIcon(os.path.join(basedir,"appIcons","magnifier-zoom-out.png")),"zoom out",self)
        self.buttonZoomOutActionImageTab2.setStatusTip("Zoom Out")
        self.buttonZoomInActionImageTab2.nombreBoton = "zoomOutTab2"
        self.buttonZoomOutActionImageTab2.triggered.connect(self.makeZoomOut)
        self.buttonZoomOutActionImageTab2.setCheckable(True)
        #button roi rectangle
        self.buttonRectRoiActionImageTab2 = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape.png")),"Roi Rect", self)
        self.buttonRectRoiActionImageTab2.setStatusTip("Rectangle Roi")
        self.buttonRectRoiActionImageTab2.nombreBoton = "roiRectanguloTab2"
        self.buttonRectRoiActionImageTab2.triggered.connect(self.drawROIRectangle)
        self.buttonRectRoiActionImageTab2.setCheckable(True)
        #button roi ellipse
        self.buttonEllipRoiActionImageTab2 = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape-ellipse.png")),"Roi Ellipse", self)
        self.buttonEllipRoiActionImageTab2.setStatusTip("Ellipse Roi")
        self.buttonEllipRoiActionImageTab2.nombreBoton = "roiEllipseTab2"
        self.buttonEllipRoiActionImageTab2.triggered.connect(self.drawROICircle)
        self.buttonEllipRoiActionImageTab2.setCheckable(True)
        #button roi line
        self.buttonLineRoiActionImageTab2 = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape-line.png")),"Roi Line", self)
        self.buttonLineRoiActionImageTab2.setStatusTip("Line Roi")
        self.buttonLineRoiActionImageTab2.nombreBoton = "roiLineTab2"
        self.buttonLineRoiActionImageTab2.triggered.connect(self.drawROILine)
        self.buttonLineRoiActionImageTab2.setCheckable(True)
        #agrego los botones al toolbar
        toolBarImageTab2.addAction(self.buttonZoomInActionImageTab2)
        toolBarImageTab2.addAction(self.buttonZoomOutActionImageTab2)
        toolBarImageTab2.addAction(self.buttonRectRoiActionImageTab2)
        toolBarImageTab2.addAction(self.buttonEllipRoiActionImageTab2)
        toolBarImageTab2.addAction(self.buttonLineRoiActionImageTab2)
        #*******
        contenedorImageToolbarCentralTab2layout.addWidget(toolBarImageTab2)
        contenedorImageToolbarCentralTab2layout.addWidget(viewPixMapItem2)
        contenedorImageToolbarCentralTab2.setLayout(contenedorImageToolbarCentralTab2layout)
        #**********************
        #**********************
        #**********************
        #**********************
        #agrego grafico 1 izquierda para la camara 2
        graficoTab2Izq1 = MplCanvas(self, width=2, height=2, dpi=100)
        #genero una dataframe de prueba para la curva de la izquierda 1
        dfTab2Izq1 = pd.DataFrame([
            [0,10],
            [5,15],
            [2,20],
            [15,25],
            [4,10]
        ], columns=['A','B'])
        dfTab2Izq1.plot(ax=graficoTab2Izq1.axes)
        #agrego grafico 2 a la izquierda para la camara 2
        graficoTab2Izq2 = MplCanvas(self,width=2, height=2, dpi=100)
        #genero un data frame de prueba para la curva de la izquierda 2
        dfTab2Izq2 = pd.DataFrame([
            [0,10],
            [5,15],
            [2,20],
            [15,25],
            [4,10]
        ], columns=['A','B'])
        dfTab2Izq2.plot(ax=graficoTab2Izq2.axes)
        
        tab2BotonVBoxSub2 = QVBoxLayout()
        tab2BotonVBoxSub2.addWidget(graficoTab2Izq1)
        tab2BotonVBoxSub2.addWidget(graficoTab2Izq2)
        sub2WindowTab2Boton.setLayout(tab2BotonVBoxSub2)
        tab2BotonHBoxSub1 = QHBoxLayout()
        tab2BotonHBoxSub1.addWidget(sub2WindowTab2Boton)
        tab2BotonHBoxSub1.addWidget(contenedorImageToolbarCentralTab2)
        sub1WindowTab2Boton.setLayout(tab2BotonHBoxSub1)
        
        tab2BotonVBox = QVBoxLayout()
        tab2BotonVBox.setContentsMargins(5,5,5,5)
        tab2BotonVBox.addWidget(textEditTab2Boton)
        tab2BotonVBox.addWidget(self.pbarTab2)
        tab2BotonVBox.addWidget(sub1WindowTab2Boton)
        
        tab2Boton.setLayout(tab2BotonVBox)
        #******************************************
        #creo el contenido de la tercer pestaña
        #******************************************
        tab3Boton = QWidget() #defino la pestaña de la 3 camara
        textEditTab3Boton = QLineEdit() #agrego un texto esta parte la vamos a reemplazar con la barra de conexion
        textEditTab3Boton.setText("Status: Conectando camara ....")
        self.pbarTab3 = QProgressBar(self)
        self.pbarTab3.setGeometry(30,40,200,25)
        self.pbarTab3.setValue(0)

        self.timerPbar3 = QTimer()
        self.timerPbar3.timeout.connect(self.handleTimer3)
        self.timerPbar3.start(1000)

        sub1WindowTab3Boton = QWidget()
        sub2WindowTab3Boton = QWidget()
        scene3 = QGraphicsScene(0,0,0,0) #agrego el contenedor para el grafico
        pixmap3 = QPixmap("imageCam3.jpg") #leo la imagen que voy a mostrar en el conetenedor de graficos
        pixmapitem3 = scene3.addPixmap(pixmap3) # cargo la imagen que voy a mostrar en el contenedor de graficos
        viewPixMapItem3 = QGraphicsView(scene3) # Creo un mostrador de contenedores de graficos
        viewPixMapItem3.setRenderHint(QPainter.Antialiasing) #acomodo un poco los datos        
        #***********
        #***********
        #***********
        #creo un contenedor para la imagen del tab2 y para el toolbar
        contenedorImageToolbarCentralTab3 = QWidget()
        #creo un layout vertical para el toolbar y la imagen
        contenedorImageToolbarCentralTab3layout = QVBoxLayout()
        #agrego el toolbar para la imagen del tab2
        toolBarImageTab3 = QToolBar("Toolbar Image Tab3")
        toolBarImageTab3.setIconSize(QSize(16,16))
        #cargo los iconos en la barra del toolbar
        #button in
        self.buttonZoomInActionImageTab3 = QAction(QIcon(os.path.join(basedir,"appIcons","magnifier-zoom-in.png")),"zoom in", self)
        self.buttonZoomInActionImageTab3.setStatusTip("Zoom In")
        self.buttonZoomInActionImageTab3.nombreBoton = "zoomInTab3"
        self.buttonZoomInActionImageTab3.triggered.connect(self.makeZoomIn)
        self.buttonZoomInActionImageTab3.setCheckable(True)
        #button out
        self.buttonZoomOutActionImageTab3 = QAction(QIcon(os.path.join(basedir,"appIcons","magnifier-zoom-out.png")),"zoom out",self)
        self.buttonZoomOutActionImageTab3.setStatusTip("Zoom Out")
        self.buttonZoomOutActionImageTab3.nombreBoton = "zoomOutTab3"
        self.buttonZoomOutActionImageTab3.triggered.connect(self.makeZoomOut)
        self.buttonZoomOutActionImageTab3.setCheckable(True)
        #button roi rectangle
        self.buttonRectRoiActionImageTab3 = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape.png")),"Roi Rect", self)
        self.buttonRectRoiActionImageTab3.setStatusTip("Rectangle Roi")
        self.buttonRectRoiActionImageTab3.nombreBoton = "roiRectanguloTab3"
        self.buttonRectRoiActionImageTab3.triggered.connect(self.drawROIRectangle)
        self.buttonRectRoiActionImageTab3.setCheckable(True)
        #button roi ellipse
        self.buttonEllipRoiActionImageTab3 = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape-ellipse.png")),"Roi Ellipse", self)
        self.buttonEllipRoiActionImageTab3.setStatusTip("Ellipse Roi")
        self.buttonEllipRoiActionImageTab3.nombreBoton = "roiEllipseTab3"
        self.buttonEllipRoiActionImageTab3.triggered.connect(self.drawROICircle)
        self.buttonEllipRoiActionImageTab3.setCheckable(True)
        #button roi line
        self.buttonLineRoiActionImageTab3 = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape-line.png")),"Roi Line", self)
        self.buttonLineRoiActionImageTab3.setStatusTip("Line Roi")
        self.buttonLineRoiActionImageTab3.nombreBoton = "roiLineTab3"
        self.buttonLineRoiActionImageTab3.triggered.connect(self.drawROILine)
        self.buttonLineRoiActionImageTab3.setCheckable(True)
        #agrego los botones al toolbar
        toolBarImageTab3.addAction(self.buttonZoomInActionImageTab3)
        toolBarImageTab3.addAction(self.buttonZoomOutActionImageTab3)
        toolBarImageTab3.addAction(self.buttonRectRoiActionImageTab3)
        toolBarImageTab3.addAction(self.buttonEllipRoiActionImageTab3)
        toolBarImageTab3.addAction(self.buttonLineRoiActionImageTab3)
        #**************************
        contenedorImageToolbarCentralTab3layout.addWidget(toolBarImageTab3)
        contenedorImageToolbarCentralTab3layout.addWidget(viewPixMapItem3)
        contenedorImageToolbarCentralTab3.setLayout(contenedorImageToolbarCentralTab3layout)       
        #**************************
        #agrego grafico 1 izquierda para la camara 3
        graficoTab3Izq1 = MplCanvas(self, width= 2, height=2, dpi=100)
        #genero una dataframe de prueba para la curva de la izquierda 1
        dfTab3Izq1 = pd.DataFrame([
            [0,10],
            [5,15],
            [2,20],
            [15,25],
            [4,10],
        ], columns=['A','B'])
        dfTab3Izq1.plot(ax=graficoTab3Izq1.axes)
        #agrego grafico 2 izquierda para la camara 3
        graficoTab3Izq2 = MplCanvas(self, width=2, height=2, dpi=100)
        dfTab3Izq2 = pd.DataFrame([
            [0,10],
            [5,15],
            [2,20],
            [15,25],
            [4,10],
        ], columns=['A','B'])
        dfTab3Izq2.plot(ax=graficoTab3Izq2.axes)
        tab3BotonVBoxSub2 = QVBoxLayout()
        tab3BotonVBoxSub2.addWidget(graficoTab3Izq1)
        tab3BotonVBoxSub2.addWidget(graficoTab3Izq2)
        sub2WindowTab3Boton.setLayout(tab3BotonVBoxSub2)
        tab3BotonHBoxSub1 = QHBoxLayout()
        tab3BotonHBoxSub1.addWidget(sub2WindowTab3Boton)
        tab3BotonHBoxSub1.addWidget(contenedorImageToolbarCentralTab3) 
        sub1WindowTab3Boton.setLayout(tab3BotonHBoxSub1)
        tab3BotonVBox = QVBoxLayout() #creo un layout vertical para mostrar los datos del widget principal verticalmente
        tab3BotonVBox.setContentsMargins(5,5,5,5) #defino los margenes 
        tab3BotonVBox.addWidget(textEditTab3Boton) #agrego a este layout el texto
        tab3BotonVBox.addWidget(self.pbarTab3)
        tab3BotonVBox.addWidget(sub1WindowTab3Boton) #agrego a este layout la imagen
        tab3Boton.setLayout(tab3BotonVBox) #agrego al widget principal de este tab3 el layout que definimos
        #******************************************
        #creo el contenido de la cuarta pestaña
        #******************************************
        tab4Boton = QWidget() #defino la pestaña de las imagenes de los historicos
        textEditTab4BotonSelCam1 = QLabel()
        textEditTab4BotonSelCam1.setText("Sel Cam: ")
        textEditTab4BotonSelCam1.setBuddy(self.camCombo1)
        self.camCombo1.setToolTip("selection the camera to show")
        textEditTab4BotonSelCam2 = QLabel()
        textEditTab4BotonSelCam2.setText("Sel Cam: ")
        textEditTab4BotonSelCam2.setBuddy(self.camCombo2)
        self.camCombo2.setToolTip("selection the camera to show")
        #genero dos imagenes una a la izquierda y otra a la derecha
        #la imagen de la izquierda es la seleccion de historico 1 y la de la derecha la seleccion de historico 2
        #cada unos de los historicos ya sea el 1 o el 2 se pueden seleccionar de la camara 1 - camara 2 - camara 3
        #asi se pueden analizar imagenes cruzadas. Combinacion de analisis de imagenes historicas
        #agrego la grafica para la ventana de historicos de la izquierda el grafico de curvas
        graficoHistoricoIzq = MplCanvas(self, width=2, height=2, dpi=100)
        #genero un dataframe de prueba para los historicos de la izquierda
        dfHistoricoIzq = pd.DataFrame([
            [0,10],
            [5,15],
            [2,20],
            [15,25],
            [4,10]
        ], columns=['A','B'])
        dfHistoricoIzq.plot(ax=graficoHistoricoIzq.axes)
        #agrego la grafica para la ventana de historicos de la derecha
        graficoHistoricoDer = MplCanvas(self, width=2, height=2, dpi=100)
        #genero un dataframe de prueba para los historicos de la derecha
        dfHistoricoDer = pd.DataFrame([
            [0,10],
            [5,15],
            [2,20],
            [15,25],
            [4,10]
        ], columns=['A','B'])
        dfHistoricoDer.plot(ax=graficoHistoricoDer.axes)
        #agrego los indicadores de las mediciones 
        #vamos a tener dos para los historicos a la izquierda
        #agregamos el label 1 de la izquierda
        self.label1MessurementRoi = QLabel("Show ROI 1:")        
        self.label1MessurementRoi.setToolTip("Messurement to region of interest 1")
        #agregamos el indicador 1 de la izquierda
        self.valorMessurement1 = "10.52" #este valor va a ser el resultado de la roi 1
        self.output1MessurementRoi = QLabel(self.valorMessurement1)        
        self.output1MessurementRoi.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.label1MessurementRoi.setBuddy(self.output1MessurementRoi)
        #agregamos el label 2 de la izquierda
        self.label2MessurementRoi = QLabel("Show ROI 2:")        
        self.label2MessurementRoi.setToolTip("Messurement to region of interest 2")
        #agregamos el indicador 2 de la izquierda
        self.valorMessurement2 = "105.2" #este valor va a ser el resultado de la roi 2 
        self.output2MessurementRoi = QLabel(self.valorMessurement2)
        self.output2MessurementRoi.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.label2MessurementRoi.setBuddy(self.output2MessurementRoi)
        #genero un widget para mostrar la curva  y en 
        #horizontal un widget vertical con los indicadores
        #de ROI de medicion
        #creo el widget horizontal
        subWindowHistory1CamSubH = QWidget()
        #creo el widget vertical
        subWindowHistory1CamSubV = QWidget()
        #creo el layout vertical
        subWindowHistory1CamSubVLayout = QVBoxLayout()
        subWindowHistory1CamSubVLayout.addWidget(self.label1MessurementRoi)
        subWindowHistory1CamSubVLayout.addWidget(self.output1MessurementRoi)
        subWindowHistory1CamSubVLayout.addWidget(self.label2MessurementRoi)
        subWindowHistory1CamSubVLayout.addWidget(self.output2MessurementRoi)
        subWindowHistory1CamSubV.setLayout(subWindowHistory1CamSubVLayout)
        #creo el layout horizontal
        subWindowHistory1CamSubHLayout = QHBoxLayout()
        subWindowHistory1CamSubHLayout.addWidget(graficoHistoricoIzq)
        subWindowHistory1CamSubHLayout.addWidget(subWindowHistory1CamSubV)
        subWindowHistory1CamSubH.setLayout(subWindowHistory1CamSubHLayout)
        #agrego en la ventana a la derecha el grafico y los indicadores
        self.label1MessurementRoiDer = QLabel("Show ROI 1:")
        self.label1MessurementRoiDer.setToolTip("Messurement to region of interest 1")
        #agregamos el indicador 1 de la derecha
        self.valorMessurement1Der = "10.52"
        self.output1MessurementRoiDer = QLabel(self.valorMessurement1Der)
        self.output1MessurementRoiDer.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.label1MessurementRoiDer.setBuddy(self.output1MessurementRoiDer)        
        #agregamos el label 2 de la derecha
        self.label2MessurementRoiDer = QLabel("Show ROI 2:")
        self.label2MessurementRoiDer.setToolTip("Messurement to region of interest 2")
        #agregamos el indicador 2 de la derecha
        self.valorMessurement2 = "105.2"
        self.output2MessurementRoiDer = QLabel(self.valorMessurement2)
        self.output2MessurementRoiDer.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.label2MessurementRoiDer.setBuddy(self.output2MessurementRoiDer)        
        #agregamos el widget para el contenedor de la der
        #agregamos el widget para el contenedor de los
        #indicadores de medicion
        subWindowHistory2CamSubH = QWidget()
        subWindowHistory2CamSubV = QWidget()
        #creamos el layout vertical
        subWindowHistory2CamSubVlayout = QVBoxLayout()
        subWindowHistory2CamSubVlayout.addWidget(self.label1MessurementRoiDer)
        subWindowHistory2CamSubVlayout.addWidget(self.output1MessurementRoiDer)
        subWindowHistory2CamSubVlayout.addWidget(self.label2MessurementRoiDer)
        subWindowHistory2CamSubVlayout.addWidget(self.output2MessurementRoiDer)
        subWindowHistory2CamSubV.setLayout(subWindowHistory2CamSubVlayout)
        #creamos el layout horizontal
        subWindowHistory2CamSubHLayout = QHBoxLayout()
        subWindowHistory2CamSubHLayout.addWidget(graficoHistoricoDer)
        subWindowHistory2CamSubHLayout.addWidget(subWindowHistory2CamSubV)
        subWindowHistory2CamSubH.setLayout(subWindowHistory2CamSubHLayout)
        
        
        subWindowHistory1Cam = QWidget()#aca va a ir todo lo del registro historico de la camara 1
        subWindowHistory2Cam = QWidget()#aca va a ir todo lo del registro historico de la camara 2
        subWindowHistory1CamBanner = QWidget()#aca va a ir el banner del label del combobox el combobox para la seleccion de camara 1
        subWindowHistory2CamBanner = QWidget()#aca va a ir el banner del label del combobox el combobox para la seleccion de camara 2
        #agrego al banner la seleccion de camara seleccion de dia y la seleccion de imagen
        bannerSelCam1 = QHBoxLayout()
        bannerSelCam2 = QHBoxLayout()
        bannerSelCam1.addWidget(textEditTab4BotonSelCam1)
        bannerSelCam1.addWidget(self.camCombo1)
        bannerSelCam1.addWidget(self.dateCam1Image)
        bannerSelCam1.addWidget(self.img1ComboBoxReading)
        bannerSelCam2.addWidget(textEditTab4BotonSelCam2)
        bannerSelCam2.addWidget(self.camCombo2)
        bannerSelCam2.addWidget(self.dateCam2Image)
        bannerSelCam2.addWidget(self.img2ComboBoxReading)
        subWindowHistory1CamBanner.setLayout(bannerSelCam1)
        subWindowHistory2CamBanner.setLayout(bannerSelCam2)

        #genero la imagen 1 a la izquierda en la pantalla de historicos
        imageHistory1CamScene = QGraphicsScene(0,0,0,0)
        imageHistory1CamPixmap = QPixmap("imageCam1.jpg")
        imageHistory1PixmapItem = imageHistory1CamScene.addPixmap(imageHistory1CamPixmap)
        imageHistory1ViewPixMapItem = QGraphicsView(imageHistory1CamScene)
        imageHistory1ViewPixMapItem.setRenderHint(QPainter.Antialiasing)
        #genero un toolbar para la imagen de la izquierda en la pantalla de historicos
        toolBarImageHistoryIzq = QToolBar("Toolbar Image History 1")
        toolBarImageHistoryIzq.setIconSize(QSize(16,16))
        #cargo los iconos en la barra del toolbar
        #button in
        self.buttonZoomInActionHistoryIzq = QAction(QIcon(os.path.join(basedir,"appIcons","magnifier-zoom-in.png")),"zoom in", self)
        self.buttonZoomInActionHistoryIzq.setStatusTip("Zoom In")
        self.buttonZoomInActionHistoryIzq.nombreBoton = "zoomInTabHistoryIzq"
        self.buttonZoomInActionHistoryIzq.triggered.connect(self.makeZoomIn)
        self.buttonZoomInActionHistoryIzq.setCheckable(True)
        #button out
        self.buttonZoomOutActionHistoryIzq = QAction(QIcon(os.path.join(basedir,"appIcons","magnifier-zoom-out.png")),"zoom out",self)
        self.buttonZoomOutActionHistoryIzq.setStatusTip("Zoom Out")
        self.buttonZoomOutActionHistoryIzq.nombreBoton = "zoomOutTabHistoryIzq"
        self.buttonZoomOutActionHistoryIzq.triggered.connect(self.makeZoomOut)
        self.buttonZoomOutActionHistoryIzq.setCheckable(True)
        #button roi rectangle
        self.buttonRectRoiActionHistoryIzq = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape.png")),"Roi Rect", self)
        self.buttonRectRoiActionHistoryIzq.setStatusTip("Rectangle Roi")
        self.buttonRectRoiActionHistoryIzq.nombreBoton = "roiRectanguloTabHistoryIzq"
        self.buttonRectRoiActionHistoryIzq.triggered.connect(self.drawROIRectangle)
        self.buttonRectRoiActionHistoryIzq.setCheckable(True)
        #button roi ellipse
        self.buttonEllipRoiActionHistoryIzq = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape-ellipse.png")),"Roi Ellipse", self)
        self.buttonEllipRoiActionHistoryIzq.setStatusTip("Ellipse Roi")
        self.buttonEllipRoiActionHistoryIzq.nombreBoton = "roiEllipseTabHistoryIzq"
        self.buttonEllipRoiActionHistoryIzq.triggered.connect(self.drawROICircle)
        self.buttonEllipRoiActionHistoryIzq.setCheckable(True)
        #button roi line
        self.buttonLineRoiActionHistoryIzq = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape-line.png")),"Roi Line", self)
        self.buttonLineRoiActionHistoryIzq.setStatusTip("Line Roi")
        self.buttonLineRoiActionHistoryIzq.nombreBoton = "roiLineTabHistoryIzq"
        self.buttonLineRoiActionHistoryIzq.triggered.connect(self.drawROILine)
        self.buttonLineRoiActionHistoryIzq.setCheckable(True)
        #agrego los botones al toolbar
        toolBarImageHistoryIzq.addAction(self.buttonZoomInActionHistoryIzq)
        toolBarImageHistoryIzq.addAction(self.buttonZoomOutActionHistoryIzq)
        toolBarImageHistoryIzq.addAction(self.buttonRectRoiActionHistoryIzq)
        toolBarImageHistoryIzq.addAction(self.buttonEllipRoiActionHistoryIzq)
        toolBarImageHistoryIzq.addAction(self.buttonLineRoiActionHistoryIzq)
        
        self.imgHistIzqWidget = QWidget() #contenedor para el toolbar y la imagen

                
        self.imgHistIzqWidgetLayout = QVBoxLayout() #defino el layout del toolbar y de la imagen
        self.imgHistIzqWidgetLayout.addWidget(toolBarImageHistoryIzq) #cargo el toolbar
        self.imgHistIzqWidgetLayout.addWidget(imageHistory1ViewPixMapItem) #cargo la imagen
        self.imgHistIzqWidget.setLayout(self.imgHistIzqWidgetLayout) #seteo el layout en el contenedor

        
        #genero la imagen 2
        imageHistory2CamScene = QGraphicsScene(0,0,0,0)
        imageHistory2CamPixmap = QPixmap("imageCam2.jpg")
        imageHistory2PixmapItem = imageHistory2CamScene.addPixmap(imageHistory2CamPixmap)
        imageHistory2ViewPixMapItem = QGraphicsView(imageHistory2CamScene)
        imageHistory2ViewPixMapItem.setRenderHint(QPainter.Antialiasing)
        #genero un toolbar para la imagen de la derecha en la pantalla de historicos
        toolBarImageHistoryDer = QToolBar("Toolbar Image History 2")
        toolBarImageHistoryDer.setIconSize(QSize(16,16))
        #cargo los iconos en la barra del toolbar
        #button In
        self.buttonZoomInActionHistoryDer = QAction(QIcon(os.path.join(basedir,"appIcons","magnifier-zoom-in.png")),"zoom in", self)
        self.buttonZoomInActionHistoryDer.setStatusTip("Zoom In")
        self.buttonZoomInActionHistoryDer.nombreBoton = "zoomInTabHistoryDer"
        self.buttonZoomInActionHistoryDer.triggered.connect(self.makeZoomIn)
        self.buttonZoomInActionHistoryDer.setCheckable(True)
        #button Out
        self.buttonZoomOutActionHistoryDer = QAction(QIcon(os.path.join(basedir,"appIcons","magnifier-zoom-out.png")),"zoom out", self)
        self.buttonZoomOutActionHistoryDer.setStatusTip("Zoom Out")
        self.buttonZoomOutActionHistoryDer.nombreBoton = "zoomOutTabHistoryDer"
        self.buttonZoomOutActionHistoryDer.triggered.connect(self.makeZoomOut)
        self.buttonZoomOutActionHistoryDer.setCheckable(True)
        #button Roi Rectangle 
        self.buttonRectRoiActionHistoryDer = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape.png")),"Roi Rect", self)
        self.buttonRectRoiActionHistoryDer.setStatusTip("Rectangle Roi")
        self.buttonRectRoiActionHistoryDer.nombreBoton ="roiRectanguloTabHistoryDer"
        self.buttonRectRoiActionHistoryDer.triggered.connect(self.drawROIRectangle)
        self.buttonRectRoiActionHistoryDer.setCheckable(True)
        #button Roi Ellipse
        self.buttonEllipRoiActionHistoryDer = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape-ellipse.png")),"Roi Ellipse", self)
        self.buttonEllipRoiActionHistoryDer.setStatusTip("Ellipse Roi")
        self.buttonEllipRoiActionHistoryDer.nombreBoton = "roiEllipseTabHistoryDer"
        self.buttonEllipRoiActionHistoryDer.triggered.connect(self.drawROICircle)
        self.buttonEllipRoiActionHistoryDer.setCheckable(True)
        #button Roi Line
        self.buttonLineRoiActionHistoryDer = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape-line.png")),"Roi Line",self)
        self.buttonLineRoiActionHistoryDer.setStatusTip("Line Roi")
        self.buttonLineRoiActionHistoryDer.nombreBoton = "roiLineTabHistoryDer"
        self.buttonLineRoiActionHistoryDer.triggered.connect(self.drawROILine)
        self.buttonLineRoiActionHistoryDer.setCheckable(True)
        #agrego los botones al toolbar
        toolBarImageHistoryDer.addAction(self.buttonZoomInActionHistoryDer)
        toolBarImageHistoryDer.addAction(self.buttonZoomOutActionHistoryDer)
        toolBarImageHistoryDer.addAction(self.buttonRectRoiActionHistoryDer)
        toolBarImageHistoryDer.addAction(self.buttonEllipRoiActionHistoryDer)
        toolBarImageHistoryDer.addAction(self.buttonLineRoiActionHistoryDer)
        
        self.imgHistDerWidget = QWidget() #contenedor para el toolbar y la imagen a la derecha del historico

        self.imgHistDerWidgetLayout = QVBoxLayout() #defino el layout del contenedor de toolbar e imagen a derecha
        self.imgHistDerWidgetLayout.addWidget(toolBarImageHistoryDer)
        self.imgHistDerWidgetLayout.addWidget(imageHistory2ViewPixMapItem)
        self.imgHistDerWidget.setLayout(self.imgHistDerWidgetLayout)

        #adjunto la imagen
        subHistory1VBox = QVBoxLayout() #creo un layout vertical para los historicos de la camara 1
        subHistory2VBox = QVBoxLayout() #creo un layout vertical para los historicos de la camara 2 
        tab4BotonHBox = QHBoxLayout() #creo un layou horizontal para contener los dos historicos el de la camara 1 y 2
        tab4BotonHBox.setContentsMargins(5,5,5,5)        
        subHistory1VBox.addWidget(subWindowHistory1CamBanner) #agrego al historico vertical el banner de la camara 1
        subHistory1VBox.addWidget(self.imgHistIzqWidget)#imageHistory1ViewPixMapItem) #agrego al historico vertical 1 la imagen registrada       
        subHistory1VBox.addWidget(subWindowHistory1CamSubH)
        subHistory2VBox.addWidget(subWindowHistory2CamBanner) #agrego al historico vertical el banner de la camara 2
        subHistory2VBox.addWidget(self.imgHistDerWidget) #agrego al historico vertical 2 la imagen registrada        
        subHistory2VBox.addWidget(subWindowHistory2CamSubH)
        subWindowHistory1Cam.setLayout(subHistory1VBox) #selecciono el layout vertical 1 para el widget history cam 1
        subWindowHistory2Cam.setLayout(subHistory2VBox) #selecciono el layout vertical 2 para el widget history cam 2       
        tab4BotonHBox.addWidget(subWindowHistory1Cam) #agrego al layout horizontal pricipal el widget vertical 1
        tab4BotonHBox.addWidget(subWindowHistory2Cam) #agrego al layout horizontal principal el widget vertical 2
        tab4Boton.setLayout(tab4BotonHBox) #selecciono el layout horizontal principal para el widget del tab historicos
        #******************************************
        #creo el contenido de la quinta pestaña
        #******************************************
        tab5Boton = QWidget() #defino la pestaña de configuracion para las cámaras
        contenedorPresetCam1 = QWidget()
        layoutContenedorPresetCam1 = QVBoxLayout()
        textEditCam1Configuration = QLabel("Configuration of camera 1")
        textEditCam1Configuration.setStyleSheet("border: 2px solid orange;border-radius: 10px;padding: 2px; text-align:center; background-color: lightyellow;")
        textEditCam1Configuration.setFixedSize(QSize(205,24))
        contenedorGrupoPresetCam1 = QGroupBox()
        contenedorGrupoPresetCam1.setStyleSheet("border: 2px solid lightblue;border-radius: 10px;")
        #zona declaracion controles de preset
        contenedorValuePreset1Cam1Layout = QHBoxLayout()
        labelValuePreset1Cam1 = QLabel("Preset 1")
        labelValuePreset1Cam1.setFixedSize(QSize(64,16))
        labelValuePreset1Cam1.setStyleSheet("border-style: none;")
        valuePreset1Cam1 = AnimatedToggle()
        valuePreset1Cam1.setFixedSize(valuePreset1Cam1.sizeHint())
        valuePreset1Cam1.setToolTip("Toggle to change preset 1")
        #Defino la funcion asociada al set y reset de los presets
        enablePreset1Cam1 = partial(self.popUpConfiguracionPresetCam1, valuePreset1Cam1)
        disablePreset1Cam1 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset1Cam1)
        valuePreset1Cam1.stateChanged.connect(lambda x: enablePreset1Cam1() if x else disablePreset1Cam1())
        #        
        contenedorValuePreset1Cam1Layout.addWidget(labelValuePreset1Cam1)
        contenedorValuePreset1Cam1Layout.addWidget(valuePreset1Cam1)
        #preset 2
        contenedorValuePreset2Cam1Layout = QHBoxLayout()
        labelValuePreset2Cam1 = QLabel("Preset 2")
        labelValuePreset2Cam1.setFixedSize(QSize(64,16))
        labelValuePreset2Cam1.setStyleSheet("border-style: none;")
        valuePreset2Cam1 = AnimatedToggle()
        valuePreset2Cam1.setFixedSize(valuePreset2Cam1.sizeHint())
        valuePreset2Cam1.setToolTip("Toggle to change preset 2")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset2Cam1 = partial(self.popUpConfiguracionPresetCam1, valuePreset2Cam1)
        disablePreset2Cam1 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset2Cam1)
        valuePreset2Cam1.stateChanged.connect(lambda x: enablePreset2Cam1() if x else disablePreset2Cam1())
        #  
        #
        contenedorValuePreset2Cam1Layout.addWidget(labelValuePreset2Cam1)
        contenedorValuePreset2Cam1Layout.addWidget(valuePreset2Cam1)    
        #preset 3
        contenedorValuePreset3Cam1Layout = QHBoxLayout()
        labelValuePreset3Cam1 = QLabel("Preset 3")
        labelValuePreset3Cam1.setFixedSize(QSize(64,16))        
        labelValuePreset3Cam1.setStyleSheet("border-style: none;")
        valuePreset3Cam1 = AnimatedToggle()
        valuePreset3Cam1.setFixedSize(valuePreset3Cam1.sizeHint())
        valuePreset3Cam1.setToolTip("Toggle to change preset 3")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset3Cam1 = partial(self.popUpConfiguracionPresetCam1, valuePreset3Cam1)
        disablePreset3Cam1 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset3Cam1)
        valuePreset3Cam1.stateChanged.connect(lambda x: enablePreset3Cam1() if x else disablePreset3Cam1())
        # 
        #
        contenedorValuePreset3Cam1Layout.addWidget(labelValuePreset3Cam1)
        contenedorValuePreset3Cam1Layout.addWidget(valuePreset3Cam1)
        #preset 4
        contenedorValuePreset4Cam1Layout = QHBoxLayout()
        labelValuePreset4Cam1 = QLabel("Preset 4")
        labelValuePreset4Cam1.setFixedSize(QSize(64,16))
        labelValuePreset4Cam1.setStyleSheet("border-style: none;")
        valuePreset4Cam1 = AnimatedToggle()
        valuePreset4Cam1.setFixedSize(valuePreset4Cam1.sizeHint())
        valuePreset4Cam1.setToolTip("Toggle to change preset 4")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset4Cam1 = partial(self.popUpConfiguracionPresetCam1, valuePreset4Cam1)
        disablePreset4Cam1 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset4Cam1)
        valuePreset4Cam1.stateChanged.connect(lambda x: enablePreset4Cam1() if x else disablePreset4Cam1())
        # 
        #
        contenedorValuePreset4Cam1Layout.addWidget(labelValuePreset4Cam1)
        contenedorValuePreset4Cam1Layout.addWidget(valuePreset4Cam1)
        #preset 5
        contenedorValuePreset5Cam1Layout = QHBoxLayout()
        labelValuePreset5Cam1 = QLabel("Preset 5")
        labelValuePreset5Cam1.setFixedSize(QSize(64,16))
        labelValuePreset5Cam1.setStyleSheet("border-style: none;")
        valuePreset5Cam1 = AnimatedToggle()
        valuePreset5Cam1.setFixedSize(valuePreset5Cam1.sizeHint())
        valuePreset5Cam1.setToolTip("Toggle to change preset 5")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset5Cam1 = partial(self.popUpConfiguracionPresetCam1, valuePreset5Cam1)
        disablePreset5Cam1 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset5Cam1)
        valuePreset5Cam1.stateChanged.connect(lambda x: enablePreset5Cam1() if x else disablePreset5Cam1())
        #
        #
        contenedorValuePreset5Cam1Layout.addWidget(labelValuePreset5Cam1)
        contenedorValuePreset5Cam1Layout.addWidget(valuePreset5Cam1)        
        #preset 6
        contenedorValuePreset6Cam1Layout = QHBoxLayout()
        labelValuePreset6Cam1 = QLabel("Preset 6")
        labelValuePreset6Cam1.setFixedSize(QSize(64,16))
        labelValuePreset6Cam1.setStyleSheet("border-style: none;")
        valuePreset6Cam1 = AnimatedToggle()
        valuePreset6Cam1.setFixedSize(valuePreset6Cam1.sizeHint())
        valuePreset6Cam1.setToolTip("Toggle to change preset 6")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset6Cam1 = partial(self.popUpConfiguracionPresetCam1, valuePreset6Cam1)
        disablePreset6Cam1 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset6Cam1)
        valuePreset6Cam1.stateChanged.connect(lambda x: enablePreset6Cam1() if x else disablePreset6Cam1())
        #
        #
        contenedorValuePreset6Cam1Layout.addWidget(labelValuePreset6Cam1)
        contenedorValuePreset6Cam1Layout.addWidget(valuePreset6Cam1)
        #preset 7
        contenedorValuePreset7Cam1Layout = QHBoxLayout()
        labelValuePreset7Cam1 = QLabel("Preset 7")
        labelValuePreset7Cam1.setFixedSize(QSize(64,16))
        labelValuePreset7Cam1.setStyleSheet("border-style: none;")
        valuePreset7Cam1 = AnimatedToggle()
        valuePreset7Cam1.setFixedSize(valuePreset7Cam1.sizeHint())
        valuePreset7Cam1.setToolTip("Toggle to change preset 7")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset7Cam1 = partial(self.popUpConfiguracionPresetCam1, valuePreset7Cam1)
        disablePreset7Cam1 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset7Cam1)
        valuePreset7Cam1.stateChanged.connect(lambda x: enablePreset7Cam1() if x else disablePreset7Cam1())
        #
        #
        contenedorValuePreset7Cam1Layout.addWidget(labelValuePreset7Cam1)
        contenedorValuePreset7Cam1Layout.addWidget(valuePreset7Cam1)
        #preset 8
        contenedorValuePreset8Cam1Layout = QHBoxLayout()
        labelValuePreset8Cam1 = QLabel("Preset 8")
        labelValuePreset8Cam1.setFixedSize(QSize(64,16))
        labelValuePreset8Cam1.setStyleSheet("border-style: none;")
        valuePreset8Cam1 = AnimatedToggle()
        valuePreset8Cam1.setFixedSize(valuePreset8Cam1.sizeHint())
        valuePreset8Cam1.setToolTip("Toggle to change preset 8")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset8Cam1 = partial(self.popUpConfiguracionPresetCam1, valuePreset8Cam1)
        disablePreset8Cam1 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset8Cam1)
        valuePreset8Cam1.stateChanged.connect(lambda x: enablePreset8Cam1() if x else disablePreset8Cam1())
        #
        #
        contenedorValuePreset8Cam1Layout.addWidget(labelValuePreset8Cam1)
        contenedorValuePreset8Cam1Layout.addWidget(valuePreset8Cam1)
        #agrego los preset en el layout vertical dentro del grupo de preset camara 1
        contenedorPresetCam1Layout = QVBoxLayout()
        contenedorPresetCam1Layout.addLayout(contenedorValuePreset1Cam1Layout)
        contenedorPresetCam1Layout.addLayout(contenedorValuePreset2Cam1Layout)
        contenedorPresetCam1Layout.addLayout(contenedorValuePreset3Cam1Layout)
        contenedorPresetCam1Layout.addLayout(contenedorValuePreset4Cam1Layout)
        contenedorPresetCam1Layout.addLayout(contenedorValuePreset5Cam1Layout)
        contenedorPresetCam1Layout.addLayout(contenedorValuePreset6Cam1Layout)
        contenedorPresetCam1Layout.addLayout(contenedorValuePreset7Cam1Layout)
        contenedorPresetCam1Layout.addLayout(contenedorValuePreset8Cam1Layout)
        contenedorGrupoPresetCam1.setLayout(contenedorPresetCam1Layout)
        #************
        textEditCam1Configuration.setBuddy(contenedorGrupoPresetCam1)
        #configuramos el layout de la camara 1 con el label y el grupo
        layoutContenedorPresetCam1.addWidget(textEditCam1Configuration)
        layoutContenedorPresetCam1.addWidget(contenedorGrupoPresetCam1)
        contenedorPresetCam1.setLayout(layoutContenedorPresetCam1)
        
        contenedorPresetCam2 = QWidget()
        layoutContenedorPresetCam2 = QVBoxLayout()
        textEditCam2Configuration = QLabel("Configuration of camera 2")
        textEditCam2Configuration.setStyleSheet("border: 2px solid orange;border-radius: 10px;padding: 2px; text-align:center; background-color: lightyellow;")
        textEditCam2Configuration.setFixedSize(QSize(205,24))
        contenedorGrupoPresetCam2 = QGroupBox()        
        contenedorGrupoPresetCam2.setStyleSheet("border: 2px solid lightblue;border-radius: 10px;")
        ##
        #zona declaracion controles de preset
        contenedorValuePreset1Cam2Layout = QHBoxLayout()
        labelValuePreset1Cam2 = QLabel("Preset 1")
        labelValuePreset1Cam2.setFixedSize(QSize(64,16))
        labelValuePreset1Cam2.setStyleSheet("border-style: none;")
        valuePreset1Cam2 = AnimatedToggle()
        valuePreset1Cam2.setFixedSize(valuePreset1Cam2.sizeHint())
        valuePreset1Cam2.setToolTip("Toggle to change preset 1")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset1Cam2 = partial(self.popUpConfiguracionPresetCam1, valuePreset1Cam2)
        disablePreset1Cam2 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset1Cam2)
        valuePreset1Cam2.stateChanged.connect(lambda x: enablePreset1Cam2() if x else disablePreset1Cam2())
        #
        #
        contenedorValuePreset1Cam2Layout.addWidget(labelValuePreset1Cam2)
        contenedorValuePreset1Cam2Layout.addWidget(valuePreset1Cam2)
        #preset 2
        contenedorValuePreset2Cam2Layout = QHBoxLayout()
        labelValuePreset2Cam2 = QLabel("Preset 2")
        labelValuePreset2Cam2.setFixedSize(QSize(64,16))
        labelValuePreset2Cam2.setStyleSheet("border-style: none;")
        valuePreset2Cam2 = AnimatedToggle()
        valuePreset2Cam2.setFixedSize(valuePreset2Cam2.sizeHint())
        valuePreset2Cam2.setToolTip("Toggle to change preset 2")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset2Cam2 = partial(self.popUpConfiguracionPresetCam1, valuePreset2Cam2)
        disablePreset2Cam2 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset2Cam2)
        valuePreset2Cam2.stateChanged.connect(lambda x: enablePreset2Cam2() if x else disablePreset2Cam2())
        #
        #
        contenedorValuePreset2Cam2Layout.addWidget(labelValuePreset2Cam2)
        contenedorValuePreset2Cam2Layout.addWidget(valuePreset2Cam2)    
        #preset 3
        contenedorValuePreset3Cam2Layout = QHBoxLayout()
        labelValuePreset3Cam2 = QLabel("Preset 3")
        labelValuePreset3Cam2.setFixedSize(QSize(64,16))
        labelValuePreset3Cam2.setStyleSheet("border-style: none;")
        valuePreset3Cam2 = AnimatedToggle()
        valuePreset3Cam2.setFixedSize(valuePreset3Cam2.sizeHint())
        valuePreset3Cam2.setToolTip("Toggle to change preset 3")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset3Cam2 = partial(self.popUpConfiguracionPresetCam1, valuePreset3Cam2)
        disablePreset3Cam2 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset3Cam2)
        valuePreset3Cam2.stateChanged.connect(lambda x: enablePreset3Cam2() if x else disablePreset3Cam2())
        #
        #
        contenedorValuePreset3Cam2Layout.addWidget(labelValuePreset3Cam2)
        contenedorValuePreset3Cam2Layout.addWidget(valuePreset3Cam2)
        #preset 4
        contenedorValuePreset4Cam2Layout = QHBoxLayout()
        labelValuePreset4Cam2 = QLabel("Preset 4")
        labelValuePreset4Cam2.setFixedSize(QSize(64,16))
        labelValuePreset4Cam2.setStyleSheet("border-style: none;")
        valuePreset4Cam2 = AnimatedToggle()
        valuePreset4Cam2.setFixedSize(valuePreset4Cam2.sizeHint())
        valuePreset4Cam2.setToolTip("Toggle to change preset 4")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset4Cam2 = partial(self.popUpConfiguracionPresetCam1, valuePreset4Cam2)
        disablePreset4Cam2 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset4Cam2)
        valuePreset4Cam2.stateChanged.connect(lambda x: enablePreset4Cam2() if x else disablePreset4Cam2())
        #
        #
        contenedorValuePreset4Cam2Layout.addWidget(labelValuePreset4Cam2)
        contenedorValuePreset4Cam2Layout.addWidget(valuePreset4Cam2)
        #preset 5
        contenedorValuePreset5Cam2Layout = QHBoxLayout()
        labelValuePreset5Cam2 = QLabel("Preset 5")
        labelValuePreset5Cam2.setFixedSize(QSize(64,16))
        labelValuePreset5Cam2.setStyleSheet("border-style: none;")
        valuePreset5Cam2 = AnimatedToggle()
        valuePreset5Cam2.setFixedSize(valuePreset5Cam2.sizeHint())
        valuePreset5Cam2.setToolTip("Toggle to change preset 5")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset5Cam2 = partial(self.popUpConfiguracionPresetCam1, valuePreset5Cam2)
        disablePreset5Cam2 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset5Cam2)
        valuePreset5Cam2.stateChanged.connect(lambda x: enablePreset5Cam2() if x else disablePreset5Cam2())
        #
        #
        contenedorValuePreset5Cam2Layout.addWidget(labelValuePreset5Cam2)
        contenedorValuePreset5Cam2Layout.addWidget(valuePreset5Cam2)
        #preset 6
        contenedorValuePreset6Cam2Layout = QHBoxLayout()
        labelValuePreset6Cam2 = QLabel("Preset 6")
        labelValuePreset6Cam2.setFixedSize(QSize(64,16))
        labelValuePreset6Cam2.setStyleSheet("border-style: none;")
        valuePreset6Cam2 = AnimatedToggle()
        valuePreset6Cam2.setFixedSize(valuePreset6Cam2.sizeHint())
        valuePreset6Cam2.setToolTip("Toggle to change preset 6")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset6Cam2 = partial(self.popUpConfiguracionPresetCam1, valuePreset6Cam2)
        disablePreset6Cam2 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset6Cam2)
        valuePreset6Cam2.stateChanged.connect(lambda x: enablePreset6Cam2() if x else disablePreset6Cam2())
        #
        #
        contenedorValuePreset6Cam2Layout.addWidget(labelValuePreset6Cam2)
        contenedorValuePreset6Cam2Layout.addWidget(valuePreset6Cam2)
        #preset 7
        contenedorValuePreset7Cam2Layout = QHBoxLayout()
        labelValuePreset7Cam2 = QLabel("Preset 7")
        labelValuePreset7Cam2.setFixedSize(QSize(64,16))
        labelValuePreset7Cam2.setStyleSheet("border-style: none;")
        valuePreset7Cam2 = AnimatedToggle()
        valuePreset7Cam2.setFixedSize(valuePreset7Cam2.sizeHint())
        valuePreset7Cam2.setToolTip("Toggle to change preset 7")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset7Cam2 = partial(self.popUpConfiguracionPresetCam1, valuePreset7Cam2)
        disablePreset7Cam2 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset7Cam2)
        valuePreset7Cam2.stateChanged.connect(lambda x: enablePreset7Cam2() if x else disablePreset7Cam2())
        #
        #
        contenedorValuePreset7Cam2Layout.addWidget(labelValuePreset7Cam2)
        contenedorValuePreset7Cam2Layout.addWidget(valuePreset7Cam2)
        #preset 8
        contenedorValuePreset8Cam2Layout = QHBoxLayout()
        labelValuePreset8Cam2 = QLabel("Preset 8")
        labelValuePreset8Cam2.setFixedSize(QSize(64,16))
        labelValuePreset8Cam2.setStyleSheet("border-style: none;")
        valuePreset8Cam2 = AnimatedToggle()
        valuePreset8Cam2.setFixedSize(valuePreset8Cam2.sizeHint())
        valuePreset8Cam2.setToolTip("Toggle to change preset 8")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset8Cam2 = partial(self.popUpConfiguracionPresetCam1, valuePreset8Cam2)
        disablePreset8Cam2 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset8Cam2)
        valuePreset8Cam2.stateChanged.connect(lambda x: enablePreset8Cam2() if x else disablePreset8Cam2())
        #
        #
        contenedorValuePreset8Cam2Layout.addWidget(labelValuePreset8Cam2)
        contenedorValuePreset8Cam2Layout.addWidget(valuePreset8Cam2)
        #agrego los preset en el layout vertical dentro del grupo de preset camara 2
        contenedorPresetCam2Layout = QVBoxLayout()
        contenedorPresetCam2Layout.addLayout(contenedorValuePreset1Cam2Layout)
        contenedorPresetCam2Layout.addLayout(contenedorValuePreset2Cam2Layout)
        contenedorPresetCam2Layout.addLayout(contenedorValuePreset3Cam2Layout)
        contenedorPresetCam2Layout.addLayout(contenedorValuePreset4Cam2Layout)
        contenedorPresetCam2Layout.addLayout(contenedorValuePreset5Cam2Layout)
        contenedorPresetCam2Layout.addLayout(contenedorValuePreset6Cam2Layout)
        contenedorPresetCam2Layout.addLayout(contenedorValuePreset7Cam2Layout)
        contenedorPresetCam2Layout.addLayout(contenedorValuePreset8Cam2Layout)
        contenedorGrupoPresetCam2.setLayout(contenedorPresetCam2Layout)
        ##
        textEditCam2Configuration.setBuddy(contenedorGrupoPresetCam2)
        #configuramos el layout de la camara 2 con el label y el grupo
        layoutContenedorPresetCam2.addWidget(textEditCam2Configuration)
        layoutContenedorPresetCam2.addWidget(contenedorGrupoPresetCam2)
        contenedorPresetCam2.setLayout(layoutContenedorPresetCam2)

        contenedorPresetCam3 = QWidget()
        layoutContenedorPresetCam3 = QVBoxLayout()
        textEditCam3Configuration = QLabel("Configuration of camera 3")
        textEditCam3Configuration.setStyleSheet("border: 2px solid orange;border-radius: 10px;padding: 2px; text-align:center; background-color: lightyellow;")
        textEditCam3Configuration.setFixedSize(QSize(205,24))
        contenedorGrupoPresetCam3 = QGroupBox()
        contenedorGrupoPresetCam3.setStyleSheet("border: 2px solid lightblue;border-radius: 10px;")
        ##
        #zona declaracion controles de preset
        contenedorValuePreset1Cam3Layout = QHBoxLayout()
        labelValuePreset1Cam3 = QLabel("Preset 1")
        labelValuePreset1Cam3.setFixedSize(QSize(64,16))
        labelValuePreset1Cam3.setStyleSheet("border-style: none;")
        valuePreset1Cam3 = AnimatedToggle()
        valuePreset1Cam3.setFixedSize(valuePreset1Cam3.sizeHint())
        valuePreset1Cam3.setToolTip("Toggle to change preset 1")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset1Cam3 = partial(self.popUpConfiguracionPresetCam1, valuePreset1Cam3)
        disablePreset1Cam3 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset1Cam3)
        valuePreset1Cam3.stateChanged.connect(lambda x: enablePreset1Cam3() if x else disablePreset1Cam3())
        #
        #
        contenedorValuePreset1Cam3Layout.addWidget(labelValuePreset1Cam3)
        contenedorValuePreset1Cam3Layout.addWidget(valuePreset1Cam3)
        #preset 2
        contenedorValuePreset2Cam3Layout = QHBoxLayout()
        labelValuePreset2Cam3 = QLabel("Preset 2")
        labelValuePreset2Cam3.setFixedSize(QSize(64,16))
        labelValuePreset2Cam3.setStyleSheet("border-style: none;")
        valuePreset2Cam3 = AnimatedToggle()
        valuePreset2Cam3.setFixedSize(valuePreset2Cam3.sizeHint())
        valuePreset2Cam3.setToolTip("Toggle to change preset 2")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset2Cam3 = partial(self.popUpConfiguracionPresetCam1, valuePreset2Cam3)
        disablePreset2Cam3 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset2Cam3)
        valuePreset2Cam3.stateChanged.connect(lambda x: enablePreset2Cam3() if x else disablePreset2Cam3())
        #        
        #
        contenedorValuePreset2Cam3Layout.addWidget(labelValuePreset2Cam3)
        contenedorValuePreset2Cam3Layout.addWidget(valuePreset2Cam3)    
        #preset 3
        contenedorValuePreset3Cam3Layout = QHBoxLayout()
        labelValuePreset3Cam3 = QLabel("Preset 3")
        labelValuePreset3Cam3.setFixedSize(QSize(64,16))
        labelValuePreset3Cam3.setStyleSheet("border-style: none;")
        valuePreset3Cam3 = AnimatedToggle()
        valuePreset3Cam3.setFixedSize(valuePreset3Cam3.sizeHint())
        valuePreset3Cam3.setToolTip("Toggle to change preset 3")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset3Cam3 = partial(self.popUpConfiguracionPresetCam1, valuePreset3Cam3)
        disablePreset3Cam3 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset3Cam3)
        valuePreset3Cam3.stateChanged.connect(lambda x: enablePreset3Cam3() if x else disablePreset3Cam3())
        #
        #
        contenedorValuePreset3Cam3Layout.addWidget(labelValuePreset3Cam3)
        contenedorValuePreset3Cam3Layout.addWidget(valuePreset3Cam3)
        #preset 4
        contenedorValuePreset4Cam3Layout = QHBoxLayout()
        labelValuePreset4Cam3 = QLabel("Preset 4")
        labelValuePreset4Cam3.setFixedSize(QSize(64,16))
        labelValuePreset4Cam3.setStyleSheet("border-style: none;")
        valuePreset4Cam3 = AnimatedToggle()
        valuePreset4Cam3.setFixedSize(valuePreset4Cam3.sizeHint())
        valuePreset4Cam3.setToolTip("Toggle to change preset 4")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset4Cam3 = partial(self.popUpConfiguracionPresetCam1, valuePreset4Cam3)
        disablePreset4Cam3 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset4Cam3)
        valuePreset4Cam3.stateChanged.connect(lambda x: enablePreset4Cam3() if x else disablePreset4Cam3())
        #
        #
        contenedorValuePreset4Cam3Layout.addWidget(labelValuePreset4Cam3)
        contenedorValuePreset4Cam3Layout.addWidget(valuePreset4Cam3)
        #preset 5
        contenedorValuePreset5Cam3Layout = QHBoxLayout()
        labelValuePreset5Cam3 = QLabel("Preset 5")
        labelValuePreset5Cam3.setFixedSize(QSize(64,16))
        labelValuePreset5Cam3.setStyleSheet("border-style: none;")
        valuePreset5Cam3 = AnimatedToggle()
        valuePreset5Cam3.setFixedSize(valuePreset5Cam3.sizeHint())
        valuePreset5Cam3.setToolTip("Toggle to change preset 5")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset5Cam3 = partial(self.popUpConfiguracionPresetCam1, valuePreset5Cam3)
        disablePreset5Cam3 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset5Cam3)
        valuePreset5Cam3.stateChanged.connect(lambda x: enablePreset5Cam3() if x else disablePreset5Cam3())
        #
        #
        contenedorValuePreset5Cam3Layout.addWidget(labelValuePreset5Cam3)
        contenedorValuePreset5Cam3Layout.addWidget(valuePreset5Cam3)
        #preset 6
        contenedorValuePreset6Cam3Layout = QHBoxLayout()
        labelValuePreset6Cam3 = QLabel("Preset 6")
        labelValuePreset6Cam3.setFixedSize(QSize(64,16))
        labelValuePreset6Cam3.setStyleSheet("border-style: none;")
        valuePreset6Cam3 = AnimatedToggle()
        valuePreset6Cam3.setFixedSize(valuePreset6Cam3.sizeHint())
        valuePreset6Cam3.setToolTip("Toggle to change preset 6")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset6Cam3 = partial(self.popUpConfiguracionPresetCam1, valuePreset6Cam3)
        disablePreset6Cam3 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset6Cam3)
        valuePreset6Cam3.stateChanged.connect(lambda x: enablePreset6Cam3() if x else disablePreset6Cam3())
        #
        #
        contenedorValuePreset6Cam3Layout.addWidget(labelValuePreset6Cam3)
        contenedorValuePreset6Cam3Layout.addWidget(valuePreset6Cam3)
        #preset 7
        contenedorValuePreset7Cam3Layout = QHBoxLayout()
        labelValuePreset7Cam3 = QLabel("Preset 7")
        labelValuePreset7Cam3.setFixedSize(QSize(64,16))
        labelValuePreset7Cam3.setStyleSheet("border-style: none;")
        valuePreset7Cam3 = AnimatedToggle()
        valuePreset7Cam3.setFixedSize(valuePreset7Cam3.sizeHint())
        valuePreset7Cam3.setToolTip("Toggle to change preset 7")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset7Cam3 = partial(self.popUpConfiguracionPresetCam1, valuePreset7Cam3)
        disablePreset7Cam3 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset7Cam3)
        valuePreset7Cam3.stateChanged.connect(lambda x: enablePreset7Cam3() if x else disablePreset7Cam3())
        #
        #
        contenedorValuePreset7Cam3Layout.addWidget(labelValuePreset7Cam3)
        contenedorValuePreset7Cam3Layout.addWidget(valuePreset7Cam3)
        #preset 8
        contenedorValuePreset8Cam3Layout = QHBoxLayout()
        labelValuePreset8Cam3 = QLabel("Preset 8")
        labelValuePreset8Cam3.setFixedSize(QSize(64,16))
        labelValuePreset8Cam3.setStyleSheet("border-style: none;")
        valuePreset8Cam3 = AnimatedToggle()
        valuePreset8Cam3.setFixedSize(valuePreset8Cam3.sizeHint())
        valuePreset8Cam3.setToolTip("Toggle to change preset 8")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset8Cam3 = partial(self.popUpConfiguracionPresetCam1, valuePreset8Cam3)
        disablePreset8Cam3 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset8Cam3)
        valuePreset8Cam3.stateChanged.connect(lambda x: enablePreset8Cam3() if x else disablePreset8Cam3())
        #
        #
        contenedorValuePreset8Cam3Layout.addWidget(labelValuePreset8Cam3)
        contenedorValuePreset8Cam3Layout.addWidget(valuePreset8Cam3)
        #agrego los preset en el layout vertical dentro del grupo de preset camara 3
        contenedorPresetCam3Layout = QVBoxLayout()
        contenedorPresetCam3Layout.addLayout(contenedorValuePreset1Cam3Layout)
        contenedorPresetCam3Layout.addLayout(contenedorValuePreset2Cam3Layout)
        contenedorPresetCam3Layout.addLayout(contenedorValuePreset3Cam3Layout)
        contenedorPresetCam3Layout.addLayout(contenedorValuePreset4Cam3Layout)
        contenedorPresetCam3Layout.addLayout(contenedorValuePreset5Cam3Layout)
        contenedorPresetCam3Layout.addLayout(contenedorValuePreset6Cam3Layout)
        contenedorPresetCam3Layout.addLayout(contenedorValuePreset7Cam3Layout)
        contenedorPresetCam3Layout.addLayout(contenedorValuePreset8Cam3Layout)
        contenedorGrupoPresetCam3.setLayout(contenedorPresetCam3Layout)
        ##
        textEditCam3Configuration.setBuddy(contenedorGrupoPresetCam3)
        #configuramos el layout de la camara 3 con el label y el grupo        
        layoutContenedorPresetCam3.addWidget(textEditCam3Configuration)
        layoutContenedorPresetCam3.addWidget(contenedorGrupoPresetCam3)
        contenedorPresetCam3.setLayout(layoutContenedorPresetCam3)

        tab5BotonHBox = QHBoxLayout() 
        tab5BotonHBox.setContentsMargins(5,5,5,5)
        tab5BotonHBox.addWidget(contenedorPresetCam1)
        tab5BotonHBox.addWidget(contenedorPresetCam2)
        tab5BotonHBox.addWidget(contenedorPresetCam3)
        tab5Boton.setLayout(tab5BotonHBox)
        #*******************************************
        #Asignamos nombres a cada uno de los widgets que van a ser los tabs
        #vamos a utilizar estos nombres para referenciar y poder cambiar las pestañas
        #*******************************************
        tab1Boton.setObjectName("tab1")
        tab2Boton.setObjectName("tab2")
        tab3Boton.setObjectName("tab3")
        tab4Boton.setObjectName("tab4")
        tab5Boton.setObjectName("tab5")

        #Agregamos cada Widget que definimos como tab dentro del 
        #TabWidget

        self.bodyTabWidget.addTab(tab1Boton, "Camera 1 Show")
        self.bodyTabWidget.addTab(tab2Boton, "Camera 2 Show")
        self.bodyTabWidget.addTab(tab3Boton, "Camera 3 Show")
        self.bodyTabWidget.addTab(tab4Boton, "Recorder Images Show")
        self.bodyTabWidget.addTab(tab5Boton, "Configure Camera Parameters")
        
        #Ocultamos el tabBar completo para que no se muestren los nombres
        #de los tabs sobre el objeto sino en el label que esta en el header
        
        self.bodyTabWidget.tabBar().hide()
        
        bodyLayout = QHBoxLayout()
        bodyLayout.addWidget(self.bodyTabWidget)

        #***********************************************
        #***********************************************
        #***********************************************
        self.pushButton1Cam1 = QPushButton("Camera 1")
        self.pushButton1Cam1.setDefault(True)
        self.pushButton1Cam1.clicked.connect(self.mostraPantallaCam1)
        self.pushButton1Cam1.setIcon(QIcon(os.path.join(basedir,"appIcons","camera-lens.png")))
        self.pushButton1Cam1.setToolTip("Show Image and Trending of Camera 1")

        self.pushButton2Cam2 = QPushButton("Camera 2")
        self.pushButton2Cam2.setDefault(False)
        self.pushButton2Cam2.clicked.connect(self.mostraPantallaCam2)
        self.pushButton2Cam2.setIcon(QIcon(os.path.join(basedir,"appIcons","camera-lens.png")))
        self.pushButton2Cam2.setToolTip("Show Image and Trending of Camera 2")

        self.pushButton3Cam3 = QPushButton("Camera 3")
        self.pushButton3Cam3.setDefault(False)
        self.pushButton3Cam3.clicked.connect(self.mostraPantallaCam3)
        self.pushButton3Cam3.setIcon(QIcon(os.path.join(basedir,"appIcons","camera-lens.png")))
        self.pushButton3Cam3.setToolTip("Show Image and Trending of Camera 3")

        self.pushButton4Recorder = QPushButton("Recorded")
        self.pushButton4Recorder.setDefault(False)
        self.pushButton4Recorder.clicked.connect(self.mostraPantallaRecorder)
        self.pushButton4Recorder.setIcon(QIcon(os.path.join(basedir,"appIcons","disk-return.png")))
        self.pushButton4Recorder.setToolTip("Show Image and Trending Recorded")

        self.pushButton5Config = QPushButton("ConfCam")
        self.pushButton5Config.setDefault(False)
        self.pushButton5Config.clicked.connect(self.mostraPantallaConfig)
        self.pushButton5Config.setIcon(QIcon(os.path.join(basedir,"appIcons","toolbox.png")))
        self.pushButton5Config.setToolTip("Show Configuration Parameters of Cameras")

        self.pushButtonExit = QPushButton("Exit")
        self.pushButtonExit.setIcon(QIcon(os.path.join(basedir,"appIcons", "cross-button.png")))
        self.pushButtonExit.clicked.connect(self.closeApp)
        self.pushButtonExit.setToolTip("Disconnect Cameras and Close Application")

        footerLayout = QHBoxLayout()
        footerLayout.addWidget(self.pushButton1Cam1)
        footerLayout.addWidget(self.pushButton2Cam2)
        footerLayout.addWidget(self.pushButton3Cam3)
        footerLayout.addWidget(self.pushButton4Recorder)
        footerLayout.addWidget(self.pushButton5Config)
        footerLayout.addStretch(60)
        footerLayout.addWidget(self.pushButtonExit)
        #***********************************************
        #***********************************************
        #***********************************************
        mainLayout = QVBoxLayout() 
        mainLayout.addLayout(topLayout)
        mainLayout.addLayout(bodyLayout)
        mainLayout.addLayout(footerLayout)
       
        self.setLayout(mainLayout)
 
    #***************************************************
    #***************************************************
    #update el grafico izquierda en el tiempo Eje X temporal
    def update_plot_dfTab1Izq(self):
        X=self.roiSelComboIzq.currentText()
        try:
            
            if X == 'ROI Rect1 Min':
                #cargamos el trendin de roi rect 1 minimo
                self.ydataIzq = self.ydataIzq[1:] + [float(self.valor1IndTab1MinRoi1Rect.text())]
            elif X == 'ROI Line1 Min':
                #agergo la medicion de la roi min line 1
                self.ydataIzq = self.ydataIzq[1:] + [float(self.valor11IndTab1MinRoi1Line.text())]
            elif X == 'ROI Ellip1 Min':
                #agergo la medicion de la roi min elipse 1
                self.ydataIzq = self.ydataIzq[1:] + [float(self.valor12IndTab1MinRoi1Ellipse.text())]
            elif X == 'ROI Rect1 Avg':
                #agergo la medicion de la roi avg rect 1
                self.ydataIzq = self.ydataIzq[1:] + [float(self.valor2IndTab1AvgRoi1Rect.text())]
            elif X == 'ROI Line1 Avg':
                #agergo la medicion de la roi avg line 1
                self.ydataIzq = self.ydataIzq[1:] + [float(self.valor21IndTab1AvgRoi1Line.text())]
            elif X == 'ROI Ellip1 Avg':
                #agergo la medicion de la roi avg elipse 1
                self.ydataIzq = self.ydataIzq[1:] + [float(self.valor22IndTab1AvgRoi1Ellipse.text())]
            elif X == 'ROI Rect1 Max':
                #agergo la medicion de la roi max rect 1
                self.ydataIzq = self.ydataIzq[1:] + [float(self.valor3IndTab1MaxRoi1Rect.text())]
            elif X == 'ROI Line1 Max':
                #agergo la medicion de la roi max line 1
                self.ydataIzq = self.ydataIzq[1:] + [float(self.valor31IndTab1MaxRoi1Line.text())]
            elif X == 'ROI Ellipse Max':
                #agergo la medicion de la roi max elipse 1
                self.ydataIzq = self.ydataIzq[1:] + [float(self.valor32IndTab1MaxRoi1Ellipse.text())]
            numpyImage = self.QImageToCvMat(self.image_label.pixmap())
            #print(numpyImage) #imprimo la matriz convertida de imagen para cada 100ms
            if self._plot_refIzq is None:
                plot_refs = self.dfTab1Izq.axes.plot(self.xdataIzq, self.ydataIzq, 'r')
                self._plot_refIzq = plot_refs[0]
            else:
                self._plot_refIzq.set_ydata(self.ydataIzq)
            self.dfTab1Izq.draw()
        except:
            print("no definido")
      
    #update el grafico izquierda 1 Eje X pixel        
    def update_plot_dfTab1Izq1(self):
        #self.ydataIzq1 = self.ydataIzq1[1:] + [random.randint(0,10)]
        X = self.profileSelComboIzq.currentText()
        if X == 'Profile Horizontal Rect1':
            self.xdataIzq1 = self.xdataIzq1RectHor
            self.ydataIzq1 = self.ydataIzq1RectHor
        elif X == 'Profile Vertical Rect1':
            self.xdataIzq1 = self.xdataIzq1RectVert
            self.ydataIzq1 = self.ydataIzq1RectVert
        elif X == 'Profile Horizontal Ellipse1':
            self.xdataIzq1 = self.xdataIzq1ElipHor
            self.ydataIzq1 = self.ydataIzq1ElipHor
        elif X == 'Profile Vertical Ellipse1':
            self.xdataIzq1 = self.xdataIzq1ElipVer
            self.ydataIzq1 = self.ydataIzq1ElipVer
        elif X == 'Profile Line1':
            self.xdataIzq1 = self.xdataIzq1Line
            self.ydataIzq1 = self.ydataIzq1Line

        if self._plot_refIzq1 is None:
            plot_refs = self.dfTab1Izq1.axes.plot(self.xdataIzq1, self.ydataIzq1, 'r')
            self._plot_refIzq1 = plot_refs[0]
        else:
            self._plot_refIzq1.set_xdata(self.xdataIzq1)
            self._plot_refIzq1.set_ydata(self.ydataIzq1)
        self.dfTab1Izq1.draw()

    #update el grafico
    def update_plot_dfTab1Der(self):
        self.ydata = self.ydata[1:] + [random.randint(0,10)]
        if self._plot_ref is None:
            plot_refs = self.dfTab1Der.axes.plot(self.xdata, self.ydata, 'r')
            self._plot_ref = plot_refs[0]
        else:
            self._plot_ref.set_ydata(self.ydata)
        self.dfTab1Der.draw()
    #
    def update_plot_dfTab1Der1(self):
        self.ydataDer1 = self.ydataDer1[1:] + [random.randint(0,10)]
        if self._plot_refDer1 is None:
            plot_refs = self.dfTab1Der1.axes.plot(self.xdataDer1, self.ydataDer1, 'r')
            self._plot_refDer1 = plot_refs[0]
        else:
            self._plot_refDer1.set_ydata(self.ydataDer1)
        self.dfTab1Der1.draw()
    #
    #funcion para convertir imagen en QT a imagenes en opencv
    #
    def QImageToCvMat(self, incomingImage):
        
        imagenQImage = QtGui.QImage(incomingImage)
        imagen = imagenQImage.convertToFormat(QtGui.QImage.Format.Format_RGBA8888)
        width = imagen.width()
        height = imagen.height()
        if width == 0 | height == 0:
            return 0
        ptr = imagen.bits()
        ptr.setsize(height * width * 4)
        arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 4))

        return arr
    #
    #Defino las funciones para manejar el evento de la thermal camera
    def closeEvent(self, event):
        self.thread.stop()
        event.accept()
    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)    
    #cargo la imagen en formato pixmap en el viewer
    #self.viewCam1.setPixmap(qt_img)
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)
    #***************************************************
    @pyqtSlot(np.ndarray)
    def thermal_image(self, thermal_img):
        #print(thermal_img[0][0])#aca tengo que extraer los datos de la imagen para cada ROI y guardar la informacion
        #Leer la lista de rectangulos 
        #tengo que identificar el tamaño de la Roi rectangulo con su height and width si es mayor a 1 puedo extraer esa zona de la imagen
        rect0PosX = self.scrollArea.listaRects[0].x()
        rect0PosY = self.scrollArea.listaRects[0].y()
        rect0Width = self.scrollArea.listaRects[0].width()
        rect0Height = self.scrollArea.listaRects[0].height()        
        #****
        rect1PosX = self.scrollArea.listaRects[1].x()
        rect1PosY = self.scrollArea.listaRects[1].y()
        rect1Width = self.scrollArea.listaRects[1].width()
        rect1Height = self.scrollArea.listaRects[1].height()
        #tengo que identificar el tamaño de la Roi recta con la distancia entre el punto 0 y el punto 1 es mayor a 1 puedo extraer esa zona de la imagen
        line0PosX1 = self.scrollArea.listaLineas[0].x1()
        line0PosY1 = self.scrollArea.listaLineas[0].y1()
        line0PosX2 = self.scrollArea.listaLineas[0].x2()
        line0PosY2 = self.scrollArea.listaLineas[0].y2()
        #****
        line1PosX1 = self.scrollArea.listaLineas[1].x1()
        line1PosY1 = self.scrollArea.listaLineas[1].y1()
        line1PosX2 = self.scrollArea.listaLineas[1].x2()
        line1PosY2 = self.scrollArea.listaLineas[1].y2()
        #tengo que identificar el tamaño de la Roi elipse con width y el height si es mayor a 1 puedo extraer esa zona de la imagen
        elipse0PosX = self.scrollArea.listaElipses[0].x()
        elipse0PosY = self.scrollArea.listaElipses[0].y()
        elipse0Width = self.scrollArea.listaElipses[0].width()
        elipse0Height = self.scrollArea.listaElipses[0].height()
        #****
        elipse1PosX = self.scrollArea.listaElipses[1].x()
        elipse1PosY = self.scrollArea.listaElipses[1].y()
        elipse1Width = self.scrollArea.listaElipses[1].width()
        elipse1Height = self.scrollArea.listaElipses[1].height()
        #***************************************************
        #***************************************************
        #a zero los valores de medicion rect 1
        roiRect1ImageValueMin = []
        roiRect1ImageValueMax = []
        roiRect1ImageValueAvg = []
        #print(thermal_img.shape)        
        if (rect0Height > 1) and (rect0Width >1):
            #sacamos los datos correspondientes a la primer roi y segunda roi rectangular
            roiRect1ImageValue = thermal_img[rect0PosY:rect0PosY+rect0Height, rect0PosX:rect0PosX+rect0Width] #ponemos alrevez los indices porque la imagen esta invertida
            if (roiRect1ImageValue.shape[0]>1) and (roiRect1ImageValue.shape[1]>1):
                roiRect1ImageValueMin = np.amin(roiRect1ImageValue)
                roiRect1ImageValueMax = np.amax(roiRect1ImageValue)
                roiRect1ImageValueAvg = np.mean(roiRect1ImageValue)
        self.valor1IndTab1MinRoi1Rect.setText(str(roiRect1ImageValueMin))
        self.valor2IndTab1AvgRoi1Rect.setText(str(roiRect1ImageValueAvg))
        self.valor3IndTab1MaxRoi1Rect.setText(str(roiRect1ImageValueMax))
        #guardo el perfil horizontal y el perfil vertical de la roi
        if (rect0Height > 1) and (rect0Width >1):
            widthRoiRect1ImageValue = roiRect1ImageValue.shape[0]
            heightRoiRect1ImageValue = roiRect1ImageValue.shape[1]
            indiceXRoiRect1ImageValue = widthRoiRect1ImageValue / 2
            indiceYHeightRoiRect1ImageValue = heightRoiRect1ImageValue / 2
            profileVerticalRoi1Rect = roiRect1ImageValue[int(indiceXRoiRect1ImageValue),:]
            profileHorizontalRoi1Rect = roiRect1ImageValue[:,int(indiceYHeightRoiRect1ImageValue)]
            self.xdataIzq1RectHor = list(range(widthRoiRect1ImageValue))
            self.ydataIzq1RectHor = profileHorizontalRoi1Rect
            self.xdataIzq1RectVert = list(range(heightRoiRect1ImageValue))
            self.ydataIzq1RectVert = profileVerticalRoi1Rect  
        
        #a zero los valores de medicion rect 2
        roiRect2ImageValueMin = []
        roiRect2ImageValueMax = []
        roiRect2ImageValueAvg = []       
        if (rect1Height > 1) and (rect1Width > 1):
            roiRect2ImageValue = thermal_img[rect1PosY:rect1PosY+rect1Height,rect1PosX:rect1PosX+rect1Width]
            if (roiRect2ImageValue.shape[0]>1) and (roiRect2ImageValue.shape[1]):
                roiRect2ImageValueMin = np.amin(roiRect2ImageValue)
                roiRect2ImageValueMax = np.amax(roiRect2ImageValue)
                roiRect2ImageValueAvg = np.mean(roiRect2ImageValue)
        self.valor4IndTab1MinRoi2Rect.setText(str(roiRect2ImageValueMin))
        self.valor5IndTab1AvgRoi2Rect.setText(str(roiRect2ImageValueAvg))
        self.valor6IndTab1MaxRoi2Rect.setText(str(roiRect2ImageValueMax))        
        #guardo el perfil horizontal y el perfil vertical de la roi
        if (rect1Height > 1) and (rect1Width > 1):
            widthRoiRect2ImageValue = roiRect2ImageValue.shape[0]
            heightRoiRect2ImageValue = roiRect2ImageValue.shape[1]
            indiceXRoiRect2ImageValue = widthRoiRect2ImageValue / 2
            indiceYHeightRoiRect2ImageValue = heightRoiRect2ImageValue / 2
            profileVerticalRoi2Rect = roiRect2ImageValue[int(indiceXRoiRect2ImageValue),:]
            profileHorizontalRoi2Rect = roiRect2ImageValue[:,int(indiceYHeightRoiRect2ImageValue)]
            self.xdataDer1RectHor = list(range(widthRoiRect2ImageValue))
            self.ydataDer1RectHor = profileHorizontalRoi2Rect
            self.xdataDer1RectVert = list(range(heightRoiRect2ImageValue))
            self.ydataDer1RectVert = profileVerticalRoi2Rect 
        
        #sacamos los datos correspondientres a la primer roi y segunda roi linea
        largoLinea0 = line0PosY2 - line0PosY1 #cantidad de elementos
        anchoLinea0 = line0PosX2 - line0PosX1
        roiLine0ImageValueMin = []
        roiLine0ImageValueMax = []
        roiLine0ImageValueAvg = []
        if (largoLinea0 > 1) and (anchoLinea0 > 1):
            valoresLinea0 =[]
            for tupla in zip(range(line0PosY1,line0PosY2),range(line0PosX1,line0PosX2)):
                valor = thermal_img[tupla[0],tupla[1]]
                valoresLinea0.append(valor)
            if len(valoresLinea0) > 0:
                roiLine0ImageValueMin = np.amin(valoresLinea0)
                roiLine0ImageValueMax = np.amax(valoresLinea0)
                roiLine0ImageValueAvg = np.mean(valoresLinea0)
        self.valor11IndTab1MinRoi1Line.setText(str(roiLine0ImageValueMin))
        self.valor21IndTab1AvgRoi1Line.setText(str(roiLine0ImageValueAvg))
        self.valor31IndTab1MaxRoi1Line.setText(str(roiLine0ImageValueMax))
        #
        if (largoLinea0 > 1) and (anchoLinea0 > 1):
            widthLine0 = len(valoresLinea0)
            self.xdataIzq1Line = list(range(widthLine0))
            self.ydataIzq1Line = valoresLinea0
        #
        largoLinea1 = line1PosY2 - line1PosY1 #cantidad de elementos
        anchoLinea1 = line1PosX2 - line1PosX1
        roiLine1ImageValueMin = []
        roiLine1ImageValueMax = []
        roiLine1ImageValueAvg = []
        if (largoLinea1 > 1) and (anchoLinea1 > 1):
            valoresLinea1 =[]
            for tupla in zip(range(line1PosY1,line1PosY2),range(line1PosX1,line1PosX2)):
                valor = thermal_img[tupla[0],tupla[1]]
                valoresLinea1.append(valor)
            if len(valoresLinea1) > 0:
                roiLine1ImageValueMin = np.amin(valoresLinea1)
                roiLine1ImageValueMax = np.amax(valoresLinea1)
                roiLine1ImageValueAvg = np.mean(valoresLinea1)
        self.valor41IndTab1MinRoi2Line.setText(str(roiLine1ImageValueMin))
        self.valor51IndTab1AvgRoi2Line.setText(str(roiLine1ImageValueAvg))
        self.valor61IndTab1MaxRoi2Line.setText(str(roiLine1ImageValueMax))
        #
        if (largoLinea1 > 1) and (anchoLinea1 > 1):
            widthLine1 = len(valoresLinea1)
            self.xdataDer1Line = list(range(widthLine1))
            self.ydataDer1Line = valoresLinea1
        #
        #sacamos los datos correspondientres a la primer roi y segunda roi elipse
        #primero creamos una elipse con los datos de x0,y0 -- width,height
        #elipse 0
        valoresThermalElipse0Min = []
        valoresThermalElipse0Max = []
        valoresThermalElipse0Avg = []
        if (int(elipse0Height) > 1) and (int(elipse0Width) > 1):
            x0 = elipse0PosX
            y0 = elipse0PosY
            a = elipse0Width
            b = elipse0Height
            #resolucion
            nx = thermal_img.shape[1]
            ny = thermal_img.shape[0]
            #configuro sistema de coordenadas
            x = np.linspace(0, nx, nx)
            y = np.linspace(0, ny, ny)
            #configuro array 
            xgrid, ygrid = np.meshgrid(x, y)
            #calculo la elipse
            ellipseMascara = (xgrid-x0)**2 / a**2 + (ygrid-y0)**2 / b**2
            #creo un array con ceros
            zerosMatriz = np.zeros((ny,nx), dtype=np.int32)
            #pongo 1 donde la elipse es menor que 1
            #zerosMatriz[ellipseMascara < 1.0] = 1
            #busco en la matriz termografica
            valoresThermalElipse0 = thermal_img[ellipseMascara < 1.0]
            if valoresThermalElipse0.shape[0]>0:
                valoresThermalElipse0Min = np.amax(valoresThermalElipse0)
                valoresThermalElipse0Max = np.amin(valoresThermalElipse0)
                valoresThermalElipse0Avg = np.mean(valoresThermalElipse0)
        self.valor12IndTab1MinRoi1Ellipse.setText(str(valoresThermalElipse0Min))
        self.valor22IndTab1AvgRoi1Ellipse.setText(str(valoresThermalElipse0Avg))
        self.valor32IndTab1MaxRoi1Ellipse.setText(str(valoresThermalElipse0Max))
        #guardo el perfil horizontal y el perfil vertical de la roi
        #calculamos los perfiles horizontal y vertical
        if (int(elipse0Height) > 1) and (int(elipse0Width) > 1):
            valoresThermalElipse0Vertical = thermal_img[int(elipse0PosY):int(elipse0PosY+elipse0Height),int(elipse0PosX+elipse0Width/2)]
            valoresThermalElipse0Horizontal = thermal_img[int(elipse0PosY+elipse0Height/2),int(elipse0PosX):int(elipse0PosX+elipse0Width)]
            self.xdataIzq1ElipHor = list(range(len(valoresThermalElipse0Horizontal)))
            self.ydataIzq1ElipHor = valoresThermalElipse0Horizontal
            self.xdataIzq1ElipVer = list(range(len(valoresThermalElipse0Vertical)))
            self.ydataIzq1ElipVer = valoresThermalElipse0Vertical 
             
        #
        #sacmos los datos correspondientes a la elipse 1
        #elipse 1
        valoresThermalElipse1Min = []
        valoresThermalElipse1Max = []
        valoresThermalElipse1Avg = []
        if (elipse1Height > 1) and (elipse1Width > 1):
            x01 = elipse1PosX
            y01 = elipse1PosY
            a1 = elipse1Width
            b1 = elipse1Height
            #resolucion
            nx1 = thermal_img.shape[1]
            ny1 = thermal_img.shape[0]
            #configuro sistema de coordenadas
            x1 = np.linspace(0, nx1, nx1)
            y1 = np.linspace(0, ny1, ny1)
            #configuro array 
            xgrid1, ygrid1 = np.meshgrid(x1, y1)
            #calculo la elipse
            ellipseMascara1 = (xgrid1-x01)**2 / a1**2 + (ygrid1-y01)**2 / b1**2
            #creo un array con ceros
            zerosMatriz1 = np.zeros((nx1,ny1), dtype=np.int32)
            #pongo 1 donde la elipse es menor que 1
            #zerosMatriz1[ellipseMascara1 < 1.0] = 1
            #busco en la matriz termografica
            valoresThermalElipse1 = thermal_img[ellipseMascara1 < 1.0]
            if valoresThermalElipse1.shape[0]>0:
                valoresThermalElipse1Min = np.amin(valoresThermalElipse1)
                valoresThermalElipse1Max = np.amax(valoresThermalElipse1)
                valoresThermalElipse1Avg = np.mean(valoresThermalElipse1)
        self.valor42IndTab1MinRoi2Ellipse.setText(str(valoresThermalElipse1Min))
        self.valor52IndTab1AvgRoi2Ellipse.setText(str(valoresThermalElipse1Avg))
        self.valor62IndTab1MaxRoi2Ellipse.setText(str(valoresThermalElipse1Max))
        #guardo el perfil horizontal y el perfil vertical de la roi
        #calculamos los perfiles horizontal y vertical
        if (elipse1Height > 1) and (elipse1Width > 1):
            valoresThermalElipse1Vertical = thermal_img[int(elipse1PosY):int(elipse1PosY+elipse1Height),int(elipse1PosX+elipse1Width/2)]
            valoresThermalElipse1Horizontal = thermal_img[int(elipse1PosY+elipse1Height/2),int(elipse1PosX):int(elipse1PosX+elipse1Width)]
            self.xdataDer1ElipHor = list(range(len(valoresThermalElipse1Horizontal)))
            self.ydataDer1ElipHor = valoresThermalElipse1Horizontal
            self.xdataDer1ElipVer = list(range(len(valoresThermalElipse1Vertical)))
            self.ydataDer1ElipVer = valoresThermalElipse1Vertical 
        #
        
        ##
        ###Tenemos los datos listos para pasar y realizar los calculos necesarios
        ##

    #defino la funcion asociada con el cambio de preset en el tab1
    def popUpSetBotonTab1(self, checkbox):
        print("ajustamos preset 1 tab1")
        if checkbox.isChecked() == True: 
            self.dlgChangePresetTab1 = PopUpWritePresetTab()
            self.dlgChangePresetTab1.show()
    def popUpResetBotonTab1(self, checkbox):
        print("reset preset 1 tab1")
        if checkbox.isChecked() == False:
            self.dlgDefaultPresetTab1 = PopUpResetPresetTab()
            self.dlgDefaultPresetTab1.show()
    #defino la funcion asociada con el cambio de preset de la camara 1
    def popUpConfiguracionPresetCam1(self, checkbox):
        print("cambiar preset seleccionado en camara 1")
        #print(checkbox)
        ##
        #Tenemos que agregar la popup W
        if checkbox.isChecked() == True:
            self.dlgChangePresetCam1 = PopUPWritePresetCam()
            self.dlgChangePresetCam1.show()
    def popUpRestartConfiguracionPresetCam1(self, checkbox):
        print("reset preset seleccion en camara 1")
        if checkbox.isChecked() == False:
            self.dlgDefaultPresetCam1 = PopUpResetPresetCam()
            self.dlgDefaultPresetCam1.show()
    #defino la funcion asociada con el cambio de preset de la camara 2
    def popUpConfiguracionPresetCam2(self, checkbox):
        print("cambiar preset seleccionado en camara 2")
        ##
        #Tenemos que agregar la popup
        if checkbox.isChecked() == True:
            self.dlgChangePresetCam2 = PopUPWritePresetCam()
            self.dlgChangePresetCam2.show()
    def popUpRestartConfiguracionPresetCam2(self, checkbox):
        print("reset preset seleccion en camara 2")
        if checkbox.isChecked() == False:
            self.dlgDefaultPresetCam2 = PopUpResetPresetCam()
            self.dlgDefaultPresetCam2.show()
    #defino la funcion asociada con el cambio de preset de la camara 2
    def popUpConfiguracionPresetCam3(self, checkbox):
        print("cambiar preset seleccionado en camara 3")
        ##
        #Tenemos que agregar la popup
        if checkbox.isChecked() == True:
            self.dlgChangePresetCam3 = PopUPWritePresetCam()
            self.dlgChangePresetCam3.show()
    #defino la funcion asociada la cargar el defaul de preset
    def popUpRestartConfiguracionPresetCam3(self, checkbox):
        print("reset preset seleccion en camara 3")
        if checkbox.isChecked() == False:
            self.dlgDefaultPresetCam3 = PopUpResetPresetCam()
            self.dlgDefaultPresetCam3.show()
    #Defino la funcion para realizar zoom in
    def makeZoomIn(self, statusButton):
        print("Zoom In to the image", statusButton)
        #logica para hacer zoomIN
        self.scrollArea.toolROIs = 3 #ningun herramienta roi
        self.scrollArea.zoomInButton = True
        self.scrollArea.zoomOutButton = False
        target = self.sender() # identificamos quien esta llamando a la funcion
        data = target.nombreBoton
        if statusButton:#verificamos que se este presionando el boton, e identificamos de que widget estoy llamando
            if data == "zoomInTab1":#determinamos quien llama a la funcion
                self.buttonRectRoiActionImageTab1.setChecked(False)
                self.buttonLineRoiActionImageTab1.setChecked(False)
                self.buttonEllipRoiActionImageTab1.setChecked(False)
                self.buttonZoomOutActionImageTab1.setChecked(False)
            elif data == "zoomInTab2":
                self.buttonRectRoiActionImageTab2.setChecked(False)
                self.buttonLineRoiActionImageTab2.setChecked(False)
                self.buttonEllipRoiActionImageTab2.setChecked(False)
                self.buttonZoomOutActionImageTab2.setChecked(False)
            elif data == "zoomInTab3":
                self.buttonRectRoiActionImageTab3.setChecked(False)
                self.buttonLineRoiActionImageTab3.setChecked(False)
                self.buttonEllipRoiActionImageTab3.setChecked(False)
                self.buttonZoomOutActionImageTab3.setChecked(False)
            elif data == "zoomInTabHistoryIzq":
                self.buttonRectRoiActionHistoryIzq.setChecked(False)
                self.buttonLineRoiActionHistoryIzq.setChecked(False)
                self.buttonEllipRoiActionHistoryIzq.setChecked(False)
                self.buttonZoomOutActionHistoryIzq.setChecked(False)
            elif data == "zoomInTabHistoryDer":
                self.buttonRectRoiActionHistoryDer.setChecked(False)
                self.buttonLineRoiActionHistoryDer.setChecked(False)
                self.buttonEllipRoiActionHistoryDer.setChecked(False)
                self.buttonZoomOutActionHistoryDer.setChecked(False)
    #Defino la funcion para realizar zoom out
    def makeZoomOut(self, statusButton):
        print("Zoom Out to the image", statusButton)
        #logica para hacer zoomOut
        self.scrollArea.toolROIs = 3 #ningun herramienta roi
        self.scrollArea.zoomInButton = False
        self.scrollArea.zoomOutButton = True
        target = self.sender()
        data = target.nombreBoton
        if statusButton:#determino si se activa el boton
            if data == "zoomOutTab1":#determino quien llama a la funcion
                self.buttonRectRoiActionImageTab1.setChecked(False)
                self.buttonLineRoiActionImageTab1.setChecked(False)
                self.buttonEllipRoiActionImageTab1.setChecked(False)
                self.buttonZoomInActionImageTab1.setChecked(False)
            elif data == "zoomOutTab2":
                self.buttonRectRoiActionImageTab2.setChecked(False)
                self.buttonLineRoiActionImageTab2.setChecked(False)
                self.buttonEllipRoiActionImageTab2.setChecked(False)
                self.buttonZoomInActionImageTab2.setChecked(False)
            elif data == "zoomOutTab3":
                self.buttonRectRoiActionImageTab3.setChecked(False)
                self.buttonLineRoiActionImageTab3.setChecked(False)
                self.buttonEllipRoiActionImageTab3.setChecked(False)
                self.buttonZoomInActionImageTab3.setChecked(False)
            elif data == "zoomOutTabHistoryIzq":
                self.buttonRectRoiActionHistoryIzq.setChecked(False)
                self.buttonLineRoiActionHistoryIzq.setChecked(False)
                self.buttonEllipRoiActionHistoryIzq.setChecked(False)
                self.buttonZoomInActionHistoryIzq.setChecked(False)
            elif data == "zoomOutTabHistoryDer":
                self.buttonRectRoiActionHistoryDer.setChecked(False)
                self.buttonLineRoiActionHistoryDer.setChecked(False)
                self.buttonEllipRoiActionHistoryDer.setChecked(False)
                self.buttonZoomInActionHistoryIzq.setChecked(False)
    #Defino la funcion para dibujar roi rectangulos
    def drawROIRectangle(self, statusButton):
        print("Dibujar Roi Rectangulo", statusButton)
        #logica para dibujar un rectangulo
        self.scrollArea.toolROIs = 0
        self.scrollArea.zoomInButton = False
        self.scrollArea.zoomOutButton = False
        target = self.sender()
        data = target.nombreBoton
        if statusButton:#si se activa el boton 
            if data == "roiRectanguloTab1":#determino quien llama a la funcion
                self.buttonLineRoiActionImageTab1.setChecked(False)
                self.buttonEllipRoiActionImageTab1.setChecked(False)
                self.buttonZoomInActionImageTab1.setChecked(False)
                self.buttonZoomOutActionImageTab1.setChecked(False)
            elif data == "roiRectanguloTab2":
                self.buttonLineRoiActionImageTab2.setChecked(False)
                self.buttonEllipRoiActionImageTab2.setChecked(False)
                self.buttonZoomInActionImageTab2.setChecked(False)
                self.buttonZoomOutActionImageTab2.setChecked(False)
            elif data == "roiRectanguloTab3":
                self.buttonLineRoiActionImageTab3.setChecked(False)
                self.buttonEllipRoiActionImageTab3.setChecked(False)
                self.buttonZoomInActionImageTab3.setChecked(False)
                self.buttonZoomOutActionImageTab3.setChecked(False)                
            elif data == "roiRectanguloTabHistoryIzq":
                self.buttonLineRoiActionHistoryIzq.setChecked(False)
                self.buttonEllipRoiActionHistoryIzq.setChecked(False)
                self.buttonZoomInActionHistoryIzq.setChecked(False)
                self.buttonZoomOutActionHistoryIzq.setChecked(False)
            elif data == "roiRectanguloTabHistoryDer":
                self.buttonLineRoiActionHistoryDer.setChecked(False)
                self.buttonEllipRoiActionHistoryDer.setChecked(False)
                self.buttonZoomInActionHistoryDer.setChecked(False)
                self.buttonZoomOutActionHistoryDer.setChecked(False) 
    #Defino la funcion para dibujar roi ellipses
    def drawROICircle(self, statusButton):
        print("Dibujar Roi Ellipse", statusButton)
        #logica para dibujar un circulo
        self.scrollArea.toolROIs = 2
        self.scrollArea.zoomInButton = False
        self.scrollArea.zoomOutButton = False
        target = self.sender()
        data = target.nombreBoton
        if statusButton:#si se activa el boton desactivo el resto
            if data == "roiEllipseTab1":#determino quien llama a la funcion
                self.buttonRectRoiActionImageTab1.setChecked(False)
                self.buttonLineRoiActionImageTab1.setChecked(False)
                self.buttonZoomInActionImageTab1.setChecked(False)
                self.buttonZoomOutActionImageTab1.setChecked(False)
            elif data == "roiEllipseTab2":
                self.buttonRectRoiActionImageTab2.setChecked(False)
                self.buttonLineRoiActionImageTab2.setChecked(False)
                self.buttonZoomInActionImageTab2.setChecked(False)
                self.buttonZoomOutActionImageTab2.setChecked(False)
            elif data == "roiEllipseTab3":
                self.buttonRectRoiActionImageTab3.setChecked(False)
                self.buttonLineRoiActionImageTab3.setChecked(False)
                self.buttonZoomInActionImageTab3.setChecked(False)
                self.buttonZoomOutActionImageTab3.setChecked(False)
            elif data == "roiEllipseTabHistoryIzq":
                self.buttonRectRoiActionHistoryIzq.setChecked(False)
                self.buttonLineRoiActionHistoryIzq.setChecked(False)
                self.buttonZoomInActionHistoryIzq.setChecked(False)
                self.buttonZoomOutActionHistoryIzq.setChecked(False)
            elif data == "roiEllipseTabHistoryDer":
                self.buttonRectRoiActionHistoryDer.setChecked(False)
                self.buttonLineRoiActionHistoryDer.setChecked(False)
                self.buttonZoomInActionHistoryDer.setChecked(False)
                self.buttonZoomOutActionHistoryDer.setChecked(False)
    #Defino la funcion para dibujar roi rectas
    def drawROILine(self, statusButton):
        print("Dibujar Roi Linea", statusButton)
        #logica para dibujar una linea
        self.scrollArea.toolROIs = 1
        self.scrollArea.zoomInButton = False
        self.scrollArea.zoomOutButton = False
        target = self.sender()
        data = target.nombreBoton
        if statusButton:#Si se activa el boton desactivo los otros
            if data == "roiLineTab1":#determino quien llama a la funcion
                self.buttonRectRoiActionImageTab1.setChecked(False)
                self.buttonEllipRoiActionImageTab1.setChecked(False)
                self.buttonZoomInActionImageTab1.setChecked(False)
                self.buttonZoomOutActionImageTab1.setChecked(False)
            elif data == "roiLineTab2":
                self.buttonRectRoiActionImageTab2.setChecked(False)
                self.buttonEllipRoiActionImageTab2.setChecked(False)
                self.buttonZoomInActionImageTab2.setChecked(False)
                self.buttonZoomOutActionImageTab2.setChecked(False)
            elif data == "roiLineTab3":
                self.buttonRectRoiActionImageTab3.setChecked(False)
                self.buttonEllipRoiActionImageTab3.setChecked(False)
                self.buttonZoomInActionImageTab3.setChecked(False)
                self.buttonZoomOutActionImageTab3.setChecked(False)
            elif data == "roiLineTabHistoryIzq":
                self.buttonRectRoiActionHistoryIzq.setChecked(False)
                self.buttonEllipRoiActionHistoryIzq.setChecked(False)
                self.buttonZoomInActionHistoryIzq.setChecked(False)
                self.buttonZoomOutActionHistoryIzq.setChecked(False)
            elif data == "roiLineTabHistoryDer":
                self.buttonRectRoiActionHistoryDer.setChecked(False)
                self.buttonEllipRoiActionHistoryDer.setChecked(False)
                self.buttonZoomInActionHistoryDer.setChecked(False)
                self.buttonZoomOutActionHistoryDer.setChecked(False)

    #Defino la funcion asociada a la barra de progreso para la camara 1
    def handleTimer1(self):
        value = self.pbarTab1.value()
        if value < 100:
            value = value + 1
            self.pbarTab1.setValue(value)
        else:
            self.timerPbar1.stop()
    #defino la funcion asociada a la barra de progreso para la camara 2
    def handleTimer2(self):
        value = self.pbarTab2.value()
        if value < 100:
            value = value + 1
            self.pbarTab2.setValue(value)
        else:
            self.timerPbar2.stop()
    #defino la funcion asociada a la barra de progreso para la camara 3
    def handleTimer3(self):
        value = self.pbarTab3.value()
        if value < 100:
            value = value + 1
            self.pbarTab3.setValue(value)
        else:
            self.timerPbar3.stop()
    #Defino la funcion asociada a la seleccion de ROI Izquierda Tab1
    def populateRoiCombo1(self):
        if not self.roiSelComboIzq.count():
            self.roiSelComboIzq.addItems(['ROI Rect1 Max', 'ROI Rect1 Min','ROI Rect1 Avg', 'ROI Line1 Max', 'ROI Line1 Min', 'ROI Line1 Avg', 'ROI Ellipse Max', 'ROI Ellip1 Min', 'ROI Ellip1 Avg'])
        #agergamos los iconos para cada herramienta de medicion
        self.roiSelComboIzq.setItemIcon(0, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roiSelComboIzq.setItemIcon(1, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roiSelComboIzq.setItemIcon(2, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roiSelComboIzq.setItemIcon(3, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roiSelComboIzq.setItemIcon(4, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roiSelComboIzq.setItemIcon(5, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roiSelComboIzq.setItemIcon(6, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roiSelComboIzq.setItemIcon(7, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roiSelComboIzq.setItemIcon(8, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
    def profileRoiCombo1(self):
        if not self.profileSelComboIzq.count():
            self.profileSelComboIzq.addItems(['Profile Horizontal Rect1', 'Profile Vertical Rect1', 'Profile Horizontal Ellipse1', 'Profile Vertical Ellipse1', 'Profile Line1'])
        self.profileSelComboIzq.setItemIcon(0, QIcon(os.path.join(basedir, "appIcons", "ruler-triangle.png")))
        self.profileSelComboIzq.setItemIcon(1, QIcon(os.path.join(basedir, "appIcons", "ruler-triangle.png")))
        self.profileSelComboIzq.setItemIcon(2, QIcon(os.path.join(basedir, "appIcons", "ruler-triangle.png")))
        self.profileSelComboIzq.setItemIcon(3, QIcon(os.path.join(basedir, "appIcons", "ruler-triangle.png")))
        self.profileSelComboIzq.setItemIcon(4, QIcon(os.path.join(basedir, "appIcons", "ruler-triangle.png")))
    #Defino la funcion asociada a la seleccion de ROI Derecha Tab1
    def populateRoiCombo2(self):
        if not self.roiSelComboDer.count():
            self.roiSelComboDer.addItems(['ROI Rect1 H', 'ROI Rect1 V','ROI Line1', 'ROI Ellip1 H', 'ROI Ellip1 V'])
        #agergamos los iconos para cada herramienta de medicion
        self.roiSelComboDer.setItemIcon(0, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roiSelComboDer.setItemIcon(1, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roiSelComboDer.setItemIcon(2, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roiSelComboDer.setItemIcon(3, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roiSelComboDer.setItemIcon(4, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
    
    #Defino la funcion asociada a la seleccion de camaras 1
    def populateCamCombo1(self):
        
        if not self.camCombo1.count():
            self.camCombo1.addItems(['cam1', 'cam2', 'cam3'])
        #agregamos los iconos para cada camara
        self.camCombo1.setItemIcon(0, QIcon(os.path.join(basedir, "appIcons", "camera-lens.png")))
        self.camCombo1.setItemIcon(1, QIcon(os.path.join(basedir, "appIcons", "camera-lens.png")))
        self.camCombo1.setItemIcon(2, QIcon(os.path.join(basedir, "appIcons", "camera-lens.png")))
    #Defino la funcion asociada a la seleccion de camaras 2
    def populateCamCombo2(self):
        
        if not self.camCombo2.count():
            self.camCombo2.addItems(['cam1', 'cam2', 'cam3'])
        #agregamos los iconos para cada camara
        self.camCombo2.setItemIcon(0, QIcon(os.path.join(basedir, "appIcons", "camera-lens.png")))
        self.camCombo2.setItemIcon(1, QIcon(os.path.join(basedir, "appIcons", "camera-lens.png")))
        self.camCombo2.setItemIcon(2, QIcon(os.path.join(basedir, "appIcons", "camera-lens.png")))
    #Defino la función asociada a logear un usuario
    def populateUserCombo(self):
        #si la cantidad de usuario esta vacia la lleno
        if not self.userCombo.count():
            self.userCombo.addItems('Iñaki Lucho Polaco'.split()) #Aca podría consultar los usuarios 
                                                                  #a la base de datos
        #Agrego los iconos a cada usuario en la lista del combobox
        self.userCombo.setItemIcon(0,QIcon(os.path.join(basedir,"appIcons","user-worker-boss.png")))
        self.userCombo.setItemIcon(1,QIcon(os.path.join(basedir,"appIcons","user-worker-boss.png")))
        self.userCombo.setItemIcon(2,QIcon(os.path.join(basedir,"appIcons","user-worker-boss.png")))
        #abrimos la pop up para notificar que se va a cambiar de usuario
        dlgLoggin = QMessageBox(self)
        dlgLoggin.setWindowTitle("User Loggin")
        dlgLoggin.setText("Do you want to change user?")
        dlgLoggin.setStandardButtons(QMessageBox.Yes | QMessageBox.No )
        dlgLoggin.setIcon(QMessageBox.Question)
        buttonSelected = dlgLoggin.exec()
        if buttonSelected == QMessageBox.Yes:
            print("test")
            #Se seleeciono realizar el loggin del usuario nuevo 
            #Se va a abrir la ventana para realizar la carga de usuario y password
            self.dlgRequestUser = PopUpLoggin()
            self.dlgRequestUser.show()
    def popUpSearchDateToHistory(self):
        self.dlgDateSearch = PopUpDateSelected()
        self.dlgDateSearch.show()
    #Defino la funcion asociada a cerrar la aplicación
    def closeApp(self):
        #self._run_flag = False
        self.close()    #Cuando hacemos un click cerramos la aplicacion
    #Defino la función asociado al botón para cambiar de pantalla Cam1
    def mostraPantallaCam1(self):
        page=self.bodyTabWidget.findChild(QWidget, 'tab1')
        index = self.bodyTabWidget.indexOf(page)
        #print(index)
        self.bodyTabWidget.setCurrentWidget(self.bodyTabWidget.findChild(QWidget,'tab1'))
        self.labelFunctionalWindowSelected.setText("Functional Window Cam 1")        
    #Defino la función asociado al botón para cambiar de pantalla Cam2
    def mostraPantallaCam2(self):
        page=self.bodyTabWidget.findChild(QWidget, 'tab2')
        index = self.bodyTabWidget.indexOf(page)
        #print(index)
        self.bodyTabWidget.setCurrentWidget(self.bodyTabWidget.findChild(QWidget,'tab2'))
        self.labelFunctionalWindowSelected.setText("Functional Window Cam 2")
    #Defino la función asociado al botón para cambiar de pantalla Cam3
    def mostraPantallaCam3(self):
        page=self.bodyTabWidget.findChild(QWidget, 'tab3')
        index = self.bodyTabWidget.indexOf(page)
        #print(index)
        self.bodyTabWidget.setCurrentWidget(self.bodyTabWidget.findChild(QWidget,'tab3'))
        self.labelFunctionalWindowSelected.setText("Functional Window Cam 3")
    #Defino la función asociado al botón para cambiar a pantalla Recorder
    def mostraPantallaRecorder(self):
        page=self.bodyTabWidget.findChild(QWidget, 'tab4')
        index = self.bodyTabWidget.indexOf(page)
        #print(index)
        self.bodyTabWidget.setCurrentWidget(self.bodyTabWidget.findChild(QWidget,'tab4'))
        self.labelFunctionalWindowSelected.setText("Functional Window Recorded")
    #Defino la función asociada al botón para cambiar a pantalla Configuración
    def mostraPantallaConfig(self):
        page=self.bodyTabWidget.findChild(QWidget, 'tab5')
        index = self.bodyTabWidget.indexOf(page)
        #print(index)
        self.bodyTabWidget.setCurrentWidget(self.bodyTabWidget.findChild(QWidget,'tab5'))
        self.labelFunctionalWindowSelected.setText("Functional Window Config Cameras")
    #***************************************************
    #***************************************************
if __name__ == '__main__':      
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(basedir,"appIcons","tgsLogo3.ico")))
    main = MainWindow()
    main.show()
    app.exec()