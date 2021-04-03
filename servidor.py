import threading			
import socket
import cv2
import numpy
import sys
import os
import select
from time import time
from time import sleep




#######################    SERVIDOR UDP ############################

class Servidor_UDP(threading.Thread):
	def __init__(self):		
		self.stopped = False			
		threading.Thread.__init__(self)
	
	def run(self):

		while True:
			try:
				ready = select.select([udp_servidor], [], [], 0)
				if ready[0]: 
					mensaje, datosCliente = udp_servidor.recvfrom(1024)
					key = str(datosCliente[0]) + ":" + str(datosCliente[1])
					t_actual = time ()
					if conexiones_udp.has_key(key): 
						# ese cliente ya esta conectado, debo actualizar su tiempo
						conexiones_udp[key] = (t_actual, datosCliente)
						print "El cliente UDP: " + str(datosCliente[0]) + " en el puerto origen " + str(datosCliente[1]) + " actualizo tiempo."

					else:
						# primera vez que hay algun cliente desde esa ip y puerto
						conexiones_udp[key] = (t_actual, datosCliente)
						print "Se ha establecido una conexion UDP con el cliente: " + str(datosCliente[0]) + " con puerto origen " + str(datosCliente[1])
				if (self.stopped):	
					break
			except:
				"Algo ha salido mal."
		udp_servidor.close()
		sys.exit()


	def stop(self):
	    self.stopped = True
				
			




#######################    SERVIDOR TCP ############################

class Servidor_TCP(threading.Thread):
	def __init__(self):	
		self.stopped = False	
		
		threading.Thread.__init__(self)
	
	def run(self):
		
		servidor_tcp = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		servidor_tcp.bind(('',puerto_tcp))
		servidor_tcp.listen(1)	
		servidor_tcp.setblocking(0)
		while True:
			#Esperamos una conexion entrante TCP por el puerto: puerto_tcp
			ready = select.select([servidor_tcp], [], [], 0)
			if ready[0]: 
				socketCliente, datosCliente = servidor_tcp.accept()
				conexiones_tcp.append(socketCliente)
				print "Se ha establecido una conexion TCP con el cliente: " + str(datosCliente[0]) + " con puerto origen " + str(datosCliente[1])
			if (self.stopped):	
				break

		servidor_tcp.close()
		sys.exit()

	def stop(self):
	    self.stopped = True
	    




#######################    PROGRAMA PRINCIPAL ############################
if __name__ == '__main__':
	
	try:

		puerto_tcp = int(sys.argv[1])
		puerto_udp = int(sys.argv[2])
		cam = True
		if(len(sys.argv) > 3):
			ubicacion_video = str(sys.argv[3])
			cam = False
			print "Se abrira " + ubicacion_video + " demorara unos segundos..." 


		conexiones_udp = {"ip: puerto": (0.0, ("ip","puertoudp")) }
		conexiones_udp.clear()

		conexiones_tcp = []

		conexiones_borrar = []

		#inicializador socket global UDP
		udp_servidor = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) 
		# escucha peticiones por el puerto: puerto_udp
		udp_servidor.bind(("", puerto_udp))

		#levanto peticiones TCP (hilo)
		server_tcp = Servidor_TCP()
		server_tcp.start()

		#levanto peticiones UDP (hilo)
		server_udp = Servidor_UDP()
		server_udp.start()
		

		if(cam):
			#seteos de la captura de video
			capture = cv2.VideoCapture(0)
			capture.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 320)
			capture.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 240)
			ret, frame = capture.read()
		else:
			#seteo del archivo video
			cap = cv2.VideoCapture(ubicacion_video)
			ret, f = cap.read()
			while (not ret):
				ret, f = cap.read()
			print "Video cargado."
			width = int(cap.get(3))  # float
		 	height = int(cap.get(4)) # float 
			frame = cv2.resize(f, ( 320, 240))
			frame_counter = 1

		encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]

		#comienza la transmision
		print "Servidor activo y esperando clientes."

		while True:
				result, imgencode = cv2.imencode('.jpg', frame, encode_param)
				data =numpy.array(imgencode)
				stringData = data.tostring()
				#tcp primero
				for cliente_tcp in conexiones_tcp:
					try:
						cliente_tcp.send(str(len(stringData)).ljust(16));
						cliente_tcp.send( stringData );
					except socket.error:
						c = cliente_tcp.getpeername() #getsockname()
						print "El cliente TCP "+ str(c[0]) +" con puerto "+ str(c[1]) +" se ha desconectado."
						cliente_tcp.close()
						conexiones_tcp.remove(cliente_tcp)
				t_actual = time()
				for clave in conexiones_udp:
					if (t_actual - conexiones_udp[clave][0]) < 90:
						udp_servidor.sendto(stringData, conexiones_udp[clave][1] ) #lo enviamos
					else:
						d = conexiones_udp[clave][1] # datos del cliente para sacarlo del hash
						conexiones_borrar.append(d)
						
				#borramos aquellos que ya superaron los 90 segundos, por fuera del for de envio
				for borrar in conexiones_borrar:
					del conexiones_udp[str(borrar[0]) + ":" + str(borrar[1])]  #quitamos al cliente del hash "hace + de 90s que no sabemos nada de el"
					print "El cliente UDP "+ str(borrar[0]) + " con puerto " + str(borrar[1]) + " ha sido desconectado."
				del conexiones_borrar 
				conexiones_borrar = []

				if (cam):
					ret, frame = capture.read()
				else:
					if (frame_counter < cap.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)):
						ret, f = cap.read()
						frame_counter += 1
					else:
						frame_counter = 0
						cap.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, 0)
						ret, f = cap.read()
						frame_counter += 1
					frame = cv2.resize(f, ( 320, 240))
					sleep(0.07)

	except KeyboardInterrupt:
		#cierro todos los sockets tcp
		for cliente_tcp in conexiones_tcp:
			cliente_tcp.close()
			conexiones_tcp.remove(cliente_tcp)
		#detengo los hilos
		server_udp.stop()
		server_tcp.stop()
		#los cierro
		server_tcp.join()
		server_udp.join()
		#cierro el cv2
		cv2.destroyAllWindows() 
		print "Servicio finalizado."
		#salgo del programa
		sys.exit(1)



		