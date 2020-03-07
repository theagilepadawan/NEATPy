from typing import List

import connection as con
from framer import Framer
from message_context import MessageContext


class MessageFramer:

    def __init__(self, framer_implementation: Framer):
        self.framer_list: List[Framer] = [framer_implementation]
        self.ongoing_transformations = {}

    def dispatch_handle_received_data(self, connection):
        self.framer_list[0].handle_received_data(connection)

    def dispatch_new_sent_message(self, connection, message_data, message_context, sent_handler, is_end_of_message):
        number_of_framers = len(self.framer_list)
        self.ongoing_transformations[message_context] = number_of_framers - 2
        self.framer_list[number_of_framers - 1].new_sent_message(connection, message_data, message_context, sent_handler, is_end_of_message)

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

    def append_framer(self, new_framer):
        self.framer_list.append(new_framer)

    def prepend_framer(self, connection, other_framer):
        """

        Before an implementation marks a Message Framer as ready, it can also dynamically add a
        protocol or framer above it in the stack. This allows protocols like STARTTLS, that need
        to add TLS conditionally, to modify the Protocol Stack based on a handshake result.
        :param connection:
        :param other_framer:
        """
        pass

    def send(self, connection, message_data, message_context, sent_handler, is_end_of_message: bool):
        """This function is used by framer implementations, sending transformed data back to the
        message framer. The message framer will send the data to the next protocol (which, could be
        additional framers, or the transport protocol backing the connection)

        :param connection: The connection in which send() was called in the first place.
        :param message_data: The transformed data
        :param message_context: The message context passed by the application with the data
        :param sent_handler: A handler / function passed by the application with the send() call.
        :param is_end_of_message: A boolean value used with partial sends, indicating if this is the final part of the partial message
        """
        # Get the next framer index
        next_framer = self.ongoing_transformations[message_context]

        # If a valid index (i.e a value >= 0), send the transformed data to the next framer
        if next_framer >= 0:
            self.ongoing_transformations[message_context] = next_framer - 1
            self.framer_list[next_framer].new_sent_message(connection, message_data, message_context, sent_handler, is_end_of_message)

        # If this was the last framer, add the message to the connection message queue, to be dispatch further down the stack with NEAT
        else:
            connection.add_to_message_queue(message_context, message_data, sent_handler, is_end_of_message)

    def parse(self, connection, minimum_incomplete_length, maximum_length) -> (bytes, MessageContext, bool):
        framer_placeholder = connection.framer_placeholder
        bytes_available = len(framer_placeholder.inbound_data) - framer_placeholder.cursor
        if bytes_available < minimum_incomplete_length:
            return None, None, None
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
        length_current_buffer = len(connection.framer_placeholder.inbound_data)
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
            message_data_object = con.MessageDataObject(data, len(data))
            handler(connection, message_data_object, message_context, is_end_of_message, None)

    def deliver(self, connection, message_context, data, is_end_of_message):
        handler, min_length, max_length = connection.receive_request_queue.pop(0)
        message_data_object = con.MessageDataObject(data, len(data))
        handler(connection, message_data_object, message_context, is_end_of_message, None)
