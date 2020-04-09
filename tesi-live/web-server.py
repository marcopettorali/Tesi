#!/usr/bin/python

from http.server import BaseHTTPRequestHandler, HTTPServer
import socketserver
import os
from os import curdir, sep
import cgi
import numpy
import cv2
import sys
sys.path.insert(0, "../../ncapi2_shim")
import mvnc_simple_api as mvnc

PORT_NUMBER = 8080

graph = ' '
camera = ' '
dim=(300,300)

#Etichette riconosciute dal sistema (tradotte in italiano):
LABELS = ('sfondo',
          'aereoplano', 'bicicletta', 'uccello', 'barca',
          'bottiglia', 'autobus', 'automobile', 'gatto', 'sedia',
          'mucca', 'tavolo, scrivania', 'cane', 'cavallo',
          'motocicletta', 'persona', 'pianta',
          'pecora', 'divano, poltrona', 'treno', 'schermo')
		  
def run_inference(image_to_classify, ssd_mobilenet_graph):

    resized_image = preprocess_image(image_to_classify)
    ssd_mobilenet_graph.LoadTensor(resized_image.astype(numpy.float16), None)

    output, userobj = ssd_mobilenet_graph.GetResult()
    num_valid_boxes = int(output[0])
    print('Numero di oggetti riconosciuti: ' + str(num_valid_boxes))
    ret_str = ' '
    for box_index in range(num_valid_boxes):
            base_index = 7+ box_index * 7
            if (not numpy.isfinite(output[base_index]) or
                    not numpy.isfinite(output[base_index + 1]) or
                    not numpy.isfinite(output[base_index + 2]) or
                    not numpy.isfinite(output[base_index + 3]) or
                    not numpy.isfinite(output[base_index + 4]) or
                    not numpy.isfinite(output[base_index + 5]) or
                    not numpy.isfinite(output[base_index + 6])):
                print('il box all\'indice: ' + str(box_index) + ' ha dati di output non definiti, ignoro')
                continue

            x1 = max(0, int(output[base_index + 3] * image_to_classify.shape[0]))
            y1 = max(0, int(output[base_index + 4] * image_to_classify.shape[1]))
            x2 = min(image_to_classify.shape[0], int(output[base_index + 5] * image_to_classify.shape[0]))
            y2 = min(image_to_classify.shape[1], int(output[base_index + 6] * image_to_classify.shape[1]))

            x1_ = str(x1)
            y1_ = str(y1)
            x2_ = str(x2)
            y2_ = str(y2)

            ret_str = ret_str + ('Oggetto n.' + str(box_index) + ' : ' + LABELS[int(output[base_index + 1])] + '<br>'
			         'Confidence: ' + str(output[base_index + 2]*100) + '%<br>' +
				 'Angolo in alto a sx: (' + x1_ + ', ' + y1_ + ')  Angolo in basso a dx: (' + x2_ + ', ' + y2_ + ')<br><br>')
    return ret_str

            

def preprocess_image(src):

    NETWORK_WIDTH = 300
    NETWORK_HEIGHT = 300
    img = cv2.resize(src, (NETWORK_WIDTH, NETWORK_HEIGHT))

    img = img - 127.5
    img = img * 0.007843
    return img


class myHandler(BaseHTTPRequestHandler):
	
	def do_GET(self):
		if self.path=="/":
			self.path="/image-classifier.html"

		try:
			sendReply = False
			if self.path.endswith(".html"):
				mimetype='text/html'
				sendReply = True
			if self.path.endswith(".jpg"):
				mimetype='image/jpg'
				sendReply = True
				f = open(curdir + sep + self.path, 'rb') 
				self.send_response(200)
				self.send_header('Content-type',mimetype)
				self.end_headers()
				self.wfile.write(f.read())
				f.close()
				return
			if self.path.endswith(".css"):
				mimetype='text/css'
				sendReply = True
			
			if "/get-image" in self.path:
				
				img_ret, image = camera.read()
				cv2.imwrite('frame.jpg', image)
				infer_image = image
				
				f = '''<!DOCTYPE html>
					<html lang="en">
					  <head>
						<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
						<title>Live Image Classifier</title>
						<meta name="author" content="Marco Pettorali">
					  </head>
					  <body>
						<h1>Live Image Classifier</h1>
						<img src="frame.jpg">
						<p>{}</p>
						</body>
					</html>
				'''.format(run_inference(infer_image, graph))

				self.send_response(200)
				self.send_header('Content-type', 'text/html')
				self.end_headers()
				self.wfile.write(bytes(f, 'utf-8'))
				return
			if sendReply == True:
				f = open(curdir + sep + self.path) 
				self.send_response(200)
				self.send_header('Content-type',mimetype)
				self.end_headers()
				self.wfile.write(bytes(f.read(), "utf-8"))
				f.close()
			return
		except IOError:
			self.send_error(404,'File Not Found: %s' % self.path)	
			
try:
	server = HTTPServer(("", PORT_NUMBER), myHandler)
	print ('Started httpserver')
	devices = mvnc.EnumerateDevices()
	#apro lo stick Movidius una volta sola all'avvio del servizio
	if len(devices) == 0:
        	print('No devices found')
        	quit()
	device = mvnc.Device(devices[0])
	device.OpenDevice()
	with open('graph', mode='rb') as f:
		graph_in_memory = f.read()
		graph = device.AllocateGraph(graph_in_memory)
	camera = cv2.VideoCapture(0)
	server.serve_forever()
except KeyboardInterrupt:
	print ('Chiudo il servizio')
	server.socket.close()
	#chiudo lo stick Movidius quando tutte le elaborazioni sono terminate
	graph.DeallocateGraph()
	device.CloseDevice()
	del(camera)
