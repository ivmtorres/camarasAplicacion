from faulthandler import disable
from functools import partial
from msilib.schema import CheckBox
from typing import ValuesView
from PyQt5 import QtGui, QtCore
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import QDateTime, Qt, QTimer, pyqtSignal, QSize, QPoint, QPointF, QRectF, QEasingCurve, QPropertyAnimation, QSequentialAnimationGroup, pyqtSlot, pyqtProperty
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
    QAction   
)
from PyQt5.QtGui import QIcon, QPaintEvent
import matplotlib
from matplotlib.widgets import Widget
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import pandas as pd
import sys, os

basedir = os.path.dirname(__file__)

try:
    from ctypes import winddl
    myappid = "ar.com.tgs.cameraApp.00"
    winddl.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass

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
        self.cancelSearchButton = QPushButton("Cancel")
        self.cancelSearchButton.clicked.connect(self.realizarBusquedaCancel)
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
        self.valueDefaultPreset = QLineEdit("....")
        self.valueDefaultPreset.setStyleSheet("border: 2px solid black;")
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

#Clase principal
class MainWindow(QDialog):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        #hago una instancia a mi combobox ==> userComboBox
        self.userCombo = UserComboBox(self) #combo box de usuarios
        self.userCombo.popupAboutToBeShown.connect(self.populateUserCombo)

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
        self.bodyTabWidget.setFixedSize(700,500)
        #***************************************
        #Creo el contenido de la primer pestaña
        #***************************************
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
 
        sub1WindowTab1Boton = QWidget() #creo una subventana para mostrar la camara1 y las curvas1
        scene = QGraphicsScene(0, 0, 0, 0)
        pixmap = QPixmap("imageCam1.jpg")                                                                                       #a reemplazar por la imagen
        pixmapitem = scene.addPixmap(pixmap)
        viewPixMapItem = QGraphicsView(scene)
        viewPixMapItem.setRenderHint(QPainter.Antialiasing)
        #agrego grafico izquierda para la camara 1
        graficoTab1Izq = MplCanvas(self, width=2, height=2, dpi=100)
        #genero un dataframe de prueba para la curva de la camara 1
        dfTab1Izq = pd.DataFrame([
            [0, 10],
            [5, 15],
            [2, 20],
            [15, 25],
            [4, 10]
        ], columns=['A','B'])
        dfTab1Izq.plot(ax=graficoTab1Izq.axes)
        #agrego grafico derecha
        graficoTab1Der = MplCanvas(self,width=2, height=2, dpi=100)
        #genero un dataframe de prueba
        dfTab1Der = pd.DataFrame([
            [0,10],
            [5,15],
            [2,20],
            [15,25],
            [4,10]
        ], columns=['A','B'])
        dfTab1Der.plot(ax=graficoTab1Der.axes)

        tab1BotonHboxSub1 = QHBoxLayout()
        tab1BotonHboxSub1.addWidget(graficoTab1Izq)
        tab1BotonHboxSub1.addWidget(viewPixMapItem)
        tab1BotonHboxSub1.addWidget(graficoTab1Der)
        sub1WindowTab1Boton.setLayout(tab1BotonHboxSub1)
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
        tab2BotonHBoxSub1.addWidget(viewPixMapItem2)
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
        tab3BotonHBoxSub1.addWidget(viewPixMapItem3) 
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
        #button Fit
        buttonZoomFitActionHistoryIzq = QAction(QIcon(os.path.join(basedir,"appIcons","magnifier-zoom-fit.png")),"zoom fit",self)
        buttonZoomFitActionHistoryIzq.setStatusTip("Zoom fit to full image")
        buttonZoomFitActionHistoryIzq.triggered.connect(self.zoomFitImage)
        buttonZoomFitActionHistoryIzq.setCheckable(True)
        #button in
        buttonZoomInActionHistoryIzq = QAction(QIcon(os.path.join(basedir,"appIcons","magnifier-zoom-in.png")),"zoom in", self)
        buttonZoomInActionHistoryIzq.setStatusTip("Zoom In")
        buttonZoomInActionHistoryIzq.triggered.connect(self.zoomInImage)
        buttonZoomInActionHistoryIzq.setCheckable(True)
        #button out
        buttonZoomOutActionHistoryIzq = QAction(QIcon(os.path.join(basedir,"appIcons","magnifier-zoom-out.png")),"zoom out",self)
        buttonZoomOutActionHistoryIzq.setStatusTip("Zoom Out")
        buttonZoomOutActionHistoryIzq.triggered.connect(self.zoomOutImage)
        buttonZoomOutActionHistoryIzq.setCheckable(True)
        #button roi rectangle
        buttonRectRoiActionHistoryIzq = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape.png")),"Roi Rect", self)
        buttonRectRoiActionHistoryIzq.setStatusTip("Rectangle Roi")
        buttonRectRoiActionHistoryIzq.triggered.connect(self.roiRectImage)
        buttonRectRoiActionHistoryIzq.setCheckable(True)
        #button roi ellipse
        buttonEllipRoiActionHistoryIzq = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape-ellipse.png")),"Roi Ellipse", self)
        buttonEllipRoiActionHistoryIzq.setStatusTip("Ellipse Roi")
        buttonEllipRoiActionHistoryIzq.triggered.connect(self.roiEllipImage)
        buttonEllipRoiActionHistoryIzq.setCheckable(True)
        #button roi line
        buttonLineRoiActionHistoryIzq = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape-line.png")),"Roi Line", self)
        buttonLineRoiActionHistoryIzq.setStatusTip("Line Roi")
        buttonLineRoiActionHistoryIzq.triggered.connect(self.roiLineImage)
        buttonLineRoiActionHistoryIzq.setCheckable(True)
        #button roi pollygon
        buttonPoliRoiActionHistoryIzq = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape-polygon.png")),"Roi Pollygon", self)
        buttonPoliRoiActionHistoryIzq.setStatusTip("Pollygon Roi")
        buttonPoliRoiActionHistoryIzq.triggered.connect(self.roiPollyImage)
        buttonPoliRoiActionHistoryIzq.setCheckable(True)
        #agrego los botones al toolbar
        toolBarImageHistoryIzq.addAction(buttonZoomFitActionHistoryIzq)
        toolBarImageHistoryIzq.addAction(buttonZoomInActionHistoryIzq)
        toolBarImageHistoryIzq.addAction(buttonZoomOutActionHistoryIzq)
        toolBarImageHistoryIzq.addAction(buttonRectRoiActionHistoryIzq)
        toolBarImageHistoryIzq.addAction(buttonEllipRoiActionHistoryIzq)
        toolBarImageHistoryIzq.addAction(buttonLineRoiActionHistoryIzq)
        toolBarImageHistoryIzq.addAction(buttonPoliRoiActionHistoryIzq)

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
        #button Fit
        buttonZoomFitActionHistoryDer = QAction(QIcon(os.path.join(basedir,"appIcons","magnifier-zoom-fit.png")),"zoom fit",self)
        buttonZoomFitActionHistoryDer.setStatusTip("Zoom fit to full image")
        buttonZoomFitActionHistoryDer.triggered.connect(self.zoomFitImage)
        buttonZoomFitActionHistoryDer.setCheckable(True)
        #button In
        buttonZoomInActionHistoryDer = QAction(QIcon(os.path.join(basedir,"appIcons","magnifier-zoom-in.png")),"zoom in", self)
        buttonZoomInActionHistoryDer.setStatusTip("Zoom In")
        buttonZoomInActionHistoryDer.triggered.connect(self.zoomInImage)
        buttonZoomInActionHistoryDer.setCheckable(True)
        #button Out
        buttonZoomOutActionHistoryDer = QAction(QIcon(os.path.join(basedir,"appIcons","magnifier-zoom-out.png")),"zoom out", self)
        buttonZoomOutActionHistoryDer.setStatusTip("Zoom Out")
        buttonZoomOutActionHistoryDer.triggered.connect(self.zoomOutImage)
        buttonZoomOutActionHistoryDer.setCheckable(True)
        #button Roi Rectangle 
        buttonRectRoiActionHistoryDer = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape.png")),"Roi Rect", self)
        buttonRectRoiActionHistoryDer.setStatusTip("Rectangle Roi")
        buttonRectRoiActionHistoryDer.triggered.connect(self.roiRectImage)
        buttonRectRoiActionHistoryDer.setCheckable(True)
        #button Roi Ellipse
        buttonEllipRoiActionHistoryDer = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape-ellipse.png")),"Roi Ellipse", self)
        buttonEllipRoiActionHistoryDer.setStatusTip("Ellipse Roi")
        buttonEllipRoiActionHistoryDer.triggered.connect(self.roiEllipImage)
        buttonEllipRoiActionHistoryDer.setCheckable(True)
        #button Roi Line
        buttonLineRoiActionHistoryDer = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape-line.png")),"Roi Line",self)
        buttonLineRoiActionHistoryDer.setStatusTip("Line Roi")
        buttonLineRoiActionHistoryDer.triggered.connect(self.roiLineImage)
        buttonLineRoiActionHistoryDer.setCheckable(True)
        #button Roi Pollygon
        buttonPoliRoiActionHistoryDer = QAction(QIcon(os.path.join(basedir,"appIcons","layer-shape-polygon.png")),"Roi Pollygon",self)
        buttonPoliRoiActionHistoryDer.setStatusTip("Pollygon Roi")
        buttonPoliRoiActionHistoryDer.triggered.connect(self.roiPollyImage)
        buttonPoliRoiActionHistoryDer.setCheckable(True)
        #agrego los botones al toolbar
        toolBarImageHistoryDer.addAction(buttonZoomFitActionHistoryDer)
        toolBarImageHistoryDer.addAction(buttonZoomInActionHistoryDer)
        toolBarImageHistoryDer.addAction(buttonZoomOutActionHistoryDer)
        toolBarImageHistoryDer.addAction(buttonRectRoiActionHistoryDer)
        toolBarImageHistoryDer.addAction(buttonEllipRoiActionHistoryDer)
        toolBarImageHistoryDer.addAction(buttonLineRoiActionHistoryDer)
        toolBarImageHistoryDer.addAction(buttonPoliRoiActionHistoryDer)

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
    #defino la funcion asociada con el cambio de preset de la camara 1
    def popUpConfiguracionPresetCam1(self, checkbox):
        print("cambiar preset seleccionado en camara 1")
        print(checkbox)
        ##
        #Tenemos que agregar la popup W
        if checkbox.isChecked() == True:
            self.dlgChangePresetCam1 = PopUPWritePresetCam()
            self.dlgChangePresetCam1.show()
        ##
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
                
        ##
    #defino la funcion asociada con el cambio de preset de la camara 2
    def popUpConfiguracionPresetCam3(self, checkbox):
        print("cambiar preset seleccionado en camara 3")
        ##
        #Tenemos que agregar la popup
        if checkbox.isChecked() == True:
            self.dlgChangePresetCam3 = PopUPWritePresetCam()
            self.dlgChangePresetCam3.show()
    
    def popUpRestartConfiguracionPresetCam3(self, checkbox):
        print("reset preset seleccion en camara 3")
        if checkbox.isChecked() == False:
            self.dlgDefaultPresetCam3 = PopUpResetPresetCam()
            self.dlgDefaultPresetCam3.show()
        ##
    #defino la funcion asociada a los zoom de imagen
    def zoomFitImage(self):
        print("Zoom Fit to the full image") #ajusto el zoom al tama;o de la imagen
                                            #la logica va a ir aca para la selccion 
                                            # de la herramienta de forma que al hacer
                                            # un click en la imagen se capture y se
                                            # magnifique en esa zona 
    def zoomInImage(self):
        print("Zoom In to the image")

    def zoomOutImage(self):
        print("Zoom Out to the image") 
    
    def roiRectImage(self):
        print("Dibujar Roi Rectangulo")
    
    def roiEllipImage(self):
        print("Dibujar Roi Ellipse")
    
    def roiLineImage(self):
        print("Dibujar Roi Linea")
    
    def roiPollyImage(self):
        print("Dibujar Roi Poligono")
    
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
        self.close()    #Cuando hacemos un click cerramos la aplicacion
    
    #Defino la función asociado al botón para cambiar de pantalla Cam1
    def mostraPantallaCam1(self):
        page=self.bodyTabWidget.findChild(QWidget, 'tab1')
        index = self.bodyTabWidget.indexOf(page)
        print(index)
        self.bodyTabWidget.setCurrentWidget(self.bodyTabWidget.findChild(QWidget,'tab1'))
        self.labelFunctionalWindowSelected.setText("Functional Window Cam 1")        
    #Defino la función asociado al botón para cambiar de pantalla Cam2
    def mostraPantallaCam2(self):
        page=self.bodyTabWidget.findChild(QWidget, 'tab2')
        index = self.bodyTabWidget.indexOf(page)
        print(index)
        self.bodyTabWidget.setCurrentWidget(self.bodyTabWidget.findChild(QWidget,'tab2'))
        self.labelFunctionalWindowSelected.setText("Functional Window Cam 2")
    #Defino la función asociado al botón para cambiar de pantalla Cam3
    def mostraPantallaCam3(self):
        page=self.bodyTabWidget.findChild(QWidget, 'tab3')
        index = self.bodyTabWidget.indexOf(page)
        print(index)
        self.bodyTabWidget.setCurrentWidget(self.bodyTabWidget.findChild(QWidget,'tab3'))
        self.labelFunctionalWindowSelected.setText("Functional Window Cam 3")
    #Defino la función asociado al botón para cambiar a pantalla Recorder
    def mostraPantallaRecorder(self):
        page=self.bodyTabWidget.findChild(QWidget, 'tab4')
        index = self.bodyTabWidget.indexOf(page)
        print(index)
        self.bodyTabWidget.setCurrentWidget(self.bodyTabWidget.findChild(QWidget,'tab4'))
        self.labelFunctionalWindowSelected.setText("Functional Window Recorded")
    #Defino la función asociada al botón para cambiar a pantalla Configuración
    def mostraPantallaConfig(self):
        page=self.bodyTabWidget.findChild(QWidget, 'tab5')
        index = self.bodyTabWidget.indexOf(page)
        print(index)
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










    