from typing import List

from connection import Connection
from framer import Framer
from message_context import MessageContext


class MessageFramer():

    def __init__(self, framer_implementation: Framer):
        self.framer_list: List[Framer] = [framer_implementation]
        pass

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

    def parse(self, connection, minimum_incomplete_length, maximum_length) -> (bytes, MessageContext, bool):
        pass

    def advance_receive_cursor(self, connection, length):
        pass

    def deliver_and_advance_receive_cursor(self, connection, message_context, length, is_end_of_message):
        pass

    def deliver(self, connection, message_context, data, is_end_of_message):
        pass
