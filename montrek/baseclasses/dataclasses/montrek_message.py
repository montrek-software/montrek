from dataclasses import dataclass

@dataclass
class MontrekMessage:
    message: str

@dataclass
class MontrekMessageError(MontrekMessage):
    message_type: str = 'error'

@dataclass
class MontrekMessageInfo(MontrekMessage):
    message_type: str = 'info'
