from typing import Callable, Optional

from connection import Connection, ReceiveError, SendError
from message_context import MessageContext

SentHandlerTypeSignature = Callable[[Optional[SendError]], None]
ReceiveHandlerTypeSignature = Callable[[Connection, Optional[bytes], MessageContext, bool, Optional[ReceiveError]], None]
