# ctypes_test.py
import ctypes
import pathlib
from time import sleep
from typing import Callable

class _Handle(ctypes.Structure):
    pass

_RESET = ctypes.CFUNCTYPE(None)
_AXIS = ctypes.CFUNCTYPE(None, ctypes.c_double)
_SENSOR = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_double))
_FUNCTION = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p))

class Client:
    libname = pathlib.Path().absolute() / "libclient.so"

    @classmethod
    def set_libname(cls, libname: str) -> None:
        cls.libname = libname

    def __init__(self):
        self._lib = ctypes.CDLL(type(self).libname)

        self._lib.InitializeLibrary.restype = ctypes.POINTER(_Handle)

        self.handle = self._lib.InitializeLibrary()

        if not self.handle:
            raise RuntimeError("Could not initialize client library")

        # Python will garbage-collect callbacks out from under us if we don't reference them somewhere *in python*
        # so keep all callbacks referenced here
        self._callbacks = []

        # bool SetName(ClientHandle *handle, const char *name);
        self._lib.SetName.restype = ctypes.c_bool
        self._lib.SetName.argtypes = [ctypes.POINTER(_Handle), ctypes.c_char_p]

        # bool SetReset(ClientHandle *handle, void(*reset)(void));
        self._lib.SetReset.restype = ctypes.c_bool
        self._lib.SetReset.argtypes = [ctypes.POINTER(_Handle), _RESET]

        # bool RegisterFunction(
        #   ClientHandle *handle,
        #   const char *name,
        #   const char (*parameters)[2],
        #   const char (*returns)[2],
        #   void(*callback)(const void *const *const, void *const *const)
        # );
        self._lib.RegisterFunction.restype = ctypes.c_bool
        self._lib.RegisterFunction.argtypes = [
            ctypes.POINTER(_Handle),
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_char_p * 2),
            ctypes.POINTER(ctypes.c_char_p * 2),
            _FUNCTION,
        ]

        # bool RegisterSensor(
        #   ClientHandle *handle,
        #   const char *name,
        #   double min,
        #   double max,
        #   void(*callback)(double *const)
        # );
        self._lib.RegisterSensor.restype = ctypes.c_bool
        self._lib.RegisterSensor.argtypes = [
            ctypes.POINTER(_Handle),
            ctypes.c_char_p,
            ctypes.c_double,
            ctypes.c_double,
            _SENSOR,
        ]

        # bool RegisterAxis(
        #   ClientHandle *handle,
        #   const char *name,
        #   double min,
        #   double max,
        #   const char *group,
        #   const char *direction,
        #   void(*callback)(const double)
        # );
        self._lib.RegisterAxis.restype = ctypes.c_bool
        self._lib.RegisterAxis.argtypes = [
            ctypes.POINTER(_Handle),
            ctypes.c_char_p,
            ctypes.c_double,
            ctypes.c_double,
            ctypes.c_char_p,
            ctypes.c_char_p,
            _AXIS,
        ]

        # RegisterStream: TODO (API still being modified)

        # bool ConnectToServer(
        #   ClientHandle *handle,
        #   const char *server,
        #   uint16_t port
        # );
        self._lib.ConnectToServer.restype = ctypes.c_bool
        self._lib.ConnectToServer.argtypes = [
            ctypes.POINTER(_Handle),
            ctypes.c_char_p,
            ctypes.c_uint16,
        ]

        # bool LibraryUpdate(ClientHandle *handle);
        self._lib.LibraryUpdate.restype = ctypes.c_bool
        self._lib.LibraryUpdate.argtypes = [
            ctypes.POINTER(_Handle),
        ]

        # void ShutdownLibrary(ClientHandle *handle);
        self._lib.ShutdownLibrary.restype = None
        self._lib.ShutdownLibrary.argtypes = [
            ctypes.POINTER(_Handle),
        ]
    # end def __init__

    def set_name(self, name: str) -> None:
        if not self.handle:
            raise ValueError("Invalid client handle")
        result = self._lib.SetName(self.handle, name.encode())
        if not result:
            raise RuntimeError("Error setting name")

    def set_reset(self, reset: Callable[[], None]) -> None:
        if not self.handle:
            raise ValueError("Invalid client handle")
        reset = _RESET(reset)
        self._callbacks.append(reset)
        result = self._lib.SetReset(self.handle, reset)
        if not result:
            raise RuntimeError("Error setting reset handler")

    # TODO: register_function

    def register_axis(self, name: str, min: float, max: float, group: str, direction: str, callback: Callable[[float], None]) -> None:
        if not self.handle:
            raise ValueError("Invalid client handle")
        callback = _AXIS(callback)
        self._callbacks.append(callback)
        result = self._lib.RegisterAxis(self.handle, name.encode(), min, max, group.encode(), direction.encode(), callback)
        if not result:
            raise RuntimeError("Error registering axis")

    def register_sensor(self, name: str, min: float, max: float, callback: Callable[[], float]) -> None:
        if not self.handle:
            raise ValueError("Invalid client handle")
        def actual_callback(p: "ctypes.POINTER(ctypes.c_double)") -> None:
            p[0] = callback()
        actual_callback = _SENSOR(actual_callback)
        self._callbacks.append(actual_callback)
        result = self._lib.RegisterSensor(self.handle, name.encode(), min, max, actual_callback)
        if not result:
            raise RuntimeError("Error registering sensor")

    # TODO: register_stream

    def connect_to_server(self, address: str, port: int) -> None:
        if not self.handle:
            raise ValueError("Invalid client handle")
        result = self._lib.ConnectToServer(self.handle, address.encode(), port)
        if not result:
            raise RuntimeError("Error connecting to server")

    def library_update(self) -> None:
        if not self.handle:
            raise ValueError("Invalid client handle")
        result = self._lib.LibraryUpdate(self.handle)
        if not result:
            raise RuntimeError("Error updating library")

    def shutdown_library(self) -> None:
        if not self.handle:
            raise ValueError("Invalid client handle")
        self._lib.ShutdownLibrary(self.handle)
        self.handle = None

if __name__ == "__main__":

    client = Client()

    print("setting name")
    client.set_name("example")

    print("setting reset callback")
    client.set_reset(lambda: print("Resetting!", flush=True))

    print("adding axis")
    client.register_axis("example", -1.0, 1.0, "example_group", "z", lambda x: print("axis:", x))

    x = 0.0
    def count() -> float:
        global x
        print(f"x = {x}")
        x += 1.0
        print(f"x+1 = {x}")
        return x

    print("adding sensor")
    client.register_sensor("count", -1.0, 1.0, count)

    print("connecting");
    client.connect_to_server("localhost", 45575)

    while(True):
        sleep(1)
        print("updating")
        client.library_update()
