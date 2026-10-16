class Logger:
    _debug_mode = False
    _instance = None
    _logger_type = None
    _file_path = None
    _storage = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def set_logger_type(self, logger_type, file_path=None, storage=None):
        self._logger_type = logger_type
        if logger_type == "file" and file_path:
            self._file_path = file_path
        if logger_type == "storage" and storage:
            self._storage = storage

    def log(self, message):
        if self._logger_type == "print":
            print(message)
        elif self._logger_type == "file" and self._file_path:
            with open(self._file_path, "a", encoding="utf-8") as f:
                f.write(str(message) + "\n")
        elif self._logger_type == "storage" and self._storage:
            # Placeholder for storage logging, e.g., DB
            self._storage.write_record("log", {"message": str(message)})
        elif self._logger_type is None:
            pass  # Do not log anything

    def set_debug_mode(self, debug):
        self._debug_mode = bool(debug)

    def debug(self, message):
        if self._debug_mode:
            self.log(f"[DEBUG] {message}")

# Usage:
# logger = Logger()
# logger.set_logger_type("print")
# logger.log("Hello World")
