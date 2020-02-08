from abc import ABC, abstractmethod
from message_framer import *


class Framer(ABC):

    def __init__(self):
        self.connection_list = []

    @abstractmethod
    def start(self, connection):
        """

        When a Message Framer generates a Start event, the framer implementation has the opportunity to start writing
        some data prior to the Connection delivering its Ready event. This allows the implementation to communicate
        control data to the remote endpoint that can be used to parse Messages.
        """
        pass

    @abstractmethod
    def stop(self, connection):
        pass

    @abstractmethod
    def new_sent_message(self, connection, message_data, message_context, is_end_of_message):
        """

        Upon receiving this event, a framer implementation is responsible for performing any necessary
        transformations and sending the resulting data back to the Message Framer, which will in turn send
        it to the next protocol.
        :param connection:
        :param message_data:
        :param message_context:
        :param is_end_of_message:
        """
        pass

    @abstractmethod
    def handle_received_data(self, connection):
        """

        Upon receiving this event, the framer implementation can inspect the inbound data. The data is parsed from
        a particular cursor representing the unprocessed data. The application requests a specific amount of data it
        needs to have available in order to parse. If the data is not available, the parse fails.
        :param connection:
        """
        pass
