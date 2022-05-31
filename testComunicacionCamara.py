
    #! /usr/bin/env python3
from ctypes.util import find_library
import numpy as np
import ctypes as ct
import cv2
import os

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import time

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

class Worker(QRunnable):
    '''Worker thread'''
    @pyqtSlot()
    def run(self):
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
        while chr(cv2.waitKey(1) & 255) != 'q':
                #get thermal and palette image with metadat
                ret = libir.evo_irimager_get_thermal_palette_image_metadata(thermal_width, thermal_height, npThermalPointer, palette_width, palette_height, npImagePointer, ct.byref(metadata))

                if ret != 0:
                        print('error on evo_irimager_get_thermal_palette_image ' + str(ret))
                        continue

                #calculate total mean value
                mean_temp = np_thermal.mean()
                mean_temp = mean_temp / 10. - 100

                print('Mean Temp: ' + str(mean_temp))

                #display palette image
                #cv2.imshow('Optris Image Test For Meditecna',np_img.reshape(palette_height.value, palette_width.value, 3)[:,:,::-1])
                frame = np_img.reshape(palette_height.value, palette_width.value, 3)[:,:,::-1]
                #cv2.imshow('prueba imagen', frame)
        # clean shutdown
        libir.evo_irimager_terminate()
class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.counter = 0

        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        layout = QVBoxLayout()

        self.l = QLabel("Start")
        b = QPushButton("Danger")
        b.pressed.connect(self.oh_no)

        c = QPushButton("?")
        c.pressed.connect(self.change_message)

        layout.addWidget(self.l)
        layout.addWidget(b)

        layout.addWidget(c)

        w = QWidget()
        w.setLayout(layout)

        self.setCentralWidget(w)

        self.show()

    def change_message(self):
        self.l.setText = "OH NO"
        print("aca")
    
    def oh_no(self):
        self.l.setText = 'press'
        worker = Worker()
        self.threadpool.start(worker)

app = QApplication([])
window = MainWindow()
app.exec()
    