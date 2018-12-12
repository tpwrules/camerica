# this file contains information on the supported cameras
from camerica_hw import CameraType

# base class
class Camera:
    # default attributes are empty
    # fill them in in a subclass!
    name = None
    
    width = None # pixels
    height = None # pixels
    fps = None # frames per second
    
    hw_type = CameraType.NONE
    
class MerlinCamera(Camera):
    name = "merlin"
    
    width = 320
    height = 256
    fps = 60
    
    hw_type = CameraType.MERLIN
    
class Photon640Camera(Camera):
    name = "photon640"
    
    width = 640
    height = 512
    fps = 30
    
    hw_type = CameraType.PHOTON_640