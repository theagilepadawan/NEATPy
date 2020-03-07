from abc import ABC, abstractmethod
from utils import shim_print


class Framer(ABC):

    def __init__(self):
        self.connection_list = []

    @abstractmethod
    def start(self, connection):
        """When a Message Framer generates a Start event, the framer implementation has the opportunity to start writing
        some data prior to the Connection delivering its Ready event. This allows the implementation to communicate
        control data to the remote endpoint that can be used to parse Messages.

        :param connection:
        """
        pass

    @abstractmethod
    def stop(self, connection):
        pass

    @abstractmethod
    def new_sent_message(self, connection, message_data, message_context, sent_handler, is_end_of_message):
        """Upon receiving this event, a framer implementation is responsible for performing any necessary
        transformations and sending the resulting data back to the Message Framer, which will in turn send
        it to the next protocol.

        :param connection:
        :param message_data:
        :param message_context:
        :param is_end_of_message:
        :param sent_handler:
        """
        pass

    @abstractmethod
    def handle_received_data(self, connection):
        """Upon receiving this event, the framer implementation can inspect the inbound data. The data is parsed from
        a particular cursor representing the unprocessed data. The application requests a specific amount of data it
        needs to have available in order to parse. If the data is not available, the parse fails.

        :param connection:
        """
        pass


class TestFramer(Framer):

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


