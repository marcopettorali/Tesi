cd ~

#installare pacchetti base
sudo apt-get update
sudo apt-get install git
sudo apt-get install python3-pip

#ingrandire file di swap
echo CONF_SWAPSIZE=1024 > dphys-swapfile-enlarged
sudo mv /etc/dphys-swapfile /etc/dphys-swapfile-original
sudo mv dphys-swapfile-enlarged /etc/dphys-swapfile
sudo /etc/init.d/dphys-swapfile restart

#installare Neural Compute SDK v.2
sudo git clone -b ncsdk2 https://github.com/movidius/ncsdk.git
cd ncsdk
sudo make install

#verificare riuscita dell'installazione con programma d'esempio
cd examples/apps/hello_ncs_py
make run

#installare opencv
cd ~/ncsdk
./install-opencv.sh

#installare dipendenze mancanti dall'installazione di opencv
pip3 install opencv-python
sudo apt-get install libgstreamer1.0-0
sudo apt-get install libqtgui4
sudo apt-get install libqt4-test
pip3 install -U numpy==1.15.4

#ripristino file di swap
sudo mv /etc/dphys-swapfile /etc/dphys-swapfile-enlarged
sudo mv /etc/dphys-swapfile-original /etc/dphys-swapfile
sudo /etc/init.d/dphys-swapfile restart

#creazione dello workspace
cd ~
mkdir -p workspace
cd workspace

#installare ncappzoo
git clone -b ncsdk2 https://github.com/movidius/ncappzoo.git
cd ncappzoo
make all
    
#installare NCS-Pi-Stream
cd ~/workspace/ncappzoo/apps/
git clone https://github.com/HanYangZhao/NCS-Pi-Stream.git
cd NCS-Pi-Stream/models
mvNCCompile MobileNetSSD_deploy.prototxt -s 12 -w MobileNetSSD_deploy.caffemodel
mv graph ../graph/mobilenetgraph

#installare SSD_MobileNet
cd ~/workspace/ncappzoo/caffe/SSD_MobileNet
make run