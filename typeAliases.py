from connection import *

SentHandlerTypeSignature = Callable[[Optional[SendError]], None]
ReceiveHandlerTypeSignature = Callable[[Connection, Optional[bytes], MessageContext, bool, Optional[ReceiveError]], None]
