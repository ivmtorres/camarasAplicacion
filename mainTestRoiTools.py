from functools import partial
import gzip
from threading import Thread, Barrier
#from time import sleep, time
from PyQt5 import QtGui, QtCore,QtWidgets
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QPen, QPalette, QFont, QDoubleValidator, QPainterPath
from PyQt5.QtCore import QDateTime, Qt, QTimer, pyqtSignal, QSize, QPoint, QPointF, QRect, QLine, QRectF, QEasingCurve, QPropertyAnimation, QSequentialAnimationGroup, pyqtSlot, QThread, QDir , pyqtProperty
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
    QScrollArea, 
    QDoubleSpinBox,
    QDialogButtonBox,
    QTreeView,
    QListView,
    QFileSystemModel,
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsLineItem   
)
from PyQt5.QtGui import QIcon, QPaintEvent
import matplotlib
from matplotlib.widgets import Widget
import time
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
import asyncio
import aiofiles
import aiofiles.os
import queue


miBarrera = Barrier(3)
_sentinelStopThread = -500#object() #objeto para indicar que los hilos deben detenerse
_sentinelArrayImgSeparator = -273#object() #objeto para indicar separador entre imagenes
pathFolder = "hola" #usamos esta variable compartida para registrar el path cargado en la popup de seleccion de archivo para leer 
posXRect1 = 10
posYRect1 = 10
#direccion base para los archivos de imagen
basedir = os.path.dirname(__file__)

#detecto si se cargo la imagen
try:
    from ctypes import winddl
    myappid = "ar.com.meditecna.cameraApp.00"
    winddl.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass
#definimos la clase elipse de dimension ajustable
class ClickableReSizedGraphicsEllipItem(QGraphicsEllipseItem):
    handleTopLeft = 1 #voy a generar marcas numericas para indicar si se esta seleccionando alguno de los puntos de modificacion del rectangulo
    handleTopMiddle = 2 #puede ser que se seleccione las esquinas o los laterales tambien puedo seleccionar la parte superior o inferior
    handleTopRight = 3
    handleMiddleLeft = 4
    handleMiddleRight = 5
    handleBottomLeft = 6
    handleBottomMiddle = 7
    handleBottomRight = 8

    handleSize = 8 #defino un tamaño en pixeles para la seleccion 
    handleSpace = -4 #defino un espacio 

    handleCursors = { #creo los cursores asociados a cada punto que permite la modificacion de la roi
        handleTopLeft: Qt.SizeFDiagCursor,
        handleTopMiddle: Qt.SizeVerCursor,
        handleTopRight: Qt.SizeBDiagCursor,
        handleMiddleLeft: Qt.SizeHorCursor,
        handleMiddleRight: Qt.SizeHorCursor,
        handleBottomLeft: Qt.SizeBDiagCursor,
        handleBottomMiddle: Qt.SizeVerCursor,
        handleBottomRight: Qt.SizeFDiagCursor
    }
    #sobre escribimo la funcion init
    def __init__(self, x, y, w, h, pen, brush):#*args):
        super(ClickableReSizedGraphicsEllipItem,self).__init__(x,y,w,h)#*args)
        self.handles = {} #creamos un diccionario para manejar los puntos de modificacion de forma
        self.handleSelected = None #un flag para indicar si seleccionamos o no un borde
        self.mousePressPos = None #un flag para indicar si se presiono o no el mouse y se esta cambiando la forma del rectangulo
        self.mousePressRect = None #un flag para indicar si se presiono o no el mouse y se esta cambiando la posicion del rectangulo
        self.setAcceptHoverEvents(True) #indicamos que acepta la funcion hover es decir el evento cuando el mouse pasa por encima del objeto
        self.setFlag(QGraphicsItem.ItemIsMovable, True) #indicamos que el item en la escena es movible
        self.setFlag(QGraphicsItem.ItemIsSelectable, True) #indicamos que el item es seleccionable dentro de la escena, lo podemos marcar
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True) #indicamos que el item puede modificar su geometria
        self.setFlag(QGraphicsItem.ItemIsFocusable, True) #indicamos que es enfocable
        self.updateHandlesPos() #llamamo a la funcion que maneja la posicion
        self.rectBrush = brush
        self.rectPen = pen
    def handleAt(self, point):
        #indicamos que indicador esta siendo seleccionado
        for k, v, in self.handles.items():
            if v.contains(point):
                return k
        return None
    
    def hoverMoveEvent(self, moveEvent):
        #se ejecuta cuando pasa sobre el rect sin presionar
        if self.isSelected():
            handle = self.handleAt(moveEvent.pos())
            cursor = Qt.ArrowCursor if handle is None else self.handleCursors[handle]
            self.setCursor(cursor)
        super().hoverMoveEvent(moveEvent)
    
    def hoverLeaveEvent(self, moveEvent):
        #ejecuto cuando salgo de la forma rect sin presionar
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(moveEvent)

    def mousePressEvent(self, mouseEvent):
        #ejecutamos cuando hacemos click
        self.handleSelected = self.handleAt(mouseEvent.pos())
        if self.handleSelected:
            self.mousePressPos = mouseEvent.pos()
            self.mousePressRect = self.boundingRect()
        super().mousePressEvent(mouseEvent)
    
    def mouseMoveEvent(self, mouseEvent):
        #ejecuamtos mientras movemos el mouse siendo presionado
        if self.handleSelected is not None:
            self.interactiveResize(mouseEvent.pos())
        else:
            super().mouseMoveEvent(mouseEvent)
    
    def mouseReleaseEvent(self, mouseEvent):
        #ejecuamta cuando soltamos el lcick
        super().mouseReleaseEvent(mouseEvent)
        self.handleSelected = None
        self.mousePressPos = None
        self.mousePressRect = None
        self.update()
        if mouseEvent.button() == Qt.LeftButton:
            print("Release ellipse")
            self.scene().itemClickedEllipse.emit(self)
    def boundingRect(self):
        #devolvemos los limites del rect incluyendo el manejo de retamao
        o = self.handleSize + self.handleSpace
        return self.rect().adjusted(-o, -o, o, o)

    def updateHandlesPos(self):
        #actualizamos el tamaño ajustando al tamaño y posicion nuevo
        s = self.handleSize
        b = self.boundingRect()
        
        self.handles[self.handleTopLeft] = QRectF(b.left(),b.top(),s,s)
        self.handles[self.handleTopMiddle] = QRectF(b.center().x() - s/2, b.top(), s, s)
        self.handles[self.handleTopRight] = QRectF(b.right() - s, b.top(), s, s)
        self.handles[self.handleMiddleLeft] = QRectF(b.left(), b.center().y() - s/2, s, s)
        self.handles[self.handleMiddleRight] = QRectF(b.right() - s, b.center().y() - s/2, s, s)
        self.handles[self.handleBottomLeft] = QRectF(b.left(), b.bottom() - s, s, s)
        self.handles[self.handleBottomMiddle] = QRectF(b.center().x() - s/2, b.bottom() - s, s, s)
        self.handles[self.handleBottomRight] = QRectF(b.right() - s, b.bottom() -s, s, s)
        
    def interactiveResize(self, mousePos):
        #ajustamos el tamaño interactivamente
        offset = self.handleSize + self.handleSpace
        boundingRect = self.boundingRect()
        rect = self.rect()
        diff = QPointF(0,0)

        self.prepareGeometryChange()
        if self.handleSelected == self.handleTopLeft:
            #si agarre este extremo
            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setLeft(toX)
            boundingRect.setTop(toY)
            rect.setLeft(boundingRect.left() + offset)
            rect.setTop(boundingRect.top() + offset)
            self.setRect(rect)
            
        elif self.handleSelected == self.handleTopMiddle:
            fromY = self.mousePressRect.top()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setY(toY - fromY)
            boundingRect.setTop(toY)
            rect.setTop(boundingRect.top() + offset)
            self.setRect(rect)
            
        elif self.handleSelected == self.handleTopRight:
            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setRight(toX)
            boundingRect.setTop(toY)
            rect.setRight(boundingRect.right() - offset)
            rect.setTop(boundingRect.top() + offset)
            self.setRect(rect)
            
        elif self.handleSelected == self.handleMiddleLeft:
            fromX = self.mousePressRect.left()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            diff.setX(toX - fromX)
            boundingRect.setLeft(toX)
            rect.setLeft(boundingRect.left() + offset)
            self.setRect(rect)
            
        elif self.handleSelected == self.handleMiddleRight:
            fromX = self.mousePressRect.right()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            diff.setX(toX - fromX)
            boundingRect.setRight(toX)
            rect.setRight(boundingRect.right() - offset)
            self.setRect(rect)
            
        elif self.handleSelected == self.handleBottomLeft:
            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setLeft(toX)
            boundingRect.setBottom(toY)
            rect.setLeft(boundingRect.left() + offset)
            rect.setBottom(boundingRect.bottom() - offset)
            self.setRect(rect)
            
        elif self.handleSelected == self.handleBottomMiddle:
            fromY = self.mousePressRect.bottom()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setY(toY - fromY)
            boundingRect.setBottom(toY)
            rect.setBottom(boundingRect.bottom() - offset)
            self.setRect(rect)
            
        elif self.handleSelected == self.handleBottomRight:
            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setRight(toX)
            boundingRect.setBottom(toY)
            rect.setRight(boundingRect.right() - offset)
            rect.setBottom(boundingRect.bottom() - offset)
            self.setRect(rect)
            
        self.updateHandlesPos()
    
    def shape(self): #sobre escribimos el metodo shape del objeto rectangulo. Parece que este metodo se llama siempre que se realice una actualizacion de la imagen
        #retorna la forma del item como un QPainterPAth
        path = QPainterPath()
        path.addRect(self.rect())
        if self.isSelected():
            for shape in self.handles.values():
                path.addEllipse(shape)
        return path

    def paint(self, painter, option, widget = None):
        #digujamos el nodo en el visor de graficos
        painter.setBrush(QBrush(QColor(255,0,0,255)))
        painter.setPen(QPen(QColor(0,255,0,255),1.0,Qt.SolidLine,Qt.RoundCap, Qt.RoundJoin))
        for handle, rect in self.handles.items():
            if self.handleSelected is None or handle == self.handleSelected:
                painter.drawEllipse(rect)
        painter.setBrush(self.rectBrush)#QBrush(QColor(0,0,0,0)))
        painter.setPen(self.rectPen)#QPen(QColor(0,255,0,255),1.0,Qt.SolidLine,Qt.RoundCap, Qt.RoundJoin))
        painter.drawEllipse(self.rect())
#definimos la clase rectangulo de dimension ajustable
class ClickableReSizedGraphicsRectItem(QGraphicsRectItem):
    handleTopLeft = 1 #voy a generar marcas numericas para indicar si se esta seleccionando alguno de los puntos de modificacion del rectangulo
    handleTopMiddle = 2 #puede ser que se seleccione las esquinas o los laterales tambien puedo seleccionar la parte superior o inferior
    handleTopRight = 3
    handleMiddleLeft = 4
    handleMiddleRight = 5
    handleBottomLeft = 6
    handleBottomMiddle = 7
    handleBottomRight = 8

    handleSize = 8 #defino un tamaño en pixeles para la seleccion 
    handleSpace = -4 #defino un espacio 

    handleCursors = { #creo los cursores asociados a cada punto que permite la modificacion de la roi
        handleTopLeft: Qt.SizeFDiagCursor,
        handleTopMiddle: Qt.SizeVerCursor,
        handleTopRight: Qt.SizeBDiagCursor,
        handleMiddleLeft: Qt.SizeHorCursor,
        handleMiddleRight: Qt.SizeHorCursor,
        handleBottomLeft: Qt.SizeBDiagCursor,
        handleBottomMiddle: Qt.SizeVerCursor,
        handleBottomRight: Qt.SizeFDiagCursor
    }
    #sobre escribimo la funcion init
    def __init__(self, x, y, w, h, pen, brush):#*args):
        super(ClickableReSizedGraphicsRectItem,self).__init__(x,y,w,h)#*args)
        self.handles = {} #creamos un diccionario para manejar los puntos de modificacion de forma
        self.handleSelected = None #un flag para indicar si seleccionamos o no un borde
        self.mousePressPos = None #un flag para indicar si se presiono o no el mouse y se esta cambiando la forma del rectangulo
        self.mousePressRect = None #un flag para indicar si se presiono o no el mouse y se esta cambiando la posicion del rectangulo
        self.setAcceptHoverEvents(True) #indicamos que acepta la funcion hover es decir el evento cuando el mouse pasa por encima del objeto
        self.setFlag(QGraphicsItem.ItemIsMovable, True) #indicamos que el item en la escena es movible
        self.setFlag(QGraphicsItem.ItemIsSelectable, True) #indicamos que el item es seleccionable dentro de la escena, lo podemos marcar
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True) #indicamos que el item puede modificar su geometria
        self.setFlag(QGraphicsItem.ItemIsFocusable, True) #indicamos que es enfocable
        self.updateHandlesPos() #llamamo a la funcion que maneja la posicion
        self.rectBrush = brush
        self.rectPen = pen
    def handleAt(self, point):
        #indicamos que indicador esta siendo seleccionado
        for k, v, in self.handles.items():
            if v.contains(point):
                return k
        return None
    
    def hoverMoveEvent(self, moveEvent):
        #se ejecuta cuando pasa sobre el rect sin presionar
        if self.isSelected():
            handle = self.handleAt(moveEvent.pos())
            cursor = Qt.ArrowCursor if handle is None else self.handleCursors[handle]
            self.setCursor(cursor)
        super().hoverMoveEvent(moveEvent)
    
    def hoverLeaveEvent(self, moveEvent):
        #ejecuto cuando salgo de la forma rect sin presionar
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(moveEvent)

    def mousePressEvent(self, mouseEvent):
        #ejecutamos cuando hacemos click
        self.handleSelected = self.handleAt(mouseEvent.pos())
        if self.handleSelected:
            self.mousePressPos = mouseEvent.pos()
            self.mousePressRect = self.boundingRect()
        super().mousePressEvent(mouseEvent)
    
    def mouseMoveEvent(self, mouseEvent):
        #ejecuamtos mientras movemos el mouse siendo presionado
        if self.handleSelected is not None:
            self.interactiveResize(mouseEvent.pos())
        else:
            super().mouseMoveEvent(mouseEvent)
    
    def mouseReleaseEvent(self, mouseEvent):
        #ejecuamta cuando soltamos el lcick
        super().mouseReleaseEvent(mouseEvent)
        self.handleSelected = None
        self.mousePressPos = None
        self.mousePressRect = None
        self.update()
        if mouseEvent.button() == Qt.LeftButton:
            print("release Rect")
            self.scene().itemClickedRect.emit(self)
    
    def boundingRect(self):
        #devolvemos los limites del rect incluyendo el manejo de retamao
        o = self.handleSize + self.handleSpace
        return self.rect().adjusted(-o, -o, o, o)

    def updateHandlesPos(self):
        #actualizamos el tamaño ajustando al tamaño y posicion nuevo
        s = self.handleSize
        b = self.boundingRect()
        
        self.handles[self.handleTopLeft] = QRectF(b.left(),b.top(),s,s)
        self.handles[self.handleTopMiddle] = QRectF(b.center().x() - s/2, b.top(), s, s)
        self.handles[self.handleTopRight] = QRectF(b.right() - s, b.top(), s, s)
        self.handles[self.handleMiddleLeft] = QRectF(b.left(), b.center().y() - s/2, s, s)
        self.handles[self.handleMiddleRight] = QRectF(b.right() - s, b.center().y() - s/2, s, s)
        self.handles[self.handleBottomLeft] = QRectF(b.left(), b.bottom() - s, s, s)
        self.handles[self.handleBottomMiddle] = QRectF(b.center().x() - s/2, b.bottom() - s, s, s)
        self.handles[self.handleBottomRight] = QRectF(b.right() - s, b.bottom() -s, s, s)
        
    def interactiveResize(self, mousePos):
        #ajustamos el tamaño interactivamente
        offset = self.handleSize + self.handleSpace
        boundingRect = self.boundingRect()
        rect = self.rect()
        diff = QPointF(0,0)

        self.prepareGeometryChange()
        if self.handleSelected == self.handleTopLeft:
            #si agarre este extremo
            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setLeft(toX)
            boundingRect.setTop(toY)
            rect.setLeft(boundingRect.left() + offset)
            rect.setTop(boundingRect.top() + offset)
            self.setRect(rect)
            
        elif self.handleSelected == self.handleTopMiddle:
            fromY = self.mousePressRect.top()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setY(toY - fromY)
            boundingRect.setTop(toY)
            rect.setTop(boundingRect.top() + offset)
            self.setRect(rect)
            
        elif self.handleSelected == self.handleTopRight:
            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setRight(toX)
            boundingRect.setTop(toY)
            rect.setRight(boundingRect.right() - offset)
            rect.setTop(boundingRect.top() + offset)
            self.setRect(rect)
            
        elif self.handleSelected == self.handleMiddleLeft:
            fromX = self.mousePressRect.left()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            diff.setX(toX - fromX)
            boundingRect.setLeft(toX)
            rect.setLeft(boundingRect.left() + offset)
            self.setRect(rect)
            
        elif self.handleSelected == self.handleMiddleRight:
            fromX = self.mousePressRect.right()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            diff.setX(toX - fromX)
            boundingRect.setRight(toX)
            rect.setRight(boundingRect.right() - offset)
            self.setRect(rect)
            
        elif self.handleSelected == self.handleBottomLeft:
            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setLeft(toX)
            boundingRect.setBottom(toY)
            rect.setLeft(boundingRect.left() + offset)
            rect.setBottom(boundingRect.bottom() - offset)
            self.setRect(rect)
            
        elif self.handleSelected == self.handleBottomMiddle:
            fromY = self.mousePressRect.bottom()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setY(toY - fromY)
            boundingRect.setBottom(toY)
            rect.setBottom(boundingRect.bottom() - offset)
            self.setRect(rect)
            
        elif self.handleSelected == self.handleBottomRight:
            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setRight(toX)
            boundingRect.setBottom(toY)
            rect.setRight(boundingRect.right() - offset)
            rect.setBottom(boundingRect.bottom() - offset)
            self.setRect(rect)
            
        self.updateHandlesPos()
    
    def shape(self): #sobre escribimos el metodo shape del objeto rectangulo. Parece que este metodo se llama siempre que se realice una actualizacion de la imagen
        #retorna la forma del item como un QPainterPAth
        path = QPainterPath()
        path.addRect(self.rect())
        if self.isSelected():
            for shape in self.handles.values():
                path.addEllipse(shape)
        return path

    def paint(self, painter, option, widget = None):
        #digujamos el nodo en el visor de graficos
        painter.setBrush(QBrush(QColor(255,0,0,255)))
        painter.setPen(QPen(QColor(0,255,0,255),1.0,Qt.SolidLine,Qt.RoundCap, Qt.RoundJoin))
        for handle, rect in self.handles.items():
            if self.handleSelected is None or handle == self.handleSelected:
                painter.drawEllipse(rect)
        painter.setBrush(self.rectBrush)#QBrush(QColor(0,0,0,0)))
        painter.setPen(self.rectPen)#QPen(QColor(0,255,0,255),1.0,Qt.SolidLine,Qt.RoundCap, Qt.RoundJoin))
        painter.drawRect(self.rect())
#definimo la clase line de dimension ajustable
class ClickableReSizedGraphicsLineItem(QGraphicsRectItem):
    handleTopLeft = 1 #voy a generar marcas numericas para indicar si se esta seleccionando alguno de los puntos de modificacion del rectangulo
    handleTopMiddle = 2 #puede ser que se seleccione las esquinas o los laterales tambien puedo seleccionar la parte superior o inferior
    handleTopRight = 3
    handleMiddleLeft = 4
    handleMiddleRight = 5
    handleBottomLeft = 6
    handleBottomMiddle = 7
    handleBottomRight = 8

    handleSize = 8 #defino un tamaño en pixeles para la seleccion 
    handleSpace = -4 #defino un espacio 

    handleCursors = { #creo los cursores asociados a cada punto que permite la modificacion de la roi
        handleTopLeft: Qt.SizeFDiagCursor,
        handleTopMiddle: Qt.SizeVerCursor,
        handleTopRight: Qt.SizeBDiagCursor,
        handleMiddleLeft: Qt.SizeHorCursor,
        handleMiddleRight: Qt.SizeHorCursor,
        handleBottomLeft: Qt.SizeBDiagCursor,
        handleBottomMiddle: Qt.SizeVerCursor,
        handleBottomRight: Qt.SizeFDiagCursor
    }
    #sobre escribimo la funcion init
    def __init__(self, x, y, w, h, pen, brush, indice):#*args):
        super(ClickableReSizedGraphicsLineItem,self).__init__(x,y,w,h)#*args)
        self.handles = {} #creamos un diccionario para manejar los puntos de modificacion de forma
        self.handleSelected = None #un flag para indicar si seleccionamos o no un borde
        self.mousePressPos = None #un flag para indicar si se presiono o no el mouse y se esta cambiando la forma del rectangulo
        self.mousePressRect = None #un flag para indicar si se presiono o no el mouse y se esta cambiando la posicion del rectangulo
        self.setAcceptHoverEvents(True) #indicamos que acepta la funcion hover es decir el evento cuando el mouse pasa por encima del objeto
        self.setFlag(QGraphicsItem.ItemIsMovable, True) #indicamos que el item en la escena es movible
        self.setFlag(QGraphicsItem.ItemIsSelectable, True) #indicamos que el item es seleccionable dentro de la escena, lo podemos marcar
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True) #indicamos que el item puede modificar su geometria
        self.setFlag(QGraphicsItem.ItemIsFocusable, True) #indicamos que es enfocable
        self.updateHandlesPos() #llamamo a la funcion que maneja la posicion
        self.rectBrush = brush
        self.rectPen = pen
        self.indiceLinea = indice
    def handleAt(self, point):
        #indicamos que indicador esta siendo seleccionado
        for k, v, in self.handles.items():
            if v.contains(point):
                return k
        return None
    
    def hoverMoveEvent(self, moveEvent):
        #se ejecuta cuando pasa sobre el rect sin presionar
        if self.isSelected():
            handle = self.handleAt(moveEvent.pos())
            cursor = Qt.ArrowCursor if handle is None else self.handleCursors[handle]
            self.setCursor(cursor)
        super().hoverMoveEvent(moveEvent)
    
    def hoverLeaveEvent(self, moveEvent):
        #ejecuto cuando salgo de la forma rect sin presionar
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(moveEvent)

    def mousePressEvent(self, mouseEvent):
        #ejecutamos cuando hacemos click
        self.handleSelected = self.handleAt(mouseEvent.pos())
        if self.handleSelected:
            self.mousePressPos = mouseEvent.pos()
            self.mousePressRect = self.boundingRect()
        super().mousePressEvent(mouseEvent)
    
    def mouseMoveEvent(self, mouseEvent):
        #ejecuamtos mientras movemos el mouse siendo presionado
        if self.handleSelected is not None:
            self.interactiveResize(mouseEvent.pos())
        else:
            super().mouseMoveEvent(mouseEvent)
    
    def mouseReleaseEvent(self, mouseEvent):
        #ejecuamta cuando soltamos el lcick
        super().mouseReleaseEvent(mouseEvent)
        self.handleSelected = None
        self.mousePressPos = None
        self.mousePressRect = None
        self.update()
        if mouseEvent.button() == Qt.LeftButton:
            print("Release rect")
            self.scene().itemClickedLine.emit(self)

    def boundingRect(self):
        #devolvemos los limites del rect incluyendo el manejo de retamao
        o = self.handleSize + self.handleSpace
        return self.rect().adjusted(-o, -o, o, o)

    def updateHandlesPos(self):
        #actualizamos el tamaño ajustando al tamaño y posicion nuevo
        s = self.handleSize
        b = self.boundingRect()
        
        self.handles[self.handleTopLeft] = QRectF(b.left(),b.top(),s,s)
        self.handles[self.handleTopMiddle] = QRectF(b.center().x() - s/2, b.top(), s, s)
        self.handles[self.handleTopRight] = QRectF(b.right() - s, b.top(), s, s)
        self.handles[self.handleMiddleLeft] = QRectF(b.left(), b.center().y() - s/2, s, s)
        self.handles[self.handleMiddleRight] = QRectF(b.right() - s, b.center().y() - s/2, s, s)
        self.handles[self.handleBottomLeft] = QRectF(b.left(), b.bottom() - s, s, s)
        self.handles[self.handleBottomMiddle] = QRectF(b.center().x() - s/2, b.bottom() - s, s, s)
        self.handles[self.handleBottomRight] = QRectF(b.right() - s, b.bottom() -s, s, s)
        
    def interactiveResize(self, mousePos):
        #ajustamos el tamaño interactivamente
        offset = self.handleSize + self.handleSpace
        boundingRect = self.boundingRect()
             
        print(boundingRect)
        rect = self.rect()
        diff = QPointF(0,0)

        self.prepareGeometryChange()
        if self.handleSelected == self.handleTopLeft:
            #si agarre este extremo
            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setLeft(toX)
            boundingRect.setTop(toY)
            rect.setLeft(boundingRect.left() + offset)
            rect.setTop(boundingRect.top() + offset)
            self.setRect(rect)
            
        elif self.handleSelected == self.handleTopMiddle:
            fromY = self.mousePressRect.top()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            print(toY - fromY)
            diff.setY(toY - fromY)
            boundingRect.setTop(toY)
            rect.setTop(boundingRect.top() + offset)
            self.setRect(rect)
            print(rect)
            print(rect.left(),rect.top(),rect.right(),rect.bottom())

        elif self.handleSelected == self.handleTopRight:
            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.top()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setRight(toX)
            boundingRect.setTop(toY)
            rect.setRight(boundingRect.right() - offset)
            rect.setTop(boundingRect.top() + offset)
            self.setRect(rect)

        elif self.handleSelected == self.handleMiddleLeft:
            fromX = self.mousePressRect.left()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            diff.setX(toX - fromX)
            boundingRect.setLeft(toX)
            rect.setLeft(boundingRect.left() + offset)
            self.setRect(rect)
            
        elif self.handleSelected == self.handleMiddleRight:
            fromX = self.mousePressRect.right()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            diff.setX(toX - fromX)
            boundingRect.setRight(toX)
            rect.setRight(boundingRect.right() - offset)
            self.setRect(rect)
            
        elif self.handleSelected == self.handleBottomLeft:
            fromX = self.mousePressRect.left()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setLeft(toX)
            boundingRect.setBottom(toY)
            rect.setLeft(boundingRect.left() + offset)
            rect.setBottom(boundingRect.bottom() - offset)
            self.setRect(rect)
            
        elif self.handleSelected == self.handleBottomMiddle:
            fromY = self.mousePressRect.bottom()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setY(toY - fromY)
            boundingRect.setBottom(toY)
            rect.setBottom(boundingRect.bottom() - offset)
            self.setRect(rect)
            
        elif self.handleSelected == self.handleBottomRight:
            fromX = self.mousePressRect.right()
            fromY = self.mousePressRect.bottom()
            toX = fromX + mousePos.x() - self.mousePressPos.x()
            toY = fromY + mousePos.y() - self.mousePressPos.y()
            diff.setX(toX - fromX)
            diff.setY(toY - fromY)
            boundingRect.setRight(toX)
            boundingRect.setBottom(toY)
            rect.setRight(boundingRect.right() - offset)
            rect.setBottom(boundingRect.bottom() - offset)
            self.setRect(rect)
            
        self.updateHandlesPos()
    
    def shape(self): #sobre escribimos el metodo shape del objeto rectangulo. Parece que este metodo se llama siempre que se realice una actualizacion de la imagen
        #retorna la forma del item como un QPainterPAth
        path = QPainterPath()
        path.addRect(self.rect())
        if self.isSelected():
            for shape in self.handles.values():
                path.addEllipse(shape)
        return path

    def paint(self, painter, option, widget = None):
        #digujamos el nodo en el visor de graficos
        painter.setBrush(QBrush(QColor(255,0,0,255)))
        painter.setPen(QPen(QColor(0,255,0,255),1.0,Qt.SolidLine,Qt.RoundCap, Qt.RoundJoin))
        for handle, rect in self.handles.items():
            if self.handleSelected is None or handle == self.handleSelected:
                painter.drawEllipse(rect)

        painter.setBrush(self.rectBrush)#QBrush(QColor(0,0,0,0)))
        painter.setPen(self.rectPen)#QPen(QColor(0,255,0,255),1.0,Qt.SolidLine,Qt.RoundCap, Qt.RoundJoin))
        print(self.indiceLinea)
        if self.indiceLinea == 0:
            painter.drawLine(self.rect().topLeft(), self.rect().bottomRight())# drawRect(self.rect())
        else:
            painter.drawLine(self.rect().bottomLeft(),self.rect().topRight())# drawRect(self.rect())

#definimos una clase que vamos a utilizar como popup para seleccion de path
class popUpListFolder(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select folder to read")
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        popUpLayout = QVBoxLayout(self)

        hlay = QHBoxLayout()

        self.treeview = QTreeView()
        self.listview = QListView()

        path = QDir().currentPath()

        self.dirModel = QFileSystemModel()
        self.dirModel.setRootPath(QDir.rootPath())
        self.dirModel.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs)

        self.fileModel = QFileSystemModel()
        self.fileModel.setFilter(QDir.NoDotAndDotDot | QDir.Files)

        self.treeview.setModel(self.dirModel)
        self.listview.setModel(self.fileModel)

        self.treeview.setRootIndex(self.dirModel.index(path))
        self.listview.setRootIndex(self.fileModel.index(path))

        self.treeview.clicked.connect(self.on_clicked)
        self.listview.clicked.connect(self.on_clickedlist)

        hlay.addWidget(self.treeview)
        hlay.addWidget(self.listview)
        popUpLayout.addLayout(hlay)
        popUpLayout.addWidget(self.buttonBox)
    
    def on_clicked(self, index):
        path = self.dirModel.fileInfo(index).absoluteFilePath()
        self.listview.setRootIndex(self.fileModel.setRootPath(path))
    
    def on_clickedlist(self, index):
        path = self.fileModel.fileInfo(index).absoluteFilePath()
        global pathFolder
        pathFolder = path
     

#******************Declaro las funciones asincronicas*******************
 #creamos la funcion para generar un directorio asincronico
#esto definiendo un nombre en el raiz del programa genera 
#una carpeta.
async def crearDirectorioAsincronico():
    returnQuery = await aiofiles.os.path.isdir('imagenes')
    #si no existe lo va a crear asincronicamente
    #await aiofiles.os.makedirs('tmp', exist_ok=True)
    if not returnQuery:        
        #creamos un directorio donde guardar las imagenes
        await aiofiles.os.makedirs('imagenes', exist_ok=True)                                                                            
    timeCreationFolderImages = datetime.datetime.now()    
    timeCreationFolderImagesStrDay = timeCreationFolderImages.strftime("%b_%d_%Y")
    returnQuery = await aiofiles.os.path.isdir('imagenes/'+timeCreationFolderImagesStrDay)
    if not returnQuery:
        await aiofiles.os.makedirs('imagenes/'+timeCreationFolderImagesStrDay,exist_ok=True)
    timeCreationFolderImagesStrHour = timeCreationFolderImages.strftime("%H")
    returnQuery = await aiofiles.os.path.isdir('imagenes/'+timeCreationFolderImagesStrDay+"/"+timeCreationFolderImagesStrHour)
    if not returnQuery:
        await aiofiles.os.makedirs('imagenes/'+timeCreationFolderImagesStrDay+"/"+timeCreationFolderImagesStrHour,exist_ok=True)
    timeCreationFolderImagesStrMinSec = timeCreationFolderImages.strftime("%M_%S")
    returnQuery = await aiofiles.os.path.isdir('imagenes/'+timeCreationFolderImagesStrDay+"/"+timeCreationFolderImagesStrHour+"/"+timeCreationFolderImagesStrMinSec)
    if not returnQuery:
        await aiofiles.os.makedirs('imagenes/'+timeCreationFolderImagesStrDay+"/"+timeCreationFolderImagesStrHour+"/"+timeCreationFolderImagesStrMinSec,exist_ok=True)
    
    #en este punto tengo creado un directorio donde voy a guardar las imagenes de esta grabacion
    return 'imagenes/'+timeCreationFolderImagesStrDay+"/"+timeCreationFolderImagesStrHour+"/"+timeCreationFolderImagesStrMinSec

#definimos una funcion para editar asincronicamente los archivos
#con esto lo que buscamos es generar una imagen con anotaciones
#de nuevo en la version final vamos a mostrar la lista de imagenes
#y luego seleccionamos una para modificarla y guardarla
async def modificarArchivoAsincronico():
    #creamos una rachivo para escritura y le cargamos un contenido
    async with aiofiles.open('test_write.txt', mode='w') as handle:
        await handle.write('hello aplicacion de imagenes!')

#****Funciones para buscar imagenes historicas
def leerArchivoSincronico(nombreArchivo):
    pathArchivo = nombreArchivo
    fTh = gzip.GzipFile(pathArchivo + ".npTh.gz", "r")
    fCv = gzip.GzipFile(pathArchivo + ".npCv.gz", "r")
    datoTh = np.load(fTh)
    datoCv = np.load(fCv)
    listaIndicesTh = np.where(datoTh == _sentinelArrayImgSeparator)
    listaIndicesCv = np.where(datoCv == _sentinelArrayImgSeparator)
    resultadoTh = np.array_split(datoTh, listaIndicesTh[0])
    resultadoCv = np.array_split(datoCv, listaIndicesCv[0])
    matrizImgTh = np.zeros((288,382,29))
    matrizImgCv = np.zeros((288,384,3,29))
    indice = 0
    for i in resultadoTh[1:]:
        subArrayDato = i[1:]
        imagen = np.reshape(subArrayDato,(288,382))
        matrizImgTh[:,:,indice] = imagen
        indice += 1
    indice = 0
    for i in resultadoCv[1:]:
        subArrayDatoCv = i[1:]
        imagenCv = np.reshape(subArrayDatoCv, (288,384,3))
        matrizImgCv[:,:,:,indice] = imagenCv
        indice += 1
    
    return (matrizImgTh, matrizImgCv)

#definimos la funcion para leer contenido asincronico
#aca debemos mostrar la lista de archivos de imagenes y dar la
#posibilidad de seleccionar la misma. 
#la imagen es doble es decir la imagen en temperatura y la imagen
#en paleta de colores. Nosotros mostramos la imagen en temepratura
#y dejamos la imagen en paleta de colores. 
#esta parte del codigo es solo de pruebas en la version final 
#debemos usar la lista de imagenees 
async def leerContenidoAsincronico():
    #leemos el contenido del archivo
    async with aiofiles.open('test_write.txt', mode='r') as handle:
        data = await handle.read()        
    print(f'Read {len(data)} bytes')

#definimos la funcion asincronica para borrar archivos. Borramos
#un archivo existente esta funcion es solo de prueba 
#la version correcta debe mostrar una lista de archivos y permitir
#seleccionar el archivo a borrar
async def borrarArchivoAsincronico():
    #creamos para prueba un archivo y lo borramos esto debrmoes reemplazarlo 
    async with aiofiles.open("files_delete.txt", mode='x') as handle:
        handle.close()
    #borramos el archivo creado en la linea de arriba
    await aiofiles.os.remove("files_delete.txt")

#definimos las funciones asincronicas para el guardado de archivos
async def renombrarArchivoAsincronico():
    returnQuery = await aiofiles.os.path.isfile('files_rename.txt')
    if not returnQuery:
        #esta funcion es de prueba para esto genera un archivo y lo renombra
        #tomar en cuenta que esto lo podemos hacer solo de prueba en la version
        #final debemos mostrar la lista de archivos que podriamos querer renombrar
        #luego realizamos la seleccion de aca 
        async with aiofiles.open("files_rename.txt", mode='x') as handle:
            handle.close()
        #renombramos el arhivo
        returnQuery1 = await aiofiles.os.path.isfile('files_rename1.txt')
        #si no existe tira falla
        if not returnQuery1:
            await aiofiles.os.rename("files_rename.txt", "files_rename1.txt")
#**********************************************************************************
#creamos un hilo para poder registrar cuando los dos hilos de guardado de
#imagenes en archivo terminan
class statusGuardadoThread(Thread):
    def __init__(self, botonLeerFolderIzq,botonLeerFolderDer,indicadorEstado):
        Thread.__init__(self)
        self.botonLeerFolderIzq = botonLeerFolderIzq
        self.botonLeerFolderDer = botonLeerFolderDer
        self.estadoGuardado = indicadorEstado
    def run(self):
        #indico que estoy guardando en disco
        self.estadoGuardado.setText("Guardando en disco...")
        #espero a que los hilos de guardado liberen la barrera
        miBarrera.wait()
        #los hilos liberados
        self.botonLeerFolderIzq.setEnabled(True)
        self.botonLeerFolderDer.setEnabled(True)
        self.estadoGuardado.setText("Imagenes guardadas en disco!")
    
#defino funcion para el guardado de archivos
def saveQueueImageInDisk(args1,args2,path):
    while True:
        print("guardado de datos sincronico")
        datoAcumuladoTh = np.array([])
        datoAcumuladoCv = np.array([])
        i = 0
        while True:
            tokenThermal = args1.get()
            tokenCV = args2.get()
            i += 1
            nameFile = random.random()
            if i >= 30:
                fTh = gzip.GzipFile(path+"/"+str(nameFile) + ".npTh.gz", "w")
                fCv = gzip.GzipFile(path+"/"+str(nameFile) + ".npCv.gz", "w")
                np.save(file=fTh, arr=datoAcumuladoTh)
                np.save(file=fCv, arr=datoAcumuladoCv)
                fTh.close()
                fCv.close()
                break
            if tokenThermal is _sentinelStopThread:
                #finalizo el hilo
                break
            datoAcumuladoTh = np.append(datoAcumuladoTh, _sentinelArrayImgSeparator)
            datoAcumuladoTh = np.append(datoAcumuladoTh, tokenThermal)
            datoAcumuladoCv = np.append(datoAcumuladoCv,_sentinelArrayImgSeparator)
            datoAcumuladoCv = np.append(datoAcumuladoCv, tokenCV)
        if tokenThermal is _sentinelStopThread:
            #finalizo el hilo
            print("Finalizo Guardado Asincronico 1")
            break
    miBarrera.wait()
#***************************************************
#estas clases se definieron para hacer 
#customizable la seleccion de objetos
#sobre la imagen mostrada, Son Rois fijas
#y las estamos reemplazando por las Rois
#ajustables dinamicamente
class ClickableGraphicsRectItem(QGraphicsRectItem):
    def __init__(self, x, y, w, h, pen, brush):
        super(ClickableGraphicsRectItem,self).__init__(x, y, w, h)
        self.setPen(pen)
        self.setBrush(brush)
        self.setFlags(self.ItemIsSelectable|self.ItemIsMovable|self.ItemIsFocusable)
    def mousePressEvent(self, event):
        super(ClickableGraphicsRectItem, self).mousePressEvent(event)
        if event.button() == Qt.LeftButton:            
            print("click Rect")
    def mouseReleaseEvent(self, event):
        super(ClickableGraphicsRectItem, self).mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton:
            print("release Rect")
            self.scene().itemClickedRect.emit(self)
class ClickableGraphicsEllipseItem(QGraphicsEllipseItem):
    def __init__(self,x, y, w, h, pen, brush):
        super(ClickableGraphicsEllipseItem, self).__init__(x, y, w, h)
        self.setPen(pen)
        self.setBrush(brush)
        self.setFlags(self.ItemIsSelectable|self.ItemIsMovable|self.ItemIsFocusable)
    def mousePressEvent(self, event):
        super(ClickableGraphicsEllipseItem,self).mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.scene().itemClickedEllipse.emit(self)
            print("click Elipse")
class ClickableGraphicsLineItem(QGraphicsLineItem):
    def __init__(self,x, y, w, h, pen):
        super(ClickableGraphicsLineItem, self).__init__(x, y, w, h)
        self.setPen(pen)
        self.setFlags(self.ItemIsSelectable|self.ItemIsMovable|self.ItemIsFocusable)
    def mousePressEvent(self, event):
        super(ClickableGraphicsLineItem,self).mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.scene().itemClickedLine.emit(self)
            print("click Line")
#defino la clase para la escena que va a contener la imagen y los objetos
class ItemClickableGraphicsScene(QGraphicsScene):
    itemClickedRect = pyqtSignal(QGraphicsItem)
    itemClickedEllipse = pyqtSignal(QGraphicsItem)
    itemClickedLine = pyqtSignal(QGraphicsItem)
#defino la clase del objeto grafico que va a contener la escena
class ClickableItemView(QGraphicsView):
    global posXRect1
    global posYRect1
    itemSelected = pyqtSignal(QGraphicsItem)
    def mouseReleaseEvent(self, event): #mousePressEvent(self, event):        
        super(ClickableItemView,self).mouseReleaseEvent(event)#mousePressEvent(event)
        #print(event.pos())
        #listo los items en la scene
        listaItems = self.items()
        #print(listaItems)
        #detecto si se realizo un click
        if event.button() == Qt.LeftButton:
            #identifico si algun item contiene el 
            #la posicion donde se realizo el click 
            item = self.itemAt(event.pos())
            #emito el item seleccionado
            if item is not None:
                self.itemSelected.emit(item)
                #verifico si el item que contiene la 
                #posicion es instancia de RectItem
                if isinstance(item, QGraphicsRectItem):
                    #print('item {} clicked'.format(item.rect()))
                    #print('item {} desplazado'.format(item.pos()))                
                    posXRect1 = item.rect().x() + item.pos().x()
                    posYRect1 = item.rect().y() + item.pos().y()
#clase para herramientas de imagen
class TestImage(QLabel):
    def __init__(self):
        super().__init__()
        ######################Escala########################
        self.scaleFactor = 1
        self.scala = 1.25
        self.escalarRois = False #defino un flag para indicar que se tiene que re escalar las rois
        self.scaleFactorOld = 1
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
            self.resize(escala)     #ajusto la escala de la imagen
            if self.escalarRois == True: #determino si hay que escalar las rois, es true si si apreto el click en la imagen seleccionado zoom in o zoom out
                #**************************Roi Rectangulos*****************************************************************************
                #*****************ROI Rect1***************************
                xEscaladoRec1=self.parent().parent().rectangulo1.x()*(1+(self.scaleFactor-self.scaleFactorOld)) #usamos la escala anterior para calcular la diferencia x
                yEscaladoRec1=self.parent().parent().rectangulo1.y()*(1+(self.scaleFactor-self.scaleFactorOld)) #usamos la escala anterior para calcular la diferencia y
                anchoEscaladoRec1 = self.parent().parent().rectangulo1.width()*(1+(self.scaleFactor-self.scaleFactorOld)) #idem para calcular la diferencia con ancho alto
                altoEscaladoRec1 = self.parent().parent().rectangulo1.height()*(1+(self.scaleFactor-self.scaleFactorOld))
                #
                beginRectanguloRec1 = QPoint(int(xEscaladoRec1),int(yEscaladoRec1))
                endRectanguloRec1 = QPoint(int(xEscaladoRec1+anchoEscaladoRec1),int(yEscaladoRec1+altoEscaladoRec1))
                self.parent().parent().rectangulo1=QRect(beginRectanguloRec1, endRectanguloRec1)
                self.posTextRect1 = beginRectanguloRec1 #utilizo la posicion de inicio del rectangulo para fijar la posicion del texto                
                #*****************************************************
                #*****************ROI Rect2***************************
                xEscaladoRec2=self.parent().parent().rectangulo2.x()*(1+(self.scaleFactor-self.scaleFactorOld)) #usamos la escala anterior para calcular la diferencia x
                yEscaladoRec2=self.parent().parent().rectangulo2.y()*(1+(self.scaleFactor-self.scaleFactorOld)) #usamos la escala anterior para calcular la diferencia y
                anchoEscaladoRec2 = self.parent().parent().rectangulo2.width()*(1+(self.scaleFactor-self.scaleFactorOld)) #idem para calcular la diferencia con ancho alto
                altoEscaladoRec2 = self.parent().parent().rectangulo2.height()*(1+(self.scaleFactor-self.scaleFactorOld))
                #
                beginRectanguloRec2 = QPoint(int(xEscaladoRec2),int(yEscaladoRec2))
                endRectanguloRec2 = QPoint(int(xEscaladoRec2+anchoEscaladoRec2),int(yEscaladoRec2+altoEscaladoRec2))
                self.parent().parent().rectangulo2=QRect(beginRectanguloRec2, endRectanguloRec2)
                self.posTextRect2 = beginRectanguloRec2 #utilizo la posicion de inicio del rectangulo para fijar la posicion del texto                
                #*****************************************************
                #********************Roi Recta 1**********************
                beginRecta1PosX = int(self.parent().parent().recta1.x1() * (1+(self.scaleFactor-self.scaleFactorOld)))
                beginRecta1PosY = int(self.parent().parent().recta1.y1() * (1+(self.scaleFactor-self.scaleFactorOld)))
                endRecta1PosX = int(self.parent().parent().recta1.x2() * (1+(self.scaleFactor-self.scaleFactorOld)))
                endRecta1PosY = int(self.parent().parent().recta1.y2() * (1+(self.scaleFactor-self.scaleFactorOld)))
                beginRecta1 = QPoint(beginRecta1PosX, beginRecta1PosY)
                endRecta1 = QPoint(endRecta1PosX, endRecta1PosY)
                self.parent().parent().recta1 = QLine(beginRecta1, endRecta1)
                self.posTextRecta1 = beginRecta1
                #*****************************************************
                #********************Roi Recta 2**********************
                beginRecta2PosX = int(self.parent().parent().recta2.x1() * (1+(self.scaleFactor-self.scaleFactorOld)))
                beginRecta2PosY = int(self.parent().parent().recta2.y1() * (1+(self.scaleFactor-self.scaleFactorOld)))
                endRecta2PosX = int(self.parent().parent().recta2.x2() * (1+(self.scaleFactor-self.scaleFactorOld)))
                endRecta2PosY = int(self.parent().parent().recta2.y2() * (1+(self.scaleFactor-self.scaleFactorOld)))
                beginRecta2 = QPoint(beginRecta2PosX, beginRecta2PosY)
                endRecta2 = QPoint(endRecta2PosX, endRecta2PosY)
                self.parent().parent().recta2 = QLine(beginRecta2, endRecta2)
                self.posTextRecta2 = beginRecta2
                #*****************************************************
                #********************Roi Elipse 1*********************
                xEscaladoElipse1=self.parent().parent().rectanguloEllipse1.x()*(1+(self.scaleFactor-self.scaleFactorOld)) #usamos la escala anterior para calcular la diferencia x
                yEscaladoElipse1=self.parent().parent().rectanguloEllipse1.y()*(1+(self.scaleFactor-self.scaleFactorOld)) #usamos la escala anterior para calcular la diferencia y
                anchoEscaladoElipse1 = self.parent().parent().rectanguloEllipse1.width()*(1+(self.scaleFactor-self.scaleFactorOld)) #idem para calcular la diferencia con ancho alto
                altoEscaladoElipse1 = self.parent().parent().rectanguloEllipse1.height()*(1+(self.scaleFactor-self.scaleFactorOld))
                #
                beginElipse1 = QPoint(int(xEscaladoElipse1),int(yEscaladoElipse1))
                endElipse1 = QPoint(int(xEscaladoElipse1+anchoEscaladoElipse1),int(yEscaladoElipse1+altoEscaladoElipse1))
                self.parent().parent().rectanguloEllipse1=QRect(beginElipse1, endElipse1)
                self.posTextEllipse1 = beginElipse1 #utilizo la posicion de inicio del rectangulo para fijar la posicion del texto                
                #*****************************************************
                #********************Roi Elipse 2*********************
                xEscaladoElipse2=self.parent().parent().rectanguloEllipse2.x()*(1+(self.scaleFactor-self.scaleFactorOld)) #usamos la escala anterior para calcular la diferencia x
                yEscaladoElipse2=self.parent().parent().rectanguloEllipse2.y()*(1+(self.scaleFactor-self.scaleFactorOld)) #usamos la escala anterior para calcular la diferencia y
                anchoEscaladoElipse2 = self.parent().parent().rectanguloEllipse2.width()*(1+(self.scaleFactor-self.scaleFactorOld)) #idem para calcular la diferencia con ancho alto
                altoEscaladoElipse2 = self.parent().parent().rectanguloEllipse2.height()*(1+(self.scaleFactor-self.scaleFactorOld))
                #
                beginElipse2 = QPoint(int(xEscaladoElipse2),int(yEscaladoElipse2))
                endElipse2 = QPoint(int(xEscaladoElipse2+anchoEscaladoElipse2),int(yEscaladoElipse2+altoEscaladoElipse2))
                self.parent().parent().rectanguloEllipse2=QRect(beginElipse2, endElipse2)
                self.posTextEllipse2 = beginElipse2 #utilizo la posicion de inicio del rectangulo para fijar la posicion del texto 
                #
                self.scaleFactorOld = self.scaleFactor                
                self.escalarRois = False #una vez escaladas bajo el flag
                #*************************************************************************************
                #****************Roi *****************************************************

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
            ancho = self.size().width()
            alto = self.size().height()
           
            #calculo resolucion imagen
            self.parent().parent().escalaImagen[0] = ancho
            self.parent().parent().escalaImagen[1] = alto
            
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
            self.escalarRois=True #indico que se modifique la dimension de las rois
        elif self.parent().parent().zoomOutButton == True:
            self.scala = 0.8
            self.escalarRois=True #indico que se modifque la dimension de las rois
        else:
            self.scala = 1
            self.escalarRois=False #indico que no se debe modificar la dimension de las rois
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
                    if self.parent().parent().ellipse1.contains(QPointF(ptoXEllipse, ptoYEllipse)) and self.flagRectEllipse1VsRectEllipse2:
                        #calculo la distrancia entre el punto x-y y el punto clickeado dentro del rectangulo
                        desplazamientoXRecEllip1 = int(self.end.x() - self.posAnteriorRectEllipse1.x())
                        desplazamientoYRecEllip1 = int(self.end.y() - self.posAnteriorRectEllipse1.y())
                        self.parent().parent().rectanguloEllipse1.translate(desplazamientoXRecEllip1, desplazamientoYRecEllip1)
                        x1Ellipse1,y1Ellipse1,x2Ellipse1,y2Ellipse1=self.parent().parent().rectanguloEllipse1.getCoords()
                        self.parent().parent().ellipse1.setRect(QRectF(x1Ellipse1,y1Ellipse1,x2Ellipse1,y2Ellipse1))
                        self.posTextEllipse1 = self.parent().parent().rectanguloEllipse1.topLeft()
                        self.posAnteriorRectEllipse1 = self.end
                        self.begin = self.end
                    #estoy dentro de la elipse 2
                    elif self.parent().parent().ellipse2.contains(QPointF(ptoXEllipse, ptoYEllipse)) and not self.flagRectEllipse1VsRectEllipse2:
                        desplazamientoXRecEllip2 = int(self.end.x() - self.posAnteriorRectEllipse2.x())
                        desplazamientoYRecEllip2 = int(self.end.y() - self.posAnteriorRectEllipse2.y())
                        self.parent().parent().rectanguloEllipse2.translate(desplazamientoXRecEllip2, desplazamientoYRecEllip2)                        
                        x1Ellipse2,y1Ellipse2,x2Ellipse2,y2Ellipse2=self.parent().parent().rectanguloEllipse2.getCoords()
                        self.parent().parent().ellipse2.setRect(QRectF(x1Ellipse2,y1Ellipse2,x2Ellipse2,y2Ellipse2))
                        self.posTextEllipse2 = self.parent().parent().rectanguloEllipse2.topLeft()
                        self.posAnteriorRectEllipse2 = self.end
                        self.begin = self.end
                    else:
                        print("no deberiamos estar aca")
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
        self._decFocusPosition = False
        self._incFocusPosition = False
        self._cancelFocusPosition = False
        self.focusPositionAnterior = 50        
        self._selRango0 = False #flag para seleccionar rango 0 se activa por la funcion y se desactiva por el hilo de run
        self._selRango1 = False #flag para seleccionar rango 1 se actia por la funcion y se desactiva por el hilo de run
        self._selRango2 = False #flag para seleccionar rango 2 se activa por la funcion y se desactiva por el hilo de run        
        self.indiceRangoSeleccionado = 0
        #flag change paleta iron medical etc
        self._changePaleta = False
        #flag change paleta tipo de ajuste manual automatico
        self._changeScalePalette = False
        #flag change rango paleta 
        self._changeRangeScalePaletteManual = False
        #ajustamos la emisividad temp y trans
        self._changeEmisividad = False #flag para sleccionar incrementar o decrementar emisividad
        self._changeTransmisividad = False #flag para incrementar o decrementar transmisividad 
        self._changeTempAmbiente = False #flag para ajustar temperatura ambiente
        #creamos 3 diccionarios uno por cada rango de temp
        #primer rango de temperatura
        self.rango0 = {"min": -20 , "max": 100}
        #segundo rango de temperatura
        self.rango1 = {"min": 0, "max": 250}
        #tercer rango de temperatura
        self.rango2 = {"min": 150 , "max": 900}

        #valor indice paleta
        self.indicePaleta = 1

        #valor indice scala paletas
        self.indiceEscalaPaleta = 1

        #valor rango escala paleta min max en manual
        self.rangoMinMaxScalePaletteManual = {"min": -20, "max":150}

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
        #pathXml = ct.c_char_p(b'C:\Users\lupus\OneDrive\Documentos\ProcesamientoDeImagenes\config\generic.xml')
        pathXml = ct.c_char_p(b'generic.xml')
        # init vars
        pathFormat = ct.c_char_p()      #tipo de formato que usamos para el path a la libreria
        
        
        pathLog = ct.c_char_p(b'logfilename')   #tipo de formato que usamos par ael path al archivo de log

        palette_width = ct.c_int() #dimension de la paleta ..ancho
        palette_height = ct.c_int()  #dimension de la paleta ..alto

        thermal_width = ct.c_int() #dimension de la paleta termica ..ancho
        thermal_height = ct.c_int() #dimension de la paleta termica ..alto

        serial = ct.c_ulong() #numero serial de la camara
        
        #valor de emisividad 
        valorEmisividadCargar = ct.c_float(0.8)

        #valor de transmisividad
        valorTransmisividadCargar = ct.c_float(1)

        #valor de temperatura ambiente
        valorTemperaturaAmbiente = ct.c_float(25)



        #rango de temperaturas
        tRango0_minimoM20 = ct.c_int(self.rango0["min"])#(-20)
        tRango0_maximo100 = ct.c_int(self.rango0["max"])#(100)

        tRango1_minimo0 = ct.c_int(self.rango1["min"])#(0)
        tRango1_maximo250 = ct.c_int(self.rango1["max"])#(250)

        tRango2_minimo150 = ct.c_int(self.rango2["min"])#(150)
        tRango2_maximo900 = ct.c_int(self.rango2["max"])#(900)
        
        
        #posicion de foco
        #focus position
        focusPosition = ct.c_float()
        focusPositionNuevo =ct.c_float()
        
        # init EvoIRFrameMetadata structure
        metadata = EvoIRFrameMetadata() #instanciamos a la clase de EVO cortex la estructura        
        #configuramos los valores iniciales de la camara
        #consultamos si existe archivo de preset camara
        #si existe los leemos 
        # buscamos cada uno de los preset de configuracion
        # 1 -> preset foco 60
        # 2 -> rango 0
        # 3 -> paleta 1
        # 4 -> forma de escalar paleta 1
        # 5 -> cambiar limite minimo y maximo de paleta (solo para forma de escalar manual)
        # 6 -> temperatura ambiente, transmisividad y emisividad
        # los leemos y cargamos las variables del archivo en las variables del programa
        #si no existe el archivo de preset camara
        #creamos el archivo de programa y guardamos en el archivo los valores por default
        #al finalizar bajamos a la camara los valores leidos del archivo o los valores por default
        palabraLeer="si imprimio esto esta mal!"
        #declaro las variables de preset camara
        #preset foco
        presetAGuardar1 = 50
        nombrePreset1 = "presetFococam1"        
        #preset rango
        presetAGuardar2 = 0
        nombrePreset2 = "presetRangocam1"
        #preset paleta
        presetAGuardar3 = 2
        nombrePreset3 = "presetPaletacam1"
        #preset forma de escalar paleta -> 1 Automatico
        presetAGuardar4 = 2
        nombrePreset4 = "presetAjustePaletacam1"
        #preset limite escala manual inferior paleta
        presetAGuardar5 = 0
        nombrePreset5 = "presetAjusteMinEscalaManualPaletacam1"
        #preset limiste escala manual superior paleta
        presetAGuardar6 = 40
        nombrePreset6 = "presetAjusteMaxEscalaManualPaletacam1"
        #preset temperatura ambiente
        presetAGuardar7 = 25
        nombrePreset7 = "presetTempAmbientecam1"
        #preset transimisividad
        presetAGuardar8 = 1 #100% transmisividad
        nombrePreset8 = "presetTransmisividadcam1"
        #preset emisividad
        presetAGuardar9 = 0.8
        nombrePreset9 = "presetEmisividadcam1"
        #lista tuplas preset
        listaPresetsAGuardar = [(nombrePreset1,presetAGuardar1),(nombrePreset2,presetAGuardar2),(nombrePreset3,presetAGuardar3)]
        if os.path.isfile("presetCamera.txt"):
            for nombrePreset,presetAGuardar in listaPresetsAGuardar:            
                with open('presetCamera.txt', 'r') as f:                
                    lines = f.readlines()
                    indiceLines = 0
                    flagEncontrePalabra = False
                    for row in lines:
                        if row.find(nombrePreset) != -1:
                            listaPalabras = row.split()
                            indicePalabraLeer = 0
                            for palabra in listaPalabras:
                                if palabra == '=':
                                    break
                                indicePalabraLeer += 1
                            palabraLeer = listaPalabras[indicePalabraLeer+1]
                            flagEncontrePalabra = True
                if flagEncontrePalabra:
                    #cargamos variable del archivo en variable del programa
                    presetAGuardar = palabraLeer
                    if nombrePreset == nombrePreset1: #foco
                        presetAGuardar1 = int(presetAGuardar)
                    elif nombrePreset == nombrePreset2: #rango
                        presetAGuardar2 = int(presetAGuardar)
                    elif nombrePreset == nombrePreset3: #paleta
                        presetAGuardar3 = int(presetAGuardar)
                    elif nombrePreset == nombrePreset4: #tipo ajuste de paleta
                        presetAGuardar4 = int(presetAGuardar)
                    elif nombrePreset == nombrePreset5: #valor minimo ajuste paleta manual
                        presetAGuardar5 = int(presetAGuardar)
                    elif nombrePreset == nombrePreset6: #valor maximo ajuste paleta manual
                        presetAGuardar6 = int(presetAGuardar)
                    elif nombrePreset == nombrePreset7: #valor temperatura ambiente
                        presetAGuardar7 = int(presetAGuardar)
                    elif nombrePreset == nombrePreset8: #valor transmisividad
                        presetAGuardar8 = float(presetAGuardar)
                    elif nombrePreset == nombrePreset9: #valor emisividad
                        presetAGuardar9 = float(presetAGuardar)
                    else:
                        print("no tengo que estar aca")
                else:
                    #creamos variable del archivo y la cargamos con variable del programa
                    with open('presetCamera.txt', 'a') as f:
                        f.write(nombrePreset + " = " + str(presetAGuardar) + "\n")
        else:
            with open('presetCamera.txt', 'w') as f:
                f.write(nombrePreset1 + " = " + str(presetAGuardar1) + "\n" + nombrePreset2 + " = " + str(presetAGuardar2) + "\n" + nombrePreset3 + " = " + str(presetAGuardar3) + "\n" + nombrePreset4 + " = " + str(presetAGuardar4) + "\n" + nombrePreset5 + " = " + str(presetAGuardar5) + "\n" + nombrePreset6 + " = " + str(presetAGuardar6) + "\n" + nombrePreset7 + " = " + str(presetAGuardar7) + "\n" + nombrePreset8 + " = " + str(presetAGuardar8) + "\n" + nombrePreset9 + " = " + str(presetAGuardar9) + "\n")
                

        print("valor preset foco", palabraLeer)

        while self._run_flag == True:
            # init lib 
            print("iniciando conexion..")
            ret = libir.evo_irimager_usb_init(pathXml, pathFormat, pathLog) #instancio a la libreria de evo para            
            if ret != 0:                                                    #conectar con camara usb de optris
                    statusCamera = [False, "conexion falla"]
                    self.status_camera_signal.emit(np.array(statusCamera))
                    print("fallo conexion!")
                    libir.evo_irimager_terminate() 
                    #exit(ret)                                               #de la camara       
                    time.sleep(10)                    
            else:
                break
        statusCamera = [True, "conexion ok"] #notifico por defecto que la conexion con la camara esta ok si falla el ret cambio el estado
        #notifico que conecto la cámara
        self.status_camera_signal.emit(np.array(statusCamera))
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

        #escribimos en la camara los valores de preset
        #escribimos foco
        self.focusPositionAnterior = presetAGuardar1
        focus = ct.c_float(presetAGuardar1)        
        ret = libir.evo_irimager_set_focusmotor_pos(focus)        
        #escribimos rango
        rango = presetAGuardar2
        if rango == 0:
            ret = libir.evo_irimager_set_temperature_range(tRango0_minimoM20, tRango0_maximo100)
            self.indiceRangoSeleccionado = 0
        elif rango == 1:
            ret = libir.evo_irimager_set_temperature_range(tRango1_minimo0, tRango1_maximo250)
            self.indiceRangoSeleccionado = 1
        elif rango == 2:
            ret = libir.evo_irimager_set_temperature_range(tRango2_minimo150, tRango2_maximo900)
            self.indiceRangoSeleccionado = 2
        else:
            print("no hay rango seleccionado correcto")
        #escribimos paleta
        self.indicePaleta = presetAGuardar3
        paleta = presetAGuardar3
        valorIndicePaleta = ct.c_int(paleta)
        ret = libir.evo_irimager_set_palette(valorIndicePaleta)
        #escribimos forma de escalar paleta
        self.indiceEscalaPaleta = presetAGuardar4
        formaEscalaPaleta = presetAGuardar4        
        valorIndiceScalePalette = ct.c_int(formaEscalaPaleta)
        ret = libir.evo_irimager_set_palette_scale(valorIndiceScalePalette)
        #escribimos limite escala manual inferior y superior paleta
        self.rangoMinMaxScalePaletteManual["min"] = presetAGuardar5
        minimo = presetAGuardar5
        self.rangoMinMaxScalePaletteManual["max"] = presetAGuardar6
        maximo = presetAGuardar6
        valorMinRangoScalePaletteManual = ct.c_float(minimo)
        valorMaxRangoScalePaletteManual = ct.c_float(maximo)                
        ret = libir.evo_irimager_set_palette_manual_temp_range(valorMinRangoScalePaletteManual, valorMaxRangoScalePaletteManual)
        #escribimos emisividad transmisividad y temperatura ambiente
        temperaturaAmbiente = ct.c_float(presetAGuardar7)
        transmisividad = ct.c_float(presetAGuardar8)
        emisividad = ct.c_float(presetAGuardar9)
        ret = libir.evo_irimager_set_radiation_parameters(emisividad ,transmisividad ,temperaturaAmbiente)
        #a partir de aca comenzamos a obtener la imagen        
        while self._run_flag == True: #capturo la imagen mientras no este activa el flag de detener
                #get thermal and palette image with metadat
                ret = libir.evo_irimager_get_thermal_palette_image_metadata(thermal_width, thermal_height, npThermalPointer, palette_width, palette_height, npImagePointer, ct.byref(metadata))
                #obtenemos de evo la imagen, ademas los datos de ancho y algo termico. los datos de imagen ancho y alto. el dato np termico y el dato np de imagen
                #le tenemos que pasar como dato la estructura evo que definimos antes
                
                if ret != 0:
                        print('error on evo_irimager_get_thermal_palette_image ' + str(ret))
                        statusCamera = [False, "fallo la conexion"] #fallo la conexion                        
                        ##
                        self.status_camera_signal.emit(np.array(statusCamera))
                        libir.evo_irimager_terminate() 
                        time.sleep(10) 
                        print("iniciando conexion..")
                        ret = libir.evo_irimager_usb_init(pathXml, pathFormat, pathLog) #instancio a la libreria de evo para            
                        if ret == 0:
                            statusCamera = [True, "conexion ok"] #notifico por defecto que la conexion con la camara esta ok si falla el ret cambio el estado
                            #notifico que conecto la cámara
                            self.status_camera_signal.emit(np.array(statusCamera))
                        continue
                ##
                if self._incFocusPosition: #consultamos si se solicito incrementar la posicion del foco
                    print("incrementar focus position 10%") 
                    #get the focus position
                    ret = libir.evo_irimager_get_focusmotor_pos(ct.byref(focusPosition)) #consultamos la posicion del foco actual
                    print('focus: ' + str(focusPosition.value))                             #mostamos la posicion actual
                    focusPositionNuevo = ct.c_float(self.focusPositionAnterior + 10)        #incrementamos la posicion anterior
                    focusPositionNuevoCrudo = self.focusPositionAnterior + 10               #seteamos la posicion actual
                    print("nuevo focus: {}".format(focusPositionNuevo.value) )              #mostramos la nueva posicion en formato c
                    ret = libir.evo_irimager_set_focusmotor_pos(focusPositionNuevo)#(pos=ct.c_float(55.5)) cargamos la posicion nueva en la camara en el formato c
                    self.focusPositionAnterior = focusPositionNuevoCrudo                    #actualizamos la posicion anterior
                    self._incFocusPosition = False                                          #deshabilitamos el flag para incrementar la posicion del foco
                    if ret != 0:                                                            #de haber algun error en el proceso de escritura salimos del loop de adquisicion
                        print('error on evo_irimager_get_thermal_palette_image ' + str(ret))#notificamos el error
                        break
                if self._decFocusPosition: #consultamos si se solicito decrementar la posicion del foco
                    print("decrementar focus position 10%")
                    #get the focus position
                    ret = libir.evo_irimager_get_focusmotor_pos(ct.byref(focusPosition)) #consultamos la posicion del foco actual
                    print('focus: ' + str(focusPosition.value))                         #mostramos la posicion actual
                    focusPositionNuevo = ct.c_float(self.focusPositionAnterior - 10)    #generamos la nueva position del foco decrementando la anterior en el formato c
                    focusPositionNuevoCrudo = self.focusPositionAnterior - 10           #guardamos en el registro la nueva position
                    print("nuevo focus: {}".format(focusPositionNuevo.value) )          #mostramos la nueva posicion del foco accediendo a la posicion en formato c
                    ret = libir.evo_irimager_set_focusmotor_pos(focusPositionNuevo)#(pos=ct.c_float(55.5)) cargamos la posicion nueva en la camara en el formato c
                    self.focusPositionAnterior = focusPositionNuevoCrudo                #actualizamos la posicion anterior de foco
                    self._decFocusPosition = False                                      #deshabilitamos el flag de decrementar posicion 
                    if ret != 0:                                                        #de haber algun error en el proceso de decrementar lo notificamos y salimos del loop
                        print('error on evo_irimager_get_thermal_palette_image ' + str(ret))
                        break
                if self._cancelFocusPosition:
                    focusPositionReset = ct.c_float(self.focusPositionAnterior)
                    ret = libir.evo_irimager_set_focusmotor_pos(focusPositionReset)
                    self._cancelFocusPosition = False
                if self._selRango0: #consultamos si se solicito cambiar el rango de temperatura 0
                    print("Cambiamos a rango de temperatura 0")
                    self._selRango0 = False #bajamos el flag despues de realizar el cambio de rango
                    ret = libir.evo_irimager_set_temperature_range(tRango0_minimoM20, tRango0_maximo100)
                    self.indiceRangoSeleccionado = 0
                    if ret != 0:
                        print("error on evo_irimager_set_temperature_range" + str(ret))
                        break
                if self._selRango1: #consultamos si se solicito cambiar al rango de temperatura 1
                    print("Cambiamos al rango de temperatura 1")
                    self._selRango1 = False #bajamos el flag despues de realizar el cambio de rango
                    ret = libir.evo_irimager_set_temperature_range(tRango1_minimo0, tRango1_maximo250)
                    self.indiceRangoSeleccionado = 1
                    if ret != 0:
                        print("error on evo_irimager_set_temperature_range" + str(ret))
                        break                
                if self._selRango2: #consultamos si se solicito cambiar al rango de temperatura 2
                    print("Cambiamos al rango de temperatura 2")
                    self._selRango2 = False #bajamos el flag despues de realizar el cambio de rango
                    ret = libir.evo_irimager_set_temperature_range(tRango2_minimo150, tRango2_maximo900)
                    self.indiceRangoSeleccionado = 2
                    if ret != 0:
                        print("error on evo_irimager_set_temperature_range" + str(ret))
                        break  
                if self._changePaleta: #consultamos si se solicito cambiar la paleta
                    print("cambiamos paleta: {}".format(self.indicePaleta))
                    self._changePaleta = False
                    valorIndicePaleta = ct.c_int(self.indicePaleta)
                    ret = libir.evo_irimager_set_palette(valorIndicePaleta)
                    if ret != 0:
                        print("error on evo_irimager_set_palette" + str(ret))
                        break
                if self._changeScalePalette: #consultamos si se solicito cambiar el tipo de escala de la paleta
                    print("se cambia el tipo de escala de la paleta: {}".format(self.indiceEscalaPaleta))
                    self._changeScalePalette = False
                    valorIndiceScalePalette = ct.c_int(self.indiceEscalaPaleta)
                    ret = libir.evo_irimager_set_palette_scale(valorIndiceScalePalette)
                    if ret != 0:
                        print("error on evo_irimager_set_palette_scale" + str(ret))
                        break
                if self._changeRangeScalePaletteManual:
                    minimoRango = float(self.rangoMinMaxScalePaletteManual["min"])
                    maximoRango = float(self.rangoMinMaxScalePaletteManual["max"])
                    print("se cambia el rango de la paleta para escala manual min:{} y max:{}".format(minimoRango, maximoRango))
                    self._changeRangeScalePaletteManual = False
                    valorMinRangoScalePaletteManual = ct.c_float(minimoRango)
                    valorMaxRangoScalePaletteManual = ct.c_float(maximoRango)                
                    ret = libir.evo_irimager_set_palette_manual_temp_range(valorMinRangoScalePaletteManual, valorMaxRangoScalePaletteManual)
                    if ret != 0:
                        print("error on evo_irimage_set_palette_manual_temp_range" + str(ret))
                        break
                if self._changeTempAmbiente: #consultamos si se solicito cambiar el valor de temperatura ambiente
                    print("cambiamos la temperatura ambiente {}".format(self.tempAmbiente)) #mostramos el valor de temperatura ambiente cargado
                    valorTemperaturaAmbiente = ct.c_float(self.tempAmbiente)
                    ret = libir.evo_irimager_set_radiation_parameters(valorEmisividadCargar ,valorTransmisividadCargar ,valorTemperaturaAmbiente)
                    self._changeTempAmbiente = False #bajamos el flag de cambio del parametro temp ambiente
                    if ret != 0:
                        print("error on evo_irimager_set_radiation_parameters" + str(ret))
                        break            
                if self._changeTransmisividad: #consultamos si se solicito cambiar el valor de transmisividad ambiente
                    print("cambiamos la transmisividad ambiente {}".format(self.transmisividad)) #mostramos el valor de transmisividad ambiente cargado
                    valorTransmisividadCargar = ct.c_float(self.transmisividad)
                    ret = libir.evo_irimager_set_radiation_parameters(valorEmisividadCargar ,valorTransmisividadCargar ,valorTemperaturaAmbiente)
                    self._changeTransmisividad = False #bajamos el flag de cambio del parametro temp ambiente
                    if ret != 0:
                        print("error on evo_irimager_set_radiation_parameters" + str(ret))
                        break
                if self._changeEmisividad: #consultamos si se solicito cambiar el valor de transmisividad ambiente
                    print("cambiamos la emisividad ambiente {}".format(self.emisividad)) #mostramos el valor de transmisividad ambiente cargado
                    valorEmisividadCargar = ct.c_float(self.emisividad)
                    ret = libir.evo_irimager_set_radiation_parameters(valorEmisividadCargar ,valorTransmisividadCargar ,valorTemperaturaAmbiente)
                    self._changeEmisividad = False #bajamos el flag de cambio del parametro temp ambiente
                    if ret != 0:
                        print("error on evo_irimager_set_radiation_parameters" + str(ret))
                        break
                                                 #si hay error salgo y retorno el error
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
    
    def incFocusPosition(self):
        #decrementamos en 5% focus position
        self._incFocusPosition = True

    def decFocusPosition(self):
        self._decFocusPosition = True
    
    def changeRange0(self):
        #seleccionamos cambiar al rango 0
        print("selccionar cambiar al rango 0")
        self._selRango0 = True
    
    def changeRange1(self):
        #selccionamos cambiar al rango 1
        print("seleccionar cambiar al rango 1")
        self._selRango1 = True

    def changeRange2(self):
        #seleccionamos cambiar al rango 2
        print("selecionamos cambiar al rango 2")
        self._selRango2 = True
    
    def selPaleta(self, EnumOptrisColoringPalette):
        print("nueva seleccion de paleta: {}".format(EnumOptrisColoringPalette))
        self._changePaleta = True
        self.indicePaleta = EnumOptrisColoringPalette
    
    def selScalePaleta(self, EnumOptrisPaletteScalingMethod):
        print("nueva seleccion escala de paleta valor: {}".format(EnumOptrisPaletteScalingMethod))
        self._changeScalePalette = True
        self.indiceEscalaPaleta = EnumOptrisPaletteScalingMethod

    def selRangeTempManual(self, valueMinRange, valueMaxRange):
        print("nueva seleccion rango min: {} y rango max: {}".format(valueMinRange, valueMaxRange))
        self._changeRangeScalePaletteManual = True
        self.rangoMinMaxScalePaletteManual["min"] = valueMinRange
        self.rangoMinMaxScalePaletteManual["max"] = valueMaxRange

    def incDecEmisividad(self, valorEmisividad):
        print("nuevo valor para cargar de emisividad {}".format(valorEmisividad))
        self.emisividad = valorEmisividad
        self._changeEmisividad = True

    def incDecTransmisividad(self, valorTransmisividad): #metodo para incrementar o decrementar la transmisividad, le pasamos el valor deseado de transmisividad ambiente
        print("nuevo valor para cargar de transmisividad ambiente {}".format(valorTransmisividad)) #mostramos el valor pasado
        self.transmisividad = valorTransmisividad #cargamos el valor de transmisividad
        self._changeTransmisividad = True           #indicamos que realice la carga en el loop de procesamiento

    def incDecTempAmbiente(self, valorTempAmbiente): #metodo para incrementar o decrementar la temp ambiente, le pasamos el valor deseado de temperatura ambiente
        print("nuevo valor para cargar de temperatura ambiente {}".format(valorTempAmbiente))        
        self.tempAmbiente = valorTempAmbiente
        self._changeTempAmbiente = True
    
    def getFocusPosition(self):
        print("consulto posicion del foco")
        currentFocusPosition = self.focusPositionAnterior
        return currentFocusPosition
    def cancelFocusPosition(self, posicionAnterior):
        print("reseteo a la posicion de foco anterior a comenzar el ajuste")
        self.focusPositionAnterior = int(posicionAnterior)
        self._cancelFocusPosition = True

    def getRange(self):
        print("consulto rango actual")
        return self.indiceRangoSeleccionado
    
    def getManAuto(self):
        print("consulto manual automatico actual")
        return self.indiceEscalaPaleta
    
    def getTipoPaleta(self):
        print("consulto tipo de paleta")
        return self.indicePaleta
    
    def getMinMaxPaletaManual(self):
        print("consulto min max rango manual paleta")
        rangoMinMaxPaletaManual=(self.rangoMinMaxScalePaletteManual["min"],self.rangoMinMaxScalePaletteManual["max"])
        return rangoMinMaxPaletaManual
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
#funcionalidad que tenga la pantalla (tab) reset control tipo volumen
class PopUpResetPresetTab(QWidget):
    def __init__(self, nombrePreset, valorPreset):
        super().__init__()
        self.valorNombreMedicion = nombrePreset
        self.valorPresetMedicion = valorPreset
        self.setWindowTitle("Reset Preset of Control")
        #aca va la funcionalidad del graficador con el control
        layoutPresetCurrentResetTab = QVBoxLayout()
        #valor de preset actual
        self.labelCurrentPresetTab = QLabel("Current Control Tab")
        valorPresetActual = self.valorPresetMedicion.text()
        self.valueCurrentPresetTab = QLineEdit(valorPresetActual) #este valor es el preset actual
        self.valueCurrentPresetTab.setStyleSheet("border: 2px solid black; background-color : lightgray;")        
        self.labelCurrentPresetTab.setBuddy(self.valueCurrentPresetTab)
        #valor de preset a cambiar
        self.labelDefaultPresetTab = QLabel("Default Control Tab")
        self.valueDefaultPresetTab = QLineEdit("24") #este valor hardcodeado es el de default y se baja a disco si se de actualizar
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
        #cargo en el preset el valor por default 
        #vamos a reemplazar esta parte por la lectura del 
        #archivo de configuracion
        if os.path.isfile("preset.txt"):
            with open("preset.txt", "r") as f:
                presetAGuardar = self.valueDefaultPresetTab.text()#self.valorNombreMedicion.text()
                nombrePreset = self.valorNombreMedicion
                lines = f.readlines()
                indiceLineas = 0
                flagEncontrePalabra = False
                for row in lines:
                    if row.find(nombrePreset) != -1:
                        listaPalabras = row.split()
                        indicePalabraReemplazar = 0
                        for palabras in listaPalabras:
                            if palabras == "=":
                                #se encontro
                                break
                            indicePalabraReemplazar += 1
                        palabraReemplazar = listaPalabras[indicePalabraReemplazar:]
                        filaOriginal = row
                        row = row.replace(palabraReemplazar[1]+"\n",presetAGuardar+"\n")
                        filaAReemplazar = row
                        flagEncontrePalabra = True
                        break
                    indiceLineas += 1
            if flagEncontrePalabra:
                with open("preset.txt","r") as f:
                    textoCompleto = f.read()
                with open("preset.txt", "w") as f:
                    textoCompleto = textoCompleto.replace(filaOriginal, filaAReemplazar)
                    f.write(textoCompleto)
            else:
                with open("preset.txt","a") as f:
                    f.write(nombrePreset + " = " + presetAGuardar + "\n")
        else:
            with open("preset.txt", "w") as f:
                presetAGuardar = self.valueDefaultPresetTab.text()
                nombrePreset = self.valorNombreMedicion
                f.write(nombrePreset + " = " + presetAGuardar + "\n")
        #lo cargo en la variable que lleva el preset
        self.valorPresetMedicion.setText("24") 
        print("Update default value al disco")
        self.close()
    def cancelUpDatePresetTab(self):
        print("Cancelar default value al disco")
        self.close()

#Clase modelo generico de preset control del tipo volumen
class PopUpWritePresetTab(QWidget):
    def __init__(self, valorLabelIndicador, valorPreset):
        super().__init__()
        self.valorNombreMedicion = valorLabelIndicador
        self.valorPresetMedicion = valorPreset        
        self.setWindowTitle("Write Preset of Control")
        layoutPresetCurrentNew = QVBoxLayout()
        #grafico powerbar
        self.volumenCtrl = PowerBar(["#5e4fa2","#3288bd","#66c2a5","#abdda4","#e6f598"])
        #
        layoutPresetCurrentNew.addWidget(self.volumenCtrl)
        #
        presetCurrent="0"
        if os.path.isfile("preset.txt"):
            with open("preset.txt","r") as f:
                nombrePresetCurrent=self.valorNombreMedicion
                linesCurrent = f.readlines()
                for row in linesCurrent:
                    if row.find(nombrePresetCurrent) != -1:
                        listaPalabrasCurrent = row.split()    
                        indicePalabraPreset = 0
                        for palabrasCurrent in listaPalabrasCurrent:
                            if palabrasCurrent == "=":
                                break
                            indicePalabraPreset += 1
                        presetCurrent = listaPalabrasCurrent[indicePalabraPreset+1]
                        break
        textoPreset = QLabel("current preset ")
        valorCurrentPreset = QLabel()
        valorCurrentPreset.setText(presetCurrent)
        layoutPresetCurrent = QHBoxLayout()
        layoutPresetCurrent.addWidget(textoPreset)
        layoutPresetCurrent.addWidget(valorCurrentPreset)
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
        layoutPresetCurrentNew.addLayout(layoutPresetCurrent)
        layoutPresetCurrentNew.addLayout(layoutPresetCurrentNewBotones)      
        #
        self.setLayout(layoutPresetCurrentNew)
        self.resize(400,20)
        self.okNewPreset.setFocus(Qt.NoFocusReason)
    def okUpDatePresetCtrl(self):
        print("Bajando preset a camara")
        #verifico si el valor es menor al preset si lo es cambiar el color de fondo
        print(self.volumenCtrl.valorQDial.text())
        #cargo el valor en el preset de alarma de medicion
        self.valorPresetMedicion.setText(self.volumenCtrl.valorQDial.text())
        if os.path.isfile("preset.txt"):
            with open('preset.txt','r') as f:                
                presetAGuardar = self.valorPresetMedicion.text()
                nombrePreset = self.valorNombreMedicion
                #f.write(nombrePreset + "=" +presetAGuardar+"\n")                
                lines=f.readlines() #separo las lineas
                indiceLineas = 0
                flagEncontrePalabra = False
                print("las lineas son:\n",lines)
                for row in lines:
                    if row.find(nombrePreset) != -1:
                        listaPalabras=row.split() #divido en palabras la fila
                        indicePalabraReemplazar = 0 
                        for palabras in listaPalabras: #buscamos la palabra "="                            
                            if palabras == "=": 
                                #indice encontrado salgo del for con el indice                               
                                break
                            indicePalabraReemplazar += 1 
                        #encuentro la palabra a reemplazar, que es la que esta despues del =
                        palabraReemplazar = listaPalabras[indicePalabraReemplazar:] 
                        print("palabra a reemplazar = ", palabraReemplazar[1]) 
                        filaOriginal = row                      
                        row = row.replace(palabraReemplazar[1]+"\n",presetAGuardar+"\n") #reemplazo en la fila el preset viejo por el nuevo
                        print("fila a reemplazar = ", row)
                        filaAReemplazar = row #texto completo a reemplazar
                        flagEncontrePalabra = True
                        break
                    indiceLineas += 1
            if flagEncontrePalabra:
                with open('preset.txt', 'r') as f:
                    textoCompleto = f.read() 
                with open('preset.txt','w') as f:                     
                    print("fila original = ", filaOriginal)              
                    print("fila reeplazada = ", filaAReemplazar)
                    textoCompleto = textoCompleto.replace(filaOriginal,filaAReemplazar)
                    f.write(textoCompleto)
            else:
                with open('preset.txt', 'a') as f:                    
                    f.write(nombrePreset + " = " +presetAGuardar+"\n") 
        else:
            with open('preset.txt','w') as f:
                presetAGuardar = self.valorPresetMedicion.text()
                nombrePreset = self.valorNombreMedicion
                f.write(nombrePreset + " = " + presetAGuardar + "\n")
        print("Update preset a disco")
        self.close()
        #if float(self.valorIndicadorMedicion.text()) > int(self.volumenCtrl.valorQDial.text()):
        #    self.valorIndicadorMedicion.setStyleSheet("border: 2px solid black;border-radius: 4px;padding: 2px; text-align:center; background-color: red;")            
        #else:
        #    self.valorIndicadorMedicion.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
    def cancelUpDatePresetCtrl(self):
        print("Cancelar preset a disco")
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
class PopUPWritePresetFocoCam(QWidget):
    def __init__(self, miThreadAdqImagen, imageAdq, nameCamera):
        super().__init__() 
        #cargo nombre preset
        self.valorNombreMedicion = "presetFoco" + nameCamera 
        #cargo valor default preset
        self.valorPresetMedicion = "0"
        #self cerrar ventana y dejar de pasar datos
        self.flagDetenerStriming = False       
        #instancia hilo
        self.threadAdqImg = miThreadAdqImagen
        self.incSelection = False
        self.setWindowTitle("Write Preset Focus Of Camera")
        layoutPresetCurrentNew = QVBoxLayout()
        #set para la imagen
        self.display_width = 640
        self.display_height = 480
        #creamos el label que va a contener la imagen
        self.image_label_changeFocusPosition = QLabel(self)
        self.imagenCamara = imageAdq.pixmap()
        self.image_label_changeFocusPosition.setPixmap(self.imagenCamara)
        self.image_label_changeFocusPosition.resize(self.display_width, self.display_height)
        #creamos los botones para controla la posicion del foco
        layoutBotonesFoco = QHBoxLayout()
        #primero creamos el boton de cambiar foco
        self.btnIncDecFocusPosition = QPushButton("Change Focus")
        self.btnIncDecFocusPosition.clicked.connect(self.btnIncDecFocusPositionState)
        #seleccionar incrementar o decrementar foco position
        self.radioButtonIncDecFocPos = QRadioButton(self)
        self.radioButtonIncDecFocPos.setText("Inc/Dec")
        self.radioButtonIncDecFocPos.clicked.connect(self.checkRadioButton)
        #agrego los botones al layout horizontal
        layoutBotonesFoco.addWidget(self.btnIncDecFocusPosition)
        layoutBotonesFoco.addWidget(self.radioButtonIncDecFocPos)
        #valor de preset actual
        self.labelCurrentPreset = QLabel("Current Preset")
        self.currentPositionFoco = str(self.threadAdqImg.getFocusPosition())
        self.valueCurrentPreset = QLineEdit(self.currentPositionFoco)
        self.valueCurrentPreset.setStyleSheet("border: 2px solid black; background-color : lightgray;")        
        self.labelCurrentPreset.setBuddy(self.valueCurrentPreset)
        #valor de preset a cambiar
        self.labelNewPreset = QLabel("New Preset")
        self.valueNewPreset = QLineEdit("....")
        self.valueNewPreset.setStyleSheet("border: 2px solid black;")
        self.labelNewPreset.setBuddy(self.valueNewPreset)
        #agrego los dos widgets al layout
        layoutPresetCurrentNew.addWidget(self.image_label_changeFocusPosition)
        layoutPresetCurrentNew.addLayout(layoutBotonesFoco)
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
    
    def upDateImage(self, imageAdq):
        imagenCamaraUpDate = imageAdq.pixmap()
        self.image_label_changeFocusPosition.setPixmap(imagenCamaraUpDate)        
        return self.flagDetenerStriming

    def okUpDatePresetCam(self):
        print("Bajando preset a camara")
        self.valorPresetMedicion = str(self.threadAdqImg.getFocusPosition())
        print("%s = %s" % (self.valorNombreMedicion,self.valorPresetMedicion))
        #guardo en disco el nombre del preset y el valor del preset 
        #verifico si existe el archivo si no existe lo creo y cargo los datos
        #si existe el arvhico verifico si el dato existe si no existe lo agrego al archivo
        #si existe los reemplazo por el dato nuevo
        if os.path.isfile("presetCamera.txt"):
            with open('presetCamera.txt', 'r') as f:
                presetAGuardar = self.valorPresetMedicion
                nombrePreset = self.valorNombreMedicion
                lines = f.readlines()
                indiceLineas = 0
                flagEncontrePalabra = False
                for row in lines:
                    if row.find(nombrePreset) != -1:
                        listaPalabras = row.split()
                        indicePalabraReemplazar = 0
                        for palabras in listaPalabras:
                            if palabras == "=":
                                break
                            indicePalabraReemplazar += 1
                        palabraReemplazar = listaPalabras[indicePalabraReemplazar:]
                        filaOriginal = row
                        row = row.replace(palabraReemplazar[1]+"\n", presetAGuardar+"\n")
                        filaAReemplazar = row
                        flagEncontrePalabra = True
                        break
                    indiceLineas += 1
            if flagEncontrePalabra:
                with open('presetCamera.txt', 'r') as f:
                    textoCompleto = f.read()
                with open('presetCamera.txt', 'w') as f:
                    textoCompleto = textoCompleto.replace(filaOriginal, filaAReemplazar)
                    f.write(textoCompleto)
            else:
                with open('presetCamera.txt', 'a') as f:
                    f.write(nombrePreset + " = " + presetAGuardar + "\n")
        else:
            with open('presetCamera.txt', 'w') as f:
                presetAGuardar = self.valorPresetMedicion
                nombrePreset = self.valorNombreMedicion
                f.write(nombrePreset + " = " + presetAGuardar + "\n")
        print("Update preset cam a disco")

                                
        #cierro la popup y detengo el streaming
        self.flagDetenerStriming = True

    
    def cancelUpDatePresetCam(self):
        print("Cancelar preset a camara")
        self.threadAdqImg.cancelFocusPosition(self.currentPositionFoco)
        self.flagDetenerStriming = True        

    def cerrarPopup(self):
        self.close()

    def btnIncDecFocusPositionState(self):
        print("boton des presionado, ejecutamos la funcion de incrementar decrementar")
        self.incDecFocusPosition()      #llamo a la funcion que determina si se debe incrementar o decrementar la posicion del foco

    def incDecFocusPosition(self):
        if self.incSelection:
            print("Llamo a funcion incrementar focus position el hilo de adq")
            self.threadAdqImg.incFocusPosition()
            time.sleep(2)
            posicionFocoActual = str(self.threadAdqImg.getFocusPosition())
            self.valueNewPreset.setText(posicionFocoActual)
        else:
            print("Llamo a funcion decrementar focus position al hilo de adq")
            self.threadAdqImg.decFocusPosition()
            time.sleep(2) #demo el proceso 2 segundos esperando que cambie el foco
            #leemos la posicion del foco
            posicionFocoActual = str(self.threadAdqImg.getFocusPosition())
            self.valueNewPreset.setText(posicionFocoActual)

    def checkRadioButton(self):
        if self.radioButtonIncDecFocPos.isChecked():
            print("seleccion incrementar")
            self.incSelection = True
        else:
            print("seleccion decrementar")
            self.incSelection = False

#clase cambio de rango de temperatura
class PopUpWritePresetTempRangeCam(QWidget):
    def __init__(self, miThreadAdqImagen, imageAdq, nameCamera):
        super().__init__()
        #cargo nombre preset
        self.valorNombreMedicion = "presetRango" + nameCamera
        #cargo valor default preset
        self.valorPresetMedicion = 0
        #realizamos configuracion de pantalla        
        print("aca realizamos la configuracion de pantalla")
        #flag ára cerrar ventana y dejar de pasar datos
        self.flagDetenerStriming = False
        #instancia Hilo
        self.threadAdqImg = miThreadAdqImagen
        self.setWindowTitle("Write Preset Range of Camera")
        layoutPresetCurrentNew = QVBoxLayout()
        #set para la imagen
        self.display_width = 640
        self.display_height = 480
        #creamos el label que va a contener la imagen
        self.image_label_changeRange = QLabel()
        self.imagenCamara = imageAdq.pixmap()
        self.image_label_changeRange.setPixmap(self.imagenCamara)
        self.image_label_changeRange.resize(self.display_width,self.display_height)
        #creamos los botones para controlar el rango
        layoutBotonesRango = QHBoxLayout()
        #primero el rango 0
        self.btnRango0Cam = QPushButton("Rango 0")
        self.btnRango0Cam.clicked.connect(self.btnRango0Camara)
        #luego el rango1
        self.btnRango1Cam = QPushButton("Rango 1")
        self.btnRango1Cam.clicked.connect(self.btnRango1Camara)
        #finalmente el rango 2
        self.btnRango2Cam = QPushButton("Rango 2")
        self.btnRango2Cam.clicked.connect(self.btnRango2Camara)
        #agregamos los botones al layout
        layoutBotonesRango.addWidget(self.btnRango0Cam)
        layoutBotonesRango.addWidget(self.btnRango1Cam)
        layoutBotonesRango.addWidget(self.btnRango2Cam)
        #valor de preset actual
        self.labelCurrentPreset = QLabel("Current Preset")
        #solicito el valor actual
        self.rango = self.threadAdqImg.getRange()
        rangoSeleccionado = "..."
        if self.rango == 0:
            rangoSeleccionado = "-20 a 100"
        elif self.rango == 1:
            rangoSeleccionado = "0 a 250"
        elif self.rango == 2:
            rangoSeleccionado = "150 a 900"
        self.valueCurrentPreset = QLineEdit(rangoSeleccionado)        
        self.valueCurrentPreset.setStyleSheet("border: 2px solid black; background-color : lightgray;")        
        self.labelCurrentPreset.setBuddy(self.valueCurrentPreset)
        #valor de preset a cambiar
        self.labelNewPreset = QLabel("New Preset")
        self.valueNewPreset = QLineEdit("....")
        self.valueNewPreset.setStyleSheet("border: 2px solid black;")
        self.labelNewPreset.setBuddy(self.valueNewPreset)
        #agrego los dos widgets al layout
        layoutPresetCurrentNew.addWidget(self.image_label_changeRange)
        layoutPresetCurrentNew.addLayout(layoutBotonesRango)
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

    def upDateImage(self, imageAdq):
        #realizamos la actualizacion de la imagen con los parametros de rango de temperatura cambiados
        #print("aca realizmaos la configuracion de rango de temperatura")
        imagenCamaraUpDate = imageAdq.pixmap()
        self.image_label_changeRange.setPixmap(imagenCamaraUpDate)        
        return self.flagDetenerStriming

    def okUpDatePresetCam(self):
        #realizamos la aceptación de los cambios
        print("aca realizamos la aceptacion de los cambios en los rangos de temperatura")
        rangoActualGuardar = self.threadAdqImg.getRange()
        print("rango a actualizar: ", rangoActualGuardar)
        if os.path.isfile("presetCamera.txt"):
            with open('presetCamera.txt', 'r') as f:
                presetAGuardar = str(rangoActualGuardar)
                nombrePreset = self.valorNombreMedicion
                lines = f.readlines()
                indiceLineas = 0
                flagEncontrePalabra = False
                for row in lines:
                    if row.find(nombrePreset) != -1:
                        listaPalabras = row.split()
                        indicePalabraReemplazar = 0
                        for palabras in listaPalabras:
                            if palabras == '=':
                                break
                            indicePalabraReemplazar += 1
                        palabraReemplazar = listaPalabras[indicePalabraReemplazar:]
                        filaOriginal = row
                        row = row.replace(palabraReemplazar[1]+"\n", presetAGuardar+"\n")
                        filaAReemplazar = row
                        flagEncontrePalabra = True
                        break
                    indiceLineas += 1
            if flagEncontrePalabra:
                with open('presetCamera.txt', 'r') as f:
                    textoCompleto = f.read()
                with open('presetCamera.txt', 'w') as f:
                    textoCompleto = textoCompleto.replace(filaOriginal, filaAReemplazar)
                    f.write(textoCompleto)
            else:
                with open('presetCamera.txt', 'a') as f:
                    f.write(nombrePreset + " = " + presetAGuardar + "\n")
        else:
            with open('presetCamera.txt', 'w') as f:
                presetAGuardar = rangoActualGuardar
                nombrePreset = self.valorNombreMedicion
                f.write(nombrePreset + " = " + presetAGuardar + "\n")
        print("update preset cam a disco")
        self.flagDetenerStriming = True

    def cancelUpDatePresetCam(self):
        #realizamos la cancelacion de los cambio solicitados
        print("Cancelar preset a camara bajo valor anterior")
        if self.rango == 0:            
            self.threadAdqImg.changeRange0()
        elif self.rango == 1:
            self.threadAdqImg.changeRange1()
        elif self.rango == 2:
            self.threadAdqImg.changeRange2()
        self.flagDetenerStriming = True 

    def cerrarPopup(self):
        self.close()

    def btnRango0Camara(self):
        #seleccionamos el rango 0
        print("aca realizamos la seleccion del rnago 0")
        self.valueNewPreset.setText("-20 a 100")
        self.threadAdqImg.changeRange0()

    def btnRango1Camara(self):
        #seleccionamos el rango 1
        print("aca realizamos la seleccion del rango 1")
        self.valueNewPreset.setText("0 a 250")
        self.threadAdqImg.changeRange1()

    def btnRango2Camara(self):
        #seleccionamos el rango 2
        print("aca realizamos la seleccion del rango 2")
        self.valueNewPreset.setText("150 a 900")
        self.threadAdqImg.changeRange2()

#clase cambio de tipo de paleta utilizada en camara
class PopUpWritePresetPalleteCam(QWidget):
    def __init__(self, miThreadAdqImagen, imageAdq, nameCamera):
        super().__init__()
        #cargo nombre preset
        self.valorNombreMedicion = "presetPaleta" + nameCamera
        #cargo valor default preset
        self.valorPresetMedicion = 2
        #realizamos la configuracion de pantalla
        print("aca realizamos la configuracion de pantalla para paleta de la camara")
        #flag para cerrar vetanta y dejar de stremear imagen
        self.flagDetenerStriming = False
        #instanacia de hilo
        self.threadAdqImg = miThreadAdqImagen
        self.setWindowTitle("Write Preset Pallete Cam")
        layoutPresetCurrentNew = QVBoxLayout()
        #set para la imagen
        self.display_width = 640
        self.display_height = 480
        #creamos el alabel que va a contener la imagen
        self.image_label_changePallete = QLabel()
        self.imageCamara = imageAdq.pixmap()
        self.image_label_changePallete.setPixmap(self.imageCamara)
        self.image_label_changePallete.resize(self.display_width,self.display_height)
        #creamos los botones para controlar la paleta        
        layoutBotonesPallete = QGridLayout()
        #creamos los botones
        btnSelAlarmBluePallete = QPushButton("eAlarmBlue")
        btnSelAlarmBluePallete.clicked.connect(self.selPaletaAlarmBlue)
        #
        btnSelAlarmBlueHiPallete = QPushButton("eAlarmBlueHi")
        btnSelAlarmBlueHiPallete.clicked.connect(self.selPaletaAlarmBlueHi)
        #
        btnSelAlarmGrayBWPallete = QPushButton("eGrayBW")
        btnSelAlarmGrayBWPallete.clicked.connect(self.selPaletaGrayBW)
        #
        btnSelAlarmGrayWBPallete = QPushButton("eGrayWB")
        btnSelAlarmGrayWBPallete.clicked.connect(self.selPaletaGrayWB)
        #
        btnSelAlarmGreenPallete = QPushButton("eAlarmGreen")
        btnSelAlarmGreenPallete.clicked.connect(self.selPaletaAlarmGreen)
        #
        btnSelAlarmIronPallete = QPushButton("eIron")
        btnSelAlarmIronPallete.clicked.connect(self.selPaletaIron)
        #
        btnSelAlarmIronHiPallete = QPushButton("eIronHi")
        btnSelAlarmIronHiPallete.clicked.connect(self.selPaletaIronHi)
        #
        btnSelAlarmMedicalPallete = QPushButton("eMedical")
        btnSelAlarmMedicalPallete.clicked.connect(self.selPaletaMedical)
        #
        btnSelAlarmRainbowPallete = QPushButton("eRainbow")
        btnSelAlarmRainbowPallete.clicked.connect(self.selPaletaRainbow)
        #
        btnSelAlarmRainbowHiPallete = QPushButton("eRainbowHi")
        btnSelAlarmRainbowHiPallete.clicked.connect(self.selPaletaRainbowHi)
        #
        btnSelAlarmRedPallete = QPushButton("eRed")
        btnSelAlarmRedPallete.clicked.connect(self.selPaletaAlarmRed)
        #agregamos los botones al layoute
        layoutBotonesPallete.addWidget(btnSelAlarmBluePallete, 0, 0)        
        layoutBotonesPallete.addWidget(btnSelAlarmBlueHiPallete, 0, 1)        
        layoutBotonesPallete.addWidget(btnSelAlarmGrayBWPallete, 0, 2)        
        layoutBotonesPallete.addWidget(btnSelAlarmGrayWBPallete, 1, 0)
        layoutBotonesPallete.addWidget(btnSelAlarmGreenPallete, 1, 1)
        layoutBotonesPallete.addWidget(btnSelAlarmIronPallete, 1, 2)
        layoutBotonesPallete.addWidget(btnSelAlarmIronHiPallete, 2, 0)
        layoutBotonesPallete.addWidget(btnSelAlarmMedicalPallete, 2, 1)
        layoutBotonesPallete.addWidget(btnSelAlarmRainbowPallete, 2, 2)
        layoutBotonesPallete.addWidget(btnSelAlarmRainbowHiPallete, 3, 0)
        layoutBotonesPallete.addWidget(btnSelAlarmRedPallete, 3, 1)
        layoutBotonesPallete.addWidget(btnSelAlarmRedPallete, 3, 2)                
        #agregamos lo botones de preset actual y cambiado
        #valor de preset actual
        self.labelCurrentPreset = QLabel("Current Preset")
        #solicito el valor actual
        self.rango = self.threadAdqImg.getTipoPaleta()
        rangoSeleccionado = "..."
        if self.rango == 1:
            rangoSeleccionado = "AlarmBlue"
        elif self.rango == 2:
            rangoSeleccionado = "AlarmBlueHi"
        elif self.rango == 3:
            rangoSeleccionado = "GrayBW"
        elif self.rango == 4:
            rangoSeleccionado = "GrayWB"
        elif self.rango == 5:
            rangoSeleccionado = "AlarmGreen"
        elif self.rango == 6:
            rangoSeleccionado = "Iron"
        elif self.rango == 7:
            rangoSeleccionado = "IronHi"
        elif self.rango == 8:
            rangoSeleccionado = "Medical"
        elif self.rango == 9:
            rangoSeleccionado = "Rainbow"
        elif self.rango == 10:
            rangoSeleccionado = "RainbowHi"
        elif self.rango == 11:
            rangoSeleccionado = "AlarmRed"
        self.valueCurrentPreset = QLineEdit(rangoSeleccionado)
        self.valueCurrentPreset.setStyleSheet("border: 2px solid black; background-color : lightgray;")        
        self.labelCurrentPreset.setBuddy(self.valueCurrentPreset)
        #valor de preset a cambiar
        self.labelNewPreset = QLabel("New Preset")
        self.valueNewPreset = QLineEdit("....")
        self.valueNewPreset.setStyleSheet("border: 2px solid black;")
        self.labelNewPreset.setBuddy(self.valueNewPreset)
        #agrego los dos widgets al layout
        layoutPresetCurrentNew.addWidget(self.image_label_changePallete)
        layoutPresetCurrentNew.addLayout(layoutBotonesPallete)
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

    def upDateImage(self, imageAdq):
        #realizamos la actualizacion de la imagen con los parametros de rango de temperatura cambiados
        #print("aca realizmaos la configuracion de rango de temperatura")
        imagenCamaraUpDate = imageAdq.pixmap()
        self.image_label_changePallete.setPixmap(imagenCamaraUpDate)        
        return self.flagDetenerStriming
    
    def okUpDatePresetCam(self):
        #realizamos la aceptación de los cambios
        print("aca realizamos la aceptacion de los cambios en los rangos de temperatura")
        rangoActualGuardar = self.threadAdqImg.getTipoPaleta()
        print("rango a actualizar: ", rangoActualGuardar)
        if os.path.isfile("presetCamera.txt"):
            with open('presetCamera.txt','r') as f:
                presetAGuardar = str(rangoActualGuardar)
                nombrePreset = self.valorNombreMedicion
                lines = f.readlines()
                indiceLineas = 0
                flagEncontrePalabra = False
                for row in lines:
                    if row.find(nombrePreset) != -1:
                        listaPalabras = row.split()
                        indicePalabraReemplazar = 0
                        for palabras in listaPalabras:
                            if palabras == '=':
                                break
                            indicePalabraReemplazar += 1
                        palabraReemplazar = listaPalabras[indicePalabraReemplazar:]
                        filaOriginal = row
                        row =  row.replace(palabraReemplazar[1]+"\n", presetAGuardar+"\n")
                        filaAReemplazar = row
                        flagEncontrePalabra = True
                        break
                    indiceLineas += 1
            if flagEncontrePalabra:
                with open('presetCamera.txt', 'r') as f:
                    textoCompleto = f.read()
                with open('presetCamera.txt', 'w') as f:
                    textoCompleto = textoCompleto.replace(filaOriginal, filaAReemplazar)
                    f.write(textoCompleto)
            else:
                with open('presetCamera.txt', 'a') as f:
                    f.write(nombrePreset + " = " + presetAGuardar + "\n")
        else:
            with open('presetCamera.txt','w') as f:
                presetAGuardar = rangoActualGuardar
                nombrePreset = self.valorNombreMedicion
                f.write(nombrePreset + " = " + presetAGuardar + "\n")
        print("update preset cam a disco")
        self.flagDetenerStriming = True

    
    def cancelUpDatePresetCam(self):
        #realizamos la cancelacion de los cambio solicitados
        print("Cancelar preset a camara")
        if self.rango == 1:            
            self.threadAdqImg.selPaleta(1) #indiceAlarmBlue
        elif self.rango == 2:            
            self.threadAdqImg.selPaleta(2) #indiceAlarmBlueHi
        elif self.rango == 3:            
            self.threadAdqImg.selPaleta(3) #indiceAlarmGrayBW
        elif self.rango == 4:            
            self.threadAdqImg.selPaleta(4) #indiceAlarmGrayWB
        elif self.rango == 5:            
            self.threadAdqImg.selPaleta(5) #indiceAlarmGreen
        elif self.rango == 6:            
            self.threadAdqImg.selPaleta(6) #indiceIron
        elif self.rango == 7:            
            self.threadAdqImg.selPaleta(7) #indiceIronHi
        elif self.rango == 8:            
            self.threadAdqImg.selPaleta(8) #indiceMedical
        elif self.rango == 9:            
            self.threadAdqImg.selPaleta(9) #indiceRainbow
        elif self.rango == 10:            
            self.threadAdqImg.selPaleta(10) #indiceRainbowHi
        elif self.rango == 11:            
            self.threadAdqImg.selPaleta(11) #indiceAlarmRed
        self.flagDetenerStriming = True 
    
    def cerrarPopup(self):
        self.close()
    
    def selPaletaAlarmBlue(self):
        print("seleccion paleta AlarmBlue")
        self.valueNewPreset.setText("AlarmBlue")
        indiceAlarmBlue = 1
        self.threadAdqImg.selPaleta(indiceAlarmBlue)
    
    def selPaletaAlarmBlueHi(self):
        print("seleccion paleta AlarmBlueHi")
        self.valueNewPreset.setText("AlarmBlueHi")
        indiceAlarmBlueHi = 2
        self.threadAdqImg.selPaleta(indiceAlarmBlueHi)
    
    def selPaletaGrayBW(self):
        print("seleccion paleta GrayBW")
        self.valueNewPreset.setText("GrayBW")
        indiceAlarmGrayBW = 3
        self.threadAdqImg.selPaleta(indiceAlarmGrayBW)
    
    def selPaletaGrayWB(self):
        print("seleccion paleta GrayWB")
        self.valueNewPreset.setText("GrayWB")
        indiceAlarmGrayWB = 4
        self.threadAdqImg.selPaleta(indiceAlarmGrayWB)        
    
    def selPaletaAlarmGreen(self):
        print("seleccion paleta AlarmGreen")
        self.valueNewPreset.setText("AlarmGreen")
        indiceAlarmGreen = 5
        self.threadAdqImg.selPaleta(indiceAlarmGreen)
    
    def selPaletaIron(self):
        print("seleccion paleta Iron")
        self.valueNewPreset.setText("Iron")
        indiceIron = 6
        self.threadAdqImg.selPaleta(indiceIron)
    
    def selPaletaIronHi(self):
        print("seleccion paleta IronHi")
        self.valueNewPreset.setText("IronHi")
        indiceIronHi = 7
        self.threadAdqImg.selPaleta(indiceIronHi)
    
    def selPaletaMedical(self):
        print("seleccion paleta Medical")
        self.valueNewPreset.setText("Medical")
        indiceMedical = 8
        self.threadAdqImg.selPaleta(indiceMedical)
    
    def selPaletaRainbow(self):
        print("seleccion paleta Rainbow")
        self.valueNewPreset.setText("Rainbow")
        indiceRainbow = 9
        self.threadAdqImg.selPaleta(indiceRainbow)
    
    def selPaletaRainbowHi(self):
        print("seleccion paleta RainbowHi")
        self.valueNewPreset.setText("RainbowHi")
        indiceRainbowHi = 10
        self.threadAdqImg.selPaleta(indiceRainbowHi)
    
    def selPaletaAlarmRed(self):    
        print("seleccion paleta AlarmRed")
        self.valueNewPreset.setText("AlarmRed")
        indiceAlarmRed = 11
        self.threadAdqImg.selPaleta(indiceAlarmRed)

#clase cambio el tipo de ajuste de limites para la paleta seleccionada
class PopUpWritePresetAutoManPalleteCam(QWidget):
    def __init__(self, miThreadAdqImagen, imageAdq, nameCamera):
        super().__init__()
        #cargo nombre preset
        self.valorNombreMedicion = "presetAjustePaleta" + nameCamera
        #cargo valor defaul preset automatico
        self.valorPresetMedicion = 2
        #realizamos la configuracion de pantalla
        print("aca realizamos la configuracion de pantalla para paleta de la camara")
        #flag para cerrar ventana y dejar de stremear
        self.flagDetenerStriming = False
        #instancia de hilo
        self.threadAdqImg = miThreadAdqImagen
        self.setWindowTitle("Write Preset Auto/Man Pallete ")
        layoutPresetCurrentNew = QVBoxLayout()
        #set para la imagen
        self.display_width = 640
        self.display_height = 480
        #creamos el label que va a contener la imagen
        self.image_label_manAutoPallete = QLabel()
        self.imageCamara = imageAdq.pixmap()
        self.image_label_manAutoPallete.setPixmap(self.imageCamara)
        self.image_label_manAutoPallete.resize(self.display_width, self.display_height)
        #creamos los botones para controlar la paleta
        layoutBotonesManAutoPallete = QGridLayout()
        #creamos los botones
        #boton Manual
        btnSelManual = QPushButton("Manual")
        btnSelManual.clicked.connect(self.selManualEscalamiento)
        #boton Min Max Automatico
        btnSelMinMaxAuto = QPushButton("Min-Max Automatico")
        btnSelMinMaxAuto.clicked.connect(self.selMinMaxEscalamiento)
        #boton 1 Sigma Automatico
        btnSelSigma1Auto = QPushButton("Sigma 1 Automatico")
        btnSelSigma1Auto.clicked.connect(self.selSigma1Escalamiento)
        #boton 3 Sigma Automatico
        btnSelSigma3Auto = QPushButton("Sigma 3 Automatico")
        btnSelSigma3Auto.clicked.connect(self.selSigma3Escalamiento)
        #agrego los botones al layout
        layoutBotonesManAutoPallete.addWidget(btnSelManual, 0, 0)
        layoutBotonesManAutoPallete.addWidget(btnSelMinMaxAuto, 0, 1)
        layoutBotonesManAutoPallete.addWidget(btnSelSigma1Auto, 1, 0)
        layoutBotonesManAutoPallete.addWidget(btnSelSigma3Auto, 1, 1)
        #agregamos los botones de preset acual y cambiado
        #valor de preset actual
        self.labelCurrentPreset = QLabel("Current Preset")
        self.indiceTipoEscalado=self.threadAdqImg.getManAuto()
        escaladoSeleccionado = "..."
        if self.indiceTipoEscalado == 1:
            escaladoSeleccionado = "Manual"
        elif self.indiceTipoEscalado == 2:
            escaladoSeleccionado = "Automatico"
        elif self.indiceTipoEscalado == 3:
            escaladoSeleccionado = "1SigmaDesv"            
        elif self.indiceTipoEscalado == 4:
            escaladoSeleccionado = "3SigmaDesv"
        self.valueCurrentPreset = QLineEdit(escaladoSeleccionado)
        self.valueCurrentPreset.setStyleSheet("border: 2px solid black; background-color : lightgray;")        
        self.labelCurrentPreset.setBuddy(self.valueCurrentPreset)
        #valor de preset a cambiar
        self.labelNewPreset = QLabel("New Preset")
        self.valueNewPreset = QLineEdit("....")
        self.valueNewPreset.setStyleSheet("border: 2px solid black;")
        self.labelNewPreset.setBuddy(self.valueNewPreset)
        #agrego los dos widgets al layout
        layoutPresetCurrentNew.addWidget(self.image_label_manAutoPallete)
        layoutPresetCurrentNew.addLayout(layoutBotonesManAutoPallete)
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

    def upDateImage(self, imageAdq):
        #realizamos la actualizacion de la imagen con los parametros de rango de temperatura cambiados
        #print("aca realizmaos la configuracion de rango de temperatura")
        imagenCamaraUpDate = imageAdq.pixmap()
        self.image_label_manAutoPallete.setPixmap(imagenCamaraUpDate)        
        return self.flagDetenerStriming
    
    def okUpDatePresetCam(self):
        #realizamos la aceptación de los cambios
        print("aca realizamos la aceptacion de los cambios en tipo de ajuste paleta")
        rangoActualGuardar = self.threadAdqImg.getManAuto()
        print("rango a actualizar: ", rangoActualGuardar)
        if os.path.isfile("presetCamera.txt"):
            with open("presetCamera.txt", 'r') as f:
                presetAGuardar = str(rangoActualGuardar)
                nombrePreset = self.valorNombreMedicion
                lines = f.readlines()
                indiceLineas = 0
                flagEncontrePalabra = False
                for row in lines:
                    if row.find(nombrePreset) != -1:
                        listaPalabras = row.split()
                        indicePalabraReemplazar = 0
                        for palabras in listaPalabras:
                            if palabras == '=':
                                break
                            indicePalabraReemplazar += 1
                        palabraReemplazar = listaPalabras[indicePalabraReemplazar:]
                        filaOriginal = row
                        row = row.replace(palabraReemplazar[1]+"\n", presetAGuardar+"\n")
                        filaAReemplazar = row
                        flagEncontrePalabra = True
                        break
                    indiceLineas += 1
            if flagEncontrePalabra:
                with open('presetCamera.txt', 'r') as f:
                    textoCompleto = f.read()
                with open('presetCamera.txt', 'w') as f:
                    textoCompleto = textoCompleto.replace(filaOriginal, filaAReemplazar)
                    f.write(textoCompleto)
            else:
                with open('presetCamera.txt', 'a') as f:
                    f.write(nombrePreset + " = " + presetAGuardar + "\n")
        else:
            with open('presetCamera.txt', 'w') as f:
                presetAGuardar = rangoActualGuardar
                nombrePreset = self.valorNombreMedicion
                f.write(nombrePreset + " = " + presetAGuardar + "\n")
        print("update preset cam a disco")
        self.flagDetenerStriming = True        

    
    def cancelUpDatePresetCam(self):
        #realizamos la cancelacion de los cambio solicitados
        print("Cancelar preset a camara")
        if self.indiceTipoEscalado == 1:
            scaleManual = 1
            self.threadAdqImg.selScalePaleta(scaleManual)
        elif self.indiceTipoEscalado == 2:
            scaleMinMax = 2
            self.threadAdqImg.selScalePaleta(scaleMinMax)
        elif self.indiceTipoEscalado == 3:
            scaleSigma1 = 3
            self.threadAdqImg.selScalePaleta(scaleSigma1)
        elif self.indiceTipoEscalado == 4:
            scaleSigma3 = 4
            self.threadAdqImg.selScalePaleta(scaleSigma3)
        self.flagDetenerStriming = True 
    
    def cerrarPopup(self):
        self.close()
    
    def selManualEscalamiento(self):
        print("seleccion escalamiento Manual")
        self.valueNewPreset.setText("Manual")
        scaleManual = 1
        self.threadAdqImg.selScalePaleta(scaleManual)
    
    def selMinMaxEscalamiento(self):
        print("seleccion escalamiento MinMax")
        self.valueNewPreset.setText("Auto")
        scaleMinMax = 2
        self.threadAdqImg.selScalePaleta(scaleMinMax)
    
    def selSigma1Escalamiento(self):
        print("seleccion escalamiento Sigma1")
        self.valueNewPreset.setText("Sigma1")
        scaleSigma1 = 3
        self.threadAdqImg.selScalePaleta(scaleSigma1)    
    
    def selSigma3Escalamiento(self):
        print("seleccion escalamiento Sigma3")
        self.valueNewPreset.setText("Sigma3")
        scaleSigma3 = 4
        self.threadAdqImg.selScalePaleta(scaleSigma3)

#clase cambio los limites de ajuste en manual
class PopUpWritePresetLimManualPalleteCam(QWidget):
    def __init__(self, miThreadAdqImagen, imageAdq, nameCamera):
        #inicializo        
        super().__init__()        
        #realizamos la configuracion de pantalla
        print("aca realizamos la configuracion")
        #flag para cerrar ventana y dejar de stremear
        self.flagdetenerStriming = False
        #instancia de hilo
        self.threadAdqImg = miThreadAdqImagen
        self.setWindowTitle("Write Preset Limites Manual Paleta")
        layoutPresetCurrentNew = QVBoxLayout()
        #set para la imagen
        self.display_width = 640
        self.display_height = 480
        #creamos el label que va a contener la imagen
        self.image_label_limManualPallete = QLabel()
        self.imageCamara = imageAdq.pixmap()
        self.image_label_limManualPallete.setPixmap(self.imageCamara)
        self.image_label_limManualPallete.resize(self.display_width, self.display_height)
        #creamos dos spinbox y un boton para actualizar el limite inferior y superior del rango de temperatura usado por la paleta.
        #agregamos un boton para bajar el cambio
        self.selRangoTempPaletaManual = QPushButton("selRango")
        self.selRangoTempPaletaManual.clicked.connect(self.btnCambiarLimitesRangoPaleta)
        self.limInferiorRangoTempPaletaManual = QSpinBox(self)
        self.limInferiorRangoTempPaletaManual.setMaximum(100)
        self.limInferiorRangoTempPaletaManual.setMinimum(-20)
        self.limInferiorRangoTempPaletaManual.setSingleStep(5)
        self.limInferiorRangoTempPaletaManual.setValue(-20)
        self.limInferiorRangoTempPaletaManual.valueChanged.connect(self.verificoLimiteInferiorSpin)
        self.limSuperiorRangoTempPaletaManual = QSpinBox(self)
        self.limSuperiorRangoTempPaletaManual.setMaximum(100)
        self.limSuperiorRangoTempPaletaManual.setMinimum(-20)
        self.limSuperiorRangoTempPaletaManual.setSingleStep(5)
        self.limSuperiorRangoTempPaletaManual.setValue(100)
        self.limSuperiorRangoTempPaletaManual.valueChanged.connect(self.verificoLimiteSuperiorSpin)
        layoutMinMaxRangoTempPaletaManual = QVBoxLayout()
        layoutMinMaxRangoTempPaletaManual.addWidget(self.limInferiorRangoTempPaletaManual)
        layoutMinMaxRangoTempPaletaManual.addWidget(self.limSuperiorRangoTempPaletaManual)
        layoutSelRangoTempPaletaManual = QHBoxLayout()
        layoutSelRangoTempPaletaManual.addLayout(layoutMinMaxRangoTempPaletaManual)
        layoutSelRangoTempPaletaManual.addWidget(self.selRangoTempPaletaManual)
        #agregamos los botones de preset acual y cambiado
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
        layoutPresetCurrentNew.addWidget(self.image_label_limManualPallete)
        layoutPresetCurrentNew.addLayout(layoutSelRangoTempPaletaManual)
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

    def upDateImage(self, imageAdq):
        #realizamos la actualizacion de la imagen con los parametros de rango de temperatura cambiados
        #print("aca realizmaos la configuracion de rango de temperatura")
        imagenCamaraUpDate = imageAdq.pixmap()
        self.image_label_limManualPallete.setPixmap(imagenCamaraUpDate)        
        
        return self.flagdetenerStriming
        
    def okUpDatePresetCam(self):
        #actualico los preset
        print("ok update")
    
    def cancelUpDatePresetCam(self):
        #realizamos la cancelacion de los cambio solicitados
        print("Cancelar preset a camara")
        self.flagdetenerStriming = True
    
    def cerrarPopup(self):
        #cerrar popup
        print("cerrar")
        self.close()    

    def verificoLimiteInferiorSpin(self):
        if self.limInferiorRangoTempPaletaManual.value() > self.limSuperiorRangoTempPaletaManual.value():
            #si el nuevo valor def sping inferior es mayor añ vañpr del sping superior lo reemplazo por una unidad menos que el mayor
            self.limInferiorRangoTempPaletaManual.setValue(self.limSuperiorRangoTempPaletaManual.value() - 1)
            print("valor inferior no valido")

    def verificoLimiteSuperiorSpin(self):
        if self.limSuperiorRangoTempPaletaManual.value() < self.limInferiorRangoTempPaletaManual.value():
            #verifico el nuevo valor del spin superior si es menor al valor del spin inferior lo reemplayo por una unidad mayor
            self.limSuperiorRangoTempPaletaManual.setValue(self.limInferiorRangoTempPaletaManual.value() + 1 )
            print("valor superior no valido")

    def btnCambiarLimitesRangoPaleta(self):
        #cambiar los limites del rango manual
        minimoRango = self.limInferiorRangoTempPaletaManual.value()
        maximoRango = self.limSuperiorRangoTempPaletaManual.value()
        print("seleccion actualizar limite inferior: {} superior: {}".format(minimoRango, maximoRango))        
        self.threadAdqImg.selRangeTempManual(minimoRango, maximoRango)

#clase cambio los valores de temperatura ambiente
class PopUpWritePresetTempAmbienteCam(QWidget):
    def __init__(self, miThreadAdqImagen, imageAdq):
        #inicializacion
        super().__init__()
        #realizamos la configuracion pantalla
        print("aca realizamos la configuracion")
        #flag para cerrar ventana y dejar de stremear
        self.flagdetenerStriming = False
        #instanci de hilo
        self.threadAdqImg = miThreadAdqImagen
        self.setWindowTitle("Write Preset Temperatura")
        layoutPresetCurrentNew = QVBoxLayout()
        #set para la imagen
        self.display_width = 640
        self.display_height = 480
        #creamos el label que va a contener la imagen
        self.image_label_emTmTrCam = QLabel()
        self.imageCamara = imageAdq.pixmap()
        self.image_label_emTmTrCam.setPixmap(self.imageCamara)
        self.image_label_emTmTrCam.resize(self.display_width, self.display_height)
        #creamos qlabel editable para ingresar el valor de temperatura y un boton para cargar ese valor
        self.valorInTemperatura =QLineEdit("25.50",self)
        self.valorInTemperatura.setFixedWidth(40)
        self.valorInTemperatura.setValidator(QDoubleValidator(0.99,99.99,2))
        self.valorInTemperatura.setMaxLength(5)
        self.valorInTemperatura.returnPressed.connect(self.cambiarTemperatura)
        self.valorInTemperatura.setAlignment(Qt.AlignRight)
        self.valorInTemperatura.setEnabled(True)
        #creamos qdobleSpin editable para ingresar el valor de transmisividad entre 0 - 1
        self.valorInTransmisividad = QDoubleSpinBox(self)
        self.valorInTransmisividad.setMaximum(100)
        self.valorInTransmisividad.setMinimum(1)
        self.valorInTransmisividad.setSingleStep(5)
        self.valorInTransmisividad.setValue(100)
        self.valorInTransmisividad.valueChanged.connect(self.cambiarTransmisividad)
        lineInTransmisividad = self.valorInTransmisividad.lineEdit()
        lineInTransmisividad.setReadOnly(True)
        self.valorInTransmisividad.setEnabled(False)
        #creamos qDobleSpin editable para ingresar el valor de emisividad entre 0 - 1
        self.valorInEmisividad = QDoubleSpinBox(self)
        self.valorInEmisividad.setMaximum(1.00)
        self.valorInEmisividad.setMinimum(0.01)
        self.valorInEmisividad.setSingleStep(0.01)
        self.valorInEmisividad.setValue(0.85)
        self.valorInEmisividad.valueChanged.connect(self.cambiarEmisividad)
        lineInEmisividad = self.valorInEmisividad.lineEdit()
        lineInEmisividad.setReadOnly(True)
        self.valorInEmisividad.setEnabled(False)
        #creamos el layout
        layoutEmiTranTemp = QVBoxLayout()
        layoutEmiTranTemp.addWidget(self.valorInTemperatura)
        layoutEmiTranTemp.addWidget(self.valorInTransmisividad)
        layoutEmiTranTemp.addWidget(self.valorInEmisividad)
        #agregamos los botones de preset acual y cambiado
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
        layoutPresetCurrentNew.addWidget(self.image_label_emTmTrCam)
        layoutPresetCurrentNew.addLayout(layoutEmiTranTemp)
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

    def upDateImage(self, imageAdq):
        #realizamos la actualizacion de la imagen con los parametros de rango de temperatura cambiados
        #print("aca realizmaos la configuracion de rango de temperatura")
        imagenCamaraUpDate = imageAdq.pixmap()
        self.image_label_emTmTrCam.setPixmap(imagenCamaraUpDate)        
        
        return self.flagdetenerStriming

    def okUpDatePresetCam(self):
        #actualico los preset
        print("ok update")

    def cancelUpDatePresetCam(self):
        #realizamos la cancelacion de los cambio solicitados
        print("Cancelar preset a camara")
        self.flagdetenerStriming = True

    def cerrarPopup(self):
        #cerrar popup
        print("cerrar popup")
        self.close()  

    def cambiarEmisividad(self):
        valorEmisividad = self.valorInEmisividad.value()
        print("el valor de emisividad seleccionado: {}".format(valorEmisividad))
        self.threadAdqImg.incDecEmisividad(valorEmisividad)

    def cambiarTransmisividad(self): #funcion para cambiar la transmisividad del ambiente
        valorTransmisividad = self.valorInTransmisividad.value() / 100
        print("el valor de transmisividad seleccionado: {}".format(valorTransmisividad))
        self.threadAdqImg.incDecTransmisividad(valorTransmisividad)

    def cambiarTemperatura(self): #funcion para cambiar la temperatura ambiente
        textoIngresado = self.valorInTemperatura.text().replace(",",".")
        if textoIngresado.isnumeric(): #verificamos que sea un numero
            valorTemp = float(textoIngresado) #leemos del Qlineedit el valor de temperatura
            print("seleccionamos cambiar temperatura ingresada: {}".format(valorTemp)) #tomamos el valor de temperatura y lo mostramos 
            self.threadAdqImg.incDecTempAmbiente(valorTemp) #cargamos en el metodo del hilo para cambiar temperatura
        else:
            print("el valor ingresado no es un numero") 

#clase cambio los valores de transmisividad
class PopUpWritePresetTransmisividadCam(QWidget):
    def __init__(self, miThreadAdqImagen, imageAdq):
        #inicializacion
        super().__init__()
        #realizamos la configuracion pantalla
        print("aca realizamos la configuracion")
        #flag para cerrar ventana y dejar de stremear
        self.flagdetenerStriming = False
        #instanci de hilo
        self.threadAdqImg = miThreadAdqImagen
        self.setWindowTitle("Write Preset Trnasmisividad")
        layoutPresetCurrentNew = QVBoxLayout()
        #set para la imagen
        self.display_width = 640
        self.display_height = 480
        #creamos el label que va a contener la imagen
        self.image_label_emTmTrCam = QLabel()
        self.imageCamara = imageAdq.pixmap()
        self.image_label_emTmTrCam.setPixmap(self.imageCamara)
        self.image_label_emTmTrCam.resize(self.display_width, self.display_height)
        #creamos qlabel editable para ingresar el valor de temperatura y un boton para cargar ese valor
        self.valorInTemperatura =QLineEdit("25.50",self)
        self.valorInTemperatura.setFixedWidth(40)
        self.valorInTemperatura.setValidator(QDoubleValidator(0.99,99.99,2))
        self.valorInTemperatura.setMaxLength(5)
        self.valorInTemperatura.returnPressed.connect(self.cambiarTemperatura)
        self.valorInTemperatura.setAlignment(Qt.AlignRight)
        self.valorInTemperatura.setEnabled(False)
        #creamos qdobleSpin editable para ingresar el valor de transmisividad entre 0 - 1
        self.valorInTransmisividad = QDoubleSpinBox(self)
        self.valorInTransmisividad.setMaximum(100)
        self.valorInTransmisividad.setMinimum(1)
        self.valorInTransmisividad.setSingleStep(5)
        self.valorInTransmisividad.setValue(100)
        self.valorInTransmisividad.valueChanged.connect(self.cambiarTransmisividad)
        lineInTransmisividad = self.valorInTransmisividad.lineEdit()
        lineInTransmisividad.setReadOnly(True)
        self.valorInTransmisividad.setEnabled(True)
        #creamos qDobleSpin editable para ingresar el valor de emisividad entre 0 - 1
        self.valorInEmisividad = QDoubleSpinBox(self)
        self.valorInEmisividad.setMaximum(1.00)
        self.valorInEmisividad.setMinimum(0.01)
        self.valorInEmisividad.setSingleStep(0.01)
        self.valorInEmisividad.setValue(0.85)
        self.valorInEmisividad.valueChanged.connect(self.cambiarEmisividad)
        lineInEmisividad = self.valorInEmisividad.lineEdit()
        lineInEmisividad.setReadOnly(True)
        self.valorInEmisividad.setEnabled(False)
        #creamos el layout
        layoutEmiTranTemp = QVBoxLayout()
        layoutEmiTranTemp.addWidget(self.valorInTemperatura)
        layoutEmiTranTemp.addWidget(self.valorInTransmisividad)
        layoutEmiTranTemp.addWidget(self.valorInEmisividad)
        #agregamos los botones de preset acual y cambiado
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
        layoutPresetCurrentNew.addWidget(self.image_label_emTmTrCam)
        layoutPresetCurrentNew.addLayout(layoutEmiTranTemp)
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

    def upDateImage(self, imageAdq):
        #realizamos la actualizacion de la imagen con los parametros de rango de temperatura cambiados
        #print("aca realizmaos la configuracion de rango de temperatura")
        imagenCamaraUpDate = imageAdq.pixmap()
        self.image_label_emTmTrCam.setPixmap(imagenCamaraUpDate)        
        
        return self.flagdetenerStriming

    def okUpDatePresetCam(self):
        #actualico los preset
        print("ok update")

    def cancelUpDatePresetCam(self):
        #realizamos la cancelacion de los cambio solicitados
        print("Cancelar preset a camara")
        self.flagdetenerStriming = True

    def cerrarPopup(self):
        #cerrar popup
        print("cerrar popup")
        self.close()  

    def cambiarEmisividad(self):
        valorEmisividad = self.valorInEmisividad.value()
        print("el valor de emisividad seleccionado: {}".format(valorEmisividad))
        self.threadAdqImg.incDecEmisividad(valorEmisividad)

    def cambiarTransmisividad(self): #funcion para cambiar la transmisividad del ambiente
        valorTransmisividad = self.valorInTransmisividad.value() / 100
        print("el valor de transmisividad seleccionado: {}".format(valorTransmisividad))
        self.threadAdqImg.incDecTransmisividad(valorTransmisividad)

    def cambiarTemperatura(self): #funcion para cambiar la temperatura ambiente
        textoIngresado = self.valorInTemperatura.text().replace(",",".")
        if textoIngresado.isnumeric(): #verificamos que sea un numero
            valorTemp = float(textoIngresado) #leemos del Qlineedit el valor de temperatura
            print("seleccionamos cambiar temperatura ingresada: {}".format(valorTemp)) #tomamos el valor de temperatura y lo mostramos 
            self.threadAdqImg.incDecTempAmbiente(valorTemp) #cargamos en el metodo del hilo para cambiar temperatura
        else:
            print("el valor ingresado no es un numero") 

#clase cambio los valores de emisividad
class PopUpWritePresetEmisividadCam(QWidget):
    def __init__(self, miThreadAdqImagen, imageAdq):
        #inicializacion
        super().__init__()
        #realizamos la configuracion pantalla
        print("aca realizamos la configuracion")
        #flag para cerrar ventana y dejar de stremear
        self.flagdetenerStriming = False
        #instanci de hilo
        self.threadAdqImg = miThreadAdqImagen
        self.setWindowTitle("Write Preset Emisividad")
        layoutPresetCurrentNew = QVBoxLayout()
        #set para la imagen
        self.display_width = 640
        self.display_height = 480
        #creamos el label que va a contener la imagen
        self.image_label_emTmTrCam = QLabel()
        self.imageCamara = imageAdq.pixmap()
        self.image_label_emTmTrCam.setPixmap(self.imageCamara)
        self.image_label_emTmTrCam.resize(self.display_width, self.display_height)
        #creamos qlabel editable para ingresar el valor de temperatura y un boton para cargar ese valor
        self.valorInTemperatura =QLineEdit("25.50",self)
        self.valorInTemperatura.setFixedWidth(40)
        self.valorInTemperatura.setValidator(QDoubleValidator(0.99,99.99,2))
        self.valorInTemperatura.setMaxLength(5)
        self.valorInTemperatura.returnPressed.connect(self.cambiarTemperatura)
        self.valorInTemperatura.setAlignment(Qt.AlignRight)
        self.valorInTemperatura.setEnabled(False)
        #creamos qdobleSpin editable para ingresar el valor de transmisividad entre 0 - 1
        self.valorInTransmisividad = QDoubleSpinBox(self)
        self.valorInTransmisividad.setMaximum(100)
        self.valorInTransmisividad.setMinimum(1)
        self.valorInTransmisividad.setSingleStep(5)
        self.valorInTransmisividad.setValue(100)
        self.valorInTransmisividad.valueChanged.connect(self.cambiarTransmisividad)
        lineInTransmisividad = self.valorInTransmisividad.lineEdit()
        lineInTransmisividad.setReadOnly(True)
        self.valorInTransmisividad.setEnabled(False)
        #creamos qDobleSpin editable para ingresar el valor de emisividad entre 0 - 1
        self.valorInEmisividad = QDoubleSpinBox(self)
        self.valorInEmisividad.setMaximum(1.00)
        self.valorInEmisividad.setMinimum(0.01)
        self.valorInEmisividad.setSingleStep(0.01)
        self.valorInEmisividad.setValue(0.85)
        self.valorInEmisividad.valueChanged.connect(self.cambiarEmisividad)
        lineInEmisividad = self.valorInEmisividad.lineEdit()
        lineInEmisividad.setReadOnly(True)
        self.valorInEmisividad.setEnabled(True)
        #creamos el layout
        layoutEmiTranTemp = QVBoxLayout()
        layoutEmiTranTemp.addWidget(self.valorInTemperatura)
        layoutEmiTranTemp.addWidget(self.valorInTransmisividad)
        layoutEmiTranTemp.addWidget(self.valorInEmisividad)
        #agregamos los botones de preset acual y cambiado
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
        layoutPresetCurrentNew.addWidget(self.image_label_emTmTrCam)
        layoutPresetCurrentNew.addLayout(layoutEmiTranTemp)
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

    def upDateImage(self, imageAdq):
        #realizamos la actualizacion de la imagen con los parametros de rango de temperatura cambiados
        #print("aca realizmaos la configuracion de rango de temperatura")
        imagenCamaraUpDate = imageAdq.pixmap()
        self.image_label_emTmTrCam.setPixmap(imagenCamaraUpDate)        
        
        return self.flagdetenerStriming

    def okUpDatePresetCam(self):
        #actualico los preset
        print("ok update")

    def cancelUpDatePresetCam(self):
        #realizamos la cancelacion de los cambio solicitados
        print("Cancelar preset a camara")
        self.flagdetenerStriming = True

    def cerrarPopup(self):
        #cerrar popup
        print("cerrar popup")
        self.close()  

    def cambiarEmisividad(self):
        valorEmisividad = self.valorInEmisividad.value()
        print("el valor de emisividad seleccionado: {}".format(valorEmisividad))
        self.threadAdqImg.incDecEmisividad(valorEmisividad)

    def cambiarTransmisividad(self): #funcion para cambiar la transmisividad del ambiente
        valorTransmisividad = self.valorInTransmisividad.value() / 100
        print("el valor de transmisividad seleccionado: {}".format(valorTransmisividad))
        self.threadAdqImg.incDecTransmisividad(valorTransmisividad)

    def cambiarTemperatura(self): #funcion para cambiar la temperatura ambiente
        textoIngresado = self.valorInTemperatura.text().replace(",",".")
        if textoIngresado.isnumeric(): #verificamos que sea un numero
            valorTemp = float(textoIngresado) #leemos del Qlineedit el valor de temperatura
            print("seleccionamos cambiar temperatura ingresada: {}".format(valorTemp)) #tomamos el valor de temperatura y lo mostramos 
            self.threadAdqImg.incDecTempAmbiente(valorTemp) #cargamos en el metodo del hilo para cambiar temperatura
        else:
            print("el valor ingresado no es un numero") 

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
class RoisComboBoxHistorico(QComboBox):
    popupAboutToBeShown = pyqtSignal()
    def showPopup(self):
        self.popupAboutToBeShown.emit()
        super(RoisComboBoxHistorico,self).showPopup()
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
class MainWindow(QWidget):#(QDialog):
   
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        #creo los registros donde llevo las imagens termicas y de vision 
        #que leemos de los archivos
        self.matrizImgThIzq = []
        self.matrizImgCvIzq = []
        self.matrizImgThDer = []
        self.matrizImgCvDer = []
        #indice para buscar las imagenes guardada
        self.indice = 0
        #path a guardado de archivos
        self.pathDirImagesFile = ""
        #creo la cola de datos
        self.queueDatosOrigenThermal = queue.Queue()
        self.queueDatosOrigenCV = queue.Queue()
        #defino un flag para habilitar la carga de datos en la cola
        self.flagQueueReady = False
        #flags para manejo de aplicacion
        self.mostrarImagenPopUpCambioFoco = False #indicamos al hilo de adquisicion en la signal emitida que muestre la imagen
        self.mostrarImagenPopUpCambioRango = False #utilizamos este flag para indicar si debe stremear la imagen a la popup de configuracion de rango de temperatura
        self.mostrarImagenPopUpCambioPaleta = False
        self.mostrarImagenPopUpManAutPaleta = False
        self.mostrarImagenPopUpLimManPaleta = False
        self.mostrarImagenPopUpCambioTmpAmb = False
        self.mostrarImagenPopUpCambioTmdAmb = False
        self.mostrarImagenPopUpCambioEmisividad = False        
        #creamos un flag para indicar que solo se stremea informacion a la pantalla de record
        self.mostrarImagenPantallaRecorded = False
        #creamos las variables locales que llevan los calculos
        #de cada roi que son min avg y max
        #rectangulo 1
        self.rect1ValueMin = 0
        self.rect1ValueAvg = 0
        self.rect1ValueMax = 0
        #linea 1
        self.line1ValueMin = 0
        self.line1ValueAvg = 0
        self.line1ValueMax = 0
        #elipse 1
        self.ellipse1ValueMin = 0
        self.ellipse1ValueAvg = 0
        self.ellipse1ValueMax = 0
        #rectangulo2
        self.rect2ValueMin = 0
        self.rect2ValueAvg = 0
        self.rect2ValueMax = 0
        #linea 2
        self.line2ValueMin = 0
        self.line2ValueAvg = 0
        self.line2ValueMax = 0
        #elipse 2
        self.ellipse2ValueMin = 0
        self.ellipse2ValueAvg = 0
        self.ellipse2ValueMax = 0
        #
        #creo los valores para ser cargados con el nivel de alarma
        #
        self.valorNuevoPresetRoiMinRect1 = QLabel("0")
        self.valorNuevoPresetRoiAvgRect1 = QLabel("0")
        self.valorNuevoPresetRoiMaxRect1 = QLabel("0")
        self.valorNuevoPresetRoiMinLine1 = QLabel("0")
        self.valorNuevoPresetRoiAvgLine1 = QLabel("0")
        self.valorNuevoPresetRoiMaxLine1 = QLabel("0")
        self.valorNuevoPresetRoiMinEllipse1 = QLabel("0")
        self.valorNuevoPresetRoiAvgEllipse1 = QLabel("0")
        self.valorNuevoPresetRoiMaxEllipse1 = QLabel("0")
        self.valorNuevoPresetRoiMinRect2 = QLabel("0")
        self.valorNuevoPresetRoiAvgRect2 = QLabel("0")
        self.valorNuevoPresetRoiMaxRect2 = QLabel("0")
        self.valorNuevoPresetRoiMinLine2 = QLabel("0")
        self.valorNuevoPresetRoiAvgLine2 = QLabel("0")
        self.valorNuevoPresetRoiMaxLine2 = QLabel("0")
        self.valorNuevoPresetRoiMinEllipse2 = QLabel("0")
        self.valorNuevoPresetRoiAvgEllipse2 = QLabel("0")
        self.valorNuevoPresetRoiMaxEllipse2 = QLabel("0")
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
        #hago una instancia a mi combox ==> roisComboBox
        self.roisComboHistoricoIzquierda = RoisComboBoxHistorico(self)
        self.roisComboHistoricoIzquierda.popupAboutToBeShown.connect(self.populateRoisComboHistoricosIzquierda)
        self.populateRoisComboHistoricosIzquierda()
        #
        self.roisComboHistoricoDerecha = RoisComboBoxHistorico(self)
        self.roisComboHistoricoDerecha.popupAboutToBeShown.connect(self.populateRoisComboHistoricosDerecha)
        self.populateRoisComboHistoricosDerecha()
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
        self.profileSelComboDer = ProfileComboBox(self)
        self.profileSelComboDer.popupAboutToBeShown.connect(self.profileRoiCombo2)
        #
        #
        self.camCombo1 = CamComboBox(self) #combo box de camaras para los historicos de la izquierda
        self.camCombo1.popupAboutToBeShown.connect(self.populateCamCombo1)
        self.populateCamCombo1()
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
        
        self.botonLeerArchivoIzq = QPushButton("ManSelFile")
        self.botonLeerArchivoIzq.clicked.connect(self.leerArchivoIzq)
        self.botonLeerArchivoIzq.setEnabled(False)
        self.botonLeerArchivoIzq.setToolTip("Push for search image in system folder")
        self.botonLeerArchivoIzq.setIcon(QIcon(os.path.join(basedir,"appIcons","folder.png")))

        self.botonBackwardFileIzq = QPushButton("BackwardFile")
        self.botonBackwardFileIzq.clicked.connect(self.retrocederArchivoIzq)
        self.botonBackwardFileIzq.setEnabled(False)
        self.botonBackwardFileIzq.setToolTip("Push for backward 1 image in selected folder")
        self.botonBackwardFileIzq.setIcon(QIcon(os.path.join(basedir,"appIcons","arrow-180.png")))

        self.botonFordwardFileIzq = QPushButton("FordwardFile")
        self.botonFordwardFileIzq.clicked.connect(self.avanzarArchivoIzq)
        self.botonFordwardFileIzq.setEnabled(False)
        self.botonFordwardFileIzq.setToolTip("Push for foradward 1 image in selected folder")
        self.botonFordwardFileIzq.setIcon(QIcon(os.path.join(basedir,"appIcons","arrow.png")))

        #
        #Defino los elementos del banner historicos de la derecha
        self.camCombo2 = CamComboBox(self) #combo box de camaras para los historicos de la derecha
        self.camCombo2.popupAboutToBeShown.connect(self.populateCamCombo2)
        self.populateCamCombo2()
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
        
        self.botonLeerArchivoDer = QPushButton("ManSelFile")
        self.botonLeerArchivoDer.clicked.connect(self.leerArchivoDer)
        self.botonLeerArchivoDer.setEnabled(False)
        self.botonLeerArchivoDer.setToolTip("Push for search image in system folder")
        self.botonLeerArchivoDer.setIcon(QIcon(os.path.join(basedir,"appIcons","folder.png")))

        self.botonBackwardFileDer = QPushButton("BackwardFile")
        self.botonBackwardFileDer.clicked.connect(self.retrocederArchivoDer)
        self.botonBackwardFileDer.setEnabled(False)
        self.botonBackwardFileDer.setToolTip("Push for backward 1 image in selected folder")
        self.botonBackwardFileDer.setIcon(QIcon(os.path.join(basedir,"appIcons","arrow-180.png")))

        self.botonFordwardFileDer = QPushButton("FordwardFile")
        self.botonFordwardFileDer.clicked.connect(self.avanzarArchivoDer)
        self.botonFordwardFileDer.setEnabled(False)
        self.botonFordwardFileDer.setToolTip("Push for fordward 1 image in selected folder")
        self.botonFordwardFileDer.setIcon(QIcon(os.path.join(basedir,"appIcons","arrow.png")))
        #
        #
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
        #self.bodyTabWidget.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Ignored)
        #self.bodyTabWidget.setFixedSize(1900,920)#700,500)
        #***************************************
        #Creo el contenido de la primer pestaña
        #***************************************
        #creo el contenido de la imagen
        #agrego las dimensiones
        self.display_width = 390
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
        self.image_label.resize(self.display_width, self.display_height)
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
        #Escala de imagen
        self.scrollArea.escalaImagen = [386,290]#{"ancho":386,"alto":290}
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
        #
        self.thread.status_camera_signal.connect(self.status_camera)
        # start the thread
        self.thread.start()
        #***************************************
        #creamo el hilo para realizar el procesamien
        #self.procesamientoThread = ProcesamientoDatosThread()
        #conectamos la señal con el slot para actualizar los datos procesados
        #self.procesamientoThread.change_datos_signal.connect(self.update_procesamiento)
        #arrancamos el hilo
        #self.procesamientoThread.start()
        #***************************************
        tab1Boton = QWidget() #defino la pestaña de la tabla asociada al boton 1
        self.textEditTab1Boton = QLineEdit() #cargo el texto en el label, esto es de ejemplo vamos a reemplazarlo por la imagen
        self.textEditTab1Boton.setText("Status: Camara conectando ....") #este texto lo vamos a 
        #vamos a agregar la barra de conexion para la camara 1
        self.pbarTab1 = QProgressBar(self)      #creo una instancia al modelo barras y le doy un nombre
        self.pbarTab1.setGeometry(30,40,200,25) #defino una dimension para la barra creada
        self.pbarTab1.setValue(0)               #inicializo en un valor
        self.statusConnectionCam1 = False       #Estado conexion con camara 1
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
        #agrego comoboBox para seleccion del perfil que vamos a mostrar

        #agrego grafico izquierda para la camara 1
        #
        self.dfTab1Izq = MplCanvas(self, width=5, height=4, dpi=100)
        self.dfTab1Izq.axes.tick_params(axis='x', color='red')
        self.dfTab1Izq.axes.grid(True, linestyle='solid')
        self.dfTab1Izq.axes.xaxis.set_major_locator(plt.MaxNLocator(5)) #fijo el numero de espacio que muestra en el eje x
        self.dfTab1Izq.axes.set_ylim([0, 100])
        self.dfTab1Izq.axes.set_ylabel("Roi1")
        self.dfTab1Izq.axes.set_xlabel('sec')
        self.dfTab1Izq.axes.set_title("Trending Roi 1") 
        n_data = 50
        #self.xdataIzq = list(range(n_data))        
        self.xdataIzq = np.array([self.now(-x*100) for x in range(0,n_data,1)][::-1],dtype='datetime64')
        self.formatoXDataIzq = np.array([x.item().strftime("%S:%f")[:-4] for x in self.xdataIzq])
        self.ydataIzq = np.array([random.randint(0,100) for i in range(n_data)])
        #       
        self._plot_refIzq = None
        #self.update_plot_dfTab1Izq()
        #defino las variables donde voy a indicar que es necesario
        #indicar en los graficos
        self.XTab1Izq = self.roiSelComboIzq.currentText() 
        self.XTab1Izq1 = self.profileSelComboIzq.currentText()
        self.XTab1Der = self.roiSelComboDer.currentText()
        self.XTab1Der1 = self.profileSelComboDer.currentText()
        #inicializo temporizador para refresco de graficos cada 2 segundos. Los graficos se cargan cad 100ms pero se refrescan cada 2 segundos 
        #self.timerRefresh = QtCore.QTimer()
        #self.timerRefresh.setInterval(2000)
        #self.timerRefresh.timeout.connect(self.update_plots)
        #self.timerRefresh.start() #No habilito el temporizador para muestrear mas lento los graficos
        #
        #agrego grafico sub izquierda para la camara 1
        #
        self.dfTab1Izq1 = MplCanvas(self, width=5, height=4, dpi=100)
        #defino los datos para el grafico de perfiles a izquierda de la imagen
        n_data1 = 50
        self.xdataIzq1 = np.array(list(range(n_data1)))
        self.ydataIzq1 = np.array([random.randint(0,100) for i in range(n_data1)])
        #defino los datos para llevar los perfiles de cada roi
        #roi rectangulo horizontal
        self.xdataIzq1RectHor = np.array(list(range(n_data1)))
        self.ydataIzq1RectHor = np.array([random.randint(0,10) for i in range(n_data1)])
        #roi rectangulo vertical
        self.xdataIzq1RectVert = np.array(list(range(n_data1)))
        self.ydataIzq1RectVert = np.array([random.randint(0,10) for i in range(n_data1)])
        #roi elipse horizontal
        self.xdataIzq1ElipHor = np.array(list(range(n_data1)))
        self.ydataIzq1ElipHor = np.array([random.randint(0,10) for i in range(n_data1)])
        #roi elipse vertical
        self.xdataIzq1ElipVer = np.array(list(range(n_data1)))
        self.ydataIzq1ElipVer = np.array([random.randint(0,10) for i in range(n_data1)])
        #roi linea
        self.xdataIzq1Line = np.array(list(range(n_data1)))
        self.ydataIzq1Line = np.array([random.randint(0,10) for i in range(n_data1)])
        #dibujo el perfil
        self._plot_refIzq1 = None
        #self.update_plot_dfTab1Izq1()
        # No actualizo el grafico lo dejo estatico
        # Ya que voy a mostrar el dato cuando se
        # actualice la medicion con el eje X en pixel
        #self.timerIzq1 = QtCore.QTimer()
        #self.timerIzq1.setInterval(1000)
        #self.timerIzq1.timeout.connect(self.update_plot_dfTab1Izq1)
        #self.timerIzq1.start()
        #
        #
        #Agrego comboBox para seleccionar el trending que vamos a mostrar en dfTab1Der
        #
        textEditTab1BotonSelROIDer = QLabel()
        textEditTab1BotonSelROIDer.setText("Selected ROI: ")
        textEditTab1BotonSelROIDer.setBuddy(self.roiSelComboDer)
        self.roiSelComboDer.setToolTip("selected the roi to show min-avg-max value")
        #
        #Agrego comboBox para seleccionar el perfil que vamos a mostrar
        textEditTab1BotonSelProfileDer = QLabel()
        textEditTab1BotonSelProfileDer.setText("Selected Profile:")
        textEditTab1BotonSelProfileDer.setBuddy(self.profileSelComboDer)
        self.profileSelComboDer.setToolTip("selected the profile to show Rois")
        #agrego grafico derecha
        #genero un dataframe de prueba
        self.dfTab1Der = MplCanvas(self, width=5, height=4, dpi=100)
        self.dfTab1Der.axes.tick_params(axis='x', color='red')
        self.dfTab1Der.axes.grid(True, linestyle='-.')
        self.dfTab1Der.axes.xaxis.set_major_locator(plt.MaxNLocator(5)) #fijo el numero de espacio que muestra en el eje x
        self.dfTab1Der.axes.set_ylim([0, 100])
        self.dfTab1Der.axes.set_ylabel("Roi2")
        self.dfTab1Der.axes.set_xlabel('sec')
        self.dfTab1Der.axes.set_title("Trending Roi 2")
        n_data = 50
        #self.xdataDer = list(range(n_data))
        self.xdataDer = np.array([self.now(-x*100) for x in range(0,n_data,1)][::-1],dtype='datetime64')
        self.formatoXDataDer = np.array([x.item().strftime("%S:.%f")[:-4] for x in self.xdataDer])
        self.ydataDer = np.array([random.randint(0,100) for i in range(n_data)])

        self._plot_refDer = None
        #self.update_plot_dfTab1Der() 

        #self.timer = QtCore.QTimer()
        #self.timer.setInterval(100)
        #self.timer.timeout.connect(self.update_plot_dfTab1Der)
        #self.timer.start()
        #
        #
        #agrego grafico derecha 1
        #genero un dataframe de prueba
        self.dfTab1Der1 = MplCanvas(self, width=5, height=4, dpi=100)

        n_data2 = 50
        self.xdataDer1 = np.array(list(range(n_data2)))
        self.ydataDer1 = np.array([random.randint(0,100) for i in range(n_data2)])
        #defino los datos para llevar los perfiles de cada roi
        #roi rectangulo horizontal
        self.xdataDer1RectHor = np.array(list(range(n_data2)))
        self.ydataDer1RectHor = np.array([random.randint(0,10) for i in range(n_data2)])
        #roi rectangulo vertical
        self.xdataDer1RectVert = np.array(list(range(n_data2)))
        self.ydataDer1RectVert = np.array([random.randint(0,10) for i in range(n_data2)])
        #roi elipse horizontal
        self.xdataDer1ElipHor = np.array(list(range(n_data2)))
        self.ydataDer1ElipHor = np.array([random.randint(0,10) for i in range(n_data2)])
        #roi elipse vertical
        self.xdataDer1ElipVer = np.array(list(range(n_data2)))
        self.ydataDer1ElipVer = np.array([random.randint(0,10) for i in range(n_data2)])
        #roi linea
        self.xdataDer1Line = np.array(list(range(n_data2)))
        self.ydataDer1Line = np.array([random.randint(0,10) for i in range(n_data2)])
 
        self._plot_refDer1 = None
        #self.update_plot_dfTab1Der1() 
        # No actualizo el grafico lo dejo estatico
        # Ya que voy a mostrar el dato cuando se
        # actualice la medicion con el eje X en pixel
        #self.timerDer1 = QtCore.QTimer()
        #self.timerDer1.setInterval(1000)
        #self.timerDer1.timeout.connect(self.update_plot_dfTab1Der1)
        #self.timerDer1.start()
        #
        self.update_plot_dfTab1Izq()

        self.timerIzq = QtCore.QTimer()
        self.timerIzq.setInterval(100)
        self.timerIzq.timeout.connect(self.update_plot_dfTab1Izq)
        self.timerIzq.start()

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
        boton1Tab1.setToolTip("MinRoiRect1")
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
        boton11Tab1.setToolTip("MinRoiLine1")
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
        boton12Tab1.setToolTip("MinRoiEllipse1")
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
        boton2Tab1.setToolTip("AvgRoiRect1")       
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
        boton21Tab1.setToolTip("AvgRoiLine1")       
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
        boton22Tab1.setToolTip("AvgRoiEllipse1")       
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
        boton3Tab1.setToolTip("MaxRoiRect1")       
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
        boton31Tab1.setToolTip("MaxRoiLine1")       
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
        boton32Tab1.setToolTip("MaxRoiEllipse1")       
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
        boton4Tab1.setToolTip("MinRoiRect2")
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
        boton41Tab1.setToolTip("MinRoiLine2")
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
        boton42Tab1.setToolTip("MinRoiEllipse2")
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
        boton5Tab1.setToolTip("AvgRoiRect2")
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
        boton51Tab1.setToolTip("AvgRoiLine2")
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
        boton52Tab1.setToolTip("AvgRoiEllipse2")
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
        boton6Tab1.setToolTip("MaxRoiRect2")
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
        boton61Tab1.setToolTip("MaxRoiLine2")
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
        boton62Tab1.setToolTip("MaxRoiEllipse2")
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
        contenedorDerTab1LayoutSub01.addWidget(textEditTab1BotonSelProfileDer)
        contenedorDerTab1LayoutSub01.addWidget(self.profileSelComboDer)
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
        tab1BotonVbox.addWidget(self.textEditTab1Boton)
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
        #rotar Imagen historicos Derecha
        self.rotarImagen180Der = False
        self.rotarImagen180Izq = False
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
        #creamos el qwidget que va a contener los elementos de cam online
        elementosIzqImagenOnlineRecord = QWidget()
        #elementosIzqImagenOnlineRecord.resize(640,640)
        #cramos el widget para contener el banner
        self.selCamaraOnlineHistoricos = QWidget()
        #creamos el layoutvertical para la coluimna de online
        layoutVerBanerCamOnline = QVBoxLayout()
        #geneero una tercer columna de informacion para la imagen a ser grabada
        textEditTab4BotonSelOnlineCam = QLabel()
        textEditTab4BotonSelOnlineCam.setText("Sel Online Cam: ")
        #selector de camara online
        self.camComboOnline = CamComboBox(self)
        self.camComboOnline.popupAboutToBeShown.connect(self.populateCamComboOnline)
        self.populateCamComboOnline() #completo el combo box
        #seteo el buddy
        textEditTab4BotonSelOnlineCam.setBuddy(self.camComboOnline)
        self.camComboOnline.setToolTip("selection of online camera")
        #creo el widget para contener el banner 
        self.elementosIzquierdaBanner = QWidget()
        #armo el layout horizontal del banner
        layoutHorBannerCamOnline = QHBoxLayout()
        layoutHorBannerCamOnline.addWidget(textEditTab4BotonSelOnlineCam)
        layoutHorBannerCamOnline.addWidget(self.camComboOnline)
        #armo un label para contener la imagen
        self.labelImagenOnlineRecorder_width = 640
        self.labelImagenOnlinerecorder_height = 480
        #agregamos el layout al banner para la camara online. Esta tomando la mitad del espacio
        #tenemos que ver bien como generar un tamaño fijo. similar al de los otros dos layouts 
        #de la misma pantalla. En los otros dos layouts tenemos definido el tamaño por el tamaño 
        #de  las imagenes pero en este layout no es asi. Vamos a tener que trabajar para poder 
        #definirlo de esa forma. Por ahora sacamos el widget contenedor y agregamos el layout 
        #directamente al widget general de camara online historico
        #self.selCamaraOnlineHistoricos.setLayout(layoutHorBannerCamOnline)
        #agreamos un texto debajo de la imagen para indicar el estado
        self.labelEstadoGuardadoImagen = QLabel(self)
        self.labelEstadoGuardadoImagen.setText("Listo para guardar")
        #creamos el label para contener la imagen
        self.labelImagenOnlineRecorder = QLabel(self)
        self.labelImagenOnlineRecorder.resize(self.labelImagenOnlineRecorder_width, self.labelImagenOnlinerecorder_height)
        #agregamos al baner vertical la imagen y el boton de seleccion
        layoutVerBanerCamOnline.addLayout(layoutHorBannerCamOnline)
        layoutVerBanerCamOnline.addWidget(self.labelImagenOnlineRecorder)
        layoutVerBanerCamOnline.addWidget(self.labelEstadoGuardadoImagen)
        #agregamos los botones
        self.playImageOnline = QPushButton("Play")
        self.playImageOnline.clicked.connect(self.playMostrarImageOnline)
        self.playImageOnline.setIcon(QIcon(os.path.join(basedir,"appIcons","control.png")))
        self.playImageOnline.setEnabled(False)
        self.stopImagenOnline = QPushButton("Stop")
        self.stopImagenOnline.clicked.connect(self.stopMostrarImagenOnline)
        self.stopImagenOnline.setIcon(QIcon(os.path.join(basedir,"appIcons","control-stop-square.png")))
        self.stopImagenOnline.setEnabled(False)
        self.recordImagenOnline = QPushButton("Record Start")
        self.recordImagenOnline.clicked.connect(self.startRecordImagenOnline)
        self.recordImagenOnline.setIcon(QIcon(os.path.join(basedir,"appIcons","control-record.png")))
        self.recordImagenOnline.setEnabled(False)        
        self.newFolderImagenOnline = QPushButton("New Folder")
        self.newFolderImagenOnline.clicked.connect(self.createNewFolderImagenOnline)
        self.newFolderImagenOnline.setIcon(QIcon(os.path.join(basedir,"appIcons","newspaper--plus.png")))
        self.newFolderImagenOnline.setEnabled(True)
        #self.moveFileImagenOnline = QPushButton("Move File")
        #self.moveFileImagenOnline.clicked.connect(self.makeMoveFileImagenOnline)
        #self.moveFileImagenOnline.setIcon(QIcon(os.path.join(basedir,"appIcons","document-move.png")))
        #self.moveFileImagenOnline.setEnabled(True)
        self.noRecordImagenOnline = QPushButton("Record Stop")
        self.noRecordImagenOnline.clicked.connect(self.stopRecordImagenOnline)
        self.noRecordImagenOnline.setIcon(QIcon(os.path.join(basedir,"appIcons","control-pause-record.png")))
        self.noRecordImagenOnline.setEnabled(False)
        self.renameFileImagenOnline = QPushButton("Rename File")
        self.renameFileImagenOnline.clicked.connect(self.makeRenameFileImagenOnline)
        self.renameFileImagenOnline.setIcon(QIcon(os.path.join(basedir,"appIcons","document-rename.png")))
        self.renameFileImagenOnline.setEnabled(True)
        self.editFileImagenOnline = QPushButton("Edit File")
        self.editFileImagenOnline.clicked.connect(self.makeEditFileImagenOnline)
        self.editFileImagenOnline.setIcon(QIcon(os.path.join(basedir,"appIcons", "edit-image.png")))
        self.editFileImagenOnline.setEnabled(True)
        self.deleteFileImagenOnline = QPushButton("Delete File")
        self.deleteFileImagenOnline.clicked.connect(self.makeDeleteFileImagenOnline)
        self.deleteFileImagenOnline.setIcon(QIcon(os.path.join(basedir, "appIcons", "node-delete-previous.png") ))
        self.deleteFileImagenOnline.setEnabled(True)
        #self.snapshotImagenOnline = QPushButton("Snapshot Image")
        #self.snapshotImagenOnline.clicked.connect(self.makeSnapshotImagenOnline)
        #self.snapshotImagenOnline.setIcon(QIcon(os.path.join(basedir, "appIcons", "camera--plus.png")))
        #self.snapshotImagenOnline.setEnabled(False)
        #self.botonLibre1ImagenOnline = QPushButton("Libre")
        #self.botonLibre1ImagenOnline.setEnabled(False)
        #self.botonLibre2ImagenOnline = QPushButton("Libre")
        #self.botonLibre2ImagenOnline.setEnabled(False)
        #self.botonLibre3ImagenOnline = QPushButton("Libre")
        #self.botonLibre3ImagenOnline.setEnabled(False)
        #self.botonLibre4ImagenOnline = QPushButton("Libre")
        #self.botonLibre4ImagenOnline.setEnabled(False)
        #creamos el grid layout
        layoutGridBotonesImagenOnline = QGridLayout()
        layoutGridBotonesImagenOnline.addWidget( self.playImageOnline, 0, 0)
        layoutGridBotonesImagenOnline.addWidget( self.stopImagenOnline, 0, 1)
        layoutGridBotonesImagenOnline.addWidget( self.recordImagenOnline, 0, 2)
        layoutGridBotonesImagenOnline.addWidget( self.newFolderImagenOnline, 0, 3)
        #layoutGridBotonesImagenOnline.addWidget( self.moveFileImagenOnline, 0, 4)
        #layoutGridBotonesImagenOnline.addWidget( self.botonLibre1ImagenOnline, 0, 5)
        #layoutGridBotonesImagenOnline.addWidget( self.botonLibre3ImagenOnline, 0, 6)
        layoutGridBotonesImagenOnline.addWidget( self.noRecordImagenOnline, 1, 0)
        layoutGridBotonesImagenOnline.addWidget( self.renameFileImagenOnline, 1, 1)
        layoutGridBotonesImagenOnline.addWidget( self.editFileImagenOnline, 1, 2)
        layoutGridBotonesImagenOnline.addWidget( self.deleteFileImagenOnline, 1, 3)
        #layoutGridBotonesImagenOnline.addWidget(self.snapshotImagenOnline, 1, 4)
        #layoutGridBotonesImagenOnline.addWidget(self.botonLibre2ImagenOnline, 1, 5)
        #layoutGridBotonesImagenOnline.addWidget(self.botonLibre4ImagenOnline, 1, 6)
        #agregamos el grid layout al layout vertical
        layoutVerBanerCamOnline.addLayout(layoutGridBotonesImagenOnline)
        elementosIzqImagenOnlineRecord.setLayout(layoutVerBanerCamOnline)
         
        
        #agrego la grafica para la ventana de historicos de la izquierda el grafico de curvas
        self.graficoHistoricoIzq = MplCanvas(self, width=300, height=2, dpi=100)
        #genero un dataframe de prueba para los historicos de la izquierda
        dfHistoricoIzq = pd.DataFrame([
            [0],
            [5],
            [2],
            [15],
            [4]
        ], columns=['line',])
        dfHistoricoIzq.plot(ax=self.graficoHistoricoIzq.axes)
        self._plot_refHistoricoIzq = None
        #agrego la grafica para la ventana de historicos de la derecha
        self.graficoHistoricoDer = MplCanvas(self, width=300, height=2, dpi=100)
        #genero un dataframe de prueba para los historicos de la derecha
        dfHistoricoDer = pd.DataFrame([
            [0],
            [5],
            [2],
            [15],
            [4]
        ], columns=['line',])
        dfHistoricoDer.plot(ax=self.graficoHistoricoDer.axes)
        self._plot_refHistoricoDer = None
        #agrego los indicadores de las mediciones 
        #vamos a tener dos para los historicos a la izquierda correspondientes a un par de ROIs
        #agregamos el label 1 de la izquierda 1
        self.label1MessurementRoiMax = QLabel("Max ROI:")        
        self.label1MessurementRoiMax.setToolTip("Messurement Max to region of interest 1")
        #agregamos el indicador 1 de la izquierda 1
        self.valorMessurement1 = "10.52" #este valor va a ser el resultado de la roi 1
        self.output1MessurementRoiMax = QLabel(self.valorMessurement1)        
        self.output1MessurementRoiMax.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.label1MessurementRoiMax.setBuddy(self.output1MessurementRoiMax)
        self.output1MessurementRoiMax.setFixedSize(QSize(50,40))        
        #agregamos el label 2 de la izquierda 1
        self.label2MessurementRoiMin = QLabel("Min ROI:")        
        self.label2MessurementRoiMin.setToolTip("Messurement Min to region of interest 1")
        #agregamos el indicador 2 de la izquierda 1
        self.valorMessurement2 = "105.2" #este valor va a ser el resultado de la roi 1 
        self.output2MessurementRoiMin = QLabel(self.valorMessurement2)
        self.output2MessurementRoiMin.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.label2MessurementRoiMin.setBuddy(self.output2MessurementRoiMin)
        self.output2MessurementRoiMin.setFixedSize(QSize(50,40))
        #agregamos el label 3 de la izquierda 1
        self.label3MessurementRoiAvg = QLabel("Avg ROI:")
        self.label3MessurementRoiAvg.setToolTip("Messurement Avg to region of interest 1")
        #agregamos el indicador 3 de la izquierda 1
        self.valorMessurement3 = "50.2" #este valor va a ser el resultado de la roi 1
        self.output3MessurementRoiAvg = QLabel(self.valorMessurement3)
        self.output3MessurementRoiAvg.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.label3MessurementRoiAvg.setBuddy(self.output3MessurementRoiAvg)
        self.output3MessurementRoiAvg.setFixedSize(QSize(50,40))
        #creo los elementos de la segunda roi para los elementos de la izquierda
        #agregamos el label 1 de la izquierda 2
        self.label4MessurementRoi2Median = QLabel("Median ROI:")        
        self.label4MessurementRoi2Median.setToolTip("Messurement Median to region of interest 1")
        #agregamos el indicador 1 de la izquierda 2
        self.valorMessurement1_2 = "10.52" #este valor va a ser el resultado de la roi 1
        self.output4MessurementRoi2Median = QLabel(self.valorMessurement1_2)        
        self.output4MessurementRoi2Median.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.label4MessurementRoi2Median.setBuddy(self.output4MessurementRoi2Median)
        self.output4MessurementRoi2Median.setFixedSize(QSize(50,40))
        #agregamos el label 2 de la izquierda 2
        self.label5MessurementRoi2Std = QLabel("Std ROI:")        
        self.label5MessurementRoi2Std.setToolTip("Messurement Std to region of interest 1")
        #agregamos el indicador 2 de la izquierda 1
        self.valorMessurement2_2 = "105.2" #este valor va a ser el resultado de la roi 1 
        self.output5MessurementRoi2Std = QLabel(self.valorMessurement2_2)
        self.output5MessurementRoi2Std.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.label5MessurementRoi2Std.setBuddy(self.output2MessurementRoiMin)
        self.output5MessurementRoi2Std.setFixedSize(QSize(50,40))
        #agregamos el label 3 de la izquierda 1
        self.label6MessurementRoi2Area = QLabel("Area ROI:")
        self.label6MessurementRoi2Area.setToolTip("Messurement Avg to region of interest 1")
        #agregamos el indicador 3 de la izquierda 1
        self.valorMessurement3_2 = "50.2" #este valor va a ser el resultado de la roi 1
        self.output6MessurementRoi2Area = QLabel(self.valorMessurement3_2)
        self.output6MessurementRoi2Area.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.label6MessurementRoi2Area.setBuddy(self.output6MessurementRoi2Area)
        self.output6MessurementRoi2Area.setFixedSize(QSize(50,40))
        #genero un widget para mostrar la curva  y en 
        #horizontal un widget vertical con los indicadores
        #de ROI de medicion
        #creo el widget horizontal
        subWindowHistory1CamSubH = QWidget()
        #creo el widget vertical 1
        subWindowHistory1CamSubV1 = QWidget()
        #creo el widget vertical 2
        subWindowHistory1CamSubV2 = QWidget()
        #creo el layout vertical
        subWindowHistory1CamSubVLayout = QVBoxLayout()
        subWindowHistory1CamSubVLayout.addWidget(self.label1MessurementRoiMax)
        subWindowHistory1CamSubVLayout.addWidget(self.output1MessurementRoiMax)
        subWindowHistory1CamSubVLayout.addWidget(self.label2MessurementRoiMin)
        subWindowHistory1CamSubVLayout.addWidget(self.output2MessurementRoiMin)
        subWindowHistory1CamSubVLayout.addWidget(self.label3MessurementRoiAvg)
        subWindowHistory1CamSubVLayout.addWidget(self.output3MessurementRoiAvg)
        subWindowHistory1CamSubV1.setLayout(subWindowHistory1CamSubVLayout)
        subWindowHistory1CamSubVLayout2 = QVBoxLayout()
        subWindowHistory1CamSubVLayout2.addWidget(self.label4MessurementRoi2Median)
        subWindowHistory1CamSubVLayout2.addWidget(self.output4MessurementRoi2Median)
        subWindowHistory1CamSubVLayout2.addWidget(self.label5MessurementRoi2Std)
        subWindowHistory1CamSubVLayout2.addWidget(self.output5MessurementRoi2Std)
        subWindowHistory1CamSubVLayout2.addWidget(self.label6MessurementRoi2Area)
        subWindowHistory1CamSubVLayout2.addWidget(self.output6MessurementRoi2Area)
        subWindowHistory1CamSubV2.setLayout(subWindowHistory1CamSubVLayout2)
        #creo el layout horizontal
        subWindowHistory1CamSubHLayout = QHBoxLayout()
        subWindowHistory1CamSubHLayout.addWidget(self.graficoHistoricoIzq)
        subWindowHistory1CamSubHLayout.addWidget(subWindowHistory1CamSubV1)
        subWindowHistory1CamSubHLayout.addWidget(subWindowHistory1CamSubV2)
        subWindowHistory1CamSubH.setLayout(subWindowHistory1CamSubHLayout)
        #agrego en la ventana a la derecha el grafico y los indicadores
        self.label1MessurementRoiMaxDer = QLabel("Max ROI:")
        self.label1MessurementRoiMaxDer.setToolTip("Messurement Max to region of interest 1")
        #agregamos el indicador 1 de la derecha 1
        self.valorMessurement1Der = "10.52"
        self.output1MessurementRoiMaxDer = QLabel(self.valorMessurement1Der)
        self.output1MessurementRoiMaxDer.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.label1MessurementRoiMaxDer.setBuddy(self.output1MessurementRoiMaxDer)   
        self.output1MessurementRoiMaxDer.setFixedSize(QSize(50,40))     
        #agregamos el label 2 de la derecha 1
        self.label2MessurementRoiMinDer = QLabel("Min ROI:")
        self.label2MessurementRoiMinDer.setToolTip("Messurement Min to region of interest 2")
        #agregamos el indicador 2 de la derecha 1
        self.valorMessurement2Der = "105.2"
        self.output2MessurementRoiMinDer = QLabel(self.valorMessurement2Der)
        self.output2MessurementRoiMinDer.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.label2MessurementRoiMinDer.setBuddy(self.output2MessurementRoiMinDer)
        self.output2MessurementRoiMinDer.setFixedSize(QSize(50,40))
        #agregamos el label 3 de la derecha 1
        self.label3MessurementRoiAvgDer = QLabel("Avg Roi:")        
        self.label3MessurementRoiAvgDer.setToolTip("Messurement Avg to region of interest 1")
        #agregamos el indicador 3 de la derecha 1
        self.valorMessurement3Der = "50.2"
        self.output3MessurementRoiAvgDer = QLabel(self.valorMessurement3Der)
        self.output3MessurementRoiAvgDer.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.label3MessurementRoiAvgDer.setBuddy(self.output3MessurementRoiAvgDer)
        self.output3MessurementRoiAvgDer.setFixedSize(QSize(50,40))
        #agregamos los indicadores de la Roi Der 2
        #agrego en la ventana a la derecha el grafico y los indicadores
        self.label4MessurementRoiMedianDer = QLabel("Median ROI:")
        self.label4MessurementRoiMedianDer.setToolTip("Messurement Median to region of interest 2")
        #agregamos el indicador 1 de la derecha 1
        self.valorMessurement1Der2 = "10.52"
        self.output4MessurementRoiMedianDer = QLabel(self.valorMessurement1Der2)
        self.output4MessurementRoiMedianDer.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.label4MessurementRoiMedianDer.setBuddy(self.output1MessurementRoiMaxDer)   
        self.output4MessurementRoiMedianDer.setFixedSize(QSize(50,40))     
        #agregamos el label 2 de la derecha 1
        self.label5MessurementRoiStdDer = QLabel("Std ROI:")
        self.label5MessurementRoiStdDer.setToolTip("Messurement Std to region of interest 2")
        #agregamos el indicador 2 de la derecha 1
        self.valorMessurementDer2 = "105.2"
        self.output5MessurementRoiStdDer = QLabel(self.valorMessurementDer2)
        self.output5MessurementRoiStdDer.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.label5MessurementRoiStdDer.setBuddy(self.output5MessurementRoiStdDer)
        self.output5MessurementRoiStdDer.setFixedSize(QSize(50,40))
        #agregamos el label 3 de la derecha 1
        self.label6MessurementRoiAreaDer = QLabel("Area Roi:")        
        self.label6MessurementRoiAreaDer.setToolTip("Messurement Area to region of interest 2")
        #agregamos el indicador 3 de la derecha 1
        self.valorMessurement3Der2 = "50.2"
        self.output6MessurementRoiAreaDer = QLabel(self.valorMessurement3Der2)
        self.output6MessurementRoiAreaDer.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
        self.label6MessurementRoiAreaDer.setBuddy(self.output6MessurementRoiAreaDer)
        self.output6MessurementRoiAreaDer.setFixedSize(QSize(50,40))
        #****
        #agregamos el widget para el contenedor de la der
        #agregamos el widget para el contenedor de los
        #indicadores de medicion
        subWindowHistory2CamSubH = QWidget()
        subWindowHistory2CamSubV1 = QWidget()
        subWindowHistory2CamSubV2 = QWidget()
        #creamos el layout vertical
        subWindowHistory2CamSubVlayout = QVBoxLayout()
        subWindowHistory2CamSubVlayout.addWidget(self.label1MessurementRoiMaxDer)
        subWindowHistory2CamSubVlayout.addWidget(self.output1MessurementRoiMaxDer)
        subWindowHistory2CamSubVlayout.addWidget(self.label2MessurementRoiMinDer)
        subWindowHistory2CamSubVlayout.addWidget(self.output2MessurementRoiMinDer)
        subWindowHistory2CamSubVlayout.addWidget(self.label3MessurementRoiAvgDer)
        subWindowHistory2CamSubVlayout.addWidget(self.output3MessurementRoiAvgDer)
        subWindowHistory2CamSubV1.setLayout(subWindowHistory2CamSubVlayout)
        subWindowHistory2CamSubVlayout2 = QVBoxLayout()
        subWindowHistory2CamSubVlayout2.addWidget(self.label4MessurementRoiMedianDer)
        subWindowHistory2CamSubVlayout2.addWidget(self.output4MessurementRoiMedianDer)
        subWindowHistory2CamSubVlayout2.addWidget(self.label5MessurementRoiStdDer)
        subWindowHistory2CamSubVlayout2.addWidget(self.output5MessurementRoiStdDer)
        subWindowHistory2CamSubVlayout2.addWidget(self.label6MessurementRoiAreaDer)
        subWindowHistory2CamSubVlayout2.addWidget(self.output6MessurementRoiAreaDer)
        subWindowHistory2CamSubV2.setLayout(subWindowHistory2CamSubVlayout2)
        
        #creamos el layout horizontal
        subWindowHistory2CamSubHLayout = QHBoxLayout()
        subWindowHistory2CamSubHLayout.addWidget(self.graficoHistoricoDer)
        subWindowHistory2CamSubHLayout.addWidget(subWindowHistory2CamSubV1)
        subWindowHistory2CamSubHLayout.addWidget(subWindowHistory2CamSubV2)
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
        bannerSelCam1.addWidget(self.botonLeerArchivoIzq)
        bannerSelCam1.addWidget(self.botonBackwardFileIzq)
        bannerSelCam1.addWidget(self.botonFordwardFileIzq)
        bannerSelCam2.addWidget(textEditTab4BotonSelCam2)
        bannerSelCam2.addWidget(self.camCombo2)
        bannerSelCam2.addWidget(self.dateCam2Image)
        bannerSelCam2.addWidget(self.img2ComboBoxReading)
        bannerSelCam2.addWidget(self.botonLeerArchivoDer)
        bannerSelCam2.addWidget(self.botonBackwardFileDer)
        bannerSelCam2.addWidget(self.botonFordwardFileDer)
        subWindowHistory1CamBanner.setLayout(bannerSelCam1)
        subWindowHistory2CamBanner.setLayout(bannerSelCam2)

        self.imageHistory1CamScene = ItemClickableGraphicsScene(0,0,384,288)#QGraphicsScene(0,0,0,0)        
        self.imageHistory1CamPixmap = QPixmap("imageCam1.jpg")
        #defino las funciones que se ejecutan cuando se dispara la señal desde la scene
        self.imageHistory1CamScene.itemClickedRect.connect(self.clickedRectImageHistory1CamScene)
        self.imageHistory1CamScene.itemClickedEllipse.connect(self.clickedEllipImageHistory1CamScene)
        self.imageHistory1CamScene.itemClickedLine.connect(self.clickedLineImageHIstory1CamScene)    
        #agrego a la scene la imagen por defecto
        self.imageHistory1PixmapItem = self.imageHistory1CamScene.addPixmap(self.imageHistory1CamPixmap)
        #creo la posicion inicial los rectangulos
        self.rect_list = [[0,0,70,35],
        [0,0,60,100]]
        #creo la posicion inicial elipse
        self.ellip_list = [[0,60,30,30],
        [0,0,30,30]]
        #creo la posicion inicial lineas
        self.line_list = [[0,0,80,80],
        [0,0,80,80,]]
        brush = QBrush(Qt.BDiagPattern)
        pen = QPen(Qt.red)
        pen.setWidth(2)
        #agrego las rois rect
        self.listaItemsRect = []
        for rect in self.rect_list:            
            rect_item = ClickableReSizedGraphicsRectItem(rect[0],rect[1],rect[2],rect[3], pen, brush)            
            rect_item.hide()
            self.listaItemsRect.append(rect_item)
        for itemRect in self.listaItemsRect:
            self.imageHistory1CamScene.addItem(itemRect)
        #agrego las rois ellipse
        self.listaItemsEllipse = []
        for ellipse in self.ellip_list:
            ellip_item = ClickableReSizedGraphicsEllipItem(ellipse[0],ellipse[1],ellipse[2],ellipse[3],pen,brush)
            ellip_item.hide()
            self.listaItemsEllipse.append(ellip_item)
        for itemEllip in self.listaItemsEllipse:
            self.imageHistory1CamScene.addItem(itemEllip)
        #agrego las rois lineas
        self.listaItemsLine = []
        indiceLinea = 0
        for line in self.line_list:
            line_item = ClickableReSizedGraphicsLineItem(line[0],line[1],line[2],line[3], pen,brush, indice=indiceLinea)
            line_item.hide()
            self.listaItemsLine.append(line_item)
            indiceLinea += 1
        for itemLine in self.listaItemsLine:
            self.imageHistory1CamScene.addItem(itemLine)
        #creo la escena
        self.imageHistory1ViewPixMapItem = ClickableItemView(self.imageHistory1CamScene)#QGraphicsView(self.imageHistory1CamScene)
        self.imageHistory1ViewPixMapItem.setRenderHint(QPainter.Antialiasing)        
        self.imageHistory1ViewPixMapItem.itemSelected.connect(self.cachedItemSeleccionado)
        #self.imageHistory1ViewPixMapItem.fitInView(QRectF(95,119,385,288),Qt.IgnoreAspectRatio)
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
        #girar 180 grados imagen
        self.buttonRot180ActionHistoryIzq = QAction(QIcon(os.path.join(basedir,"appIcons","screwdriver--pencil.png")),"Rot 180", self)
        self.buttonRot180ActionHistoryIzq.setStatusTip("Rotate 180 deg")
        self.buttonRot180ActionHistoryIzq.nombreBoton = "rotate 180"
        self.buttonRot180ActionHistoryIzq.triggered.connect(self.rotateimagenIzq)                          
        self.buttonRot180ActionHistoryIzq.setCheckable(True)
        #agrego los botones al toolbar
        toolBarImageHistoryIzq.addAction(self.buttonZoomInActionHistoryIzq)
        toolBarImageHistoryIzq.addAction(self.buttonZoomOutActionHistoryIzq)
        toolBarImageHistoryIzq.addAction(self.buttonRectRoiActionHistoryIzq)
        toolBarImageHistoryIzq.addAction(self.buttonEllipRoiActionHistoryIzq)
        toolBarImageHistoryIzq.addAction(self.buttonLineRoiActionHistoryIzq)
        toolBarImageHistoryIzq.addAction(self.buttonRot180ActionHistoryIzq)
        self.imgHistIzqWidget = QWidget() #contenedor para el toolbar y la imagen

                
        self.imgHistIzqWidgetLayout = QVBoxLayout() #defino el layout del toolbar y de la imagen
        self.imgHistIzqWidgetLayout.addWidget(toolBarImageHistoryIzq) #cargo el toolbar
        self.imgHistIzqWidgetLayout.addWidget(self.imageHistory1ViewPixMapItem) #cargo la imagen
        self.imgHistIzqWidget.setLayout(self.imgHistIzqWidgetLayout) #seteo el layout en el contenedor

        
        #genero la imagen 2
        self.imageHistory2CamScene = ItemClickableGraphicsScene(0,0,384,288)#QGraphicsScene(0,0,0,0)
        self.imageHistory2CamPixmap = QPixmap("imageCam2.jpg")
        #defino las funciones
        self.imageHistory2CamScene.itemClickedRect.connect(self.clickedRectImageHistory2CamScene)
        self.imageHistory2CamScene.itemClickedEllipse.connect(self.clickedEllipImageHistory2CamScene)
        self.imageHistory2CamScene.itemClickedLine.connect(self.clickedLineImageHIstory2CamScene)
        
        self.imageHistory2PixmapItem = self.imageHistory2CamScene.addPixmap(self.imageHistory2CamPixmap)
        #creo la posicion incial los rectangulos
        self.rect_list2 = [[0,0,70,35],
        [0,0,60,100]]
        #creo la posicion inicial elipse
        self.ellip_list2 = [[0,0,30,30],
        [0,0,30,30]]
        #creo la posicion inicial linea
        self.line_list2 = [[0,0,80,80],
        [0,0,80,80]]
        brush = QBrush(Qt.BDiagPattern)
        pen = QPen(Qt.red)
        pen.setWidth(2)
        #agrego las rois rect
        self.listaItemsRect2 = []
        for rect2 in self.rect_list2:
            rect_item2 = ClickableReSizedGraphicsRectItem(rect2[0],rect2[1],rect2[2],rect2[3],pen,brush)
            rect_item2.hide()
            self.listaItemsRect2.append(rect_item2)
        for itemRect2 in self.listaItemsRect2:
            self.imageHistory2CamScene.addItem(itemRect2)
        #agrego las rois ellipse
        self.listaItemsEllipse2 = []
        for ellipse2 in self.ellip_list2:
            ellip_item2 = ClickableReSizedGraphicsEllipItem(ellipse2[0],ellipse2[1],ellipse2[2],ellipse2[3],pen,brush)
            ellip_item2.hide()
            self.listaItemsEllipse2.append(ellip_item2)
        for itemEllip2 in self.listaItemsEllipse2:
            self.imageHistory2CamScene.addItem(itemEllip2)
        #agrego las rois lineas
        self.listaItemsLine2 = []
        indiceLinea = 0
        for line2 in self.line_list2:
            line_item2 = ClickableReSizedGraphicsLineItem(line2[0],line2[1],line2[2],line2[3],pen,brush,indiceLinea)
            line_item2.hide()
            self.listaItemsLine2.append(line_item2)
            indiceLinea += 1
        for itemLine2 in self.listaItemsLine2:
            self.imageHistory2CamScene.addItem(itemLine2)
        #creo la escena
        self.imageHistory2ViewPixMapItem = ClickableItemView(self.imageHistory2CamScene)#QGraphicsView(self.imageHistory2CamScene)
        self.imageHistory2ViewPixMapItem.setRenderHint(QPainter.Antialiasing)
        self.imageHistory2ViewPixMapItem.itemSelected.connect(self.cachedItemSeleccionado)
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
        #agrego el boton de rotar 180
        self.buttonRot180ActionHistoryDer = QAction(QIcon(os.path.join(basedir,"appIcons","screwdriver--pencil.png")),"Roi Line",self)        #agrego los botones al toolbar
        self.buttonRot180ActionHistoryDer.setStatusTip("Rotate 180 de")
        self.buttonRot180ActionHistoryDer.nombreBoton = "rotate 180"
        self.buttonRot180ActionHistoryDer.triggered.connect(self.rotateimagenDer)
        self.buttonRot180ActionHistoryDer.setCheckable(True)
        #amo los datos
        toolBarImageHistoryDer.addAction(self.buttonZoomInActionHistoryDer)
        toolBarImageHistoryDer.addAction(self.buttonZoomOutActionHistoryDer)
        toolBarImageHistoryDer.addAction(self.buttonRectRoiActionHistoryDer)
        toolBarImageHistoryDer.addAction(self.buttonEllipRoiActionHistoryDer)
        toolBarImageHistoryDer.addAction(self.buttonLineRoiActionHistoryDer)
        toolBarImageHistoryDer.addAction(self.buttonRot180ActionHistoryDer)
        
        
        self.imgHistDerWidget = QWidget() #contenedor para el toolbar y la imagen a la derecha del historico

        self.imgHistDerWidgetLayout = QVBoxLayout() #defino el layout del contenedor de toolbar e imagen a derecha
        self.imgHistDerWidgetLayout.addWidget(toolBarImageHistoryDer)
        self.imgHistDerWidgetLayout.addWidget(self.imageHistory2ViewPixMapItem)
        self.imgHistDerWidget.setLayout(self.imgHistDerWidgetLayout)

        #adjunto la imagen
        subHistory1VBox = QVBoxLayout() #creo un layout vertical para los historicos de la camara 1
        subHistory2VBox = QVBoxLayout() #creo un layout vertical para los historicos de la camara 2 
        tab4BotonHBox = QHBoxLayout() #creo un layou horizontal para contener los dos historicos el de la camara 1 y 2
        tab4BotonHBox.setContentsMargins(5,5,5,5)        
        subHistory1VBox.addWidget(subWindowHistory1CamBanner) #agrego al historico vertical el banner de la camara 1
        subHistory1VBox.addWidget(self.imgHistIzqWidget)#imageHistory1ViewPixMapItem) #agrego al historico vertical 1 la imagen registrada       
        subHistory1VBox.addWidget(self.roisComboHistoricoIzquierda)
        subHistory1VBox.addWidget(subWindowHistory1CamSubH)
        
        subHistory2VBox.addWidget(subWindowHistory2CamBanner) #agrego al historico vertical el banner de la camara 2
        subHistory2VBox.addWidget(self.imgHistDerWidget) #agrego al historico vertical 2 la imagen registrada        
        subHistory2VBox.addWidget(self.roisComboHistoricoDerecha)
        subHistory2VBox.addWidget(subWindowHistory2CamSubH)
        
        subWindowHistory1Cam.setLayout(subHistory1VBox) #selecciono el layout vertical 1 para el widget history cam 1
        subWindowHistory2Cam.setLayout(subHistory2VBox) #selecciono el layout vertical 2 para el widget history cam 2       
        #agregamos el layout vertical
        tab4BotonHBox.addWidget(elementosIzqImagenOnlineRecord)
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
        #El preset 1 es ajuste de foco
        labelValuePreset1Cam1 = QLabel("Change Focus Position")     
        labelValuePreset1Cam1.setFixedSize(QSize(350,24))
        labelValuePreset1Cam1.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset1Cam1 = QFont("Times",10,QtGui.QFont.Light) #defino un objeto fuente, donde configuro que sea bolt y el tipo de fuente
        fuenteLabelValuePreset1Cam1.setBold(True)
        labelValuePreset1Cam1.setFont(fuenteLabelValuePreset1Cam1)        
        labelValuePreset1Cam1.setAlignment(QtCore.Qt.AlignCenter)
        valuePreset1Cam1 = AnimatedToggle()
        valuePreset1Cam1.setFixedSize(valuePreset1Cam1.sizeHint())
        valuePreset1Cam1.setToolTip("Toggle to change position focus cam 1")
        #Defino la funcion asociada al set y reset de los presets
        enablePreset1Cam1 = partial(self.popUpConfiguracionPresetCam1, valuePreset1Cam1)
        disablePreset1Cam1 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset1Cam1)
        valuePreset1Cam1.stateChanged.connect(lambda x: enablePreset1Cam1() if x else disablePreset1Cam1())
        #        
        contenedorValuePreset1Cam1Layout.addWidget(labelValuePreset1Cam1)
        contenedorValuePreset1Cam1Layout.addWidget(valuePreset1Cam1)
        #El preset 2 es seleccion de rango de temperatura de la camara, los tres rangos el 0 - 1 - 2
        contenedorValuePreset2Cam1Layout = QHBoxLayout()
        labelValuePreset2Cam1 = QLabel("Change Temperature Range Selected")
        labelValuePreset2Cam1.setFixedSize(QSize(350,24))
        labelValuePreset2Cam1.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset2Cam1 = QFont("Times", 10, QtGui.QFont.Light)        
        fuenteLabelValuePreset2Cam1.setBold(True)
        labelValuePreset2Cam1.setFont(fuenteLabelValuePreset2Cam1)
        labelValuePreset2Cam1.setAlignment(QtCore.Qt.AlignCenter)
        valuePreset2Cam1 = AnimatedToggle()
        valuePreset2Cam1.setFixedSize(valuePreset2Cam1.sizeHint())
        valuePreset2Cam1.setToolTip("Toggle to change range (-20,100)-(0,250)-(150,900) of camera")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset2Cam1 = partial(self.popUpConfiguracionPreset2Cam1, valuePreset2Cam1)
        disablePreset2Cam1 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset2Cam1)
        valuePreset2Cam1.stateChanged.connect(lambda x: enablePreset2Cam1() if x else disablePreset2Cam1())
        #  
        #
        contenedorValuePreset2Cam1Layout.addWidget(labelValuePreset2Cam1)
        contenedorValuePreset2Cam1Layout.addWidget(valuePreset2Cam1)    
        #El preset 3 es definicion de limites minimos y maximos para la paleta de temperatura 
        contenedorValuePreset3Cam1Layout = QHBoxLayout()
        labelValuePreset3Cam1 = QLabel("Change Manual Temperature Limits to Pallete")
        labelValuePreset3Cam1.setFixedSize(QSize(350,24))        
        labelValuePreset3Cam1.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset3Cam1 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset3Cam1.setBold(True)
        labelValuePreset3Cam1.setFont(fuenteLabelValuePreset3Cam1)
        labelValuePreset3Cam1.setAlignment(QtCore.Qt.AlignCenter)
        valuePreset3Cam1 = AnimatedToggle()
        valuePreset3Cam1.setFixedSize(valuePreset3Cam1.sizeHint())
        valuePreset3Cam1.setToolTip("Toggle to change Min and Max Limits to Pallete only in Manual Selected")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset3Cam1 = partial(self.popUpConfiguracionPreset3Cam1, valuePreset3Cam1)
        disablePreset3Cam1 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset3Cam1)
        valuePreset3Cam1.stateChanged.connect(lambda x: enablePreset3Cam1() if x else disablePreset3Cam1())
        # 
        #
        contenedorValuePreset3Cam1Layout.addWidget(labelValuePreset3Cam1)
        contenedorValuePreset3Cam1Layout.addWidget(valuePreset3Cam1)
        #El preset 4 es seleccion de tipo de ajuste para la paleta, puede ser Manual - Automatico MinMax - Automatico Sigma1 - Automatico Sigma3
        contenedorValuePreset4Cam1Layout = QHBoxLayout()
        labelValuePreset4Cam1 = QLabel("Change Automatic vs Manual Type Adjust Pallete")
        labelValuePreset4Cam1.setFixedSize(QSize(350,24))
        labelValuePreset4Cam1.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset4Cam1 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset4Cam1.setBold(True)
        labelValuePreset4Cam1.setFont(fuenteLabelValuePreset4Cam1)
        labelValuePreset4Cam1.setAlignment(QtCore.Qt.AlignCenter)
        valuePreset4Cam1 = AnimatedToggle()
        valuePreset4Cam1.setFixedSize(valuePreset4Cam1.sizeHint())
        valuePreset4Cam1.setToolTip("Toggle to change type of adjust of limits pallete Manual Automatic Sigma1 Sigma3")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset4Cam1 = partial(self.popUpConfiguracionPreset4Cam1, valuePreset4Cam1)
        disablePreset4Cam1 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset4Cam1)
        valuePreset4Cam1.stateChanged.connect(lambda x: enablePreset4Cam1() if x else disablePreset4Cam1())
        # 
        #
        contenedorValuePreset4Cam1Layout.addWidget(labelValuePreset4Cam1)
        contenedorValuePreset4Cam1Layout.addWidget(valuePreset4Cam1)
        #preset 5
        contenedorValuePreset5Cam1Layout = QHBoxLayout()
        labelValuePreset5Cam1 = QLabel("Change Type of Pallete")
        labelValuePreset5Cam1.setFixedSize(QSize(350,24))
        labelValuePreset5Cam1.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset5Cam1 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset5Cam1.setBold(True)
        labelValuePreset5Cam1.setFont(fuenteLabelValuePreset5Cam1)
        labelValuePreset5Cam1.setAlignment(QtCore.Qt.AlignCenter)
        valuePreset5Cam1 = AnimatedToggle()
        valuePreset5Cam1.setFixedSize(valuePreset5Cam1.sizeHint())
        valuePreset5Cam1.setToolTip("Toggle to change type of pallete to AlarmBlue-AlarmBlueHi-GrayBW-GrayWB-AlarmGreen-Iron-IronHi-Medical-Rainbow-RainbowHi-AlarmRed")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset5Cam1 = partial(self.popUpConfiguracionPreset5Cam1, valuePreset5Cam1)
        disablePreset5Cam1 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset5Cam1)
        valuePreset5Cam1.stateChanged.connect(lambda x: enablePreset5Cam1() if x else disablePreset5Cam1())
        #
        #
        contenedorValuePreset5Cam1Layout.addWidget(labelValuePreset5Cam1)
        contenedorValuePreset5Cam1Layout.addWidget(valuePreset5Cam1)        
        #preset 6
        contenedorValuePreset6Cam1Layout = QHBoxLayout()
        labelValuePreset6Cam1 = QLabel("Change Ambient Temperature of Camera")
        labelValuePreset6Cam1.setFixedSize(QSize(350,24))
        labelValuePreset6Cam1.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset6Cam1 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset6Cam1.setBold(True)
        labelValuePreset6Cam1.setFont(fuenteLabelValuePreset6Cam1)
        labelValuePreset6Cam1.setAlignment(QtCore.Qt.AlignCenter)       
        valuePreset6Cam1 = AnimatedToggle()
        valuePreset6Cam1.setFixedSize(valuePreset6Cam1.sizeHint())
        valuePreset6Cam1.setToolTip("Toggle to change ambient temperature")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset6Cam1 = partial(self.popUpConfiguracionPreset6Cam1, valuePreset6Cam1)
        disablePreset6Cam1 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset6Cam1)
        valuePreset6Cam1.stateChanged.connect(lambda x: enablePreset6Cam1() if x else disablePreset6Cam1())
        #
        #
        contenedorValuePreset6Cam1Layout.addWidget(labelValuePreset6Cam1)
        contenedorValuePreset6Cam1Layout.addWidget(valuePreset6Cam1)
        #preset 7
        contenedorValuePreset7Cam1Layout = QHBoxLayout()
        labelValuePreset7Cam1 = QLabel("Change Transmisivity of Camera")
        labelValuePreset7Cam1.setFixedSize(QSize(350,24))
        labelValuePreset7Cam1.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset7Cam1 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset7Cam1.setBold(True)
        labelValuePreset7Cam1.setFont(fuenteLabelValuePreset7Cam1)
        labelValuePreset7Cam1.setAlignment(QtCore.Qt.AlignCenter)
        valuePreset7Cam1 = AnimatedToggle()
        valuePreset7Cam1.setFixedSize(valuePreset7Cam1.sizeHint())
        valuePreset7Cam1.setToolTip("Toggle to change transmisivity of camera")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset7Cam1 = partial(self.popUpConfiguracionPreset7Cam1, valuePreset7Cam1)
        disablePreset7Cam1 = partial(self.popUpRestartConfiguracionPresetCam1, valuePreset7Cam1)
        valuePreset7Cam1.stateChanged.connect(lambda x: enablePreset7Cam1() if x else disablePreset7Cam1())
        #
        #
        contenedorValuePreset7Cam1Layout.addWidget(labelValuePreset7Cam1)
        contenedorValuePreset7Cam1Layout.addWidget(valuePreset7Cam1)
        #preset 8
        contenedorValuePreset8Cam1Layout = QHBoxLayout()
        labelValuePreset8Cam1 = QLabel("Change Emisivity of Objet to Messurement")
        labelValuePreset8Cam1.setFixedSize(QSize(350,24))
        labelValuePreset8Cam1.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset8Cam1 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset8Cam1.setBold(True)
        labelValuePreset8Cam1.setFont(fuenteLabelValuePreset8Cam1)
        labelValuePreset8Cam1.setAlignment(QtCore.Qt.AlignCenter)
        valuePreset8Cam1 = AnimatedToggle()
        valuePreset8Cam1.setFixedSize(valuePreset8Cam1.sizeHint())
        valuePreset8Cam1.setToolTip("Toggle to change emisivity of object")
        #
        #Defino la funcion asociada al set y reset de los presets
        enablePreset8Cam1 = partial(self.popUpConfiguracionPreset8Cam1, valuePreset8Cam1)
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
        labelValuePreset1Cam2 = QLabel("Change Focus Position")
        labelValuePreset1Cam2.setFixedSize(QSize(350,24))
        labelValuePreset1Cam2.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset1Cam2 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset1Cam2.setBold(True)
        labelValuePreset1Cam2.setFont(fuenteLabelValuePreset1Cam2)
        labelValuePreset1Cam2.setAlignment(QtCore.Qt.AlignCenter)
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
        labelValuePreset2Cam2 = QLabel("Change Temperature Range Selected")
        labelValuePreset2Cam2.setFixedSize(QSize(350,24))
        labelValuePreset2Cam2.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset2Cam2 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset2Cam2.setBold(True)
        labelValuePreset2Cam2.setFont(fuenteLabelValuePreset2Cam2)
        labelValuePreset2Cam2.setAlignment(QtCore.Qt.AlignCenter)
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
        labelValuePreset3Cam2 = QLabel("Change Manual Temperature Limits to Pallete")
        labelValuePreset3Cam2.setFixedSize(QSize(350,24))
        labelValuePreset3Cam2.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset3Cam2 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset3Cam2.setBold(True)
        labelValuePreset3Cam2.setFont(fuenteLabelValuePreset3Cam2)
        labelValuePreset3Cam2.setAlignment(QtCore.Qt.AlignCenter)
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
        labelValuePreset4Cam2 = QLabel("Change Automatic vs Manual Type Adjust Pallete")
        labelValuePreset4Cam2.setFixedSize(QSize(350,24))
        labelValuePreset4Cam2.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset4Cam2 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset4Cam2.setBold(True)
        labelValuePreset4Cam2.setFont(fuenteLabelValuePreset4Cam2)
        labelValuePreset4Cam2.setAlignment(QtCore.Qt.AlignCenter)
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
        labelValuePreset5Cam2 = QLabel("Change Type of Pallete")
        labelValuePreset5Cam2.setFixedSize(QSize(350,24))
        labelValuePreset5Cam2.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset5Cam2 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset5Cam2.setBold(True)
        labelValuePreset5Cam2.setFont(fuenteLabelValuePreset5Cam2)
        labelValuePreset5Cam2.setAlignment(QtCore.Qt.AlignCenter)
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
        labelValuePreset6Cam2 = QLabel("Change Ambient Temperature of Camera")
        labelValuePreset6Cam2.setFixedSize(QSize(350,24))
        labelValuePreset6Cam2.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset6Cam2 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset6Cam2.setBold(True)
        labelValuePreset6Cam2.setFont(fuenteLabelValuePreset6Cam2)
        labelValuePreset6Cam2.setAlignment(QtCore.Qt.AlignCenter)        
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
        labelValuePreset7Cam2 = QLabel("Change Transmisivity of Camera")
        labelValuePreset7Cam2.setFixedSize(QSize(350,24))
        labelValuePreset7Cam2.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset7Cam2 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset7Cam2.setBold(True)
        labelValuePreset7Cam2.setFont(fuenteLabelValuePreset7Cam2)
        labelValuePreset7Cam2.setAlignment(QtCore.Qt.AlignCenter)
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
        labelValuePreset8Cam2 = QLabel("Change Emisivity of Objet to Messurement")
        labelValuePreset8Cam2.setFixedSize(QSize(350,24))
        labelValuePreset8Cam2.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset8Cam2 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset8Cam2.setBold(True)
        labelValuePreset8Cam2.setFont(fuenteLabelValuePreset8Cam2)
        labelValuePreset8Cam2.setAlignment(QtCore.Qt.AlignCenter)
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
        labelValuePreset1Cam3 = QLabel("Change Focus Position")
        labelValuePreset1Cam3.setFixedSize(QSize(350,24))
        labelValuePreset1Cam3.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset1Cam3 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset1Cam3.setBold(True)
        labelValuePreset1Cam3.setFont(fuenteLabelValuePreset1Cam3)
        labelValuePreset1Cam3.setAlignment(QtCore.Qt.AlignCenter)
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
        labelValuePreset2Cam3 = QLabel("Change Temperature Range Selected")
        labelValuePreset2Cam3.setFixedSize(QSize(350,24))
        labelValuePreset2Cam3.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset2Cam2 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset2Cam2.setBold(True)
        labelValuePreset2Cam3.setFont(fuenteLabelValuePreset2Cam2)
        labelValuePreset2Cam3.setAlignment(QtCore.Qt.AlignCenter)        
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
        labelValuePreset3Cam3 = QLabel("Change Manual Temperature Limits to Pallete")
        labelValuePreset3Cam3.setFixedSize(QSize(350,24))
        labelValuePreset3Cam3.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset3Cam3 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset3Cam3.setBold(True)
        labelValuePreset3Cam3.setFont(fuenteLabelValuePreset3Cam3)
        labelValuePreset3Cam3.setAlignment(QtCore.Qt.AlignCenter)
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
        labelValuePreset4Cam3 = QLabel("Change Automatic vs Manual Type Adjust Pallete")
        labelValuePreset4Cam3.setFixedSize(QSize(350,24))
        labelValuePreset4Cam3.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset4Cam3 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset4Cam3.setBold(True)
        labelValuePreset4Cam3.setFont(fuenteLabelValuePreset4Cam3)
        labelValuePreset4Cam3.setAlignment(QtCore.Qt.AlignCenter)
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
        labelValuePreset5Cam3 = QLabel("Change Type of Pallete")
        labelValuePreset5Cam3.setFixedSize(QSize(350,24))
        labelValuePreset5Cam3.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset5Cam3 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset5Cam3.setBold(True)
        labelValuePreset5Cam3.setFont(fuenteLabelValuePreset5Cam3)
        labelValuePreset5Cam3.setAlignment(QtCore.Qt.AlignCenter)
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
        labelValuePreset6Cam3 = QLabel("Change Ambient Temperature of Camera")
        labelValuePreset6Cam3.setFixedSize(QSize(350,24))
        labelValuePreset6Cam3.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset6Cam3 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset6Cam3.setBold(True)
        labelValuePreset6Cam3.setFont(fuenteLabelValuePreset6Cam3)
        labelValuePreset6Cam3.setAlignment(QtCore.Qt.AlignCenter)
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
        labelValuePreset7Cam3 = QLabel("Change Transmisivity of Camera")
        labelValuePreset7Cam3.setFixedSize(QSize(350,24))
        labelValuePreset7Cam3.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset7Cam3 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset7Cam3.setBold(True)
        labelValuePreset7Cam3.setFont(fuenteLabelValuePreset7Cam3)
        labelValuePreset7Cam3.setAlignment(QtCore.Qt.AlignCenter)
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
        labelValuePreset8Cam3 = QLabel("Change Emisivity of Objet to Messurement")
        labelValuePreset8Cam3.setFixedSize(QSize(350,24))
        labelValuePreset8Cam3.setStyleSheet(
            "background-color: gray; border-width: 2px; border-color: darkkhaki; border-style: solid; border-radius: 5; padding: 3px; min-width: 9ex; min-height: 2.5ex; color: black;")
        fuenteLabelValuePreset8Cam3 = QFont("Times", 10, QtGui.QFont.Light)
        fuenteLabelValuePreset8Cam3.setBold(True)
        labelValuePreset8Cam3.setFont(fuenteLabelValuePreset8Cam3)
        labelValuePreset8Cam3.setAlignment(QtCore.Qt.AlignCenter)

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
        self.pushButton1Cam1.setDefault(False)
        self.pushButton1Cam1.clicked.connect(self.mostraPantallaCam1)
        self.pushButton1Cam1.setIcon(QIcon(os.path.join(basedir,"appIcons","camera-lens.png")))
        self.pushButton1Cam1.setToolTip("Show Image and Trending of Camera 1")
        self.pushButton1Cam1.setCheckable(True)

        self.pushButton2Cam2 = QPushButton("Camera 2")
        self.pushButton2Cam2.setDefault(False)
        self.pushButton2Cam2.clicked.connect(self.mostraPantallaCam2)
        self.pushButton2Cam2.setIcon(QIcon(os.path.join(basedir,"appIcons","camera-lens.png")))
        self.pushButton2Cam2.setToolTip("Show Image and Trending of Camera 2")
        self.pushButton2Cam2.setCheckable(True)

        self.pushButton3Cam3 = QPushButton("Camera 3")
        self.pushButton3Cam3.setDefault(False)
        self.pushButton3Cam3.clicked.connect(self.mostraPantallaCam3)
        self.pushButton3Cam3.setIcon(QIcon(os.path.join(basedir,"appIcons","camera-lens.png")))
        self.pushButton3Cam3.setToolTip("Show Image and Trending of Camera 3")
        self.pushButton3Cam3.setCheckable(True)

        self.pushButton4Recorder = QPushButton("Recorded")
        self.pushButton4Recorder.setDefault(False)
        self.pushButton4Recorder.clicked.connect(self.mostraPantallaRecorder)
        self.pushButton4Recorder.setIcon(QIcon(os.path.join(basedir,"appIcons","disk-return.png")))
        self.pushButton4Recorder.setToolTip("Show Image and Trending Recorded")
        self.pushButton4Recorder.setCheckable(True)

        self.pushButton5Config = QPushButton("ConfCam")
        self.pushButton5Config.setDefault(False)
        self.pushButton5Config.clicked.connect(self.mostraPantallaConfig)
        self.pushButton5Config.setIcon(QIcon(os.path.join(basedir,"appIcons","toolbox.png")))
        self.pushButton5Config.setToolTip("Show Configuration Parameters of Cameras")
        self.pushButton5Config.setCheckable(True)

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
    #funciones asociadas a los botones de guardado de imagenes
    def playMostrarImageOnline(self):
        print("play")
        self.mostrarImagenPantallaRecorded = True
        #habilito los controles permitidos en la adquisicion
        self.playImageOnline.setEnabled(False)
        self.stopImagenOnline.setEnabled(True)
        self.recordImagenOnline.setEnabled(True)
        self.newFolderImagenOnline.setEnabled(False)
        #self.moveFileImagenOnline.setEnabled(False)
        self.noRecordImagenOnline.setEnabled(False)
        self.renameFileImagenOnline.setEnabled(False)
        self.editFileImagenOnline.setEnabled(False)
        self.deleteFileImagenOnline.setEnabled(False)
        #self.snapshotImagenOnline.setEnabled(True)        
    def stopMostrarImagenOnline(self):
        print("stop")
        self.mostrarImagenPantallaRecorded = False
        #habilito los controles permitidos en la no adquisicion
        self.playImageOnline.setEnabled(True)
        self.stopImagenOnline.setEnabled(False)
        self.recordImagenOnline.setEnabled(False)
        self.newFolderImagenOnline.setEnabled(True)
        #self.moveFileImagenOnline.setEnabled(True)
        self.noRecordImagenOnline.setEnabled(False)
        self.renameFileImagenOnline.setEnabled(True)
        self.editFileImagenOnline.setEnabled(True)
        self.deleteFileImagenOnline.setEnabled(True)
        #self.snapshotImagenOnline.setEnabled(False)
    def startRecordImagenOnline(self):
        print("start record")
        self.recordImagenOnline.setEnabled(False)
        self.noRecordImagenOnline.setEnabled(True)
        self.botonLeerArchivoIzq.setEnabled(False)
        self.botonLeerArchivoDer.setEnabled(False)
        self.labelEstadoGuardadoImagen.setText("Guardando en memoria !")
        #cargamos la funcion que guarda en el  hilo de guardado de imagen
        threads = []
        for n in range(2):
            t = Thread(target=saveQueueImageInDisk, args=(self.queueDatosOrigenThermal,self.queueDatosOrigenCV,self.pathDirImagesFile))
            t.start()
            threads.append(t)
        #notifico que se debe cargar la queue
        self.flagQueueReady = True
        self.noRecordImagenOnline.setEnabled(True)
        self.recordImagenOnline.setEnabled(False)
    def createNewFolderImagenOnline(self):
        print("new folder")
        self.pathDirImagesFile = asyncio.run(crearDirectorioAsincronico())
        #falta la habilitacion de guardar e inhabilitar los botones 
        self.recordImagenOnline.setEnabled(True) #habilito guardar imagen
        self.newFolderImagenOnline.setEnabled(False) #deshabilito el crear nuevo archivo
        self.botonLeerArchivoIzq.setEnabled(True) #habilito los botones de busqueda de archivo Izq
        self.botonLeerArchivoDer.setEnabled(True) #habilito los botones de busqueda de archivo Der
        self.playImageOnline.setEnabled(True)
        #no vamos a poner la habilitacion de leer porque asumimos que lo
        #vamosa buscar con las herramientas en el centro y extremo derecho 
        #de la pantalla
    def makeMoveFileImagenOnline(self):
        print("move file")
        #no implementamos la funcion porque en el so de windows 
        #no nos esta permitiendo realizarla
    def stopRecordImagenOnline(self):
        print("detener record file")
        self.recordImagenOnline.setEnabled(True)
        self.noRecordImagenOnline.setEnabled(False)
        #detenemos el flag de guardar archivo
        self.flagQueueReady = False #indico que no encole mas imagenes
        for i in range(2):
            self.queueDatosOrigenThermal.put(_sentinelStopThread)
            self.queueDatosOrigenCV.put(_sentinelStopThread)
        print(i)
        #aca tiene que dar la habilitacion creando el hilo que termina
        #los dos hilos tomando el ultimo lugar de la barrera
        #self.botonNuevoFolder
        miStatusGuardadoThread = statusGuardadoThread(self.botonLeerArchivoIzq, self.botonLeerArchivoDer, self.labelEstadoGuardadoImagen)
        miStatusGuardadoThread.start()

    def makeRenameFileImagenOnline(self):
        print("rename file")
        asyncio.run(renombrarArchivoAsincronico())
    def makeEditFileImagenOnline(self):
        print("edit image")
        asyncio.run(modificarArchivoAsincronico())
    def makeDeleteFileImagenOnline(self):
        print("delete file")
        asyncio.run(borrarArchivoAsincronico())
    def makeSnapshotImagenOnline(self):
        print("snapshot image")
        #leemos el contenido
        asyncio.run(leerContenidoAsincronico())
    #***************************************************
    #funcion para obtener estampa de tiempo actual
    def now(self, x):
        n = datetime.datetime.now()
        return n + datetime.timedelta(milliseconds=x)
    #update el grafico izquierda en el tiempo Eje X temporal
    def update_plot_dfTab1Izq(self):
        #self.XTab1Izq=self.roiSelComboIzq.currentText()                        
        self.XTab1Izq = self.roiSelComboIzq.currentText() #actualizo que debo graficar
        self.XTab1Izq1 = self.profileSelComboIzq.currentText()
        self.XTab1Der = self.roiSelComboDer.currentText()
        self.XTab1Der1 = self.profileSelComboDer.currentText()
        if self.XTab1Izq == 'ROI Rect1 Min':
            #cargamos el trendin de roi rect 1 minimo
            self.ydataIzq = np.append(self.ydataIzq[1:],self.rect1ValueMin)#float(self.valor1IndTab1MinRoi1Rect.text()))
        elif self.XTab1Izq == 'ROI Line1 Min':
            #agergo la medicion de la roi min line 1
            self.ydataIzq = np.append(self.ydataIzq[1:],self.line1ValueMin)#float(self.valor11IndTab1MinRoi1Line.text()))
        elif self.XTab1Izq == 'ROI Ellip1 Min':
            #agergo la medicion de la roi min elipse 1
            self.ydataIzq = np.append(self.ydataIzq[1:],self.ellipse1ValueMin)#float(self.valor12IndTab1MinRoi1Ellipse.text()))
        elif self.XTab1Izq == 'ROI Rect1 Avg':
            #agergo la medicion de la roi avg rect 1
            self.ydataIzq = np.append(self.ydataIzq[1:],self.rect1ValueAvg)#float(self.valor2IndTab1AvgRoi1Rect.text()))
        elif self.XTab1Izq == 'ROI Line1 Avg':
            #agergo la medicion de la roi avg line 1
            self.ydataIzq = np.append(self.ydataIzq[1:],self.line1ValueAvg)#float(self.valor21IndTab1AvgRoi1Line.text()))
        elif self.XTab1Izq == 'ROI Ellip1 Avg':
            #agergo la medicion de la roi avg elipse 1
            self.ydataIzq = np.append(self.ydataIzq[1:],self.ellipse1ValueAvg)#float(self.valor22IndTab1AvgRoi1Ellipse.text()))
        elif self.XTab1Izq == 'ROI Rect1 Max':
            #agergo la medicion de la roi max rect 1
            self.ydataIzq = np.append(self.ydataIzq[1:],self.rect1ValueMax)#float(self.valor3IndTab1MaxRoi1Rect.text()))
        elif self.XTab1Izq == 'ROI Line1 Max':
            #agergo la medicion de la roi max line 1
            self.ydataIzq = np.append(self.ydataIzq[1:],self.line1ValueMax)#float(self.valor31IndTab1MaxRoi1Line.text()))
        elif self.XTab1Izq == 'ROI Ellipse Max':
            #agergo la medicion de la roi max elipse 1
            self.ydataIzq = np.append(self.ydataIzq[1:],self.ellipse1ValueMax)#float(self.valor32IndTab1MaxRoi1Ellipse.text()))
        #Procesamiento de datos para el grafico de tendencia izquierdo
        #        
        if self._plot_refIzq is None:#la idea es no llamar a la fucnion now, tomamos la ultima estampa de tiempo y le sumamos 1 segundo que es el tiempo de muestreo
            self.xdataIzq = np.append(self.xdataIzq[1:],self.xdataIzq[-1]+np.array([datetime.timedelta(milliseconds=100)],dtype='timedelta64[ms]')[0])            
            self.formatoXDataIzq = np.append(self.formatoXDataIzq[1:],self.xdataIzq[-1].item().strftime("%S:%f")[:-4])
            plot_refsIzqCurva0, = self.dfTab1Izq.axes.plot(self.formatoXDataIzq, self.ydataIzq, 'r') #.strftime("%M:%S")
            self._plot_refIzq = plot_refsIzqCurva0#[0]
        else:
            self.xdataIzq = np.append(self.xdataIzq[1:],self.xdataIzq[-1]+np.array([datetime.timedelta(milliseconds=100)],dtype='timedelta64[ms]')[0])            
            self.formatoXDataIzq = np.append(self.formatoXDataIzq[1:],self.xdataIzq[-1].item().strftime("%S:%f")[:-4])
            self._plot_refIzq.set_ydata(self.ydataIzq)            
            self._plot_refIzq.set_xdata(self.formatoXDataIzq)
            self._plot_refIzq.axes.set_xlim([self.formatoXDataIzq[0],self.formatoXDataIzq[49]]) #actualizo los limites
        #
        #muestro los datos del grafico izq arriba     
        self.dfTab1Izq.draw()
        if self.XTab1Izq1 == 'Profile Horizontal Rect1':
            self.xdataIzq1 = self.xdataIzq1RectHor
            self.ydataIzq1 = self.ydataIzq1RectHor
        elif self.XTab1Izq1 == 'Profile Vertical Rect1':
            self.xdataIzq1 = self.xdataIzq1RectVert
            self.ydataIzq1 = self.ydataIzq1RectVert
        elif self.XTab1Izq1 == 'Profile Horizontal Ellipse1':
            self.xdataIzq1 = self.xdataIzq1ElipHor
            self.ydataIzq1 = self.ydataIzq1ElipHor
        elif self.XTab1Izq1 == 'Profile Vertical Ellipse1':
            self.xdataIzq1 = self.xdataIzq1ElipVer
            self.ydataIzq1 = self.ydataIzq1ElipVer
        elif self.XTab1Izq1 == 'Profile Line1':
            self.xdataIzq1 = self.xdataIzq1Line
            self.ydataIzq1 = self.ydataIzq1Line
        if self._plot_refIzq1 is None:
            plot_refs = self.dfTab1Izq1.axes.plot(self.xdataIzq1, self.ydataIzq1, 'r')
            self._plot_refIzq1 = plot_refs[0]
            self.dfTab1Izq1.axes.grid(True, linestyle='-.')
            self.dfTab1Izq1.axes.set_ylim([0,100])
            self.dfTab1Izq1.axes.set_ylabel("Roi1")
            self.dfTab1Izq1.axes.set_xlabel('pixel')
            self.dfTab1Izq1.axes.set_title("Profile Roi 1")
        else:
            self._plot_refIzq1.set_xdata(self.xdataIzq1)
            self._plot_refIzq1.set_ydata(self.ydataIzq1)
        #muestro los datos del grafico izquierda abajo            
        self.dfTab1Izq1.draw()    
        if self.XTab1Der == 'ROI Rect2 Min':
            #cargamos el trendin de roi rect 2 minimo
            self.ydataDer = np.append(self.ydataDer[1:],self.rect2ValueMin)#float(self.valor4IndTab1MinRoi2Rect.text()))
        elif self.XTab1Der == 'ROI Line2 Min':
            #agergo la medicion de la roi min line 2
            self.ydataDer = np.append(self.ydataDer[1:],self.line2ValueMin)#float(self.valor41IndTab1MinRoi2Line.text()))
        elif self.XTab1Der == 'ROI Ellip2 Min':
            #agergo la medicion de la roi min elipse 2
            self.ydataDer = np.append(self.ydataDer[1:],self.ellipse2ValueMin)#float(self.valor42IndTab1MinRoi2Ellipse.text()))
        elif self.XTab1Der == 'ROI Rect2 Avg':
            #agergo la medicion de la roi avg rect 2
            self.ydataDer = np.append(self.ydataDer[1:],self.rect2ValueAvg)#float(self.valor5IndTab1AvgRoi2Rect.text()))
        elif self.XTab1Der == 'ROI Line2 Avg':
            #agergo la medicion de la roi avg line 2
            self.ydataDer = np.append(self.ydataDer[1:],self.line2ValueAvg)#float(self.valor51IndTab1AvgRoi2Line.text()))
        elif self.XTab1Der == 'ROI Ellip2 Avg':
            #agergo la medicion de la roi avg elipse 2
            self.ydataDer = np.append(self.ydataDer[1:],self.ellipse2ValueAvg)#float(self.valor52IndTab1AvgRoi2Ellipse.text()))
        elif self.XTab1Der == 'ROI Rect2 Max':
            #agergo la medicion de la roi max rect 2
            self.ydataDer = np.append(self.ydataDer[1:],self.rect2ValueMax)#float(self.valor6IndTab1MaxRoi2Rect.text()))
        elif self.XTab1Der == 'ROI Line2 Max':
            #agergo la medicion de la roi max line 2
            self.ydataDer = np.append(self.ydataDer[1:],self.line2ValueMax)#float(self.valor61IndTab1MaxRoi2Line.text()))
        elif self.XTab1Der == 'ROI Ellip2 Max':
            #agergo la medicion de la roi max elipse 2
            self.ydataDer = np.append(self.ydataDer[1:],self.ellipse2ValueMax)#float(self.valor62IndTab1MaxRoi2Ellipse.text()))
        #Procesamiento de datos para el grafico de tendencia derecha
        #         
        if self._plot_refDer is None:
            self.xdataDer = np.append(self.xdataDer[1:],self.xdataDer[-1]+np.array([datetime.timedelta(milliseconds=100)],dtype='timedelta64[ms]')[0])
            self.formatoXDataDer = np.append(self.formatoXDataDer[1:],self.xdataDer[-1].item().strftime("%S:%f")[:-4])
            plot_refsDerCurva0, = self.dfTab1Der.axes.plot(self.formatoXDataDer, self.ydataDer, 'r')
            self._plot_refDer = plot_refsDerCurva0            
        else:            
            self.xdataDer = np.append(self.xdataDer[1:],self.xdataDer[-1]+np.array([datetime.timedelta(milliseconds=100)],dtype='timedelta64[ms]')[0])            
            self.formatoXDataDer = np.append(self.formatoXDataDer[1:],self.xdataDer[-1].item().strftime("%S:%f")[:-4])    
            self._plot_refDer.set_ydata(self.ydataDer)
            self._plot_refDer.set_xdata(self.formatoXDataDer)
            self._plot_refDer.axes.set_xlim([self.formatoXDataDer[0],self.formatoXDataDer[49]]) #actualizo los limites
        #
        #muestro los datos del grafico derecha arriba
        self.dfTab1Der.draw()    
        if self.XTab1Der1 == 'Profile Horizontal Rect2':
            self.xdataDer1 = self.xdataDer1RectHor
            self.ydataDer1 = self.ydataDer1RectHor
        elif self.XTab1Der1 == 'Profile Vertical Rect2':
            self.xdataDer1 = self.xdataDer1RectVert
            self.ydataDer1 = self.ydataDer1RectVert
        elif self.XTab1Der1 == 'Profile Horizontal Ellipse2':
            self.xdataDer1 = self.xdataDer1ElipHor
            self.ydataDer1 = self.ydataDer1ElipHor
        elif self.XTab1Der1 == 'Profile Vertical Ellipse2':
            self.xdataDer1 = self.xdataDer1ElipVer
            self.ydataDer1 = self.ydataDer1ElipVer
        elif self.XTab1Der1 == 'Profile Line1':
            self.xdataDer1 = self.xdataDer1Line
            self.ydataDer1 = self.ydataDer1Line
        if self._plot_refDer1 is None:
            plot_refs = self.dfTab1Der1.axes.plot(self.xdataDer1, self.ydataDer1, 'r')
            self._plot_refDer1 = plot_refs[0]
            self.dfTab1Der1.axes.grid(True, linestyle='-.')
            self.dfTab1Der1.axes.set_ylim([0,100])
            self.dfTab1Der1.axes.set_ylabel("Roi2")
            self.dfTab1Der1.axes.set_xlabel('pixel')
            self.dfTab1Der1.axes.set_title("Profile Roi 2")
        else:
            self._plot_refDer1.set_xdata(self.xdataDer1)
            self._plot_refDer1.set_ydata(self.ydataDer1)
        #muestro los graficos derecha abajo
        self.dfTab1Der1.draw()
    #
    def update_plots(self):
        #muestreo mas lento las funciones que grafican
        #self.dfTab1Izq.draw()
        #self.dfTab1Izq1.draw()
        #self.dfTab1Der.draw()
        #self.dfTab1Der1.draw()
        print("no deberia estar aca, no vamos a usar un temporizador mas lento solo mostramos a 100 ms")

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
    #hilo procesamiento de datos
    @pyqtSlot(np.ndarray)
    def update_procesamiento(self, procesamientoDatos):
        print(procesamientoDatos[0]+" "+procesamientoDatos[1]+" "+procesamientoDatos[2]+" "+procesamientoDatos[3])

    @pyqtSlot(np.ndarray)
    def status_camera(self, statusConnectionCamera):
        if statusConnectionCamera[0] == "True":
            self.statusConnectionCam1 = True #la conexion fue establecida con la camra lo indicamos con un flag
                                              #esto detiene la ejecucion del timer y la progresion de la barra de
                                              #conexion
            self.textEditTab1Boton.setText("Camara Conectada")
        else:
            self.textEditTab1Boton.setText("Camara Desconectada")

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        #mostrar informacion en recorder
        if self.mostrarImagenPantallaRecorded == True:
            #print("striming pantalla recorded")
            qt_img = self.convert_cv_qt(cv_img)
            self.labelImagenOnlineRecorder.setPixmap(qt_img)   
            if self.flagQueueReady:
                cv_img_reshaped = cv_img.flatten()
                self.queueDatosOrigenCV.put(cv_img_reshaped)             
        else:            
            #mostrar informacion en pantalla principal
            """Updates the image_label with a new opencv image"""
            qt_img = self.convert_cv_qt(cv_img)
            self.image_label.setPixmap(qt_img)
            #mostrar informacion en pantalla de popups
            if self.mostrarImagenPopUpCambioFoco == True: #en el caso de que este flag activo strimeo a la popup de ajuste de foco
                #print("enviando imagen a popup")
                flagDetenerFoco = self.configuracionFoco.upDateImage(self.image_label)
                if flagDetenerFoco == True:
                    self.mostrarImagenPopUpCambioFoco = False
                    self.configuracionFoco.cerrarPopup()

            if self.mostrarImagenPopUpCambioRango == True:
                flagDetenerRango = self.configuracionRango.upDateImage(self.image_label)
                if flagDetenerRango == True:
                    self.mostrarImagenPopUpCambioRango = False
                    self.configuracionRango.cerrarPopup()

            if self.mostrarImagenPopUpLimManPaleta == True:
                flagDetenerRango = self.configuracionLimManPaleta.upDateImage(self.image_label)
                if flagDetenerRango == True:
                    print("stop streaming")
                    self.mostrarImagenPopUpLimManPaleta = False
                    self.configuracionLimManPaleta.cerrarPopup()

            if self.mostrarImagenPopUpManAutPaleta == True:
                flagDetenerRango = self.configuracionManAutPaleta.upDateImage(self.image_label)
                if flagDetenerRango == True:
                    self.mostrarImagenPopUpManAutPaleta = False
                    self.configuracionManAutPaleta.cerrarPopup()

            if self.mostrarImagenPopUpCambioPaleta == True:
                flagDetenerRango = self.configuracionPaleta.upDateImage(self.image_label)
                if flagDetenerRango == True:
                    self.mostrarImagenPopUpCambioPaleta = False
                    self.configuracionPaleta.cerrarPopup()

            if self.mostrarImagenPopUpCambioTmpAmb == True:
                flagDetenerRango = self.configuracionTmp.upDateImage(self.image_label)
                if flagDetenerRango == True:
                    self.mostrarImagenPopUpCambioTmpAmb = False
                    self.configuracionTmp.cerrarPopup()
            
            if self.mostrarImagenPopUpCambioTmdAmb == True:
                flagDetenerRango = self.configuracionTmd.upDateImage(self.image_label)
                if flagDetenerRango == True:
                    self.mostrarImagenPopUpCambioTmdAmb = False
                    self.configuracionTmd.cerrarPopup()
            
            if self.mostrarImagenPopUpCambioEmisividad == True:
                flagDetenerRango = self.configuracionEmi.upDateImage(self.image_label)
                if flagDetenerRango == True:
                    self.mostrarImagenPopUpCambioEmisividad = False
                    self.configuracionEmi.cerrarPopup()
            
    #cargo la imagen en formato pixmap en el viewer
    #self.viewCam1.setPixmap(qt_img)
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.display_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)
    #***************************************************
    @pyqtSlot(np.ndarray)
    def thermal_image(self, thermal_img):
        if self.flagQueueReady: #si indicamos que tiene que guardar imagenes en la pila solo va a hacer esto sin mostrar mas informacion 
            thermal_img_reshaped = thermal_img.flatten()
            self.queueDatosOrigenThermal.put(thermal_img_reshaped) #los datos en la pila van a ser sacados por el hilo en paralelo que guarda los datos en disco
        else: #solo si no esta encolando los datos de imagen termografica va a sacar los datos para procesamiento
            ancho = self.scrollArea.escalaImagen[0]#['ancho']#self.image_label.size().width()
            alto = self.scrollArea.escalaImagen[1]#['alto']#self.image_label.size().height()
            thermal_img = np.resize(thermal_img,(alto,ancho))
            #thermal_imgMirror = thermal_img
            #thermal_imgMirror = np.resize(thermal_imgMirror,(alto,ancho))
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
            roiRect1ImageValueMin = 0
            roiRect1ImageValueMax = 0
            roiRect1ImageValueAvg = 0
            altoThermalImgDim, anchoThermalImgDim = ancho, alto #thermal_img.shape        
            if (rect0Height > 1) and (rect0Width >1):
                #sacamos los datos correspondientes a la primer roi y segunda roi rectangular
                roiRect1ImageValue = thermal_img[rect0PosY:rect0PosY+rect0Height, rect0PosX:rect0PosX+rect0Width] #ponemos alrevez los indices porque la imagen esta invertida
                if (roiRect1ImageValue.shape[0]>1) and (roiRect1ImageValue.shape[1]>1):
                    roiRect1ImageValueMin = np.amin(roiRect1ImageValue)
                    roiRect1ImageValueMax = np.amax(roiRect1ImageValue)
                    roiRect1ImageValueAvg = np.mean(roiRect1ImageValue)
            
            #cargo los indicadores para rectangulo 1
            self.valor1IndTab1MinRoi1Rect.setText(str(roiRect1ImageValueMin))
            self.valor2IndTab1AvgRoi1Rect.setText(str(roiRect1ImageValueAvg))
            self.valor3IndTab1MaxRoi1Rect.setText(str(roiRect1ImageValueMax))
            
            #cargo los registros locales
            self.rect1ValueMin = roiRect1ImageValueMin #el valor minimo calculado
            self.rect1ValueAvg = roiRect1ImageValueAvg #el valor promedio calculado
            self.rect1ValueMax = roiRect1ImageValueMax #el valor maximo calculado
            #guardo el perfil horizontal y el perfil vertical de la roi
            if (rect0Height > 1) and (rect0Width >1):
                widthRoiRect1ImageValue = roiRect1ImageValue.shape[0]
                heightRoiRect1ImageValue = roiRect1ImageValue.shape[1]
                indiceXRoiRect1ImageValue = widthRoiRect1ImageValue / 2
                indiceYHeightRoiRect1ImageValue = heightRoiRect1ImageValue / 2
                profileVerticalRoi1Rect = roiRect1ImageValue[int(indiceXRoiRect1ImageValue),:]
                profileHorizontalRoi1Rect = roiRect1ImageValue[:,int(indiceYHeightRoiRect1ImageValue)]
                self.xdataIzq1RectHor = np.array(list(range(widthRoiRect1ImageValue)))
                self.ydataIzq1RectHor = profileHorizontalRoi1Rect
                self.xdataIzq1RectVert = np.array(list(range(heightRoiRect1ImageValue)))
                self.ydataIzq1RectVert = profileVerticalRoi1Rect  
            #a zero los valores de medicion rect 2
            roiRect2ImageValueMin = 0
            roiRect2ImageValueMax = 0
            roiRect2ImageValueAvg = 0       
            if (rect1Height > 1) and (rect1Width > 1):
                roiRect2ImageValue = thermal_img[rect1PosY:rect1PosY+rect1Height,rect1PosX:rect1PosX+rect1Width]
                if (roiRect2ImageValue.shape[0]>1) and (roiRect2ImageValue.shape[1]):
                    roiRect2ImageValueMin = np.amin(roiRect2ImageValue)
                    roiRect2ImageValueMax = np.amax(roiRect2ImageValue)
                    roiRect2ImageValueAvg = np.mean(roiRect2ImageValue)
            
            #cargo los indicadores para el rectangulo 2
            self.valor4IndTab1MinRoi2Rect.setText(str(roiRect2ImageValueMin))
            self.valor5IndTab1AvgRoi2Rect.setText(str(roiRect2ImageValueAvg))
            self.valor6IndTab1MaxRoi2Rect.setText(str(roiRect2ImageValueMax))        
            
            #cargo los registros locales
            self.rect2ValueMin = roiRect2ImageValueMin #cargo el valor minimo
            self.rect2ValueAvg = roiRect2ImageValueAvg #cargo el valor promedio
            self.rect2ValueMax = roiRect2ImageValueMax #cargo el valor maximo
            #guardo el perfil horizontal y el perfil vertical de la roi
            if (rect1Height > 1) and (rect1Width > 1):
                widthRoiRect2ImageValue = roiRect2ImageValue.shape[0]
                heightRoiRect2ImageValue = roiRect2ImageValue.shape[1]
                indiceXRoiRect2ImageValue = widthRoiRect2ImageValue / 2
                indiceYHeightRoiRect2ImageValue = heightRoiRect2ImageValue / 2
                profileVerticalRoi2Rect = roiRect2ImageValue[int(indiceXRoiRect2ImageValue),:]
                profileHorizontalRoi2Rect = roiRect2ImageValue[:,int(indiceYHeightRoiRect2ImageValue)]
                self.xdataDer1RectHor = np.array(list(range(widthRoiRect2ImageValue)))
                self.ydataDer1RectHor = profileHorizontalRoi2Rect
                self.xdataDer1RectVert = np.array(list(range(heightRoiRect2ImageValue)))
                self.ydataDer1RectVert = profileVerticalRoi2Rect 
            #sacamos los datos correspondientres a la primer roi y segunda roi linea
            largoLinea0 = line0PosY2 - line0PosY1 #cantidad de elementos
            anchoLinea0 = line0PosX2 - line0PosX1
            roiLine0ImageValueMin = 0
            roiLine0ImageValueMax = 0
            roiLine0ImageValueAvg = 0
            if (largoLinea0 > 1) and (anchoLinea0 > 1):
                valoresLinea0 =[]
                for tupla in zip(range(line0PosY1,line0PosY2),range(line0PosX1,line0PosX2)):
                    indiceAnchoL0 = tupla[0] #cargo los indices
                    indiceAltoL0 = tupla[1]
                    anchoImagenL0, altoImagenL0 = altoThermalImgDim, anchoThermalImgDim #cargo la dimension de la imagen
                    if indiceAnchoL0>=anchoImagenL0: #verifico que este dentro de los limites
                        indiceAnchoL0 = anchoImagenL0-1 #si no esta limito
                    if indiceAltoL0>=altoImagenL0: #verifico que este dentro de los limites
                        indiceAltoL0 = altoImagenL0-1 #si no esta limito
                    valor = thermal_img[indiceAnchoL0,indiceAltoL0]
                    valoresLinea0.append(valor)
                if len(valoresLinea0) > 0:
                    roiLine0ImageValueMin = np.amin(valoresLinea0)
                    roiLine0ImageValueMax = np.amax(valoresLinea0)
                    roiLine0ImageValueAvg = np.mean(valoresLinea0)
            
            #cargo los valores min avg y promedio en los indicadores
            self.valor11IndTab1MinRoi1Line.setText(str(roiLine0ImageValueMin))
            self.valor21IndTab1AvgRoi1Line.setText(str(roiLine0ImageValueAvg))
            self.valor31IndTab1MaxRoi1Line.setText(str(roiLine0ImageValueMax))
            
            #cargo los registros locales
            self.line1ValueMin = roiLine0ImageValueMin 
            self.line1ValueAvg = roiLine0ImageValueAvg
            self.line1ValueMax = roiLine0ImageValueMax
            #
            if (largoLinea0 > 1) and (anchoLinea0 > 1):
                widthLine0 = len(valoresLinea0)
                self.xdataIzq1Line = np.array(list(range(widthLine0)))
                self.ydataIzq1Line = valoresLinea0
            #
            largoLinea1 = line1PosY2 - line1PosY1 #cantidad de elementos
            anchoLinea1 = line1PosX2 - line1PosX1
            roiLine1ImageValueMin = 0
            roiLine1ImageValueMax = 0
            roiLine1ImageValueAvg = 0
            if (largoLinea1 > 1) and (anchoLinea1 > 1):
                valoresLinea1 =[]
                for tupla in zip(range(line1PosY1,line1PosY2),range(line1PosX1,line1PosX2)):
                    indiceAnchoL1 = tupla[0] #cargo los indices
                    indiceAltoL1 = tupla[1]
                    anchoImagenL1, altoImagenL1 = altoThermalImgDim, anchoThermalImgDim #cargo la dimension de la imagen 
                    if indiceAnchoL1>=anchoImagenL1: #verifico que este dentro de los limites
                        indiceAnchoL1 = anchoImagenL1-1 #si no esta limito
                    if indiceAltoL1>=altoImagenL1: #verifico que este dentro de los limites
                        indiceAltoL1 = altoImagenL1-1 #si no esta limito
                    valor = thermal_img[indiceAnchoL1,indiceAltoL1] #obtengo el dato
                    valoresLinea1.append(valor)
                if len(valoresLinea1) > 0:
                    roiLine1ImageValueMin = np.amin(valoresLinea1)
                    roiLine1ImageValueMax = np.amax(valoresLinea1)
                    roiLine1ImageValueAvg = np.mean(valoresLinea1)
            
            #cargo los indicadores de min avg y promedio
            self.valor41IndTab1MinRoi2Line.setText(str(roiLine1ImageValueMin))
            self.valor51IndTab1AvgRoi2Line.setText(str(roiLine1ImageValueAvg))
            self.valor61IndTab1MaxRoi2Line.setText(str(roiLine1ImageValueMax))
            
            #cargo los valores locales
            self.line2ValueMin = roiLine1ImageValueMin
            self.line2ValueAvg = roiLine1ImageValueAvg
            self.line2ValueMax = roiLine1ImageValueMax
            #
            if (largoLinea1 > 1) and (anchoLinea1 > 1):
                widthLine1 = len(valoresLinea1)
                self.xdataDer1Line = np.array(list(range(widthLine1)))
                self.ydataDer1Line = valoresLinea1
            #sacamos los datos correspondientres a la primer roi y segunda roi elipse
            #primero creamos una elipse con los datos de x0,y0 -- width,height
            #elipse 0
            valoresThermalElipse0Min = 0
            valoresThermalElipse0Max = 0
            valoresThermalElipse0Avg = 0
            x0 = int(elipse0PosX)
            y0 = int(elipse0PosY)
            a = int(elipse0Width/2)
            b = int(elipse0Height/2)
            if (b > 1) and (a > 1) and (x0 > 1) and (y0 > 1):
                #construimos la mascara
                mask = np.zeros_like(thermal_img)
                #mostramos filas y columnas
                rows, cols = mask.shape
                #creamos una ellipse blanca
                mask = cv2.ellipse(mask, center=(x0,y0), axes=(a,b), angle=0, startAngle=0, endAngle=360, color=(255,255,255), thickness=-1 )
                #aplico el filtro para dejar todo lo que esta fuera de la elipse en negro
                result = np.bitwise_and(thermal_img.astype(int), mask.astype(int))            
                #extraemos los componentes distintos de cero
                valoresInternosElipse = result[result>0]
                #calculamos los resultados
                if len(valoresInternosElipse)>0:
                    valoresThermalElipse0Min = np.amax(valoresInternosElipse)
                    valoresThermalElipse0Max = np.amin(valoresInternosElipse)
                    valoresThermalElipse0Avg = np.mean(valoresInternosElipse)
                
            #cargo los valores en los indicadores
            self.valor12IndTab1MinRoi1Ellipse.setText(str(valoresThermalElipse0Min))
            self.valor22IndTab1AvgRoi1Ellipse.setText(str(valoresThermalElipse0Avg))
            self.valor32IndTab1MaxRoi1Ellipse.setText(str(valoresThermalElipse0Max))
            
            #cargo los valores locales
            self.ellipse1ValueMin = valoresThermalElipse0Min
            self.ellipse1ValueAvg = valoresThermalElipse0Avg
            self.ellipse1ValueMax = valoresThermalElipse0Max
            #guardo el perfil horizontal y el perfil vertical de la roi
            #calculamos los perfiles horizontal y vertical
            if (int(elipse0Height) > 1) and (int(elipse0Width) > 1):
                anchoMaximoEli0 = anchoThermalImgDim              #determino el tama;o actual de la imagen
                altoMaximoEli0 = altoThermalImgDim               #luego calculo si la longitud solicitad
                longValoresVerticales = elipse0PosY+elipse0Height   #supera el tamao de la imagen 
                longValoresHorizontales = elipse0PosX+elipse0Width  #en el caso que lo haga recorto la solicitud
                if longValoresHorizontales > anchoMaximoEli0:
                    longValoresHorizontales = anchoMaximoEli0 #recorto
                if longValoresVerticales > altoMaximoEli0:
                    longValoresVerticales = altoMaximoEli0 #recorto
                valoresThermalElipse0Vertical = thermal_img[int(elipse0PosY):int(longValoresVerticales),int(elipse0PosX+elipse0Width/2)]
                valoresThermalElipse0Horizontal = thermal_img[int(elipse0PosY+elipse0Height/2),int(elipse0PosX):int(longValoresHorizontales)]
                self.xdataIzq1ElipHor = np.array(list(range(len(valoresThermalElipse0Horizontal))))
                self.ydataIzq1ElipHor = valoresThermalElipse0Horizontal
                self.xdataIzq1ElipVer = np.array(list(range(len(valoresThermalElipse0Vertical))))
                self.ydataIzq1ElipVer = valoresThermalElipse0Vertical 
            #sacamos los datos correspondientes a la elipse 1
            #elipse 1
            valoresThermalElipse1Min = 0
            valoresThermalElipse1Max = 0
            valoresThermalElipse1Avg = 0
            x01 = int(elipse1PosX)
            y01 = int(elipse1PosY)
            a1 = int(elipse1Width/2)
            b1 = int(elipse1Height/2)
            if (b1 > 1) and (a1 > 1) and (x01 > 1) and (y01 > 1):            
                #construimos la mascara de la elipse 1
                mask1 = np.zeros_like(thermal_img)
                #mostramos filas y columnas
                rows, cols = mask1.shape
                #creamos una ellipse blanca
                mask1 = cv2.ellipse(mask1, center=(x01,y01), axes=(a1,b1), angle=0, startAngle=0, endAngle=360, color=(255,255,255), thickness=-1)
                #aplicamos el filtro para dejar todo lo que esta fuera de la elipse en negro
                result1 = np.bitwise_and(thermal_img.astype(int), mask1.astype(int))
                #extraenos los componentes distintos de cero
                valoresInternosElipse1 = result1[result1>0]
                if len(valoresInternosElipse1)>0:
                    valoresThermalElipse1Min = np.amin(valoresInternosElipse1)
                    valoresThermalElipse1Max = np.amax(valoresInternosElipse1)
                    valoresThermalElipse1Avg = np.mean(valoresInternosElipse1)        
            #cargo los indicadores de los elipses 2
            self.valor42IndTab1MinRoi2Ellipse.setText(str(valoresThermalElipse1Min))
            self.valor52IndTab1AvgRoi2Ellipse.setText(str(valoresThermalElipse1Avg))
            self.valor62IndTab1MaxRoi2Ellipse.setText(str(valoresThermalElipse1Max))
            #cargo los valores locales
            self.ellipse2ValueMin = valoresThermalElipse1Min
            self.ellipse2ValueAvg = valoresThermalElipse1Max
            self.ellipse2ValueMax = valoresThermalElipse1Avg
            #guardo el perfil horizontal y el perfil vertical de la roi
            #calculamos los perfiles horizontal y vertical
            if (elipse1Height > 1) and (elipse1Width > 1):
                anchoMaximoEli1 = anchoThermalImgDim              #determino el tama;o actual de la imagen
                altoMaximoEli1 = altoThermalImgDim               #luego calculo si la longitud solicitad
                longValoresVerticales1 = elipse1PosY+elipse1Height   #supera el tamao de la imagen 
                longValoresHorizontales1 = elipse1PosX+elipse1Width  #en el caso que lo haga recorto la solicitud
                if longValoresHorizontales1 > anchoMaximoEli1:
                    longValoresHorizontales = anchoMaximoEli1 # recorto
                if longValoresVerticales1 > altoMaximoEli1:
                    longValoresVerticales = altoMaximoEli1 #recorto
                valoresThermalElipse1Vertical = thermal_img[int(elipse1PosY):int(longValoresVerticales1),int(elipse1PosX+elipse1Width/2)]
                valoresThermalElipse1Horizontal = thermal_img[int(elipse1PosY+elipse1Height/2),int(elipse1PosX):int(longValoresHorizontales1)]
                self.xdataDer1ElipHor = np.array(list(range(len(valoresThermalElipse1Horizontal))))
                self.ydataDer1ElipHor = valoresThermalElipse1Horizontal
                self.xdataDer1ElipVer = np.array(list(range(len(valoresThermalElipse1Vertical))))
                self.ydataDer1ElipVer = valoresThermalElipse1Vertical 
            #verifico si el valor minimo es menor al error
            #el valor de valorNuevoPreset1 es actualizado desde la popup de ajuste de alarma
            if roiRect1ImageValueMin > float(self.valorNuevoPresetRoiMinRect1.text()):
                self.valor1IndTab1MinRoi1Rect.setStyleSheet("border: 2px solid black;border-radius: 4px;padding: 2px; text-align:center; background-color: red;")
            else:
                self.valor1IndTab1MinRoi1Rect.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
            #*****************************
            if roiRect1ImageValueAvg > float(self.valorNuevoPresetRoiAvgRect1.text()):
                self.valor2IndTab1AvgRoi1Rect.setStyleSheet("border: 2px solid black;border-radius: 4px;padding: 2px; text-align:center; background-color: red;")
            else:
                self.valor2IndTab1AvgRoi1Rect.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
            #*****************************
            if roiRect1ImageValueMax > float(self.valorNuevoPresetRoiMaxRect1.text()):
                self.valor3IndTab1MaxRoi1Rect.setStyleSheet("border: 2px solid black;border-radius: 4px;padding: 2px; text-align:center; background-color: red;")
            else:
                self.valor3IndTab1MaxRoi1Rect.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
            #*****************************
            if roiRect2ImageValueMin > float(self.valorNuevoPresetRoiMinRect2.text()):
                self.valor4IndTab1MinRoi2Rect.setStyleSheet("border: 2px solid black;border-radius: 4px;padding: 2px; text-align:center; background-color: red;")
            else:
                self.valor4IndTab1MinRoi2Rect.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
            #*****************************
            if roiRect2ImageValueAvg > float(self.valorNuevoPresetRoiAvgRect2.text()):
                self.valor5IndTab1AvgRoi2Rect.setStyleSheet("border: 2px solid black;border-radius: 4px;padding: 2px; text-align:center; background-color: red;")
            else:
                self.valor5IndTab1AvgRoi2Rect.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
            #*****************************
            if roiRect2ImageValueMax > float(self.valorNuevoPresetRoiMaxRect2.text()):
                self.valor6IndTab1MaxRoi2Rect.setStyleSheet("border: 2px solid black;border-radius: 4px;padding: 2px; text-align:center; background-color: red;")
            else:
                self.valor6IndTab1MaxRoi2Rect.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
            #*****************************
            if roiLine0ImageValueMin > float(self.valorNuevoPresetRoiMinLine1.text()):
                self.valor11IndTab1MinRoi1Line.setStyleSheet("border: 2px solid black;border-radius: 4px;padding: 2px; text-align:center; background-color: red;")
            else:
                self.valor11IndTab1MinRoi1Line.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
            #*****************************
            if roiLine0ImageValueAvg > float(self.valorNuevoPresetRoiAvgLine1.text()):
                self.valor21IndTab1AvgRoi1Line.setStyleSheet("border: 2px solid black;border-radius: 4px;padding: 2px; text-align:center; background-color: red;")
            else:
                self.valor21IndTab1AvgRoi1Line.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
            #*****************************
            if roiLine0ImageValueMax > float(self.valorNuevoPresetRoiMaxLine1.text()):
                self.valor31IndTab1MaxRoi1Line.setStyleSheet("border: 2px solid black;border-radius: 4px;padding: 2px; text-align:center; background-color: red;")
            else:
                self.valor31IndTab1MaxRoi1Line.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
            #*****************************
            if roiLine1ImageValueMin > float(self.valorNuevoPresetRoiMinLine2.text()):
                self.valor41IndTab1MinRoi2Line.setStyleSheet("border: 2px solid black;border-radius: 4px;padding: 2px; text-align:center; background-color: red;")
            else:
                self.valor41IndTab1MinRoi2Line.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
            #*****************************
            if roiLine1ImageValueAvg > float(self.valorNuevoPresetRoiAvgLine2.text()):
                self.valor51IndTab1AvgRoi2Line.setStyleSheet("border: 2px solid black;border-radius: 4px;padding: 2px; text-align:center; background-color: red;")
            else:
                self.valor51IndTab1AvgRoi2Line.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
            #*****************************
            if roiLine1ImageValueMax > float(self.valorNuevoPresetRoiMaxLine2.text()):
                self.valor61IndTab1MaxRoi2Line.setStyleSheet("border: 2px solid black;border-radius: 4px;padding: 2px; text-align:center; background-color: red;")
            else:
                self.valor61IndTab1MaxRoi2Line.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
            #***************************** 
            if valoresThermalElipse0Min > float(self.valorNuevoPresetRoiMinEllipse1.text()):
                self.valor12IndTab1MinRoi1Ellipse.setStyleSheet("border: 2px solid black;border-radius: 4px;padding: 2px; text-align:center; background-color: red;")
            else:
                self.valor12IndTab1MinRoi1Ellipse.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
            #*****************************
            if valoresThermalElipse0Avg > float(self.valorNuevoPresetRoiAvgEllipse1.text()):
                self.valor22IndTab1AvgRoi1Ellipse.setStyleSheet("border: 2px solid black;border-radius: 4px;padding: 2px; text-align:center; background-color: red;")
            else:
                self.valor22IndTab1AvgRoi1Ellipse.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
            #*****************************
            if valoresThermalElipse0Max > float(self.valorNuevoPresetRoiMaxEllipse1.text()):
                self.valor32IndTab1MaxRoi1Ellipse.setStyleSheet("border: 2px solid black;border-radius: 4px;padding: 2px; text-align:center; background-color: red;")
            else:
                self.valor32IndTab1MaxRoi1Ellipse.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
            #*****************************
            if valoresThermalElipse1Min > float(self.valorNuevoPresetRoiMinEllipse2.text()):
                self.valor42IndTab1MinRoi2Ellipse.setStyleSheet("border: 2px solid black;border-radius: 4px;padding: 2px; text-align:center; background-color: red;")
            else:
                self.valor42IndTab1MinRoi2Ellipse.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
            #*****************************
            if valoresThermalElipse1Avg > float(self.valorNuevoPresetRoiAvgEllipse2.text()):
                self.valor52IndTab1AvgRoi2Ellipse.setStyleSheet("border: 2px solid black;border-radius: 4px;padding: 2px; text-align:center; background-color: red;")
            else:
                self.valor52IndTab1AvgRoi2Ellipse.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
            #*****************************
            if valoresThermalElipse1Max > float(self.valorNuevoPresetRoiMaxEllipse2.text()):
                self.valor62IndTab1MaxRoi2Ellipse.setStyleSheet("border: 2px solid black;border-radius: 4px;padding: 2px; text-align:center; background-color: red;")
            else:
                self.valor62IndTab1MaxRoi2Ellipse.setStyleSheet("border: 2px solid green;border-radius: 4px;padding: 2px; text-align:center; background-color: lightgreen;")
            #*****************************              
    #defino la funcion asociada con el cambio de preset en el tab1
    def popUpSetBotonTab1(self, checkbox):
        print("ajustamos preset 1 tab1 = ", checkbox.toolTip() ) 
        print("cambiar el color de fondo = ", self.valor1IndTab1MinRoi1Rect.text())      
        if checkbox.isChecked() == True: #determinamos si se activo el checkbox que control lo esta disparando y editamos ese control
            #self.dlgChangePresetTab1 = PopUpWritePresetTab(valorLabelIndicador=self.valor1IndTab1MinRoi1Rect, valorPreset=self.valorNuevoPresetRoiMinRect1)
            if checkbox.toolTip() == "MinRoiRect1":
                self.dlgChangePresetTab1 = PopUpWritePresetTab(valorLabelIndicador="MinRoiRect1", valorPreset=self.valorNuevoPresetRoiMinRect1)#self.valor1IndTab1MinRoi1Rect
            elif checkbox.toolTip() == "MinRoiLine1":
                self.dlgChangePresetTab1 = PopUpWritePresetTab(valorLabelIndicador="MinRoiLine1", valorPreset=self.valorNuevoPresetRoiMinLine1)#self.valor11IndTab1MinRoi1Line
            elif checkbox.toolTip() == "MinRoiEllipse1":
                self.dlgChangePresetTab1 = PopUpWritePresetTab(valorLabelIndicador="MinRoiEllipse1", valorPreset=self.valorNuevoPresetRoiMinEllipse1)#self.valor12IndTab1MinRoi1Ellipse
            elif checkbox.toolTip() == "AvgRoiRect1":
                self.dlgChangePresetTab1 = PopUpWritePresetTab(valorLabelIndicador="AvgRoiRect1", valorPreset=self.valorNuevoPresetRoiAvgRect1)#self.valor2IndTab1AvgRoi1Rect
            elif checkbox.toolTip() == "AvgRoiLine1":
                self.dlgChangePresetTab1 = PopUpWritePresetTab(valorLabelIndicador="AvgRoiLine1", valorPreset=self.valorNuevoPresetRoiAvgLine1)#self.valor21IndTab1AvgRoi1Line
            elif checkbox.toolTip() == "AvgRoiEllipse1":
                self.dlgChangePresetTab1 = PopUpWritePresetTab(valorLabelIndicador="AvgRoiEllipse1", valorPreset=self.valorNuevoPresetRoiAvgEllipse1)#self.valor22IndTab1AvgRoi1Ellipse
            elif checkbox.toolTip() == "MaxRoiRect1":
                self.dlgChangePresetTab1 = PopUpWritePresetTab(valorLabelIndicador="MaxRoiRect1", valorPreset=self.valorNuevoPresetRoiMaxRect1)#self.valor3IndTab1MaxRoi1Rect
            elif checkbox.toolTip() == "MaxRoiLine1":
                self.dlgChangePresetTab1 = PopUpWritePresetTab(valorLabelIndicador="MaxRoiLine1", valorPreset=self.valorNuevoPresetRoiMaxLine1)#self.valor31IndTab1MaxRoi1Line
            elif checkbox.toolTip() == "MaxRoiEllipse1":
                self.dlgChangePresetTab1 = PopUpWritePresetTab(valorLabelIndicador="MaxRoiEllipse1", valorPreset=self.valorNuevoPresetRoiMaxEllipse1)#self.valor32IndTab1MaxRoi1Ellipse
            elif checkbox.toolTip() == "MinRoiRect2":
                self.dlgChangePresetTab1 = PopUpWritePresetTab(valorLabelIndicador="MinRoiRect2", valorPreset=self.valorNuevoPresetRoiMinRect2)#self.valor4IndTab1MinRoi2Rect
            elif checkbox.toolTip() == "MinRoiLine2":
                self.dlgChangePresetTab1 = PopUpWritePresetTab(valorLabelIndicador="MinRoiLine2", valorPreset=self.valorNuevoPresetRoiMinLine2)#self.valor41IndTab1MinRoi2Line
            elif checkbox.toolTip() == "MinRoiEllipse2":
                self.dlgChangePresetTab1 = PopUpWritePresetTab(valorLabelIndicador="MinRoiEllipse2", valorPreset=self.valorNuevoPresetRoiMinEllipse2)#self.valor42IndTab1MinRoi2Ellipse
            elif checkbox.toolTip() == "AvgRoiRect2":
                self.dlgChangePresetTab1 = PopUpWritePresetTab(valorLabelIndicador="AvgRoiRect2", valorPreset=self.valorNuevoPresetRoiAvgRect2)#self.valor5IndTab1AvgRoi2Rect
            elif checkbox.toolTip() == "AvgRoiLine2":
                self.dlgChangePresetTab1 = PopUpWritePresetTab(valorLabelIndicador="AvgRoiLine2", valorPreset=self.valorNuevoPresetRoiAvgLine2)#self.valor51IndTab1AvgRoi2Line
            elif checkbox.toolTip() == "AvgRoiEllipse2":
                self.dlgChangePresetTab1 = PopUpWritePresetTab(valorLabelIndicador="AvgRoiEllipse2", valorPreset=self.valorNuevoPresetRoiAvgEllipse2)#self.valor52IndTab1AvgRoi2Ellipse
            elif checkbox.toolTip() == "MaxRoiRect2":
                self.dlgChangePresetTab1 = PopUpWritePresetTab(valorLabelIndicador="MaxRoiRect2", valorPreset=self.valorNuevoPresetRoiMaxRect2)#self.valor6IndTab1MaxRoi2Rect
            elif checkbox.toolTip() == "MaxRoiLine2":
                self.dlgChangePresetTab1 = PopUpWritePresetTab(valorLabelIndicador="MaxRoiLine2", valorPreset=self.valorNuevoPresetRoiMaxLine2)#self.valor61IndTab1MaxRoi2Line
            elif checkbox.toolTip() == "MaxRoiEllipse2":
                self.dlgChangePresetTab1 = PopUpWritePresetTab(valorLabelIndicador="MaxRoiEllipse2", valorPreset=self.valorNuevoPresetRoiMaxEllipse2)#self.valor62IndTab1MaxRoi2Ellipse
            #mostramos la popup
            self.dlgChangePresetTab1.show()
    def popUpResetBotonTab1(self, checkbox):
        print("reset preset 1 tab1")
        if checkbox.isChecked() == False:
            #determinamos que checkbox esta disparando el popup
            #utilizando el tooltip
            if checkbox.toolTip() == "MinRoiRect1":
                self.dlgDefaultPresetTab1 = PopUpResetPresetTab(nombrePreset="MinRoiRect1",valorPreset=self.valorNuevoPresetRoiMinRect1)
                self.dlgDefaultPresetTab1.show()
            elif checkbox.toolTip() == "MinRoiLine1":
                self.dlgDefaultPresetTab1 = PopUpResetPresetTab(nombrePreset="MinRoiLine1",valorPreset=self.valorNuevoPresetRoiMinLine1)
                self.dlgDefaultPresetTab1.show()
            elif checkbox.toolTip() == "MinroiEllipse1":
                self.dlgDefaultPresetTab1 = PopUpResetPresetTab(nombrePreset="MinroiEllipse1",valorPreset=self.valorNuevoPresetRoiMinEllipse1)
                self.dlgDefaultPresetTab1.show()
            elif checkbox.toolTip() == "AvgRoiRect1":
                self.dlgDefaultPresetTab1 = PopUpResetPresetTab(nombrePreset="AvgRoiRect1",valorPreset=self.valorNuevoPresetRoiAvgRect1)
                self.dlgDefaultPresetTab1.show()
            elif checkbox.toolTip() == "AvgRoiLine1":
                self.dlgDefaultPresetTab1 = PopUpResetPresetTab(nombrePreset="AvgRoiLine1",valorPreset=self.valorNuevoPresetRoiAvgLine1)
                self.dlgDefaultPresetTab1.show()
            elif checkbox.toolTip() == "AvgRoiEllipse1":
                self.dlgDefaultPresetTab1 = PopUpResetPresetTab(nombrePreset="AvgRoiEllipse1",valorPreset=self.valorNuevoPresetRoiAvgEllipse1)
                self.dlgDefaultPresetTab1.show()
            elif checkbox.toolTip() == "MaxRoiRect1":
                self.dlgDefaultPresetTab1 = PopUpResetPresetTab(nombrePreset="MaxRoiRect1",valorPreset=self.valorNuevoPresetRoiMaxRect1)
                self.dlgDefaultPresetTab1.show()
            elif checkbox.toolTip() == "MaxRoiLine1":
                self.dlgDefaultPresetTab1 = PopUpResetPresetTab(nombrePreset="MaxRoiLine1",valorPreset=self.valorNuevoPresetRoiMaxLine1)
                self.dlgDefaultPresetTab1.show()
            elif checkbox.toolTip() == "MaxRoiEllipse1":
                self.dlgDefaultPresetTab1 = PopUpResetPresetTab(nombrePreset="MaxRoiEllipse1",valorPreset=self.valorNuevoPresetRoiMaxEllipse1)
                self.dlgDefaultPresetTab1.show()
            elif checkbox.toolTip() == "MinRoiRect2":
                self.dlgDefaultPresetTab1 = PopUpResetPresetTab(nombrePreset="MinRoiRect2",valorPreset=self.valorNuevoPresetRoiMinRect2)
                self.dlgDefaultPresetTab1.show()
            elif checkbox.toolTip() == "MinRoiLine2":
                self.dlgDefaultPresetTab1 = PopUpResetPresetTab(nombrePreset="MinRoiLine2",valorPreset=self.valorNuevoPresetRoiMinLine2)
                self.dlgDefaultPresetTab1.show()
            elif checkbox.toolTip() == "MinRoiEllipse2":
                self.dlgDefaultPresetTab1 = PopUpResetPresetTab(nombrePreset="MinRoiEllipse2",valorPreset=self.valorNuevoPresetRoiMinEllipse2)
                self.dlgDefaultPresetTab1.show()
            elif checkbox.toolTip() == "AvgRoiRect2":
                self.dlgDefaultPresetTab1 = PopUpResetPresetTab(nombrePreset="AvgRoiRect2",valorPreset=self.valorNuevoPresetRoiAvgRect2)
                self.dlgDefaultPresetTab1.show()
            elif checkbox.toolTip() == "AvgRoiLine2":
                self.dlgDefaultPresetTab1 = PopUpResetPresetTab(nombrePreset="AvgRoiLine2",valorPreset=self.valorNuevoPresetRoiAvgLine2)
                self.dlgDefaultPresetTab1.show()
            elif checkbox.toolTip() == "AvgRoiEllipse2":
                self.dlgDefaultPresetTab1 = PopUpResetPresetTab(nombrePreset="AvgRoiEllipse2",valorPreset=self.valorNuevoPresetRoiAvgEllipse2)
                self.dlgDefaultPresetTab1.show()
            elif checkbox.toolTip() == "MaxRoiRect2":
                self.dlgDefaultPresetTab1 = PopUpResetPresetTab(nombrePreset="MaxRoiRect2",valorPreset=self.valorNuevoPresetRoiMaxRect2)
                self.dlgDefaultPresetTab1.show()
            elif checkbox.toolTip() == "MaxRoiLine2":
                self.dlgDefaultPresetTab1 = PopUpResetPresetTab(nombrePreset="MaxRoiLine2",valorPreset=self.valorNuevoPresetRoiMaxLine2)
                self.dlgDefaultPresetTab1.show()
            elif checkbox.toolTip() == "MaxRoiEllipse2":
                self.dlgDefaultPresetTab1 = PopUpResetPresetTab(nombrePreset="MaxRoiEllipse2",valorPreset=self.valorNuevoPresetRoiMaxEllipse2)
                self.dlgDefaultPresetTab1.show()

    #defino la funcion asociada con el cambio de preset de la camara 1
    def popUpConfiguracionPresetCam1(self, checkbox):
        print("cambiar preset seleccionado en camara 1")
        #print(checkbox)
        ##
        #Tenemos que agregar la popup W
        if checkbox.isChecked() == True:
            #creo un hilo para mostrar la imagen y permitir ajustar los parametros de la camara
            self.configuracionFoco = PopUPWritePresetFocoCam(self.thread, self.image_label, nameCamera="cam1")
            self.configuracionFoco.show()
            print("mostramos popup ajuste de foco")
            self.mostrarImagenPopUpCambioFoco = True
    
    def popUpConfiguracionPreset2Cam1(self, checkbox):
        if checkbox.isChecked() == True:
            #creamos un hilo para mostrar la imagen y permitir ajustar el rango de temperatura 
            self.configuracionRango = PopUpWritePresetTempRangeCam(self.thread, self.image_label, nameCamera="cam1")
            self.configuracionRango.show()
            print("mostramos popup ajuste de rango")
            self.mostrarImagenPopUpCambioRango = True
    
    def popUpConfiguracionPreset3Cam1(self, checkbox):
        if checkbox.isChecked() == True:
            #creamos un hilo para mostrar la imagen y permitir ajustar el rango de temperatura 
            self.configuracionLimManPaleta = PopUpWritePresetLimManualPalleteCam(self.thread, self.image_label, nameCamera="cam1")
            self.configuracionLimManPaleta.show()
            print("mostramos popup ajuste de rango")
            self.mostrarImagenPopUpLimManPaleta = True
    
    def popUpConfiguracionPreset4Cam1(self, checkbox):
        if checkbox.isChecked() == True:
            #creamos un hilo para mostrar la imagen y permitir ajustar el rango de temperatura 
            self.configuracionManAutPaleta = PopUpWritePresetAutoManPalleteCam(self.thread, self.image_label, nameCamera="cam1")
            self.configuracionManAutPaleta.show()
            print("mostramos popup cambio de paleta")
            self.mostrarImagenPopUpManAutPaleta = True

    def popUpConfiguracionPreset5Cam1(self, checkbox):
        if checkbox.isChecked() == True:
            #creamos un hilo para mostrar la imagen y permitir ajustar el rango de temperatura 
            self.configuracionPaleta = PopUpWritePresetPalleteCam(self.thread, self.image_label, nameCamera="cam1")
            self.configuracionPaleta.show()
            print("mostramos popup cambio de paleta")
            self.mostrarImagenPopUpCambioPaleta = True
    
    def popUpConfiguracionPreset6Cam1(self, checkbox):
        if checkbox.isChecked() == True:
            #creamos un hilo para mostrar la imagen y permitir ajustar el rango de temperatura 
            self.configuracionTmp = PopUpWritePresetTempAmbienteCam(self.thread, self.image_label)
            self.configuracionTmp.show()
            print("mostramos popup cambio de temperatura")
            self.mostrarImagenPopUpCambioTmpAmb = True

    def popUpConfiguracionPreset7Cam1(self, checkbox):
        if checkbox.isChecked() == True:
            #creamos un hilo para mostrar la imagen y permitir ajustar el rango de temperatura 
            self.configuracionTmd = PopUpWritePresetTransmisividadCam(self.thread, self.image_label)
            self.configuracionTmd.show()
            print("mostramos popup cambio de transmisividad")
            self.mostrarImagenPopUpCambioTmdAmb = True
    
    def popUpConfiguracionPreset8Cam1(self, checkbox):
        if checkbox.isChecked() == True:
            #creamos un hilo para mostrar la imagen y permitir ajustar el rango de emisividad 
            self.configuracionEmi = PopUpWritePresetEmisividadCam(self.thread, self.image_label)
            self.configuracionEmi.show()
            print("mostramos popup cambio de emisividad")
            self.mostrarImagenPopUpCambioEmisividad = True

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
            self.dlgChangePresetCam2 = PopUPWritePresetFocoCam(self.thread,self.image_label, nameCamera="cam2")
            self.dlgChangePresetCam2.show()
    #defino la funcion para restaurar la configuracion de la camara 2
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
            self.dlgChangePresetCam3 = PopUPWritePresetFocoCam(self.thread,self.image_label, nameCamera="cam3")
            self.dlgChangePresetCam3.show()
    #defino la funcion asociada la cargar el defaul de preset
    def popUpRestartConfiguracionPresetCam3(self, checkbox):
        print("reset preset seleccion en camara 3")
        if checkbox.isChecked() == False:
            self.dlgDefaultPresetCam3 = PopUpResetPresetCam()
            self.dlgDefaultPresetCam3.show()
    #defino la funcion de click emitida por la imagen hsitorica de la izquierda al click en rect
    def clickedRectImageHistory1CamScene(self, item):
        #imprimimos capturando la forma del rectang
        #vamos a identificar cual es el rect
        #y vamos a cambiar la forma que tiene
        #print('item {} clicked!'.format(item.rect()))
        #buscamos el item rectangulo que esta disparando
        #el evento.
        itemRect1 = self.listaItemsRect[0]
        itemRect2 = self.listaItemsRect[1]
        #print("el item rect seleccionado es: {}".format(item))
        #print("el item rect 1 es: {}".format(itemRect1))
        #print("el item rect 2 es: {}".format(itemRect2))
        dx = item.pos().x() #desplazamiento x
        dy = item.pos().y() #desplazamiento y
        x0 = item.rect().x() #posicion inicial x
        y0 = item.rect().y() #posicion inicial y
        x = x0 + dx #calculo la posicion final x
        y = y0 + dy #calculo la posicion final y
        if item == itemRect1:            
            print(f"Select rectangle 1, pos {x} pos {y}")
            print(f"Shift Pos x: {dx} Pos y: {dy}")
            print(f"Origen Pos x: {x0} Pos y: {y0}")
            #item.setRect(x,y,item.rect().width(),item.rect().height())
        elif item == itemRect2:
            print(f"Select rectangle 2, pos {x} pos {y}")
            #item.setRect(x,y,item.rect().width(),item.rect().height())
            print(f"Shift Pos x: {dx} Pos y: {dy}")
            print(f"Origen Pos x: {x0} Pos y: {y0}")
        else:
            print("no es el rect")
    #defino la funcion de click emitida por la imagen hsitorica de la izquierda al click en elipse
    def clickedEllipImageHistory1CamScene(self, item):
        #imprimimos capturan la forma de la elipse
        #vamosa identificar cual es la elipse
        #y vamos a cambiar la forma que tiene
        #print('item {} clicked!'.format(item.rect()))
        #buscamos el item elipse que esta disparando el evento
        itemEllip1 = self.listaItemsEllipse[0]
        itemEllip2 = self.listaItemsEllipse[1]
        #print("el item ellip seleccionado es: {}".format(item))
        #print("el item ellip 1 es: {}".format(itemEllip1))
        #print("el item ellip 2 es: {}".format(itemEllip2))
        dx = item.pos().x()
        dy = item.pos().y()
        x0 = item.rect().x()
        y0 = item.rect().y()
        x = x0 + dx
        y = y0 + dy        
        if item == itemEllip1:
            print(f"Select elipse 1, pos {x} pox {y}")
            print(f"Shift Pox x: {dx} Pos y: {dy}")
            print(f"Origen Pos x: {x0} Pos y: {y0}")
        elif item == itemEllip2:
            print(f"Select ellipse 2, pos {x} pos {y}")
            print(f"Shift Pos x: {dx} Pos y: {dy}")
            print(f"Origen Pos x: {x0} Pos y: {y0}")
        else:
            print("no es elipse")
    #defino la funcion de click emitida por la imagen historico de la izquierda al click en la recta
    def clickedLineImageHIstory1CamScene(self, item):
        #imprimimos capturando la forma de la recta
        #vamos a identificar cual es la linea 
        #y vamos a cambiar la forma que tiene
        #print('item {} clicked!'.format(item.line()))
        #buscamos el item linea que esta disparando el evento
        itemLine1 = self.listaItemsLine[0]
        itemLine2 = self.listaItemsLine[1]
        #print("el item line seleccionador es: {}".format(item))
        #print("el item line 1 es: {}".format(itemLine1))
        #print("el item line 2 es: {}".format(itemLine2))
        dx = item.pos().x()
        dy = item.pos().y()
        x0 = item.rect().x()
        y0 = item.rect().y()
        x = x0 + dx
        y = y0 + dy
        
        if item == itemLine1:
            print(f"Select line 1, pos {x} pos {y}")
            print(f"Shift Pos x:{dx} Pos y: {dy}")
            print(f"Origen Pos x:{x0} Pos y:{y0}")            
        elif item == itemLine2:
            print(f"Select line 2, pos {x} pos {y}")
            print(f"Shift Pos x: {dx} Pos y: {dy}")
            print(f"Origen Pos x: {x0} Pos y: {y0}")
        else:
            print("no es line")
    #defino la funcion de click emitida por la imagen hsitorica de la izquierda al click en rect
    def clickedRectImageHistory2CamScene(self, item):
        #imprimimos capturando la forma del rectang
        #vamos a identificar cual es el rect
        #y vamos a cambiar la forma que tiene
        #print('item {} clicked!'.format(item.rect()))
        #buscamos el item rectangulo que esta disparando
        #el evento.
        itemRect1 = self.listaItemsRect2[0]
        itemRect2 = self.listaItemsRect2[1]
        #print("el item rect seleccionado es: {}".format(item))
        #print("el item rect 1 es: {}".format(itemRect1))
        #print("el item rect 2 es: {}".format(itemRect2))
        dx = item.pos().x() #desplazamiento x
        dy = item.pos().y() #desplazamiento y
        x0 = item.rect().x() #posicion inicial x
        y0 = item.rect().y() #posicion inicial y
        x = x0 + dx #calculo la posicion final x
        y = y0 + dy #calculo la posicion final y
        if item == itemRect1:            
            print(f"Select rectangle 1, pos {x} pos {y}")
            print(f"Shift Pos x: {dx} Pos y: {dy}")
            print(f"Origen Pos x: {x0} Pos y: {y0}")
            #item.setRect(x,y,item.rect().width(),item.rect().height())
        elif item == itemRect2:
            print(f"Select rectangle 2, pos {x} pos {y}")
            #item.setRect(x,y,item.rect().width(),item.rect().height())
            print(f"Shift Pos x: {dx} Pos y: {dy}")
            print(f"Origen Pos x: {x0} Pos y: {y0}")
        else:
            print("no es el rect")
    #defino la funcion de click emitida por la imagen hsitorica de la izquierda al click en elipse
    def clickedEllipImageHistory2CamScene(self, item):
        #imprimimos capturan la forma de la elipse
        #vamosa identificar cual es la elipse
        #y vamos a cambiar la forma que tiene
        #print('item {} clicked!'.format(item.rect()))
        #buscamos el item elipse que esta disparando el evento
        itemEllip1 = self.listaItemsEllipse2[0]
        itemEllip2 = self.listaItemsEllipse2[1]
        #print("el item ellip seleccionado es: {}".format(item))
        #print("el item ellip 1 es: {}".format(itemEllip1))
        #print("el item ellip 2 es: {}".format(itemEllip2))
        dx = item.pos().x()
        dy = item.pos().y()
        x0 = item.rect().x()
        y0 = item.rect().y()
        x = x0 + dx
        y = y0 + dy        
        if item == itemEllip1:
            print(f"Select elipse 1, pos {x} pox {y}")
            print(f"Shift Pox x: {dx} Pos y: {dy}")
            print(f"Origen Pos x: {x0} Pos y: {y0}")
        elif item == itemEllip2:
            print(f"Select ellipse 2, pos {x} pos {y}")
            print(f"Shift Pos x: {dx} Pos y: {dy}")
            print(f"Origen Pos x: {x0} Pos y: {y0}")
        else:
            print("no es elipse")
    #defino la funcion de click emitida por la imagen historico de la izquierda al click en la recta
    def clickedLineImageHIstory2CamScene(self, item):
        #imprimimos capturando la forma de la recta
        #vamos a identificar cual es la linea 
        #y vamos a cambiar la forma que tiene
        #print('item {} clicked!'.format(item.line()))
        #buscamos el item linea que esta disparando el evento
        itemLine1 = self.listaItemsLine2[0]
        itemLine2 = self.listaItemsLine2[1]
        #print("el item line seleccionador es: {}".format(item))
        #print("el item line 1 es: {}".format(itemLine1))
        #print("el item line 2 es: {}".format(itemLine2))
        dx = item.pos().x()
        dy = item.pos().y()
        x0 = item.rect().x()
        y0 = item.rect().y()
        x = x0 + dx
        y = y0 + dy
        
        if item == itemLine1:
            print(f"Select line 1, pos {x} pos {y}")
            print(f"Shift Pos x:{dx} Pos y: {dy}")
            print(f"Origen Pos x:{x0} Pos y:{y0}")            
        elif item == itemLine2:
            print(f"Select line 2, pos {x} pos {y}")
            print(f"Shift Pos x: {dx} Pos y: {dy}")
            print(f"Origen Pos x: {x0} Pos y: {y0}")
        else:
            print("no es line")
    #defino la funcion que indica que item fue seleccionad
    def cachedItemSeleccionado(self, item):
        #print("el item seleccionado es: ", item)
        #posicion es instancia de RectItem
        if isinstance(item, QGraphicsRectItem):            
            posXRect1 = item.rect().x() + item.pos().x()
            posYRect1 = item.rect().y() + item.pos().y()
            indice = 0
            for itemRectLista in self.listaItemsRect:#es instancia de rectangulo y lo estamos usando como rectangulo
                if item == itemRectLista:
                    #print(f"Seleccionamos el Rectangulo {indice+1} en x:{posXRect1}, y:{posYRect1} en Historicos Izq")                                        
                    if indice == 0:
                        self.roisComboHistoricoIzquierda.setCurrentText('Rectangle-1')
                        #leer imagen Termografica                        
                        sampleImagenTh = self.matrizImgThIzq[:,:,self.indice]        
                        #print(sampleImagenTh.shape)
                        anchoRect = item.rect().width()
                        altoRect = item.rect().height()
                        #print(f"start x:{posXRect1}-y:{posYRect1}, width:{anchoRect}-height:{altoRect}")
                        roiRect1ThValues = sampleImagenTh[int(posYRect1):int(posYRect1+altoRect),int(posXRect1):int(posXRect1+anchoRect)]
                        dimX = roiRect1ThValues.shape[0]
                        dimY = roiRect1ThValues.shape[1]
                        #print(f"dimensin x:{dimX}-y:{dimY}")
                        if (dimX>1) and (dimY>1): #realizamos los calculos y mostramos los resultados en los indicadores
                            minThRoi = np.amin(roiRect1ThValues)
                            maxThRoi = np.amax(roiRect1ThValues)
                            avgThRoi = np.mean(roiRect1ThValues)
                            medianaThRoi = np.median(roiRect1ThValues)
                            desvioThRoi = np.std(roiRect1ThValues)
                            area = dimX * dimY
                            self.output1MessurementRoiMax.setText(str(maxThRoi))
                            self.output2MessurementRoiMin.setText(str(minThRoi))
                            self.output3MessurementRoiAvg.setText(str(avgThRoi))
                            self.output4MessurementRoi2Median.setText(str(medianaThRoi))
                            self.output5MessurementRoi2Std.setText(str(desvioThRoi))
                            self.output6MessurementRoi2Area.setText(str(area))
                            #print(f"calculamos los valores min:{minThRoi}-max:{maxThRoi}-avg:{avgThRoi}")                            
                    elif indice == 1:
                        self.roisComboHistoricoIzquierda.setCurrentText('Rectangle-2')                        
                        #leer imagen Termografica. Estamos repitiendo el procesamiento. Esto lo tenemos que mejorar llamando a una funcion                        
                        sampleImagenTh = self.matrizImgThIzq[:,:,self.indice]        
                        #print(sampleImagenTh.shape)
                        anchoRect = item.rect().width()
                        altoRect = item.rect().height()
                        #print(f"start x:{posXRect1}-y:{posYRect1}, width:{anchoRect}-height:{altoRect}")
                        roiRect1ThValues = sampleImagenTh[int(posYRect1):int(posYRect1+altoRect),int(posXRect1):int(posXRect1+anchoRect)]
                        dimX = roiRect1ThValues.shape[0]
                        dimY = roiRect1ThValues.shape[1]
                        #print(f"dimensin x:{dimX}-y:{dimY}")
                        if (dimX>1) and (dimY>1): #realizamos los calculos y mostramos los resultados en los indicadores
                            minThRoi = np.amin(roiRect1ThValues)
                            maxThRoi = np.amax(roiRect1ThValues)
                            avgThRoi = np.mean(roiRect1ThValues)
                            medianaThRoi = np.median(roiRect1ThValues)
                            desvioThRoi = np.std(roiRect1ThValues)
                            area = dimX * dimY
                            self.output1MessurementRoiMax.setText(str(maxThRoi))
                            self.output2MessurementRoiMin.setText(str(minThRoi))
                            self.output3MessurementRoiAvg.setText(str(avgThRoi))
                            self.output4MessurementRoi2Median.setText(str(medianaThRoi))
                            self.output5MessurementRoi2Std.setText(str(desvioThRoi))
                            self.output6MessurementRoi2Area.setText(str(area))
                            #print(f"calculamos los valores min:{minThRoi}-max:{maxThRoi}-avg:{avgThRoi}")                            
                    break
                indice += 1
            indice = 0
            for itemLineLista in self.listaItemsLine: #es instancia de rectangulos pero lo estamos usando como lineas
                if item == itemLineLista:
                    #print(f"Seleccionamos la Linea {indice+1} en x:{posXRect1}, y:{posYRect1} en Historicos Izq")                                      
                    if indice == 0:
                        self.roisComboHistoricoIzquierda.setCurrentText('Line-1')
                        if self.rotarImagen180Izq == True:
                            rotada = np.rot90(self.matrizImgThIzq)
                            rotada = np.rot90(rotada)
                            sampleImagenTh = rotada[:,:,self.indice]
                        else:                            
                            sampleImagenTh = self.matrizImgThIzq[:,:,self.indice]
                        #print(sampleImagenTh.shape)
                        anchoRect = item.rect().width()
                        altoRect = item.rect().height()
                        #print(f"start x:{posXRect1}-y:{posYRect1}, width:{anchoRect}-height:{altoRect}")
                        roiRect1ThValues = sampleImagenTh[int(posYRect1):int(posYRect1+altoRect),int(posXRect1):int(posXRect1+anchoRect)]
                        dimX = roiRect1ThValues.shape[0]
                        dimY = roiRect1ThValues.shape[1]
                        #print(f"dimensin x:{dimX}-y:{dimY}")
                        if (dimX>1) and (dimY>1):
                            #tengo que extraer la recta del rectangulo 
                            #la recta comienza en 
                            #(posXRect1,posYRect1) hasta (posXRect1+ancho,posYRect1+alto)
                            ejeX = np.arange(int(posXRect1), int(posXRect1+anchoRect),1)
                            y0 = posYRect1
                            pendiente = altoRect / anchoRect
                            ejeY = pendiente * np.arange(0,anchoRect,1) + y0
                            #print(ejeX)
                            #print(ejeY)
                            #print(ejeY.astype(int))
                            ejeYRedondeado = ejeY.astype(int)
                            listaValoresRecta = np.array([])
                            #print(ejeX.shape[0])
                            #print(ejeYRedondeado.shape[0])
                            for indice in np.arange(ejeX.shape[0]): #recorro la lista
                                #print(indice)
                                indiceX = ejeX[indice]             
                                indiceY = ejeYRedondeado[indice] 
                                #print(f"indice x:{indiceX}, y:{indiceY}")                                                
                                indexado = sampleImagenTh[indiceY, indiceX]
                                listaValoresRecta=np.append(listaValoresRecta,indexado)
                            #print(np.size(listaValoresRecta)) 
                            minThRoi = np.amin(listaValoresRecta)
                            maxThRoi = np.amax(listaValoresRecta)
                            avgThRoi = np.mean(listaValoresRecta)
                            medianaThRoi = np.median(listaValoresRecta)
                            desvioThRoi = np.std(listaValoresRecta)
                            longitud = np.size(listaValoresRecta)
                            #print(f"min:{minThRoi} max:{maxThRoi} avg:{avgThRoi} mediana:{medianaThRoi} std:{desvioThRoi} long:{longitud}")
                            self.output1MessurementRoiMax.setText(str(maxThRoi))
                            self.output2MessurementRoiMin.setText(str(minThRoi))
                            self.output3MessurementRoiAvg.setText(str(avgThRoi))
                            self.output4MessurementRoi2Median.setText(str(medianaThRoi))
                            self.output5MessurementRoi2Std.setText(str(desvioThRoi))
                            self.output6MessurementRoi2Area.setText(str(longitud))
                            xdataLine = np.array(list(range(longitud)))
                            ydataLine = listaValoresRecta
                            if self._plot_refHistoricoIzq is None:                                
                                plot_refs = self.graficoHistoricoIzq.axes.plot(xdataLine,ydataLine, 'r')
                                self._plot_refHistoricoIzq = plot_refs[0]                                
                                self.graficoHistoricoIzq.axes.grid(True, linestyle='-.')
                                self.graficoHistoricoIzq.axes.set_ylim([0,100])
                                self.graficoHistoricoIzq.axes.set_ylabel("Line")
                                self.graficoHistoricoIzq.axes.set_xlabel('pixel')
                                self.graficoHistoricoIzq.axes.set_title("Profile Roi Line 1")
                            else:
                                self._plot_refHistoricoIzq.set_xdata(xdataLine)
                                self._plot_refHistoricoIzq.set_ydata(ydataLine)
                                self.graficoHistoricoIzq.axes.set_title("Profile Roi Line 1")
                            self.graficoHistoricoIzq.draw()
                    elif indice == 1:
                        self.roisComboHistoricoIzquierda.setCurrentText('Line-2')
                        if self.rotarImagen180Izq == True:
                            rotada = np.rot90(self.matrizImgThIzq)
                            rotada = np.rot90(rotada)
                            sampleImagenTh = rotada[:,:,self.indice]
                        else:
                            sampleImagenTh = self.matrizImgThIzq[:,:,self.indice]
                        #print(sampleImagenTh.shape)
                        anchoRect = item.rect().width()
                        altoRect = item.rect().height()
                        #print(f"start x:{posXRect1}-y:{posYRect1}, width:{anchoRect}-height:{altoRect}")
                        roiRect1ThValues = sampleImagenTh[int(posYRect1):int(posYRect1+altoRect),int(posXRect1):int(posXRect1+anchoRect)]
                        dimX = roiRect1ThValues.shape[0]
                        dimY = roiRect1ThValues.shape[1]
                        #print(f"dimensin x:{dimX}-y:{dimY}")
                        if (dimX>1) and (dimY>1):
                            #tengo que extraer la recta del rectangulo 
                            #la recta comienza en 
                            #(posXRect1,posYRect1) hasta (posXRect1+ancho,posYRect1+alto)
                            ejeX = np.arange(int(posXRect1), int(posXRect1+anchoRect),1)
                            y0 = posYRect1
                            pendiente = altoRect / anchoRect
                            ejeY = -pendiente * np.arange(0,anchoRect,1) + y0 + altoRect
                            #print(ejeX)
                            #print(ejeY)
                            #print(ejeY.astype(int))
                            ejeYRedondeado = ejeY.astype(int)
                            listaValoresRecta = np.array([])
                            #print(ejeX.shape[0])
                            #print(ejeYRedondeado.shape[0])
                            for indice in np.arange(ejeX.shape[0]): #recorro la lista
                                #print(indice)
                                indiceX = ejeX[indice]             
                                indiceY = ejeYRedondeado[indice] 
                                #print(f"indice x:{indiceX}, y:{indiceY}")                                                
                                indexado = sampleImagenTh[indiceY, indiceX]
                                listaValoresRecta=np.append(listaValoresRecta,indexado)
                            #print(np.size(listaValoresRecta)) 
                            minThRoi = np.amin(listaValoresRecta)
                            maxThRoi = np.amax(listaValoresRecta)
                            avgThRoi = np.mean(listaValoresRecta)
                            medianaThRoi = np.median(listaValoresRecta)
                            desvioThRoi = np.std(listaValoresRecta)
                            longitud = np.size(listaValoresRecta)
                            #print(f"min:{minThRoi} max:{maxThRoi} avg:{avgThRoi} mediana:{medianaThRoi} std:{desvioThRoi} long:{longitud}")
                            self.output1MessurementRoiMax.setText(str(maxThRoi))
                            self.output2MessurementRoiMin.setText(str(minThRoi))
                            self.output3MessurementRoiAvg.setText(str(avgThRoi))
                            self.output4MessurementRoi2Median.setText(str(medianaThRoi))
                            self.output5MessurementRoi2Std.setText(str(desvioThRoi))
                            self.output6MessurementRoi2Area.setText(str(longitud))
                            xdataLine = np.array(list(range(longitud)))
                            ydataLine = listaValoresRecta
                            if self._plot_refHistoricoIzq is None:                                
                                plot_refs = self.graficoHistoricoIzq.axes.plot(xdataLine,ydataLine, 'r')
                                self._plot_refHistoricoIzq = plot_refs[0]                                
                                self.graficoHistoricoIzq.axes.grid(True, linestyle='-.')
                                self.graficoHistoricoIzq.axes.set_ylim([0,100])
                                self.graficoHistoricoIzq.axes.set_ylabel("Line")
                                self.graficoHistoricoIzq.axes.set_xlabel('pixel')
                                self.graficoHistoricoIzq.axes.set_title("Profile Roi Line 2")
                            else:
                                self._plot_refHistoricoIzq.set_xdata(xdataLine)
                                self._plot_refHistoricoIzq.set_ydata(ydataLine)
                                self.graficoHistoricoIzq.axes.set_title("Profile Roi Line 2")
                            self.graficoHistoricoIzq.draw()
                    break
                indice += 1 
            indice = 0
            for itemRect2Lista in self.listaItemsRect2:
                if item == itemRect2Lista:
                    print(f"Seleccionamos el Rectangulo {indice+1} en x:{posXRect1}, y:{posYRect1} en Historicos Der")                                        
                    if indice == 0:
                        self.roisComboHistoricoDerecha.setCurrentText('Rectangle-1')
                        #leer imagen Termografica                        
                        sampleImagenTh = self.matrizImgThIzq[:,:,self.indice]        
                        #print(sampleImagenTh.shape)
                        anchoRect = item.rect().width()
                        altoRect = item.rect().height()
                        #print(f"start x:{posXRect1}-y:{posYRect1}, width:{anchoRect}-height:{altoRect}")
                        roiRect1ThValues = sampleImagenTh[int(posYRect1):int(posYRect1+altoRect),int(posXRect1):int(posXRect1+anchoRect)]
                        dimX = roiRect1ThValues.shape[0]
                        dimY = roiRect1ThValues.shape[1]
                        #print(f"dimensin x:{dimX}-y:{dimY}")
                        if (dimX>1) and (dimY>1): #realizamos los calculos y mostramos los resultados en los indicadores
                            minThRoi = np.amin(roiRect1ThValues)
                            maxThRoi = np.amax(roiRect1ThValues)
                            avgThRoi = np.mean(roiRect1ThValues)
                            medianaThRoi = np.median(roiRect1ThValues)
                            desvioThRoi = np.std(roiRect1ThValues)
                            area = dimX * dimY
                            self.output1MessurementRoiMaxDer.setText(str(maxThRoi))
                            self.output2MessurementRoiMinDer.setText(str(minThRoi))
                            self.output3MessurementRoiAvgDer.setText(str(avgThRoi))
                            self.output4MessurementRoiMedianDer.setText(str(medianaThRoi))
                            self.output5MessurementRoiStdDer.setText(str(desvioThRoi))
                            self.output6MessurementRoiAreaDer.setText(str(area))
                            #print(f"calculamos los valores min:{minThRoi}-max:{maxThRoi}-avg:{avgThRoi}")                            
                    elif indice == 1:
                        self.roisComboHistoricoDerecha.setCurrentText('Rectangle-2')
                        #leer imagen Termografica                        
                        sampleImagenTh = self.matrizImgThIzq[:,:,self.indice]        
                        #print(sampleImagenTh.shape)
                        anchoRect = item.rect().width()
                        altoRect = item.rect().height()
                        #print(f"start x:{posXRect1}-y:{posYRect1}, width:{anchoRect}-height:{altoRect}")
                        roiRect1ThValues = sampleImagenTh[int(posYRect1):int(posYRect1+altoRect),int(posXRect1):int(posXRect1+anchoRect)]
                        dimX = roiRect1ThValues.shape[0]
                        dimY = roiRect1ThValues.shape[1]
                        #print(f"dimensin x:{dimX}-y:{dimY}")
                        if (dimX>1) and (dimY>1): #realizamos los calculos y mostramos los resultados en los indicadores
                            minThRoi = np.amin(roiRect1ThValues)
                            maxThRoi = np.amax(roiRect1ThValues)
                            avgThRoi = np.mean(roiRect1ThValues)
                            medianaThRoi = np.median(roiRect1ThValues)
                            desvioThRoi = np.std(roiRect1ThValues)
                            area = dimX * dimY
                            self.output1MessurementRoiMaxDer.setText(str(maxThRoi))
                            self.output2MessurementRoiMinDer.setText(str(minThRoi))
                            self.output3MessurementRoiAvgDer.setText(str(avgThRoi))
                            self.output4MessurementRoiMedianDer.setText(str(medianaThRoi))
                            self.output5MessurementRoiStdDer.setText(str(desvioThRoi))
                            self.output6MessurementRoiAreaDer.setText(str(area))
                            #print(f"calculamos los valores min:{minThRoi}-max:{maxThRoi}-avg:{avgThRoi}")                            
                    break
                indice += 1
            indice = 0
            for itemLine2Lista in self.listaItemsLine2:
                if item == itemLine2Lista:
                    print(f"Seleccionamos la Linea {indice+1} en x:{posXRect1}, y:{posYRect1} en Historicos Der")                                      
                    if indice == 0:
                        self.roisComboHistoricoDerecha.setCurrentText('Line-1')
                        if self.rotarImagen180Der == True:
                            rotada = np.rot90(self.matrizImgThDer)
                            rotada = np.rot90(rotada)
                            sampleImagenTh = rotada[:,:,self.indice]
                        else:                                
                            sampleImagenTh = self.matrizImgThDer[:,:,self.indice]
                        #print(sampleImagenTh.shape)
                        anchoRect = item.rect().width()
                        altoRect = item.rect().height()
                        #print(f"start x:{posXRect1}-y:{posYRect1}, width:{anchoRect}-height:{altoRect}")
                        roiRect1ThValues = sampleImagenTh[int(posYRect1):int(posYRect1+altoRect),int(posXRect1):int(posXRect1+anchoRect)]
                        dimX = roiRect1ThValues.shape[0]
                        dimY = roiRect1ThValues.shape[1]
                        #print(f"dimensin x:{dimX}-y:{dimY}")
                        if (dimX>1) and (dimY>1):
                            #tengo que extraer la recta del rectangulo 
                            #la recta comienza en 
                            #(posXRect1,posYRect1) hasta (posXRect1+ancho,posYRect1+alto)
                            ejeX = np.arange(int(posXRect1), int(posXRect1+anchoRect),1)
                            y0 = posYRect1
                            pendiente = altoRect / anchoRect
                            ejeY = pendiente * np.arange(0,anchoRect,1) + y0
                            #print(ejeX)
                            #print(ejeY)
                            #print(ejeY.astype(int))
                            ejeYRedondeado = ejeY.astype(int)
                            listaValoresRecta = np.array([])
                            #print(ejeX.shape[0])
                            #print(ejeYRedondeado.shape[0])
                            for indice in np.arange(ejeX.shape[0]): #recorro la lista
                                #print(indice)
                                indiceX = ejeX[indice]             
                                indiceY = ejeYRedondeado[indice] 
                                #print(f"indice x:{indiceX}, y:{indiceY}")                                                
                                indexado = sampleImagenTh[indiceY, indiceX]
                                listaValoresRecta=np.append(listaValoresRecta,indexado)
                            #print(np.size(listaValoresRecta)) 
                            minThRoi = np.amin(listaValoresRecta)
                            maxThRoi = np.amax(listaValoresRecta)
                            avgThRoi = np.mean(listaValoresRecta)
                            medianaThRoi = np.median(listaValoresRecta)
                            desvioThRoi = np.std(listaValoresRecta)
                            longitud = np.size(listaValoresRecta)
                            #print(f"min:{minThRoi} max:{maxThRoi} avg:{avgThRoi} mediana:{medianaThRoi} std:{desvioThRoi} long:{longitud}")
                            self.output1MessurementRoiMaxDer.setText(str(maxThRoi))
                            self.output2MessurementRoiMinDer.setText(str(minThRoi))
                            self.output3MessurementRoiAvgDer.setText(str(avgThRoi))
                            self.output4MessurementRoiMedianDer.setText(str(medianaThRoi))
                            self.output5MessurementRoiStdDer.setText(str(desvioThRoi))
                            self.output6MessurementRoiAreaDer.setText(str(longitud))
                            xdataLine = np.array(list(range(longitud)))
                            ydataLine = listaValoresRecta
                            if self._plot_refHistoricoDer is None:                                
                                plot_refs = self.graficoHistoricoDer.axes.plot(xdataLine,ydataLine, 'r')
                                self._plot_refHistoricoDer = plot_refs[0]                                
                                self.graficoHistoricoDer.axes.grid(True, linestyle='-.')
                                self.graficoHistoricoDer.axes.set_ylim([0,100])
                                self.graficoHistoricoDer.axes.set_ylabel("Line")
                                self.graficoHistoricoDer.axes.set_xlabel('pixel')
                                self.graficoHistoricoDer.axes.set_title("Profile Roi Line 1")
                            else:
                                self._plot_refHistoricoDer.set_xdata(xdataLine)
                                self._plot_refHistoricoDer.set_ydata(ydataLine)
                                self.graficoHistoricoDer.axes.set_title("Profile Roi Line 1")
                            self.graficoHistoricoDer.draw()
                    elif indice == 1:
                        self.roisComboHistoricoDerecha.setCurrentText('Line-2')
                        if self.rotarImagen180Der == True:
                            rotada = np.rot90(self.matrizImgThDer)
                            rotada = np.rot90(rotada)
                            sampleImagenTh = rotada[:,:,self.indice]
                        else:                            
                            sampleImagenTh = self.matrizImgThDer[:,:,self.indice]
                        #print(sampleImagenTh.shape)
                        anchoRect = item.rect().width()
                        altoRect = item.rect().height()
                        #print(f"start x:{posXRect1}-y:{posYRect1}, width:{anchoRect}-height:{altoRect}")
                        roiRect1ThValues = sampleImagenTh[int(posYRect1):int(posYRect1+altoRect),int(posXRect1):int(posXRect1+anchoRect)]
                        dimX = roiRect1ThValues.shape[0]
                        dimY = roiRect1ThValues.shape[1]
                        #print(f"dimensin x:{dimX}-y:{dimY}")
                        if (dimX>1) and (dimY>1):
                            #tengo que extraer la recta del rectangulo 
                            #la recta comienza en 
                            #(posXRect1,posYRect1) hasta (posXRect1+ancho,posYRect1+alto)
                            ejeX = np.arange(int(posXRect1), int(posXRect1+anchoRect),1)
                            y0 = posYRect1
                            pendiente = altoRect / anchoRect
                            ejeY = -pendiente * np.arange(0,anchoRect,1) + y0 + altoRect
                            #print(ejeX)
                            #print(ejeY)
                            #print(ejeY.astype(int))
                            ejeYRedondeado = ejeY.astype(int)
                            listaValoresRecta = np.array([])
                            #print(ejeX.shape[0])
                            #print(ejeYRedondeado.shape[0])
                            for indice in np.arange(ejeX.shape[0]): #recorro la lista
                                #print(indice)
                                indiceX = ejeX[indice]             
                                indiceY = ejeYRedondeado[indice] 
                                #print(f"indice x:{indiceX}, y:{indiceY}")                                                
                                indexado = sampleImagenTh[indiceY, indiceX]
                                listaValoresRecta=np.append(listaValoresRecta,indexado)
                            #print(np.size(listaValoresRecta)) 
                            minThRoi = np.amin(listaValoresRecta)
                            maxThRoi = np.amax(listaValoresRecta)
                            avgThRoi = np.mean(listaValoresRecta)
                            medianaThRoi = np.median(listaValoresRecta)
                            desvioThRoi = np.std(listaValoresRecta)
                            longitud = np.size(listaValoresRecta)
                            #print(f"min:{minThRoi} max:{maxThRoi} avg:{avgThRoi} mediana:{medianaThRoi} std:{desvioThRoi} long:{longitud}")
                            self.output1MessurementRoiMaxDer.setText(str(maxThRoi))
                            self.output2MessurementRoiMinDer.setText(str(minThRoi))
                            self.output3MessurementRoiAvgDer.setText(str(avgThRoi))
                            self.output4MessurementRoiMedianDer.setText(str(medianaThRoi))
                            self.output5MessurementRoiStdDer.setText(str(desvioThRoi))
                            self.output6MessurementRoiAreaDer.setText(str(longitud))
                            xdataLine = np.array(list(range(longitud)))
                            ydataLine = listaValoresRecta
                            if self._plot_refHistoricoDer is None:                                
                                plot_refs = self.graficoHistoricoDer.axes.plot(xdataLine,ydataLine, 'r')
                                self._plot_refHistoricoDer = plot_refs[0]                                
                                self.graficoHistoricoDer.axes.grid(True, linestyle='-.')
                                self.graficoHistoricoDer.axes.set_ylim([0,100])
                                self.graficoHistoricoDer.axes.set_ylabel("Line")
                                self.graficoHistoricoDer.axes.set_xlabel('pixel')
                                self.graficoHistoricoDer.axes.set_title("Profile Roi Line 2")
                            else:
                                self._plot_refHistoricoDer.set_xdata(xdataLine)
                                self._plot_refHistoricoDer.set_ydata(ydataLine)
                                self.graficoHistoricoDer.axes.set_title("Profile Roi Line 2")
                            self.graficoHistoricoDer.draw()
                    break
                indice += 1 
        elif isinstance(item, QGraphicsEllipseItem):            
            posXRect1 = item.rect().x() + item.pos().x()
            posYRect1 = item.rect().y() + item.pos().y()
            indice = 0
            for itemEllipseLista in self.listaItemsEllipse:
                if item == itemEllipseLista:
                    #print(f"Seleccionamos la Elipse {indice+1} en x:{posXRect1}, y:{posYRect1} en Historicos Izq")                                      
                    if indice == 0:
                        self.roisComboHistoricoIzquierda.setCurrentText('Elipse-1')                        
                        ancho = item.rect().width()
                        alto = item.rect().height()
                        centroEllipseX = (alto/2) + posXRect1
                        centroEllipseY = (ancho/2) + posYRect1                       
                        #print(f"centroX:{centroEllipseX}-centroY:{centroEllipseY}-ancho:{ancho}-alto:{alto}")
                        x = np.linspace(0,382,382)
                        y = np.linspace(0,288,288)[:,None]
                        ellipse = ((x-centroEllipseX)/ancho)**2+((y-centroEllipseY)/alto)**2 <= 1
                        sampleImagenTh = self.matrizImgThIzq[:,:,self.indice]        
                        valoresDentroElipse = sampleImagenTh[ellipse]
                        if valoresDentroElipse.shape[0] > 0:
                            minThRoi = np.amin(valoresDentroElipse)
                            maxThRoi = np.amax(valoresDentroElipse)
                            avgThRoi = np.mean(valoresDentroElipse)
                            medianaThRoi = np.median(valoresDentroElipse)
                            desvioThRoi = np.std(valoresDentroElipse)
                            area = ancho * alto * 3.14 #ancho*alto*pi
                            self.output1MessurementRoiMax.setText(str(maxThRoi))
                            self.output2MessurementRoiMin.setText(str(minThRoi))
                            self.output3MessurementRoiAvg.setText(str(avgThRoi))
                            self.output4MessurementRoi2Median.setText(str(medianaThRoi))
                            self.output5MessurementRoi2Std.setText(str(desvioThRoi))
                            self.output6MessurementRoi2Area.setText(str(area))
                            #print(f"calculamos los valores min:{minThRoi}-max:{maxThRoi}-avg:{avgThRoi}")                            
                        #print(valoresDentroElipse)
                    elif indice == 1:
                        self.roisComboHistoricoIzquierda.setCurrentText('Elipse-2')
                        ancho = item.rect().width()
                        alto = item.rect().height()
                        centroEllipseX = (alto/2) + posXRect1
                        centroEllipseY = (ancho/2) + posYRect1                       
                        #print(f"centroX:{centroEllipseX}-centroY:{centroEllipseY}-ancho:{ancho}-alto:{alto}")
                        x = np.linspace(0,382,382)
                        y = np.linspace(0,288,288)[:,None]
                        ellipse = ((x-centroEllipseX)/ancho)**2+((y-centroEllipseY)/alto)**2 <= 1
                        sampleImagenTh = self.matrizImgThIzq[:,:,self.indice]        
                        valoresDentroElipse = sampleImagenTh[ellipse]
                        if valoresDentroElipse.shape[0] > 0:
                            minThRoi = np.amin(valoresDentroElipse)
                            maxThRoi = np.amax(valoresDentroElipse)
                            avgThRoi = np.mean(valoresDentroElipse)
                            medianaThRoi = np.median(valoresDentroElipse)
                            desvioThRoi = np.std(valoresDentroElipse)
                            area = ancho * alto * 3.14 #ancho*alto*pi
                            self.output1MessurementRoiMax.setText(str(maxThRoi))
                            self.output2MessurementRoiMin.setText(str(minThRoi))
                            self.output3MessurementRoiAvg.setText(str(avgThRoi))
                            self.output4MessurementRoi2Median.setText(str(medianaThRoi))
                            self.output5MessurementRoi2Std.setText(str(desvioThRoi))
                            self.output6MessurementRoi2Area.setText(str(area))
                            #print(f"calculamos los valores min:{minThRoi}-max:{maxThRoi}-avg:{avgThRoi}")                            
                        #print(valoresDentroElipse)
                    break
                indice += 1            
            indice = 0
            for itemEllipse2Lista in self.listaItemsEllipse2:
                if item == itemEllipse2Lista:
                    print(f"Seleccionamos la Elipse {indice+1} en x:{posXRect1}, y:{posYRect1} en Historicos Der")                                      
                    if indice == 0:
                        self.roisComboHistoricoDerecha.setCurrentText('Elipse-1')
                        ancho = item.rect().width()
                        alto = item.rect().height()
                        centroEllipseX = (alto/2) + posXRect1
                        centroEllipseY = (ancho/2) + posYRect1                       
                        #print(f"centroX:{centroEllipseX}-centroY:{centroEllipseY}-ancho:{ancho}-alto:{alto}")
                        x = np.linspace(0,382,382)
                        y = np.linspace(0,288,288)[:,None]
                        ellipse = ((x-centroEllipseX)/ancho)**2+((y-centroEllipseY)/alto)**2 <= 1
                        sampleImagenTh = self.matrizImgThIzq[:,:,self.indice]        
                        valoresDentroElipse = sampleImagenTh[ellipse]
                        if valoresDentroElipse.shape[0] > 0:
                            minThRoi = np.amin(valoresDentroElipse)
                            maxThRoi = np.amax(valoresDentroElipse)
                            avgThRoi = np.mean(valoresDentroElipse)
                            medianaThRoi = np.median(valoresDentroElipse)
                            desvioThRoi = np.std(valoresDentroElipse)
                            area = ancho * alto * 3.14 #ancho*alto*pi
                            self.output1MessurementRoiMaxDer.setText(str(maxThRoi))
                            self.output2MessurementRoiMinDer.setText(str(minThRoi))
                            self.output3MessurementRoiAvgDer.setText(str(avgThRoi))
                            self.output4MessurementRoiMedianDer.setText(str(medianaThRoi))
                            self.output5MessurementRoiStdDer.setText(str(desvioThRoi))
                            self.output6MessurementRoiAreaDer.setText(str(area))
                            #print(f"calculamos los valores min:{minThRoi}-max:{maxThRoi}-avg:{avgThRoi}")                            
                        #print(valoresDentroElipse)
                    elif indice == 1:
                        self.roisComboHistoricoDerecha.setCurrentText('Elipse-2')
                        ancho = item.rect().width()
                        alto = item.rect().height()
                        centroEllipseX = (alto/2) + posXRect1
                        centroEllipseY = (ancho/2) + posYRect1                       
                        #print(f"centroX:{centroEllipseX}-centroY:{centroEllipseY}-ancho:{ancho}-alto:{alto}")
                        x = np.linspace(0,382,382)
                        y = np.linspace(0,288,288)[:,None]
                        ellipse = ((x-centroEllipseX)/ancho)**2+((y-centroEllipseY)/alto)**2 <= 1
                        sampleImagenTh = self.matrizImgThIzq[:,:,self.indice]        
                        valoresDentroElipse = sampleImagenTh[ellipse]
                        if valoresDentroElipse.shape[0] > 0:
                            minThRoi = np.amin(valoresDentroElipse)
                            maxThRoi = np.amax(valoresDentroElipse)
                            avgThRoi = np.mean(valoresDentroElipse)
                            medianaThRoi = np.median(valoresDentroElipse)
                            desvioThRoi = np.std(valoresDentroElipse)
                            area = ancho * alto * 3.14 #ancho*alto*pi
                            self.output1MessurementRoiMaxDer.setText(str(maxThRoi))
                            self.output2MessurementRoiMinDer.setText(str(minThRoi))
                            self.output3MessurementRoiAvgDer.setText(str(avgThRoi))
                            self.output4MessurementRoiMedianDer.setText(str(medianaThRoi))
                            self.output5MessurementRoiStdDer.setText(str(desvioThRoi))
                            self.output6MessurementRoiAreaDer.setText(str(area))
                            #print(f"calculamos los valores min:{minThRoi}-max:{maxThRoi}-avg:{avgThRoi}")                            
                        #print(valoresDentroElipse)
                    break
                indice += 1            
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
                #print("tengo que meter zoom en izq")
                #hago zoom sobre la imagen
                self.imageHistory1ViewPixMapItem.scale(1.01,1.01)
                #self.buttonRectRoiActionHistoryIzq.setChecked(False)
                #self.buttonLineRoiActionHistoryIzq.setChecked(False)
                #self.buttonEllipRoiActionHistoryIzq.setChecked(False)
                self.buttonZoomOutActionHistoryIzq.setChecked(False)
            elif data == "zoomInTabHistoryDer":
                #print("tengo que meter zoom en der")
                self.imageHistory2ViewPixMapItem.scale(1.01,1.01)
                #self.buttonRectRoiActionHistoryDer.setChecked(False)
                #self.buttonLineRoiActionHistoryDer.setChecked(False)
                #self.buttonEllipRoiActionHistoryDer.setChecked(False)
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
                #print("tengo que sacar zoom en izq")
                #hago zoom out sobre la imagen
                self.imageHistory1ViewPixMapItem.scale(0.99,0.99)
                #self.buttonRectRoiActionHistoryIzq.setChecked(False)
                #self.buttonLineRoiActionHistoryIzq.setChecked(False)
                #self.buttonEllipRoiActionHistoryIzq.setChecked(False)
                self.buttonZoomInActionHistoryIzq.setChecked(False)
            elif data == "zoomOutTabHistoryDer":
                #print("tengo que sacar zoom en der")
                self.imageHistory2ViewPixMapItem.scale(0.99,0.955)
                #self.buttonRectRoiActionHistoryDer.setChecked(False)
                #self.buttonLineRoiActionHistoryDer.setChecked(False)
                #self.buttonEllipRoiActionHistoryDer.setChecked(False)
                self.buttonZoomInActionHistoryDer.setChecked(False)
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
                print("tengo que mostrar u ocultar los rectangulos der")
                #self.buttonLineRoiActionHistoryIzq.setChecked(False)
                #self.buttonEllipRoiActionHistoryIzq.setChecked(False)
                self.buttonZoomInActionHistoryIzq.setChecked(False)
                self.buttonZoomOutActionHistoryIzq.setChecked(False)
                #mostramos los rectangulos
                self.listaItemsRect[0].show()
                self.listaItemsRect[1].show()
            elif data == "roiRectanguloTabHistoryDer":
                print("tengo que mostrar u ocultar los rectangulos der")
                #self.buttonLineRoiActionHistoryDer.setChecked(False)
                #self.buttonEllipRoiActionHistoryDer.setChecked(False)
                self.buttonZoomInActionHistoryDer.setChecked(False)
                self.buttonZoomOutActionHistoryDer.setChecked(False)
                #mostramos los rectangulos
                self.listaItemsRect2[0].show()
                self.listaItemsRect2[1].show()
        else:
            if data == "roiRectanguloTabHistoryIzq" :
                self.listaItemsRect[0].hide()
                self.listaItemsRect[1].hide()
            elif data == "roiRectanguloTabHistoryDer":
                self.listaItemsRect2[0].hide()
                self.listaItemsRect2[1].hide()
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
                print("tengo que mostrar u ocultar circulo izq")
                #self.buttonRectRoiActionHistoryIzq.setChecked(False)
                #self.buttonLineRoiActionHistoryIzq.setChecked(False)
                self.buttonZoomInActionHistoryIzq.setChecked(False)
                self.buttonZoomOutActionHistoryIzq.setChecked(False)
                self.listaItemsEllipse[0].show()
                self.listaItemsEllipse[1].show()
            elif data == "roiEllipseTabHistoryDer":
                print("tengo que mostrar u ocultar circulo der")
                #self.buttonRectRoiActionHistoryDer.setChecked(False)
                #self.buttonLineRoiActionHistoryDer.setChecked(False)
                self.buttonZoomInActionHistoryDer.setChecked(False)
                self.buttonZoomOutActionHistoryDer.setChecked(False)
                self.listaItemsEllipse2[0].show()
                self.listaItemsEllipse2[1].show()
        else:
            if data == "roiEllipseTabHistoryIzq":
                self.listaItemsEllipse[0].hide()
                self.listaItemsEllipse[1].hide()
            elif data == "roiEllipseTabHistoryDer":
                self.listaItemsEllipse2[0].hide()
                self.listaItemsEllipse2[1].hide()
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
                print("tengo que mostrar u ocultar linea izq")
                #self.buttonRectRoiActionHistoryIzq.setChecked(False)
                #self.buttonEllipRoiActionHistoryIzq.setChecked(False)
                self.buttonZoomInActionHistoryIzq.setChecked(False)
                self.buttonZoomOutActionHistoryIzq.setChecked(False)
                self.listaItemsLine[0].show()
                self.listaItemsLine[1].show()
            elif data == "roiLineTabHistoryDer":
                print("tengo que mostrar u ocultar linea der")
                #self.buttonRectRoiActionHistoryDer.setChecked(False)
                #self.buttonEllipRoiActionHistoryDer.setChecked(False)
                self.buttonZoomInActionHistoryDer.setChecked(False)
                self.buttonZoomOutActionHistoryDer.setChecked(False)
                self.listaItemsLine2[0].show()
                self.listaItemsLine2[1].show()
        else:
            if data == "roiLineTabHistoryIzq":
                self.listaItemsLine[0].hide()
                self.listaItemsLine[1].hide()
            elif data == "roiLineTabHistoryDer":
                self.listaItemsLine2[0].hide()
                self.listaItemsLine2[1].hide()
    #roto imagen de la izquierda
    def rotateimagenIzq(self, statusButton):
        if statusButton == True:
            self.rotarImagen180Izq = True
        else:
            self.rotarImagen180Izq = False
    #rot imagen de la derecha
    def rotateimagenDer(self, statusButton):
        if statusButton == True:
            self.rotarImagen180Der = True
        else:
            self.rotarImagen180Der = False
    #Defino la funcion asociada a la barra de progreso para la camara 1
    def handleTimer1(self):
        value = self.pbarTab1.value()
        print("estado=",self.statusConnectionCam1)
        if value < 100 and self.statusConnectionCam1 == False:
            value = value + 1
            self.pbarTab1.setValue(value)
        else:
            print("stop timer 1")
            self.pbarTab1.setValue(100) #termino de conectar la camara indico con un valor de 100 %
            self.timerPbar1.stop()
    #defino la funcion asociada a la barra de progreso para la camara 2
    def handleTimer2(self):
        value = self.pbarTab2.value()
        if value < 100 and self.statusConnectionCam1 == False:
            value = value + 1
            self.pbarTab2.setValue(value)
        else:
            print("stop timer 2")
            self.pbarTab2.setValue(100)
            self.timerPbar2.stop()
    #defino la funcion asociada a la barra de progreso para la camara 3
    def handleTimer3(self):
        value = self.pbarTab3.value()
        if value < 100 and self.statusConnectionCam1 == False:
            value = value + 1
            self.pbarTab3.setValue(value)
        else:
            print("stop timer 3")
            self.timerPbar3.stop()
            self.pbarTab3.setValue(100)
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
    def profileRoiCombo2(self):
        if not self.profileSelComboDer.count():
            self.profileSelComboDer.addItems(['Profile Horizontal Rect2', 'Profile Vertical Rect2', 'Profile Horizontal Ellipse2', 'Profile Vertical Ellipse2', 'Profile Line2'])
        self.profileSelComboDer.setItemIcon(0, QIcon(os.path.join(basedir, "appIcons", "ruler-triangle.png")))
        self.profileSelComboDer.setItemIcon(1, QIcon(os.path.join(basedir, "appIcons", "ruler-triangle.png")))
        self.profileSelComboDer.setItemIcon(2, QIcon(os.path.join(basedir, "appIcons", "ruler-triangle.png")))
        self.profileSelComboDer.setItemIcon(3, QIcon(os.path.join(basedir, "appIcons", "ruler-triangle.png")))
        self.profileSelComboDer.setItemIcon(4, QIcon(os.path.join(basedir, "appIcons", "ruler-triangle.png")))
    #Defino la funcion asociada a la seleccion de ROI Derecha Tab1
    def populateRoiCombo2(self):
        if not self.roiSelComboDer.count():
            self.roiSelComboDer.addItems(['ROI Rect2 Max', 'ROI Rect2 Min','ROI Rect2 Avg', 'ROI Line2 Max', 'ROI Line2 Min', 'ROI Line2 Avg', 'ROI Ellip2 Max', 'ROI Ellip2 Min', 'ROI Ellip2 Avg'])
        #agergamos los iconos para cada herramienta de medicion
        self.roiSelComboDer.setItemIcon(0, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roiSelComboDer.setItemIcon(1, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roiSelComboDer.setItemIcon(2, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roiSelComboDer.setItemIcon(3, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roiSelComboDer.setItemIcon(4, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roiSelComboDer.setItemIcon(5, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roiSelComboDer.setItemIcon(6, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roiSelComboDer.setItemIcon(7, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roiSelComboDer.setItemIcon(8, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
    #Defino la funcion asociada a la seleccion de camaras online
    def populateCamComboOnline(self):
        
        if not self.camComboOnline.count():
            self.camComboOnline.addItems(['cam1', 'cam2', 'cam3'])
        #agregamos los iconos para cada camara
        self.camComboOnline.setItemIcon(0, QIcon(os.path.join(basedir, "appIcons", "camera-lens.png")))
        self.camComboOnline.setItemIcon(1, QIcon(os.path.join(basedir, "appIcons", "camera-lens.png")))
        self.camComboOnline.setItemIcon(2, QIcon(os.path.join(basedir, "appIcons", "camera-lens.png")))
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
    #Defino la funcion asociada a seleccionar Rois
    #***
    def populateRoisComboHistoricosIzquierda(self):
        #si la cantidad de Rois esta vacia la lleno
        if not self.roisComboHistoricoIzquierda.count():
            self.roisComboHistoricoIzquierda.addItems(['Rectangle-1','Rectangle-2','Elipse-1','Elipse-2','Line-1','Line-2'])
        #agregamos los iconos
        self.roisComboHistoricoIzquierda.setItemIcon(0, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roisComboHistoricoIzquierda.setItemIcon(1, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roisComboHistoricoIzquierda.setItemIcon(2, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roisComboHistoricoIzquierda.setItemIcon(3, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roisComboHistoricoIzquierda.setItemIcon(4, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roisComboHistoricoIzquierda.setItemIcon(5, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
    def populateRoisComboHistoricosDerecha(self):
        #si la cantidad de Rois esta vacia la lleno
        if not self.roisComboHistoricoDerecha.count():
            self.roisComboHistoricoDerecha.addItems(['Rectangle-1','Rectangle-2','Elipse-1','Elipse-2','Line-1','Line-2'])
        #agregamos los iconos
        self.roisComboHistoricoDerecha.setItemIcon(0, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roisComboHistoricoDerecha.setItemIcon(1, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roisComboHistoricoDerecha.setItemIcon(2, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))   
        self.roisComboHistoricoDerecha.setItemIcon(3, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roisComboHistoricoDerecha.setItemIcon(4, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))
        self.roisComboHistoricoDerecha.setItemIcon(5, QIcon(os.path.join(basedir, "appIcons","ruler-crop.png")))   
    #***
    #instancio a la clase que muestra la popup de busqueda en calendario
    def popUpSearchDateToHistory(self):
        self.dlgDateSearch = PopUpDateSelected()
        self.dlgDateSearch.show()
    #aca tengo que instanciar a la clase que muestra la popup que muestra los archivos donde buscar la imagen 
    def leerArchivoIzq(self):
        print("leer archivo para imagen historica izquierda")
        popUp = popUpListFolder()
        if popUp.exec():
            print(f"nuevo path:{pathFolder[:-8]}")
            nombreArchivo = pathFolder[:-8]
            valorRetornadoMatriz = leerArchivoSincronico(nombreArchivo)
            self.matrizImgThIzq = valorRetornadoMatriz[0]
            self.matrizImgCvIzq = valorRetornadoMatriz[1]
            self.botonBackwardFileIzq.setEnabled(True)
            self.botonFordwardFileIzq.setEnabled(True)
        else:
            print("cancel")
    #aca tengo que dar la funcionalidad de retroceder en las imagenes cargadas
    def retrocederArchivoIzq(self):
        print("presiono boton retroceder una imagen en historicos izquierda")
        self.indice -= 1
        if self.indice <= 0:
            self.indice = 28        
        #leer imagne cv
        sampleImagenCv = np.array(self.matrizImgCvIzq[:,:,:,self.indice], dtype=np.uint8)
        qt_imgCv = self.convert_cv_qt(sampleImagenCv)
        self.imageHistory1CamScene.removeItem(self.imageHistory1PixmapItem)
        self.imageHistory1PixmapItem=self.imageHistory1CamScene.addPixmap(qt_imgCv)                
        self.imageHistory1PixmapItem.setZValue(-1)
        if self.rotarImagen180Izq == True:
            puntoRotacion = self.imageHistory1PixmapItem.boundingRect().center()
            self.imageHistory1PixmapItem.setTransformOriginPoint(puntoRotacion)
            self.imageHistory1PixmapItem.setRotation(180)
        self.imageHistory1ViewPixMapItem.setScene(self.imageHistory1CamScene)        
    #aca tengo que dar la funcionalidad de avanzar en la imagenes cargadas
    def avanzarArchivoIzq(self):
        print("presiono boton avanzar una imagen en historicos izquierda")
        self.indice += 1
        if self.indice >= 29:
            self.indice = 0
        sampleImagenCv = np.array(self.matrizImgCvIzq[:,:,:,self.indice], dtype=np.uint8)
        qt_imgCv = self.convert_cv_qt(sampleImagenCv)
        self.imageHistory1CamScene.removeItem(self.imageHistory1PixmapItem)
        self.imageHistory1PixmapItem=self.imageHistory1CamScene.addPixmap(qt_imgCv)                
        self.imageHistory1PixmapItem.setZValue(-1)
        if self.rotarImagen180Izq == True:
            puntoRotacion = self.imageHistory1PixmapItem.boundingRect().center()
            self.imageHistory1PixmapItem.setTransformOriginPoint(puntoRotacion)
            self.imageHistory1PixmapItem.setRotation(180)            
        self.imageHistory1ViewPixMapItem.setScene(self.imageHistory1CamScene)        
    #aca tengo que instanciar a la clase que muestra la popup que muestra los archivos donde buscar la imagen 
    def leerArchivoDer(self):
        print("leer archivo para imagen historica derecha")
        popUp = popUpListFolder()
        if popUp.exec():
            print(f"nuevo path:{pathFolder[:-8]}")
            nombreArchivo = pathFolder[:-8]
            (self.matrizImgThDer, self.matrizImgCvDer) = leerArchivoSincronico(nombreArchivo)
            self.botonBackwardFileDer.setEnabled(True)
            self.botonFordwardFileDer.setEnabled(True)
        else:
            print("cancel")
    #aca tengo que dar la funcionalidad de retroceder en las magenes cargadas 
    def retrocederArchivoDer(self):
        print("presiono boton retroceder una imagen en historicos derecha")
        self.indice -= 1
        if self.indice <= 0:
            self.indice = 28
        sampleImagenCv = np.array(self.matrizImgCvDer[:,:,:,self.indice], dtype=np.uint8)
        qt_imgCv = self.convert_cv_qt(sampleImagenCv)
        self.imageHistory2CamScene.removeItem(self.imageHistory2PixmapItem)
        self.imageHistory2PixmapItem=self.imageHistory2CamScene.addPixmap(qt_imgCv)                
        self.imageHistory2PixmapItem.setZValue(-1)
        if self.rotarImagen180Der == True:
            puntoRotacion = self.imageHistory2PixmapItem.boundingRect().center()
            self.imageHistory2PixmapItem.setTransformOriginPoint(puntoRotacion)
            self.imageHistory2PixmapItem.setRotation(180)        
        self.imageHistory2ViewPixMapItem.setScene(self.imageHistory2CamScene)                
    #aca tengo que da la funionalidad de avanzar 
    def avanzarArchivoDer(self):
        print("presiono boton avanzar una imagen en historicos derecha")
        self.indice += 1
        if self.indice >= 29:
            self.indice = 0
        sampleImagenCv = np.array(self.matrizImgCvDer[:,:,:,self.indice], dtype=np.uint8)
        qt_imgCv = self.convert_cv_qt(sampleImagenCv)
        self.imageHistory2CamScene.removeItem(self.imageHistory2PixmapItem)
        self.imageHistory2PixmapItem=self.imageHistory2CamScene.addPixmap(qt_imgCv)                
        self.imageHistory2PixmapItem.setZValue(-1)
        if self.rotarImagen180Der == True:
            puntoRotacion = self.imageHistory2PixmapItem.boundingRect().center()
            self.imageHistory2PixmapItem.setTransformOriginPoint(puntoRotacion)
            self.imageHistory2PixmapItem.setRotation(180)            
        self.imageHistory2ViewPixMapItem.setScene(self.imageHistory2CamScene)                
    #*********
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
        self.pushButton1Cam1.setEnabled(False)
        if self.pushButton2Cam2.isChecked():                        
            self.pushButton2Cam2.toggle()
            self.pushButton2Cam2.setEnabled(True)
        if self.pushButton3Cam3.isChecked():
            self.pushButton3Cam3.toggle()
            self.pushButton3Cam3.setEnabled(True)
        if self.pushButton4Recorder.isChecked():
            self.pushButton4Recorder.toggle()
            self.pushButton4Recorder.setEnabled(True)
        if self.pushButton5Config.isChecked():
            self.pushButton5Config.toggle()
            self.pushButton5Config.setEnabled(True)
    #Defino la función asociado al botón para cambiar de pantalla Cam2
    def mostraPantallaCam2(self):
        page=self.bodyTabWidget.findChild(QWidget, 'tab2')
        index = self.bodyTabWidget.indexOf(page)
        #print(index)
        self.bodyTabWidget.setCurrentWidget(self.bodyTabWidget.findChild(QWidget,'tab2'))
        self.labelFunctionalWindowSelected.setText("Functional Window Cam 2")
        self.pushButton2Cam2.setEnabled(False)
        if self.pushButton1Cam1.isChecked():            
            self.pushButton1Cam1.toggle()
            self.pushButton1Cam1.setEnabled(True)
        if self.pushButton3Cam3.isChecked():
            self.pushButton3Cam3.toggle()
            self.pushButton3Cam3.setEnabled(True)
        if self.pushButton4Recorder.isChecked():
            self.pushButton4Recorder.toggle()
            self.pushButton4Recorder.setEnabled(True)
        if self.pushButton5Config.isChecked():
            self.pushButton5Config.toggle()
            self.pushButton5Config.setEnabled(True)
    #Defino la función asociado al botón para cambiar de pantalla Cam3
    def mostraPantallaCam3(self):
        page=self.bodyTabWidget.findChild(QWidget, 'tab3')
        index = self.bodyTabWidget.indexOf(page)
        #print(index)
        self.bodyTabWidget.setCurrentWidget(self.bodyTabWidget.findChild(QWidget,'tab3'))
        self.labelFunctionalWindowSelected.setText("Functional Window Cam 3")
        self.pushButton3Cam3.setEnabled(False)        
        if self.pushButton1Cam1.isChecked():            
            self.pushButton1Cam1.toggle()
            self.pushButton1Cam1.setEnabled(True)
        if self.pushButton2Cam2.isChecked():
            self.pushButton2Cam2.toggle()
            self.pushButton2Cam2.setEnabled(True)
        if self.pushButton4Recorder.isChecked():
            self.pushButton4Recorder.toggle()
            self.pushButton4Recorder.setEnabled(True)
        if self.pushButton5Config.isChecked():
            self.pushButton5Config.toggle()
            self.pushButton5Config.setEnabled(True)
    #Defino la función asociado al botón para cambiar a pantalla Recorder
    def mostraPantallaRecorder(self):
        page=self.bodyTabWidget.findChild(QWidget, 'tab4')
        index = self.bodyTabWidget.indexOf(page)
        #print(index)
        self.bodyTabWidget.setCurrentWidget(self.bodyTabWidget.findChild(QWidget,'tab4'))
        self.labelFunctionalWindowSelected.setText("Functional Window Recorded")
        self.pushButton4Recorder.setEnabled(False)
        if self.pushButton1Cam1.isChecked():            
            self.pushButton1Cam1.toggle()
            self.pushButton1Cam1.setEnabled(True)
        if self.pushButton2Cam2.isChecked():
            self.pushButton2Cam2.toggle()
            self.pushButton2Cam2.setEnabled(True)
        if self.pushButton3Cam3.isChecked():
            self.pushButton3Cam3.toggle()
            self.pushButton3Cam3.setEnabled(True)
        if self.pushButton5Config.isChecked():
            self.pushButton5Config.toggle()
            self.pushButton5Config.setEnabled(True)
    #Defino la función asociada al botón para cambiar a pantalla Configuración
    def mostraPantallaConfig(self):
        page=self.bodyTabWidget.findChild(QWidget, 'tab5')
        index = self.bodyTabWidget.indexOf(page)
        #print(index)
        self.bodyTabWidget.setCurrentWidget(self.bodyTabWidget.findChild(QWidget,'tab5'))
        self.labelFunctionalWindowSelected.setText("Functional Window Config Cameras")
        self.pushButton5Config.setEnabled(False)
        if self.pushButton1Cam1.isChecked():            
            self.pushButton1Cam1.toggle()
            self.pushButton1Cam1.setEnabled(True)
        if self.pushButton2Cam2.isChecked():
            self.pushButton2Cam2.toggle()
            self.pushButton2Cam2.setEnabled(True)
        if self.pushButton3Cam3.isChecked():
            self.pushButton3Cam3.toggle()
            self.pushButton3Cam3.setEnabled(True)
        if self.pushButton4Recorder.isChecked():
            self.pushButton4Recorder.toggle()
            self.pushButton4Recorder.setEnabled(True)
    #***************************************************
    #***************************************************
if __name__ == '__main__':      
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(basedir,"appIcons","logo.ico"))) #tgsLogo3.ico
    main = MainWindow()
    main.show()
    app.exec()