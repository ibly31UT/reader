#!flask/bin/python
from app import app
from threading import Thread
import time, sys

"""class SystemThread(Thread):
	def __init__(self):
		Thread.__init__(self)

	def run(self):
		time.sleep(1)
		while True:
			try:
				time.sleep(1)
				print "Step..."
			except KeyboardInterrupt:
				print "Exiting..."
				exit()
				break"""

class ServerThread(Thread):
	def __init__(self):
		Thread.__init__(self)

	def run(self):
		app.run(threaded=True, debug=True)

if __name__ == "__main__":
	app.run(threaded=False, debug=True)
	#SystemThread().start()	