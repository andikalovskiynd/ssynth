import os
import inspect

class Log:
    RESET = "\033[0m"
    RED   = "\033[31m"
    GREEN = "\033[32m"
    YELLOW= "\033[33m"
    BLUE  = "\033[34m"
    GRAY  = "\033[90m"

    @staticmethod
    def _caller():
        frame = inspect.stack()[2]
        filename = os.path.basename(frame.filename)
        line = frame.lineno
        return f"{filename}:{line}"

    @staticmethod
    def ok(msg):
        loc = Log._caller()
        print(f"{Log.GREEN}[ SUCCESS ]{Log.RESET} {loc} - {msg}")

    @staticmethod
    def warn(msg):
        loc = Log._caller()
        print(f"{Log.YELLOW}[ WARNING ]{Log.RESET} {loc} - {msg}")

    @staticmethod
    def err(msg):
        loc = Log._caller()
        print(f"{Log.RED}[ ERROR ]{Log.RESET} {loc} - {msg}")

    @staticmethod
    def dbg(msg):
        loc = Log._caller()
        print(f"{Log.GRAY}[ DEBUG ]{Log.RESET} {loc} - {msg} {Log.RESET}")