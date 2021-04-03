import socket
import cv2
import cv2.cv as cv
import sys
import numpy
from time import time

def recvall(sock, count):
    buf = b''
    while count:
        try:
            newbuf = sock.recv(count)
            if not newbuf: return None
            buf += newbuf
            count -= len(newbuf)
        except:
            print "Conexion cerrada por el servidor"
            sys.exit(1)
    return buf



if __name__ == '__main__':

    PROTOCOLO = sys.argv[1]
    IP_SERVIDOR = sys.argv[2]
    PUERTO_SERVIDOR = int(sys.argv[3])
    PROTOCOLO = PROTOCOLO.upper()

    if (PROTOCOLO == "UDP"):
    ############################# CLIENTE UDP #############################
        udp_cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        mensaje = "me quiero conectar"
        udp_cliente.sendto (mensaje, (IP_SERVIDOR, PUERTO_SERVIDOR))    
        cv.NamedWindow("servidor camara udp", 1) # Nombre de la ventana
        buff = 1024 #seteamos el tamanio del buffer, solo se permiten enviar buffers o strings entre sockets
        t_ini = time()
        udp_cliente.settimeout(5)
        while True:
            t_act = time()
            if(t_act - t_ini >= 30):
                print "Pasaron 30, y mando al servidor que sigo aca"
                udp_cliente.sendto (mensaje, (IP_SERVIDOR, PUERTO_SERVIDOR))
                t_ini = time()
            try:    
                jpgstring, addr = udp_cliente.recvfrom(buff*64) #Recibimos el buffer y lo multiplicamos por 64
            except socket.timeout: 
                print "Conexion cerrada por el servidor" #socket.timeout
                sys.exit(1)
            narray = numpy.fromstring(jpgstring, dtype = "uint8") #Separamos lo encodeado, en un arreglo
            decimg = cv2.imdecode(narray,1) #leemos ese arreglo en decimg
            cv2.imshow("servidor camara udp", decimg) #leemos
            if cv.WaitKey(10) == 27: #salida con escape, tecla 27
                break
        udp_cliente.close()




    elif (PROTOCOLO == "TCP"):
    ############################# CLIENTE TCP #############################
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((IP_SERVIDOR, PUERTO_SERVIDOR))
        except:
            print "La IP o el puerto dados o bien son invalidos o el servidor no existe."    
            sys.exit(1)
        cv.NamedWindow("servidor camara tcp", 1) # Nombre de la ventana

        while True:
            try:
                length = recvall(s,16)
                stringData = recvall(s, int(length))
                data = numpy.fromstring(stringData, dtype='uint8')
                decimg=cv2.imdecode(data,1)
                cv2.imshow('servidor camara tcp',decimg)
                cv2.waitKey(10)
                if cv.WaitKey(10) == 27: #salida con escape, tecla 27
                    break
            except:
                print "Conexion cerrada por el servidor"
                sys.exit(1)
        s.close()
    else:
        print "Elija un protocolo valido."


    cv2.destroyAllWindows() 