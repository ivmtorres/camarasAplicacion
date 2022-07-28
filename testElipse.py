import numpy as np
import cv2
import matplotlib.pyplot as plt

elipse0PosX = 120
elipse0PosY = 120
elipse0Width = 20
elipse0Height = 10
thermal_img = np.random.randint(low=0,high=200,size=(382,288))

if (int(elipse0Height) > 1) and (int(elipse0Width) > 1):
            x0 = elipse0PosX
            y0 = elipse0PosY
            a = elipse0Width
            b = elipse0Height
            #construimos la mascara
            mask = np.zeros_like(thermal_img)
            #mostramos filas y columnas
            rows, cols = mask.shape
            #creamos una ellipse blanca
            mask = cv2.ellipse(mask, center=(elipse0PosX,elipse0PosY), axes=(int(elipse0Width/2),int(elipse0Height/2)), angle=0, startAngle=0, endAngle=360, color=(255,255,255), thickness=-1 )
            #aplico el filtro para dejar todo lo que esta fuera de la elipse en negro
            result = np.bitwise_and(thermal_img, mask)
            #imprimimos la dimension
            print(result.shape)
            #extraemos los componentes distintos de cero
            valoresInternosElipse = result[result>0]
            #mostramos dimension de los valores internos a la elipse
            print(len(valoresInternosElipse))
            # Plotting the results
            plt.subplot(131)
            plt.imshow(thermal_img)
            plt.subplot(132)
            plt.imshow(mask)
            plt.subplot(133)
            plt.imshow(result)
            plt.show()