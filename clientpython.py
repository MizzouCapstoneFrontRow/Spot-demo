# ctypes_test.py
import ctypes
import pathlib
from time import sleep

from numpy import cdouble
import clientlibrarywrappyr


# void example_axis(const double value) {
#     printf("Axis got %lf.\n", value);
# }

AXIS = ctypes.CFUNCTYPE(None, ctypes.c_double)

def axis (x):
    print(x)

axisdef = AXIS(axis)

if __name__ == "__main__":
    # Load the shared library into ctypes

    client = clientlibrarywrappyr.wrappyr()
    handle = client.InitializeLibrary()

    success = client.SetName(handle, "example")
    print(success)

    success = client.RegisterAxis(handle, "example", -1.0, 1.0, "example_group", "z", axisdef)
    print(success)

    print("connecting")
    success = client.ConnectToServer(handle, "localhost", 45575)


    while(True):
        sleep(2)
        print("updating")
        success = client.LibraryUpdate(handle)
        print(success)
        if(success == False):
            break
# 

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
