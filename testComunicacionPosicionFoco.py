from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout,QHBoxLayout, QPushButton, QRadioButton, QMenu, QLineEdit, QDoubleSpinBox
from PyQt5.QtGui import QPixmap, QDoubleValidator
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from matplotlib.pyplot import text
import numpy as np
from ctypes.util import find_library
import numpy as np
import ctypes as ct
import cv2
import os

#Define EvoIRFrameMetadata structure for additional frame infos
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

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self._incFocusPosition = False #flag para incrementar la posicion de focus se activa por la funcino asociada y se desactiva por el hilo de run
        self._decFocusPosition = False #flag para decrementar la posicion de focus se activa por la funcion asociada y se desactiva por el hilo de run       
        self.focusPositionAnterior = 50
        self._selRango0 = False #flag para seleccionar rango 0 se activa por la funcion y se desactiva por el hilo de run
        self._selRango1 = False #flag para seleccionar rango 1 se actia por la funcion y se desactiva por el hilo de run
        self._selRango2 = False #flag para seleccionar rango 2 se activa por la funcion y se desactiva por el hilo de run        
        self._changeEmisividad = False #flag para sleccionar incrementar o decrementar emisividad
        self._changeTransmisividad = False #flag para incrementar o decrementar transmisividad 
        self._changeTempAmbiente = False #flag para ajustar temperatura ambiente
        self._changePaleta = False
        #creamos 3 diccionarios uno por cada rango de temp
        #primer rango de temperatura
        self.rango0 = {"min": -20 , "max": 100}
        #segundo rango de temperatura
        self.rango1 = {"min": 0, "max": 250}
        #tercer rango de temperatura
        self.rango2 = {"min": 150 , "max": 900}
        #creamos una lista de 20 valores de emisividad
        self.emisividad = 0.85
        #seleccionamos el valores de transmisividad entre diez valores posibles
        self.transmisividad= 1
        #valor de temperatra ambiente 
        self.tempAmbiente=25
        #valor indice paleta
        self.indicePaleta = 1
    def run(self):
        # capture from thermal cam
        # load library
        if os.name == 'nt':
                #windows:
                libir = ct.CDLL("c:\\irDirectSDK\\sdk\\x64\\libirimager.dll") 
        else:
                #linux:
                libir = ct.cdll.LoadLibrary(ct.util.find_library("irdirectsdk"))

        #path to config xml file ---> ../config/generic.xml 
        pathXml = ct.c_char_p(b'C:\Users\lupus\OneDrive\Documentos\ProcesamientoDeImagenes\config\generic.xml ')

        # init vars
        pathFormat = ct.c_char_p()
        
        #log archivo
        pathLog = ct.c_char_p(b'logfilename')

        #resolicion imagen visible
        palette_width = ct.c_int() 
        palette_height = ct.c_int() 

        #resolucion imagen termica
        thermal_width = ct.c_int()
        thermal_height = ct.c_int()

        #valor numero de serie
        serial = ct.c_ulong()

        #valor de indice paleta
        valorIndicePaleta = ct.c_int()

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

        #focus position
        focusPosition = ct.c_float()
        focusPositionNuevo =ct.c_float()

        # init EvoIRFrameMetadata structure
        metadata = EvoIRFrameMetadata()

        # init lib
        ret = libir.evo_irimager_usb_init(pathXml, pathFormat, pathLog)
        if ret != 0:
                print("error at init")
                exit(ret)

        # get the serial number
        ret = libir.evo_irimager_get_serial(ct.byref(serial))
        print('serial: ' + str(serial.value))
        #get the focus position
        ret = libir.evo_irimager_get_focusmotor_pos(ct.byref(focusPosition))
        print('focus: ' + str(focusPosition.value))

        # get thermal image size
        libir.evo_irimager_get_thermal_image_size(ct.byref(thermal_width), ct.byref(thermal_height))
        print('thermal width: ' + str(thermal_width.value))
        print('thermal height: ' + str(thermal_height.value))

        # init thermal data container
        np_thermal = np.zeros([thermal_width.value * thermal_height.value], dtype=np.uint16)
        npThermalPointer = np_thermal.ctypes.data_as(ct.POINTER(ct.c_ushort))

        # get palette image size, width is different to thermal image width duo to stride alignment!!!
        libir.evo_irimager_get_palette_image_size(ct.byref(palette_width), ct.byref(palette_height))
        print('palette width: ' + str(palette_width.value))
        print('palette height: ' + str(palette_height.value))

        # init image container
        np_img = np.zeros([palette_width.value * palette_height.value * 3], dtype=np.uint8)
        npImagePointer = np_img.ctypes.data_as(ct.POINTER(ct.c_ubyte))


        # capture and display image till q is pressed
        while self._run_flag == True:
            #get thermal and palette image with metadat
            ret = libir.evo_irimager_get_thermal_palette_image_metadata(thermal_width, thermal_height, npThermalPointer, palette_width, palette_height, npImagePointer, ct.byref(metadata))

            if ret != 0:
                    print('error on evo_irimager_get_thermal_palette_image ' + str(ret))
                    continue
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
            if self._selRango0: #consultamos si se solicito cambiar el rango de temperatura 0
                print("Cambiamos a rango de temperatura 0")
                self._selRango0 = False #bajamos el flag despues de realizar el cambio de rango
                ret = libir.evo_irimager_set_temperature_range(tRango0_minimoM20, tRango0_maximo100)
                if ret != 0:
                    print("error on evo_irimager_set_temperature_range" + str(ret))
                    break
            if self._selRango1: #consultamos si se solicito cambiar al rango de temperatura 1
                print("Cambiamos al rango de temperatura 1")
                self._selRango1 = False #bajamos el flag despues de realizar el cambio de rango
                ret = libir.evo_irimager_set_temperature_range(tRango1_minimo0, tRango1_maximo250)
                if ret != 0:
                    print("error on evo_irimager_set_temperature_range" + str(ret))
                    break                
            if self._selRango2: #consultamos si se solicito cambiar al rango de temperatura 2
                print("Cambiamos al rango de temperatura 2")
                self._selRango2 = False #bajamos el flag despues de realizar el cambio de rango
                ret = libir.evo_irimager_set_temperature_range(tRango2_minimo150, tRango2_maximo900)
                if ret != 0:
                    print("error on evo_irimager_set_temperature_range" + str(ret))
                    break            
            if self._changeEmisividad: #consultamos si se solicito decrementar el valor de emisividad
                print("Modificamos la emisividad en una escala del rango {}".format(self.emisividad))
                valorEmisividadCargar = ct.c_float(self.emisividad)
                ret = libir.evo_irimager_set_radiation_parameters(valorEmisividadCargar, valorTransmisividadCargar, valorTemperaturaAmbiente)                
                self._changeEmisividad = False #bajamos el flag de decrementar emisividad despues de haber la decrementado
                if ret != 0:
                    print("error on evo_irimager_set_radiation_parameters" + str(ret))
                    break
            if self._changeTransmisividad: #consultamos si se solicito incrementar el valor de transmisividad
                print("cargamos el valor de transmisividad: {}".format(self.transmisividad))
                valorTransmisividadCargar = ct.c_float(self.transmisividad)
                ret = libir.evo_irimager_set_radiation_parameters(valorEmisividadCargar, valorTransmisividadCargar, valorTemperaturaAmbiente)
                self._changeTransmisividad = False #bajamos el flag indicando que ya se incremento la transmisividad
                if ret != 0:
                    print("error on evo_irimager_set_radiation_parameters" + str(ret))
                    break
            if self._changeTempAmbiente: #consultamos si se solicito cambiar el valor de temperatura ambiente
                print("cambiamos la temperatura ambiente {}".format(self.tempAmbiente)) #mostramos el valor de temperatura ambiente cargado
                valorTemperaturaAmbiente = ct.c_float(self.tempAmbiente)
                ret = libir.evo_irimager_set_radiation_parameters(valorEmisividadCargar ,valorTransmisividadCargar ,valorTemperaturaAmbiente)
                self._changeTempAmbiente = False #bajamos el flag de cambio del parametro temp ambiente
                if ret != 0:
                    print("error on evo_irimager_set_radiation_parameters" + str(ret))
                    break
            if self._changePaleta: #consultamos si se solicito cambiar la paleta
                print("cambiamos paleta: {}".format(self.indicePaleta))
                self._changePaleta = False
                valorIndicePaleta = ct.c_int(self.indicePaleta)
                ret = libir.evo_irimager_set_palette(valorIndicePaleta)
                if ret != 0:
                    print("error on evo_irimager_set_palette" + str(ret))
                    break
            #calculate total mean value
            mean_temp = np_thermal.mean()
            mean_temp = mean_temp / 10. - 100

            #print('Mean Temp: ' + str(mean_temp))

            #display palette image
            #cv2.imshow('Optris Image Test For Meditecna',np_img.reshape(palette_height.value, palette_width.value, 3)[:,:,::-1])
            frame = np_img.reshape(palette_height.value, palette_width.value, 3)[:,:,::-1]
            self.change_pixmap_signal.emit(frame)
        # clean shutdown
        libir.evo_irimager_terminate()   

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()

    def selPaleta(self, EnumOptrisColoringPalette):
        print("nueva seleccion de paleta: {}".format(EnumOptrisColoringPalette))
        self._changePaleta = True
        self.indicePaleta = EnumOptrisColoringPalette
        
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
        
    def incFocusPosition(self):             #estos metodos de la clase hilo son llamadas desde la funcion asociada al boton incrementar
        #incrementamos en 5% focus position
        self._incFocusPosition = True       #activamos el flag para incrementar la posicion del foco
    
    def decFocusPosition(self):             #este metodo de la clase hilo es llamada desde la funcion asociada al boton decrementar
        #decrementamos en 5% focus position
        self._decFocusPosition = True       #activamos el flag para decrementar la posicion del foco

    def selRango0Camara(self):
        #selecciono el rango cero que es de -20 a 100
        self._selRango0 = True              #indicamos en True el rango seleccionado bajaremos el flag dentro de la rutina de adquisicion
    
    def selRango1Camara(self):
        #selecciono el rango uno que es de 0 a 250
        self._selRango1 = True              #indicamos en True el rango seleccionado bajaremo el flag dentro de la rutina de adquisicion
    
    def selRango2Camara(self):
        #selecciono el rango dos que es de 150 a 900
        self._selRango2 = True              #indicamos en True el rango seleccionado bajaremos el flag dentro de la rutina de adquisicion 

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.incSelection = True
        self.setWindowTitle("Qt live label demo")
        self.disply_width = 640
        self.display_height = 480
        # create the label that holds the image
        self.image_label = QLabel(self)
        self.image_label.resize(self.disply_width, self.display_height)
        # create a text label
        self.textLabel = QLabel('THCam: ')
        #creo boton de incrementar focus position
        self.btnIncDecFocusPosition = QPushButton("+Focus")
        self.btnIncDecFocusPosition.clicked.connect(self.btnIncDecFocusPositionState)
        #seleccionar incrementar o decrementar foco position
        self.radioButtonIncDecFocPos = QRadioButton(self)
        self.radioButtonIncDecFocPos.setText("Inc/Dec")
        self.radioButtonIncDecFocPos.clicked.connect(self.checkRadioButton)
        #creamos boton para seleccionar el rango 
        self.selRangoTempBoton = QPushButton("selRango")
        menu = QMenu(self)
        menu.addAction("-20 a 100",self.selRango0)
        menu.addSeparator()
        menu.addAction("0 a 250",self.selRango1)
        menu.addSeparator()
        menu.addAction("150 a 900",self.selRango2)
        self.selRangoTempBoton.setMenu(menu)
        #creamos boton para seleccionar el color de la paleta
        self.selTipoPaleta = QPushButton("selPaleta")
        menuPaleta = QMenu(self)
        menuPaleta.addAction("eAlarmBlue",self.selPaletaAlarmBlue)
        menuPaleta.addSeparator()
        menuPaleta.addAction("eAlarmBlueHi", self.selPaletaAlarmBlueHi)
        menuPaleta.addSeparator()
        menuPaleta.addAction("eGrayBW", self.selPaletaGrayBW)
        menuPaleta.addSeparator()
        menuPaleta.addAction("eGrayWB", self.selPaletaGrayWB)
        menuPaleta.addSeparator()
        menuPaleta.addAction("eAlarmGreen",self.selPaletaAlarmGreen)
        menuPaleta.addSeparator()
        menuPaleta.addAction("eIron", self.selPaletaIron)
        menuPaleta.addSeparator()
        menuPaleta.addAction("eIronHi", self.selPaletaIronHi)
        menuPaleta.addSeparator()
        menuPaleta.addAction("eMedical", self.selPaletaMedical)
        menuPaleta.addSeparator()
        menuPaleta.addAction("eRainbow", self.selPaletaRainbow)
        menuPaleta.addSeparator()
        menuPaleta.addAction("eRainbowHi", self.selPaletaRainbowHi)
        menuPaleta.addSeparator()
        menuPaleta.addAction("eAlarmRed", self.selPaletaAlarmRed)
        menuPaleta.addSeparator()
        self.selTipoPaleta.setMenu(menuPaleta)
        #creamos qlabel editable para ingresar el valor de temperatura y un boton para cargar ese valor
        self.valorInTemperatura =QLineEdit("25.50",self)
        self.valorInTemperatura.setFixedWidth(40)
        self.valorInTemperatura.setValidator(QDoubleValidator(0.99,99.99,2))
        self.valorInTemperatura.setMaxLength(5)
        self.valorInTemperatura.returnPressed.connect(self.cambiarTemperatura)
        self.valorInTemperatura.setAlignment(Qt.AlignRight)
        #creamos qdobleSpin editable para ingresar el valor de transmisividad entre 0 - 1
        self.valorInTransmisividad = QDoubleSpinBox(self)
        self.valorInTransmisividad.setMaximum(100)
        self.valorInTransmisividad.setMinimum(1)
        self.valorInTransmisividad.setSingleStep(5)
        self.valorInTransmisividad.setValue(100)
        self.valorInTransmisividad.valueChanged.connect(self.cambiarTransmisividad)
        lineInTransmisividad = self.valorInTransmisividad.lineEdit()
        lineInTransmisividad.setReadOnly(True)
        #creamos qDobleSpin editable para ingresar el valor de emisividad entre 0 - 1
        self.valorInEmisividad = QDoubleSpinBox(self)
        self.valorInEmisividad.setMaximum(1.00)
        self.valorInEmisividad.setMinimum(0.01)
        self.valorInEmisividad.setSingleStep(0.01)
        self.valorInEmisividad.setValue(0.85)
        self.valorInEmisividad.valueChanged.connect(self.cambiarEmisividad)
        lineInEmisividad = self.valorInEmisividad.lineEdit()
        lineInEmisividad.setReadOnly(True)
        #creo boton de exit
        self.btnClose = QPushButton("Exit")
        self.btnClose.clicked.connect(self.closeApp)
        # create a vertical box layout and add the two labels
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        vbox.addWidget(self.image_label)
        hbox.addWidget(self.textLabel)
        hbox.addWidget(self.selTipoPaleta)
        hbox.addWidget(self.valorInEmisividad)
        hbox.addWidget(self.valorInTransmisividad)
        hbox.addWidget(self.valorInTemperatura)
        hbox.addWidget(self.selRangoTempBoton)
        hbox.addWidget(self.radioButtonIncDecFocPos)
        hbox.addWidget(self.btnIncDecFocusPosition)
        hbox.addWidget(self.btnClose)        
        vbox.addLayout(hbox)
        # set the vbox layout as the widgets layout
        self.setLayout(vbox)

        # create the video capture thread
        self.thread = VideoThread()
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()

    def selPaletaAlarmBlue(self):
        print("seleccion paleta AlarmBlue")
        indiceAlarmBlue = 1
        self.thread.selPaleta(indiceAlarmBlue)
        

    def selPaletaAlarmBlueHi(self):
        print("seleccion paleta AlarmBlueHi")
        indiceAlarmBlueHi = 2
        self.thread.selPaleta(indiceAlarmBlueHi)

    def selPaletaGrayBW(self):
        print("seleccion paleta GrayBW")
        indiceAlarmGrayBW = 3
        self.thread.selPaleta(indiceAlarmGrayBW)
    
    def selPaletaGrayWB(self):
        print("seleccion paleta GrayWB")
        indiceAlarmGrayWB = 4
        self.thread.selPaleta(indiceAlarmGrayWB)        

    def selPaletaAlarmGreen(self):
        print("seleccion paleta AlarmGreen")
        indiceAlarmGreen = 5
        self.thread.selPaleta(indiceAlarmGreen)

    def selPaletaIron(self):
        print("seleccion paleta Iron")
        indiceIron = 6
        self.thread.selPaleta(indiceIron)

    def selPaletaIronHi(self):
        print("seleccion paleta IronHi")
        indiceIronHi = 7
        self.thread.selPaleta(indiceIronHi)

    def selPaletaMedical(self):
        print("seleccion paleta Medical")
        indiceMedical = 8
        self.thread.selPaleta(indiceMedical)

    def selPaletaRainbow(self):
        print("seleccion paleta Rainbow")
        indiceRainbow = 9
        self.thread.selPaleta(indiceRainbow)
    
    def selPaletaRainbowHi(self):
        print("seleccion paleta RainbowHi")
        indiceRainbowHi = 10
        self.thread.selPaleta(indiceRainbowHi)
    
    def selPaletaAlarmRed(self):
        print("seleccion paleta AlarmRed")
        indiceAlarmRed = 11
        self.thread.selPaleta(indiceAlarmRed)

    def cambiarEmisividad(self):
        valorEmisividad = self.valorInEmisividad.value()
        print("el valor de emisividad seleccionado: {}".format(valorEmisividad))
        self.thread.incDecEmisividad(valorEmisividad)

    def cambiarTransmisividad(self): #funcion para cambiar la transmisividad del ambiente
        valorTransmisividad = self.valorInTransmisividad.value() / 100
        print("el valor de transmisividad seleccionado: {}".format(valorTransmisividad))
        self.thread.incDecTransmisividad(valorTransmisividad)

    def cambiarTemperatura(self): #funcion para cambiar la temperatura ambiente
        textoIngresado = self.valorInTemperatura.text().replace(",",".")
        if textoIngresado.isnumeric(): #verificamos que sea un numero
            valorTemp = float(textoIngresado) #leemos del Qlineedit el valor de temperatura
            print("seleccionamos cambiar temperatura ingresada: {}".format(valorTemp)) #tomamos el valor de temperatura y lo mostramos 
            self.thread.incDecTempAmbiente(valorTemp) #cargamos en el metodo del hilo para cambiar temperatura
        else:
            print("el valor ingresado no es un numero")

    def selRango0(self): #funcion para seleccionar rango 0
        print("seleccionamos rango 0")
        self.thread.selRango0Camara() #indicamos al hilo que cambie a rango 0

    def selRango1(self): #funcion para seleccionar rango 1
        print("seleccionamos rango 1")
        self.thread.selRango1Camara() #indicamos al hilo que cambie a rango 1

    def selRango2(self): #funcion para seleccionar rango 2
        print("seleccionamos rango 2")
        self.thread.selRango2Camara() #indicamos al hilo que cambie a rango 2

    def checkRadioButton(self): #funcion asociada al radio buton seleccionar accion incrementar o decrementar
        if self.radioButtonIncDecFocPos.isChecked(): #verificamos el estado del radio button si fue tildado 
            print("seleccion incrementar")          #cambiamos el estado del flag que indica si al presionar 
            self.incSelection=True                  #boton modificacion posicion del foco debemos incrementar
        else:
            print("seleccion decrementar")  
            self.incSelection=False                 #o debemos decrementar la posicion del foco

    def btnIncDecFocusPositionState(self): #funcion asociada al boton modificar posicion del foco 
            print("boton des presionado, ejecutamos la funcion de incrementar decrementar")
            self.incDecFocusPosition()      #llamo a la funcion que determina si se debe incrementar o decrementar la posicion del foco

    def incDecFocusPosition(self):         #esta funcion determina si se solicita incrementar o decrementar
        if self.incSelection:               #consultamos al flag de seleccion estado incrementar si es True 
            print("llamo a funcion incrementar focus position en el hilo de adquisicion de camara")
            self.thread.incFocusPosition()  #llamamos al metodo del hilo de adquisicion de la camara para incrementar el focus position
        else:                               #consultamos el flag de seleccion estado decrementar si es False 
            print("llamo a funcion decrementar focus position en el hilo de adquisicion de camara")
            self.thread.decFocusPosition()  #llamamos al metodo del hilo de adquisicion de la camara para decrementar el focus position

    def closeApp(self):
        print("cierro aplicacion!")
        self.close() #genera el evento de close
    def closeEvent(self, event): #capturo el evento de close y cierro el hilo
        self.thread.stop() #cierro el hilo
        event.accept()



    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img): #slot asociado al hilo de procesamiento de imagenes 
        """Updates the image_label with a new opencv image""" #cada vez que el hilo procese una imagen emite una señal
        qt_img = self.convert_cv_qt(cv_img)                     #esta señal esta asociada a esta funcion, la funcion
        self.image_label.setPixmap(qt_img)                  #recibe la señal la procesa y convirtiendo el dato qt a un dato de cv2 y lo carga
    
    def convert_cv_qt(self, cv_img):                        #convertimos el dato en qt de imagen a un dato en cv2
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