import ctypes
import pathlib

from matplotlib import cbook
from numpy import cdouble

# THIS IS JUST A WRAPPER CLASS FOR THE CLIENT LIBRARY
# FOR REAL DOCUMENTATION, PLEASE LOOK AT THE ACTUAL CLIENT LIBRARY HEADER

library_name = pathlib.Path().absolute() / "libclient.so"
c_lib = ctypes.CDLL(library_name)

class wrappyr:

    #InitializeLibrary Method wrapper
    def InitializeLibrary(self):
        c_lib.InitializeLibrary.restype = ctypes.c_void_p
        return c_lib.InitializeLibrary()

    def SetName(self, clientHandle, name): # return tipe is simply a boolean, 0 or 1
        c_lib.SetName.restype = ctypes.c_bool
        c_lib.SetName.argtypes = (ctypes.c_void_p, ctypes.c_char_p)
        return c_lib.SetName(clientHandle, str.encode(name))

    def SetReset(self, clientHandle, callback):
        c_lib.SetReset.restype = ctypes.c_bool
        return c_lib.SetReset(ctypes.c_void_p(clientHandle), callback)

    # TODO: wrap function
    def RegisterFunction(self, clientHandle, name, parameters, returns, callback):
        return 0
    
    # TODO: Wrap function
    def RegisterSensor(self, clientHandle, name, min, max, callback):
        return 0

    def RegisterAxis(self, clientHandle, name, min, max, group, direction, callback):
        c_lib.RegisterAxis.restype = ctypes.c_bool
        return c_lib.RegisterAxis(
            ctypes.c_void_p(clientHandle), 
            ctypes.c_char_p(str.encode(name)),
            ctypes.c_double(min),
            ctypes.c_double(max),
            ctypes.c_char_p(str.encode(group)),
            ctypes.c_char_p(str.encode(direction)),
            callback
        )

    # TODO: Wrap function
    def RegisterStream(self, clientHandle, name, format, address, port):
        return 0

    #TODO: WRAP Function
    def ConnectToServer(self, clientHandle, server, port):
        c_lib.ConnectToServer.restype = ctypes.c_bool
        # c_lib.ConnectToServer.argtypes 
        return c_lib.ConnectToServer(
            ctypes.c_void_p(clientHandle),
            ctypes.c_char_p(str.encode(server)),
            ctypes.c_uint16(port)
        )

    def LibraryUpdate(self, clientHandle):
        c_lib.LibraryUpdate.restype = ctypes.c_bool
        return c_lib.LibraryUpdate(ctypes.c_void_p(clientHandle))