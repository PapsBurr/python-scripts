import customtkinter as ctk
import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

class ClampedIntVar(ctk.IntVar):
    def __init__(self, master=None, value=0, min_val=1, max_val=10):
        self.min_val = min_val
        self.max_val=  max_val
        super().__init__(master, value=value)
        self.trace_add("write", self._clamp_value)

    def _clamp_value(self, *args):
        try:
            val = self.get()
            clamped = max(self.min_val, min(val, self.max_val))
            if val != clamped:
                self.set(clamped)
        except (ValueError, TypeError):
            self.set(self.min_val)