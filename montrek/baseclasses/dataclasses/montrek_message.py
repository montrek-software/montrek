from dataclasses import dataclass


@dataclass
class MontrekMessage:
    message: str
    message_type: str


@dataclass
class MontrekMessageError(MontrekMessage):
    message_type: str = "error"


@dataclass
class MontrekMessageInfo(MontrekMessage):
    message_type: str = "info"


@dataclass
class MontrekMessageWarning(MontrekMessage):
    message_type: str = "warning"
