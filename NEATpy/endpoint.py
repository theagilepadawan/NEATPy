# coding=utf-8
# !/usr/bin/env python3


class LocalEndpoint:
    """This class holds information about a local endpoint. It could be passed when initiating a :py:class:`preconnection`.
    Furthermore it is required when trying to establish a connection with a remote endpoint with :py:meth:`.listen`.
    """
    def __init__(self):
        self.port = None
        self.address = None
        self.interface = None

    def with_interface(self, interface: str) -> None:
        """This function sets the interface desired to with the local endpoint.

        :param interface: The endpoint to set.
        """
        self.interface = interface

    def with_address(self, address: str) -> None:
        """This function sets the address desired to use with the local endpoint.

        :param address: The address to set.
        """
        self.address = address

    def with_port(self, portNumber: int) -> None:
        """This function sets the port desired to use with the local endpoint.

        :param portNumber: The port to set.
        """
        self.port = portNumber


class RemoteEndpoint:
    """This class holds information about a remote endpoint. It could be passed when initiating a :py:class:`preconnection`.
    Furthermore it is required when trying to establish a connection with a remote endpoint with :py:meth:`.initiate`.
    """
    def __init__(self):
        self.address = None
        self.port = None
        self.host_name = None
        self.interface = None

    def with_interface(self, interface: str) -> None:
        """This function sets the interface desired to with the local endpoint.

        :param interface: The endpoint to set.
        """
        self.interface = interface

    def with_address(self, address: str) -> None:
        """This function sets the address desired to use with the local endpoint.

        :param address: The address to set.
        """
        self.address = address

    def with_port(self, portNumber: int) -> None:
        """This function sets the port desired to use with the local endpoint.

        :param portNumber: The port to set.
        """
        self.port = portNumber

    def with_hostname(self, hostname: str) -> None:
        """This function sets the hostname for the remote endpoint.

        :param hostname: The hostname to set.
        """
        self.host_name = hostname

