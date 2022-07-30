from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout,QHBoxLayout, QPushButton, QRadioButton
from PyQt5.QtGui import QPixmap
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
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
        self._incFocusPosition = False
        self._decFocusPosition = False
        self.focusPositionAnterior = 50
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
        
        
        pathLog = ct.c_char_p(b'logfilename')

        palette_width = ct.c_int() 
        palette_height = ct.c_int() 

        thermal_width = ct.c_int()
        thermal_height = ct.c_int()

        serial = ct.c_ulong()

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
            if self._incFocusPosition:
                print("incrementar focus position 10%")
                #get the focus position
                ret = libir.evo_irimager_get_focusmotor_pos(ct.byref(focusPosition))
                print('focus: ' + str(focusPosition.value))
                focusPositionNuevo = ct.c_float(self.focusPositionAnterior + 10)
                focusPositionNuevoCrudo = self.focusPositionAnterior + 10
                print("nuevo focus: {}".format(focusPositionNuevo.value) )
                ret = libir.evo_irimager_set_focusmotor_pos(focusPositionNuevo)#(pos=ct.c_float(55.5))
                self.focusPositionAnterior = focusPositionNuevoCrudo
                self._incFocusPosition = False
                if ret != 0:
                    print('error on evo_irimager_get_thermal_palette_image ' + str(ret))
                    break
            if self._decFocusPosition:
                print("incrementar focus position 10%")
                #get the focus position
                ret = libir.evo_irimager_get_focusmotor_pos(ct.byref(focusPosition))
                print('focus: ' + str(focusPosition.value))
                focusPositionNuevo = ct.c_float(self.focusPositionAnterior - 10)
                focusPositionNuevoCrudo = self.focusPositionAnterior - 10
                print("nuevo focus: {}".format(focusPositionNuevo.value) )
                ret = libir.evo_irimager_set_focusmotor_pos(focusPositionNuevo)#(pos=ct.c_float(55.5))
                self.focusPositionAnterior = focusPositionNuevoCrudo
                self._decFocusPosition = False
                if ret != 0:
                    print('error on evo_irimager_get_thermal_palette_image ' + str(ret))
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
    
    def incFocusPosition(self):
        #incrementamos en 5% focus position
        self._incFocusPosition = True
    
    def decFocusPosition(self):
        #decrementamos en 5% focus position
        self._decFocusPosition = True


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
        
        #creo boton de exit
        self.btnClose = QPushButton("Exit")
        self.btnClose.clicked.connect(self.closeApp)
        # create a vertical box layout and add the two labels
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        vbox.addWidget(self.image_label)
        hbox.addWidget(self.textLabel)
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
    def checkRadioButton(self):
        if self.radioButtonIncDecFocPos.isChecked():
            print("seleccion incrementar")
            self.incSelection=True
        else:
            print("seleccion decrementar")
            self.incSelection=False

    def btnIncDecFocusPositionState(self):               
            print("boton des presionado, ejecutamos la funcion de incrementar decrementar")
            self.incDecFocusPosition()

    def incDecFocusPosition(self):
        if self.incSelection:
            print("llamo a funcion incrementar focus position en el hilo de adquisicion de camara")
            self.thread.incFocusPosition()
        else:
            print("llamo a funcion decrementar focus position en el hilo de adquisicion de camara")
            self.thread.decFocusPosition()

    def closeApp(self):
        print("cierro aplicacion!")
        self.close() #genera el evento de close
    def closeEvent(self, event): #capturo el evento de close y cierro el hilo
        self.thread.stop() #cierro el hilo
        event.accept()



    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)
    
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