from typing import List

from connection import Connection, MessageDataObject
from framer import Framer
from message_context import MessageContext


class MessageFramer():

    def __init__(self, framer_implementation: Framer):
        self.framer_list: List[Framer] = [framer_implementation]
        pass

    def dispatch_handle_received_data(self, connection: Connection):
        self.framer_list[0].handle_received_data(connection)

    def fail_connection(self, connection, error):
        """
        Should the framer implementation deem the candidate selected during racing unsuitable it can signal this by
        failing the Connection prior to marking it as ready. If there are no other candidates available, the Connection
        will fail. Otherwise, the Connection will select a different candidate and the Message Framer will generate a new Start event.
        :param connection: The connection to fail
        :param error: An error specifying why the framer is failing the connection
        """
        pass

    def make_connection_ready(self):
        pass

    def prepend_framer(self, connection, other_framer):
        """

        Before an implementation marks a Message Framer as ready, it can also dynamically add a
        protocol or framer above it in the stack. This allows protocols like STARTTLS, that need
        to add TLS conditionally, to modify the Protocol Stack based on a handshake result.
        :param connection:
        :param other_framer:
        """
        pass

    def send(self, connection: Connection, data, message_context, sent_handler, is_end_of_message):
        # More logic here?
        connection.add_to_message_queue(message_context, data, sent_handler, is_end_of_message)

    def parse(self, connection: Connection, minimum_incomplete_length, maximum_length) -> (bytes, MessageContext, bool):
        framer_placeholder = connection.framer_placeholder
        bytes_available = len(framer_placeholder.inbound_data) - framer_placeholder.cursor
        if bytes_available < minimum_incomplete_length:
            return None
        else:
            if bytes_available < maximum_length:
                end = len(connection.framer_placeholder.inbound_data) - 1
            else:
                end = connection.framer_placeholder.cursor + maximum_length
            parsed_bytes = connection.framer_placeholder.inbound_data[connection.framer_placeholder.cursor:end]
            message_context = MessageContext()
            return parsed_bytes, message_context, True

    def advance_receive_cursor(self, connection, length):
        connection.framer_placeholder.advance(length)

    def deliver_and_advance_receive_cursor(self, connection, message_context, length, is_end_of_message):
        # Check if the whole message is received by the transport already
        length_current_buffer = len(connection.framer_placeholder)
        if length_current_buffer < length:
            connection.framer_placeholder.buffered_data = connection.framer_placeholder.inbound_data
            connection.framer_placeholder.earmarked_bytes_missing = length - length_current_buffer
            connection.framer_placeholder.saved_message_context = message_context
            connection.framer_placeholder.saved_is_end_of_message = is_end_of_message
            connection.framer_placeholder.inbound_data = []
        else:
            handler, min_length, max_length = connection.receive_request_queue.pop(0)
            data = connection.framer_placeholder.inbound_data[0:length] # length-1?
            connection.framer_placeholder.advance(length)
            message_data_object = MessageDataObject(data, len(data))
            handler(connection, message_data_object, message_context, is_end_of_message, None)

    def deliver(self, connection, message_context, data, is_end_of_message):
        handler, min_length, max_length = connection.receive_request_queue.pop(0)
        message_data_object = MessageDataObject(data, len(data))
        handler(connection, message_data_object, message_context, is_end_of_message, None)
