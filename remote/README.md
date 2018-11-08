Remote services
===================================

The beaglebone will connect as server to two clients via USB using the Zero4U hub.
ZMQ in combination with SSH will be used. <br>

  * Laser spot client; <br>
      Raspberry PI zero camera with no lens and neutral density filter
      Determines laser spot size from image <br>
      laserspot_client.py
  * PCB detection client; <br>
      Raspberry Pi zero camera with refocussed stock lens and light
      Calculates PCB position <br>
      not implemented
   