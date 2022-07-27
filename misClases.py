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

import datetime


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
            """
            #calculo resolucion imagen
            self.parent().parent().escalaImagen['ancho'] = self.size().width()
            self.parent().parent().escalaImagen['alto'] = self.size().height()
            """
            #mostramos la lista de cada uno de los rois
            #print(self.parent().parent().listaRects)
            #print(self.parent().parent().listaLineas)
            #print(self.parent().parent().listaElipses)
        else:
            print("tenemos un error en la adquisicion no agregamos los objetos en la imagen")
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
    status_camera_signal = pyqtSignal(np.ndarray)
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
        statusCamera = [True, "conexion ok"] #notifico por defecto que la conexion con la camara esta ok si falla el ret cambio el estado
        if ret != 0:                                                    #conectar con camara usb de optris
                print("error at init")
                statusCamera = [False, "conexion falla"]
                self.status_camera_signal.emit(np.array(statusCamera))
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
                        statusCamera = [False, "fallo la conexion"] #fallo la conexion                        
                        continue
                self.status_camera_signal.emit(np.array(statusCamera))                                  #si hay error salgo y retorno el error
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
#Clase para procesamiento de datos
class ProcesamientoDatosThread(QThread):
    #definimos el canal de comunicaciones
    change_datos_signal = pyqtSignal(np.ndarray)
    #sobre escribimos la clase y definimos el flag de stop del hilo
    def __init__(self):
        super().__init__()
        self._run_flag_procesamiento = True #utilizamos este flag para indicar al hilo que termine la adquisicion
    #sobre escribimos la clase para cuando esta en run el hilo
    def run(self):
        while self._run_flag_procesamiento == True:
            datoEmitido = np.array(["este", "es","el", "dato"])
            #cada 100ms actualizo el envio de datos si se apreto la letra q cambio el texto            
            if cv2.waitKey(1000)&0xFF == ord('q'):
                #realizo el procesamiento de datos por el hilo de procesamiento!")
                datoEmitido = np.array(["este", "es","el", "editado"])
            self.change_datos_signal.emit()
    #sobre escribimos la clase para cuando esta en stop el hilo
    def stop(self):
        self._run_flag_procesamiento = False #cambio el estado del flag
        self.wait()
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
    def __init__(self, valorPreset):
        super().__init__()
        self.valorPresetMedicion = valorPreset
        self.setWindowTitle("Reset Preset of Control")
        #aca va la funcionalidad del graficador con el control
        layoutPresetCurrentResetTab = QVBoxLayout()
        #valor de preset actual
        self.labelCurrentPresetTab = QLabel("Current Control Tab")
        valorPresetActual = self.valorPresetMedicion.text()
        self.valueCurrentPresetTab = QLineEdit(valorPresetActual)
        self.valueCurrentPresetTab.setStyleSheet("border: 2px solid black; background-color : lightgray;")        
        self.labelCurrentPresetTab.setBuddy(self.valueCurrentPresetTab)
        #valor de preset a cambiar
        self.labelDefaultPresetTab = QLabel("Default Control Tab")
        self.valueDefaultPresetTab = QLineEdit("24") #este valor lo tengo que leer del archivo de configuracion de presets.
        self.valueDefaultPresetTab.setStyleSheet("border: 2px solid black;background-color:lightgreen;") #el archivo lo tenemos que crear
        self.labelDefaultPresetTab.setBuddy(self.valueDefaultPresetTab) #cada vez que se cierre la aplicacion guarda el archivo con los preset actuales
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
        #cargo en el preset el valor por default 
        #vamos a reemplazar esta parte por la lectura del 
        #archivo de configuracion
        self.valorPresetMedicion.setText("24")
    def cancelUpDatePresetTab(self):
        print("Cancelar default value al control")
        self.close()
#Clase modelo generico de preset control 
class PopUpWritePresetTab(QWidget):
    def __init__(self, valorIndicador, valorPreset):
        super().__init__()
        self.valorIndicadorMedicion = valorIndicador
        self.valorPresetMedicion = valorPreset        
        self.setWindowTitle("Write Preset of Control")
        layoutPresetCurrentNew = QVBoxLayout()
        #grafico powerbar
        self.volumenCtrl = PowerBar(["#5e4fa2","#3288bd","#66c2a5","#abdda4","#e6f598"])
        #
        layoutPresetCurrentNew.addWidget(self.volumenCtrl)
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
        #verifico si el valor es menor al preset si lo es cambiar el color de fondo
        print(self.volumenCtrl.valorQDial.text())
        #cargo el valor en el preset de alarma de medicion
        self.valorPresetMedicion.setText(self.volumenCtrl.valorQDial.text())
        #if float(self.valorIndicadorMedicion.text()) > int(self.volumenCtrl.valorQDial.text()):
        #    self.valorIndicadorMedicion.setStyleSheet("border: 2px solid black;border-radius: 4px;padding: 2px; text-align:center; background-color: red;")            
        #else:
        #    self.valorIndicadorMedicion.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
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
