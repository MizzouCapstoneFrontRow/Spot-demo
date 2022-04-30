# ctypes_test.py
import ctypes
import pathlib
import io
from time import sleep
from typing import Callable
from enum import Enum

class _Handle(ctypes.Structure):
    pass

_ErrorCodeRaw = ctypes.c_int

class ErrorCode(Enum):
    # Success
    NoError = 0
    # An invalid handle was passed (and the error was detected)
    InvalidHandle = 1
    # An operation that requires a connected handle was called
    # with an unconencted handle.
    NotConnected = 2
    # An operation that requires an unconnected handle was called
    # with a conencted handle.
    AlreadyConnected = 3
    # A required parameter was null.
    NullParameter = 4
    # A string was not UTF8.
    NonUtf8String = 5
    # A parameter was invalid.
    InvalidParameter = 6
    # An error occurred reading a message
    MessageReadError = 7
    # The server sent an invalid message
    InvalidMessageReceived = 8
    # An error occurred writing a message
    MessageWriteError = 9
    # Tried to register a axis/function/sensor/stream with the same name as an
    # existing one of the same thing.
    DuplicateName = 10
    # The server disconnected.
    ServerDisconnected = 11
    # The operation is unsupported (e.g. streams on Windows).
    Unsupported = 12
    # The server rejected the connection.
    ConnectionRejected = 13
    # Failed to connect because a required value (e.g. name) was not set.
    MissingRequiredValue = 14
    # Error connecting to server.
    ConnectionError = 15
    # Other error (nonfatal) e.g. server sent a FunctionCall with invalid parameters
    # or a message that should never be sent to machine (e.g. AxisReturn)
    Other = 16


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

        # Python will garbage-collect and close files out from under us if we don't reference them somewhere *in python*
        # so keep all files referenced here
        self._files = []

        # bool SetName(ClientHandle *handle, const char *name);
        self._lib.SetName.restype = _ErrorCodeRaw
        self._lib.SetName.argtypes = [ctypes.POINTER(_Handle), ctypes.c_char_p]

        # bool SetReset(ClientHandle *handle, void(*reset)(void));
        self._lib.SetReset.restype = _ErrorCodeRaw
        self._lib.SetReset.argtypes = [ctypes.POINTER(_Handle), _RESET]

        # bool RegisterFunction(
        #   ClientHandle *handle,
        #   const char *name,
        #   const char (*parameters)[2],
        #   const char (*returns)[2],
        #   void(*callback)(const void *const *const, void *const *const)
        # );
        self._lib.RegisterFunction.restype = _ErrorCodeRaw
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
        self._lib.RegisterSensor.restype = _ErrorCodeRaw
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
        self._lib.RegisterAxis.restype = _ErrorCodeRaw
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
        self._lib.ConnectToServer.restype = _ErrorCodeRaw
        self._lib.ConnectToServer.argtypes = [
            ctypes.POINTER(_Handle),
            ctypes.c_char_p,
            ctypes.c_uint16,
            ctypes.c_uint16,
        ]

        # bool LibraryUpdate(ClientHandle *handle);
        self._lib.LibraryUpdate.restype = _ErrorCodeRaw
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
        if result != 0:
            raise RuntimeError("Error setting name", ErrorCode(result))

    def set_reset(self, reset: Callable[[], None]) -> None:
        if not self.handle:
            raise ValueError("Invalid client handle")
        reset = _RESET(reset)
        self._callbacks.append(reset)
        result = self._lib.SetReset(self.handle, reset)
        if result != 0:
            raise RuntimeError("Error setting reset handler", ErrorCode(result))

    # TODO: register_function

    def register_axis(self, name: str, min: float, max: float, group: str, direction: str, callback: Callable[[float], None]) -> None:
        if not self.handle:
            raise ValueError("Invalid client handle")
        callback = _AXIS(callback)
        self._callbacks.append(callback)
        result = self._lib.RegisterAxis(self.handle, name.encode(), min, max, group.encode(), direction.encode(), callback)
        if result != 0:
            raise RuntimeError("Error registering axis", ErrorCode(result))

    def register_sensor(self, name: str, min: float, max: float, callback: Callable[[], float]) -> None:
        if not self.handle:
            raise ValueError("Invalid client handle")
        def actual_callback(p: "ctypes.POINTER(ctypes.c_double)") -> None:
            p[0] = callback()
        actual_callback = _SENSOR(actual_callback)
        self._callbacks.append(actual_callback)
        result = self._lib.RegisterSensor(self.handle, name.encode(), min, max, actual_callback)
        if result != 0:
            raise RuntimeError("Error registering sensor", ErrorCode(result))

    def register_stream(self, name: str, format: str, file: io.IOBase) -> None:
        if not self.handle:
            raise ValueError("Invalid client handle")
        fd: int = file.fileno() # may raise OSError if not supported
        self._files.append(file)
        result = self._lib.RegisterStream(self.handle, name.encode(), format.encode(), fd)
        if result != 0:
            raise RuntimeError("Error registering stream", ErrorCode(result))

    def connect_to_server(self, address: str, port: int, stream_port: int) -> None:
        if not self.handle:
            raise ValueError("Invalid client handle")
        result = self._lib.ConnectToServer(self.handle, address.encode(), port, stream_port)
        if result != 0:
            raise RuntimeError("Error connecting to server", ErrorCode(result))

    def library_update(self) -> None:
        if not self.handle:
            raise ValueError("Invalid client handle")
        result = self._lib.LibraryUpdate(self.handle)
        if result != 0:
            raise RuntimeError("Error updating library", ErrorCode(result))

    def shutdown_library(self) -> None:
        if not self.handle:
            raise ValueError("Invalid client handle")
        self._lib.ShutdownLibrary(self.handle)
        self.handle = None

if __name__ == "__main__":
    import sys

    client = Client()

    print("setting name")
    client.set_name("example")

    print("setting reset callback")
    client.set_reset(lambda: print("Resetting!", flush=True))

    print("adding axis")
    client.register_axis("example", -1.0, 1.0, "example_group", "z", lambda x: print("axis:", x))

    print("adding stream")
    client.register_stream("stdin", "lol", sys.stdin)

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
    client.connect_to_server("localhost", 45575, 45577)

    while(True):
        sleep(1)
        print("updating")
        client.library_update()
