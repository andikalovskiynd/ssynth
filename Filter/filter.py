import numpy as np
import ctypes

class Filter:
    def __init__(self, filter_type='lpf'):
        if filter_type not in ['lpf', 'hpf']:
            raise ValueError("Unknown filter type")
        
        self.filter_type = filter_type
        self.lib = ctypes.CDLL('./Filter/Compiled/libfilter.so')
        self.prev_y = np.array([0.0], dtype=np.float32)

        if filter_type == 'lpf':
            self.func = self.lib.process_lpf
        
        elif filter_type == 'hpf':
            self.func = self.lib.process_hpf

        self.func.argtypes = [
            ctypes.POINTER(ctypes.c_float),     # x
            ctypes.POINTER(ctypes.c_float),     # y
            ctypes.c_int,                       # N
            ctypes.c_float,                     # alpha 
            ctypes.POINTER(ctypes.c_float)      # prev_y
        ]
        self.func.restype = None

    def process(self, x, alpha=None):
        x = np.array(x, dtype=np.float32)
        y = np.zeros_like(x)

        if alpha is None:
            alpha = 0.01
        
        self.func(
            x.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            y.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            x.size,
            alpha,  # Pass alpha as value, not pointer
            self.prev_y.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        )

        return y