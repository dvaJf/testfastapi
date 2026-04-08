from fastapi import HTTPException

class RaceNotFoundException(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="Race not found")

class AlreadyRegisteredException(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="Already registered")

class NotRegisteredException(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="Not registered")

class RaceFullException(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="Race is full")

class RegistrationClosedException(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="Registration closed")

class ResutException(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="Resut Exception")