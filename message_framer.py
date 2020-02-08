from message_context import MessageContext


class MessageFramer():

    def __init__(self, framer_implementation):
        self.framer_implementation = framer_implementation
        pass

    def fail_connection(self, connection, error):
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

    def send(self, connection, data):
        pass

    def parse(self, connection, minimum_incomplete_length, maximum_length) -> (bytes, MessageContext, bool):
        pass

    def advance_receive_cursor(self, connection, length):
        pass

    def deliver_and_advance_receive_cursor(self, connection, message_context, length, is_end_of_message):
        pass

    def deliver(self, connection, message_context, data, is_end_of_message):
        pass
