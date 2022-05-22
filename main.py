from PyQt5 import QtGui, QtCore
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtCore import QDateTime, Qt, QTimer, pyqtSignal
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
    QGraphicsView   
)
from PyQt5.QtGui import QIcon
import matplotlib
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
#Clase para graficar curvas
class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width,height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas,self).__init__(fig)

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
#Clase principal
class MainWindow(QDialog):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        #hago una instancia a mi combobox ==> userComboBox
        self.userCombo = UserComboBox(self)
        self.userCombo.popupAboutToBeShown.connect(self.populateCombo)

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

        tab1Boton = QWidget() #defino la pestaña de la tabla asociada al boton 1
        textEditTab1Boton = QLineEdit() #cargo el texto en el label, esto es de ejemplo vamos a reemplazarlo por la imagen
        textEditTab1Boton.setText("Aca va a ir en lugar del texto la barra de conexion") #este texto lo vamos a 
        subWindowTab1Boton = QWidget()
        scene = QGraphicsScene(0, 0, 0, 0)
        pixmap = QPixmap("imageCam1.jpg")                                                                                       #a reemplazar por la imagen
        pixmapitem = scene.addPixmap(pixmap)
        viewPixMapItem = QGraphicsView(scene)
        viewPixMapItem.setRenderHint(QPainter.Antialiasing)
        #agrego grafico izquierda
        graficoTab1Izq = MplCanvas(self, width=2, height=2, dpi=100)
        #genero un dataframe de prueba
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

        tab1BotonHbox = QHBoxLayout()
        tab1BotonHbox.addWidget(graficoTab1Izq)
        tab1BotonHbox.addWidget(viewPixMapItem)
        tab1BotonHbox.addWidget(graficoTab1Der)
        subWindowTab1Boton.setLayout(tab1BotonHbox)
        #agrego el texto q representa la barra de conexion y la ventana de trending e imagen                                                                               #
        tab1BotonVbox = QVBoxLayout()
        tab1BotonVbox.setContentsMargins(5,5,5,5)
        tab1BotonVbox.addWidget(textEditTab1Boton)
        tab1BotonVbox.addWidget(subWindowTab1Boton)
        tab1Boton.setLayout(tab1BotonVbox)

        tab2Boton = QWidget() #defino la pestaña de la 2 camara
        textEditTab2Boton = QLineEdit()
        textEditTab2Boton.setText("Aca va a ir en lugar del texto la barra de conexion")
        scene2 = QGraphicsScene(0,0,0,0)
        pixmap2 = QPixmap("imageCam2.jpg")
        pixmapitem2 = scene2.addPixmap(pixmap2)
        viewPixMapItem2 = QGraphicsView(scene2)
        viewPixMapItem2.setRenderHint(QPainter.Antialiasing)
        tab2BotonVBox = QVBoxLayout()
        tab2BotonVBox.setContentsMargins(5,5,5,5)
        tab2BotonVBox.addWidget(textEditTab2Boton)
        tab2BotonVBox.addWidget(viewPixMapItem2)
        tab2Boton.setLayout(tab2BotonVBox)

        tab3Boton = QWidget() #defino la pestaña de la 3 camara
        textEditTab3Boton = QLineEdit()
        textEditTab3Boton.setText("Aca va a ir en lugar del texto la barra de conexion")
        scene3 = QGraphicsScene(0,0,0,0)
        pixmap3 = QPixmap("imageCam3.jpg")
        pixmapitem3 = scene3.addPixmap(pixmap3)
        viewPixMapItem3 = QGraphicsView(scene3)
        viewPixMapItem3.setRenderHint(QPainter.Antialiasing)        
        tab3BotonVBox = QVBoxLayout()
        tab3BotonVBox.setContentsMargins(5,5,5,5)
        tab3BotonVBox.addWidget(textEditTab3Boton)
        tab3BotonVBox.addWidget(viewPixMapItem3)
        tab3Boton.setLayout(tab3BotonVBox)

        tab4Boton = QWidget() #defino la pestaña de las imagenes de los historicos
        textEditTab4Boton = QTextEdit()
        textEditTab4Boton.setPlainText("Aca va a ir en lugar de texto los registros historicos imagen y curvas")

        tab4BotonHBox = QHBoxLayout()
        tab4BotonHBox.setContentsMargins(5,5,5,5)
        tab4BotonHBox.addWidget(textEditTab4Boton)
        tab4Boton.setLayout(tab4BotonHBox)

        tab5Boton = QWidget() #defino la pestaña de configuracion para las cámaras
        textEditTab5Boton = QTextEdit()
        textEditTab5Boton.setPlainText("Aca va a ir en lugar de texto los controles para configuracion de las camaras")

        tab5BotonHBox = QHBoxLayout()
        tab5BotonHBox.setContentsMargins(5,5,5,5)
        tab5BotonHBox.addWidget(textEditTab5Boton)
        tab5Boton.setLayout(tab5BotonHBox)
        
        #Asignamos nombres a cada uno de los widgets que van a ser los tabs
        #vamos a utilizar estos nombres para referenciar y poder cambiar las pestañas

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
    #Defino la función asociada a logear un usuario
    def populateCombo(self):
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










    