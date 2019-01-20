A Readme for Asus Tinker Board Implementation

	setps to install GPIO:
		1.sudo apt-get update
		2.sudo apt-get install python-dev python3-dev
		3.cd gpio_source/gpio_lib_python/
		4.sudo python setup.py install
		5.sudo python3 setup.py install 
	   Note: Reference codes
		There're few sample codes under this folder /gpio_lib_python/test
	steps to install numpy and scypi
		1.sudo apt install python-numpy python-scipy
		
		--> for python 3
		1.sudo apt install python3-numpy python3-scipy	

	GPIO user

	--import ASUS.GPIO as GPIO	

	Opencv Install 
	-- sudo apt-get install python-opencv

	Run vlc as root:
		sudo sed -i 's/geteuid/getppid/' /usr/bin/vlc

	CV2 version required
		import cv2
 		cv2.__version__
		'2.4.9.1'
