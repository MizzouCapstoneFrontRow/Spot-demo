# ctypes_test.py
import ctypes
import pathlib
from time import sleep

from numpy import cdouble


# void example_axis(const double value) {
#     printf("Axis got %lf.\n", value);
# }

AXIS = ctypes.CFUNCTYPE(None, ctypes.c_double)

def axis (x):
    print(x)

axisdef = AXIS(axis)


if __name__ == "__main__":
    # Load the shared library into ctypes
    libname = pathlib.Path().absolute() / "libclient.so"
    c_lib = ctypes.CDLL(libname)

    # x, y = 6, 2.3
    # c_lib.cmult.restype = ctypes.c_float
    # asn = c_lib.cmult(x,ctypes.c_float(y))
    # print(asn)
    c_lib.InitializeLibrary.restype = ctypes.c_void_p

    handle = c_lib.InitializeLibrary()
    # print(handle)

    success = False
    print("setting name")
    success = c_lib.SetName(ctypes.c_void_p(handle), ctypes.c_char_p(str.encode("Example")))
    print(success)

    print("adding axis")
    success = c_lib.RegisterAxis(ctypes.c_void_p(handle), ctypes.c_char_p(str.encode("example")), ctypes.c_double(-1.0), ctypes.c_double(1.0), ctypes.c_char_p(str.encode("example_group")), ctypes.c_char_p(str.encode("z")), axisdef);
    print(success)


    server = "localhost"
    ser_converted = ctypes.c_char_p(str.encode(server))


    print("connecting");
    success = c_lib.ConnectToServer(ctypes.c_void_p(handle), ser_converted, ctypes.c_uint16(45575))
    print(success)

    while(True):
        sleep(10)
        print("updating")
        success = c_lib.LibraryUpdate(ctypes.c_void_p(handle))

        print(success)
