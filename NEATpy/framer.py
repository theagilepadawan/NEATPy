from abc import ABC, abstractmethod
from utils import shim_print
from typing import Callable



class Framer(ABC):

    def __init__(self):
        self.connection_list = []

    @abstractmethod
    def start(self, connection):
        """When a Message Framer generates a Start event, the framer implementation has the opportunity to start writing
        some data prior to the Connection delivering its Ready event. This allows the implementation to communicate
        control data to the remote endpoint that can be used to parse Messages.

        :param connection: The connection that the framer is registered with.
        """
        pass

    @abstractmethod
    def stop(self, connection):
        pass

    @abstractmethod
    def new_sent_message(self, connection, message_data: bytearray, message_context, sent_handler: Callable[['Connection', 'SendErrorReason'], None], is_end_of_message: bool):
        """Upon receiving this event, a framer implementation is responsible for performing any necessary
        transformations and sending the resulting data back to the Message Framer, which will in turn send
        it to the next protocol.

        :param connection:The connection the framer is registered with.
        :param message_data: The data to send.
        :param message_context: Additional :py:class:`message_properties` can be sent by adding them to a Message Context object `Optinoal`.
        :param sent_handler: A function that is called after completion / error.
        :param end_of_message: When set to false indicates a partial send.
        """
        pass

    @abstractmethod
    def handle_received_data(self, connection):
        """Upon receiving this event, the framer implementation can inspect the inbound data. The data is parsed from
        a particular cursor representing the unprocessed data. The application requests a specific amount of data it
        needs to have available in order to parse. If the data is not available, the parse fails.

        :param connection: The connection the framer is registered with.
        """
        pass


class ExampleFramer(Framer):
    """To provide an example this class implements the abstract interface in :py:class:`framer` class. It's a simple TLV framer
    that frame TCP messages by prepending message size. This is then parsed by the same framer at the destination.

    To use the framer, simply create an instace, and pass it to a :py:class:`preconnection` like so::

        new_preconnection = Preconnection(remote_endpoint=ep)
        preconnection.add_framer(framer.ExampleFramer())
    """

    def start(self, connection):
        pass

    def stop(self, connection):
        pass

    def new_sent_message(self, connection, message_data, message_context, sent_handler, is_end_of_message):
        """
        To provide an example, a simple protocol that adds a length as a header would receive the NewSentMessage event,
        create a data representation of the length of the Message data, and then send a block of data that is the
        concatenation of the length header and the original Message data.
        """
        shim_print(f"Framer got message: {message_data}")
        new_block = (len(message_data)).to_bytes(4, byteorder='big') + message_data
        connection.message_framer.send(connection, new_block, message_context, sent_handler, is_end_of_message)

    def handle_received_data(self, connection):
        """
        To provide an example, a simple protocol that parses a length as a header value would receive the
        HandleReceivedData event, and call Parse with a minimum and maximum set to the length of the header field.
        Once the parse succeeded, it would call AdvanceReceiveCursor with the length of the header field, and then call
        DeliverAndAdvanceReceiveCursor with the length of the body that was parsed from the header, marking the new Message as complete.
        """
        shim_print("Framer handles received data")
        header, context, is_end = connection.message_framer.parse(connection, 4, 4)
        length = int.from_bytes(header, byteorder='big')
        shim_print(f"Header is {length}")
        connection.message_framer.advance_receive_cursor(connection, 4)
        connection.message_framer.deliver_and_advance_receive_cursor(connection, context, length, True)

class SecondFramer(Framer):

    def start(self, connection):
        pass

    def stop(self, connection):
        pass

    def new_sent_message(self, connection, message_data, message_context, sent_handler, is_end_of_message):
        """
        To provide an example, a simple protocol that adds a length as a header would receive the NewSentMessage event,
        create a data representation of the length of the Message data, and then send a block of data that is the
        concatenation of the length header and the original Message data.
        """
        shim_print(f"Framer got message: {message_data}")
        new_block = "😘".encode() + message_data
        connection.message_framer.send(connection, new_block, message_context, sent_handler, is_end_of_message)

    def handle_received_data(self, connection):
        pass


