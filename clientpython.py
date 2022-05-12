# ctypes_test.py
import ctypes
import pathlib
from time import sleep

from numpy import cdouble
import client


# AXIS = ctypes.CFUNCTYPE(None, ctypes.c_double)

def axis (x):
    print(x)

# axisdef = AXIS(axis)

if __name__ == "__main__":
    
    client = client.Client()

    print("Setting name")
    client.set_name("spot-demo")

    print("Setting reset callback")
    client.set_reset(lambda: print("Resetting!", flush=True))

    print("adding axis")
    client.register_axis("rotate", -1.0, 1.0, "example_group", "z", axis)

    print("connecting")
    client.connect_to_server("172.31.0.1", 45575)
    while(True):
        sleep(1)
        print("updating")
        client.library_update()

#     libname = pathlib.Path().absolute() / "libclient.so"
#     c_lib = ctypes.CDLL(libname)

#     # x, y = 6, 2.3
#     # c_lib.cmult.restype = ctypes.c_float
#     # asn = c_lib.cmult(x,ctypes.c_float(y))
#     # print(asn)
#     c_lib.InitializeLibrary.restype = ctypes.c_void_p
#     c_lib.SetName.argtypes = (ctypes.c_void_p, ctypes.c_char_p)

#     handle = c_lib.InitializeLibrary()
#     # print(handle)

#     success = False
#     print("setting name")
#     success = c_lib.SetName(handle, str.encode("example"))
#     print(success)

    # print("adding axis")
    # success = .c_char_p(str.encode("example_group")), ctypes.c_char_p(str.encode("z")), axisdef);
    # print(success)


    # server = "localhost"
#     ser_converted = ctypes.c_char_p(str.encode(server))

#     print("connecting");
    # success = c_lib.ConnectToServer(ctypes.c_void_p(handle), ser_converted, ctypes.c_uint16(45575))
#     print(success)
