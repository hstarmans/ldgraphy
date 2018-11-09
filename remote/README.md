Remote services
===================================

The Beaglebone will connect as server to a client via USB.
ZMQ in combination with SSH will be used. <br>

  * Laser spot client; <br>
      Raspberry PI zero camera with no lens and neutral density filter
      Determines laser spot size from direct illumanation. At the moment, a laptop with
      uEye camera is used as it was readily available. <br>
      laserspot_client.py