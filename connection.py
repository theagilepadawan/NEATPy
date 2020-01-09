# coding=utf-8
# !/usr/bin/env python3

from neat import *
import sys
import ctypes


class Connection():
    def __init__(self, preconnection):
        print("CONNECTION CREATED!!!")
        self.preconnection = preconnection

        # self.local_endpoint = preconnection.local_endpoint
        # self.remote_endpoint = preconnection.remote_endpoint
        # self.context = ctx
        # self.flow = flow
        # self.ops = ops
        #
        # self.ops.on_writable = self.on_writable
        # self.ops.on_all_written = self.on_all_written
        # self.ops.on_received = self.on_received
        #
        # neat_set_operations(self.context, self.flow, self.ops)
        # print("OPERATIONS SET!!!")
        return
    #
    # def on_writable(self, ops):
    #     print("ON WRITABLE RAN")
    #     message = "Hello, this is NEAT!"
    #     neat_write(self.context, self.flow, message, 20, None, 0)
    #     return NEAT_OK
    #
    # def on_all_written(self, ops):
    #     neat_close(self.context, self.flow)
    #     return NEAT_OK

    #
    #     """ Function that blocks until new data has arrived
    #     """
    #     async def await_data(self):
    #         waiter = self.loop.create_future()
    #         self.waiters.append(waiter)
    #         try:
    #             await waiter
    #         finally:
    #             del self.waiters[0]
    #
    #     async def active_open(self, transport):
    #         self.transport = transport
    #         print_time("Connected successfully.", color)
    #         self.state = ConnectionState.ESTABLISHED
    #         if self.framer:
    #             # Send a start even to the framer and wait for a reply
    #             await self.framer.handle_start(self)
    #         if self.ready:
    #             self.loop.create_task(self.ready(self))
    #         return
    #
    #     # Asyncio Callbacks
    #
    #     """ ASYNCIO function that gets called when a new
    #         connection has been made, similar to TAPS ready callback.
    #     """
    #     def connection_made(self, transport):
    #         # Check if its an incoming or outgoing connection
    #         if self.active is False:
    #             self.transport = transport
    #             new_remote_endpoint = RemoteEndpoint()
    #             print_time("Received new connection.", color)
    #             # Get information about the newly connected endpoint
    #             new_remote_endpoint.with_address(
    #                 transport.get_extra_info("peername")[0])
    #             new_remote_endpoint.with_port(
    #                 transport.get_extra_info("peername")[1])
    #             self.remote_endpoint = new_remote_endpoint
    #             self.state = ConnectionState.ESTABLISHED
    #             if self.connection_received:
    #                 self.loop.create_task(self.connection_received(self))
    #             return
    #
    #         elif self.active:
    #             self.loop.create_task(self.active_open(transport))
    #     """ ASYNCIO function that gets called when new data is made available
    #         by the OS. Stores new data in buffer and triggers the receive waiter
    #     """
    #     def data_received(self, data):
    #         print_time("Received " + data.decode(), color)
    #
    #         # See if we already have so data buffered
    #         if self.recv_buffer is None:
    #             self.recv_buffer = data
    #         else:
    #             self.recv_buffer = self.recv_buffer + data
    #         for i in range(self.open_receives):
    #             self.loop.create_task(self.framer.handle_received_data(self))
    #         # If there is already a receive queued by the connection,
    #         # trigger its waiter to let it know new data has arrived
    #         if self.framer:
    #             for i in self.waiters:
    #                 i.set_result(None)
    #             return
    #         for w in self.waiters:
    #             if not w.done():
    #                 w.set_result(None)
    #                 return
    #
    #     """ ASYNCIO function that gets called when EOF is received
    #     """
    #     def eof_received(self):
    #         print_time("EOF received", color)
    #         self.at_eof = True
    #     """ ASYNCIO function that gets called when a new datagram
    #         is received. It stores the datagram in the recv_buffer
    #     """
    #     def datagram_received(self, data, addr):
    #         if self.recv_buffer is None:
    #             self.recv_buffer = list()
    #         self.recv_buffer.append(data)
    #         print_time("Received %d-byte datagram" % len(data), color)
    #         for i in range(self.open_receives):
    #             self.loop.create_task(self.framer.handle_received_data(self))
    #         if self.framer:
    #             for i in self.waiters:
    #                 i.set_result(None)
    #         for w in self.waiters:
    #             if not w.done():
    #                 w.set_result(None)
    #                 return
    #     """ ASYNCIO function that gets called when the connection has
    #         an error.
    #         TODO: proper error handling
    #     """
    #     def error_received(self, err):
    #         if type(err) is ConnectionRefusedError:
    #             print_time("Connection Error occured.", color)
    #             print(err)
    #             if self.connection_error:
    #                 self.loop.create_task(self.connection_error())
    #             return
    #
    #     """ ASNYCIO function that gets called when the connection
    #         is lost
    #     """
    #     def connection_lost(self, exc):
    #         print_time("Connection lost", color)
    #
    #
    #     """ ASYNCIO function that gets called when joining a multicast flow
    #     """
    #     async def multicast_join(self):
    #         print_time("joining multicast session.", color)
    #         do_join(self)
    #
    #     def send_udp(self, data, message_count):
    #         """ Sends udp data
    #         """
    #         print_time("Writing UDP data.", color)
    #         try:
    #             # See if the udp flow was the result of passive or active open
    #             if self.active:
    #                 # Write the data
    #                 self.transport.sendto(data.encode())
    #             else:
    #                 # Delegate sending to the datagram handler
    #                 self.handler.send_to(self, data.encode())
    #         except:
    #             print_time("SendError occured.", color)
    #             if self.send_error:
    #                 self.loop.create_task(self.send_error(message_count))
    #             return
    #         print_time("Data written successfully.", color)
    #         if self.sent:
    #             self.loop.create_task(self.sent(message_count))
    #         return
    #
    #     def send_tcp(self, data, message_count):
    #         """ Send tcp data
    #         """
    #         print_time("Writing TCP data.", color)
    #         try:
    #             # Attempt to write data
    #             self.transport.write(data.encode())
    #         except:
    #             print_time("SendError occured.", color)
    #             if self.send_error:
    #                 self.loop.create_task(self.send_error(message_count))
    #             return
    #         print_time("Data written successfully.", color)
    #         if self.sent:
    #             self.loop.create_task(self.sent(message_count))
    #         return
    #
    #     def send_data(self, data, message_count):
    #         """ Selects correct send call dependent on protocol
    #         """
    #         if self.protocol == 'tcp':
    #             self.send_tcp(data, message_count)
    #         elif self.protocol == 'udp':
    #             self.send_udp(data, message_count)
    #
    #     async def process_send_data(self, data, message_count):
    #         """ Function responsible for sending data. It decides which
    #             protocol is used and then uses the appropriate functions
    #         """
    #         if self.state is not ConnectionState.ESTABLISHED:
    #             print_time("SendError occured, connection is not established.",
    #                        color)
    #             if self.send_error:
    #                 self.loop.create_task(self.send_error(message_count))
    #             return
    #         # Frame the data
    #         if self.framer:
    #             self.framer.handle_new_sent_message(data, None, False)
    #         else:
    #             self.send_data(data, message_count)
    #
    #     async def send_message(self, data):
    #         """ Attempts to send data on the connection.
    #             Attributes:
    #                 data (string, required):
    #                     Data to be send.
    #         """
    #         self.message_count += 1
    #         self.loop.create_task(self.process_send_data(data, self.message_count))
    #         return self.message_count
    #
    #     async def read_buffer(self, max_length=-1):
    #         # If the buffer is empty, wait for new data
    #         if self.recv_buffer is None or len(self.recv_buffer) == 0:
    #             await self.await_data()
    #         # See if we have to deal datagrams or stream data
    #         if self.message_based:
    #             if len(self.recv_buffer[0]) <= max_length or max_length == -1:
    #                 data = self.recv_buffer.pop(0)
    #                 return data
    #             elif len(self.recv_buffer[0]) > max_length:
    #                 data = self.recv_buffer[0][:max_length]
    #                 self.recv_buffer[0] = self.recv_buffer[0][max_length:]
    #                 return data
    #         else:
    #             if max_length == -1 or len(self.recv_buffer) <= max_length:
    #                 data = self.recv_buffer
    #                 self.recv_buffer = None
    #                 return data
    #             elif len(self.recv_buffer) > max_length:
    #                 data = self.recv_buffer[:max_length]
    #                 self.recv_buffer = self.recv_buffer[max_length:]
    #                 return data
    #
    #     """ Receive handling if a framer is in use
    #     """
    #     async def receive_framed(self, min_incomplete_length,
    #                              max_length):
    #         print_time("Ready to read message with framer", color)
    #         # If the buffer is empty, wait for new data
    #         if not self.recv_buffer:
    #             await self.await_data()
    #         print_time("Deframing", color)
    #         self.open_receives += 1
    #         context, message, eom = await self.framer.handle_received(self)
    #         if self.received:
    #             self.loop.create_task(self.received(message,
    #                                                 "Context", self))
    #         self.open_receives -= 1
    #         return
    #
    #     async def receive_message(self, min_incomplete_length,
    #                               max_length):
    #         """ Queues reception of a message if there is no framer. Will block until
    #             message that is at least min_incomplete_length long is in the
    #             msg_buffer
    #         """
    #         print_time("Reading message", color)
    #
    #         # Try to read data from the recv_buffer
    #         try:
    #             data = await self.read_buffer()
    #             if self.msg_buffer is None:
    #                 self.msg_buffer = data.decode()
    #             else:
    #                 self.msg_buffer = self.msg_buffer + data.decode()
    #         except:
    #             print_time("Connection Error", color)
    #             if self.connection_error is not None:
    #                 self.loop.create_task(self.connection_error(self))
    #             return
    #         # If we are at EOF or message based, issue a full message received cb
    #         if self.message_based or self.at_eof:
    #             print_time("Received full message", color)
    #             if self.received:
    #                 self.loop.create_task(self.received(self.msg_buffer,
    #                                                     "Context", self))
    #             self.msg_buffer = None
    #             return
    #         else:
    #             # Wait until message is equal or longer than min_incomplete length
    #             while(len(self.msg_buffer) < min_incomplete_length):
    #                 data = await self.read_buffer(max_length)
    #                 self.msg_buffer = self.msg_buffer + data.decode()
    #
    #             print_time("Received partial message.", color)
    #             if self.received_partial:
    #                 self.loop.create_task(self.received_partial(self.msg_buffer,
    #                                                             "Context", False, self))
    #                 self.msg_buffer = None
    #
    #     async def receive(self, min_incomplete_length=float("inf"), max_length=-1):
    #         """ Queues the reception of a message.
    #
    #         Attributes:
    #             min_incomplete_length (integer, optional):
    #                 The minimum length an incomplete message
    #                 needs to have.
    #
    #             max_length (integer, optional):
    #                 The maximum length a message can have.
    #         """
    #         if self.framer:
    #             self.loop.create_task(self.receive_framed(min_incomplete_length,
    #                                                       max_length))
    #         else:
    #             self.loop.create_task(self.receive_message(min_incomplete_length,
    #                                                        max_length))
    #
    #     async def close_connection(self):
    #         """ Function wrapped by close
    #         """
    #         print_time("Closing connection.", color)
    #         self.transport.close()
    #         self.state = ConnectionState.CLOSED
    #         if self.closed:
    #             self.loop.create_task(self.closed())
    #
    #     def close(self):
    #         """ Attempts to close the connection, issues a closed event
    #         on success.
    #         """
    #         self.loop.create_task(self.close_connection())
    #         self.state = ConnectionState.CLOSING
    #
    #     # Events for active open
    #     def on_ready(self, callback):
    #         """ Set callback for ready events that get thrown once the connection is ready
    #         to send and receive data.
    #
    #         Attributes:
    #             callback (callback, required): Function that implements the
    #                 callback.
    #         """
    #         self.ready = callback
    #
    #     def on_initiate_error(self, callback):
    #         """ Set callback for initiate error events that get thrown if an error occurs
    #         during initiation.
    #
    #         Attributes:
    #             callback (callback, required): Function that implements the
    #                 callback.
    #         """
    #         self.initiate_error = callback
    #
    #     # Events for sending messages
    #     def on_sent(self, callback):
    #         """ Set callback for sent events that get thrown if a message has been
    #         succesfully sent.
    #
    #         Attributes:
    #             callback (callback, required): Function that implements the
    #                 callback.
    #         """
    #         self.sent = callback
    #
    #     def on_send_error(self, callback):
    #         """ Set callback for send error events that get thrown if an error occurs
    #         during sending of a message.
    #
    #         Attributes:
    #             callback (callback, required): Function that implements the
    #                 callback.
    #         """
    #         self.send_error = callback
    #
    #     def on_expired(self, callback):
    #         """ Set callback for expired events that get thrown if a message expires.
    #
    #         Attributes:
    #             callback (callback, required): Function that implements the
    #                 callback.
    #         """
    #         self.expired = callback
    #
    # Events for receiving messages
    # def on_received(self, ops):
    #     """ Set callback for received events that get thrown if a new message
    #     has been received.
    #
    #     Attributes:
    #         callback (callback, required): Function that implements the
    #             callback.
    #     """
    #     print("ON RECEIVED!!!!")
    #     bytes_read = 0
    #     buffer = ctypes.create_string_buffer(32)
    #     if (neat_read(self.context, self.flow, buffer, 31, bytes_read, None, 0) == NEAT_OK):
    #         print("Read {} bytes:\n{}".format(bytes_read, buffer))
    #     return NEAT_OK
#
#     def on_received_partial(self, callback):
#         """ Set callback for partial received events that get thrown if a new partial
#         message has been received.
#
#         Attributes:
#             callback (callback, required): Function that implements the
#                 callback.
#         """
#         self.received_partial = callback
#
#     def on_receive_error(self, callback):
#         """ Set callback for receive error events that get thrown if an error occurs
#         during reception of a message.
#
#         Attributes:
#             callback (callback, required): Function that implements the
#                 callback.
#         """
#         self.receive_error = callback
#
#     def on_connection_error(self, callback):
#         """ Set callback for connection error events that get thrown if an error occurs
#         while the connection is open.
#
#         Attributes:
#             callback (callback, required): Function that implements the
#                 callback.
#         """
#         self.connection_error = callback
#
#     # Events for closing a connection
#     def on_closed(self, callback):
#         """ Set callback for on closed events that get thrown if the
#         connection has been closed succesfully.
#
#         Attributes:
#             callback (callback, required): Function that implements the
#                 callback.
#         """
#         self.closed = callback
#
#
# class DatagramHandler(asyncio.Protocol):
#     """ Class required to handle incoming datagram flows
#     """
#     def __init__(self, preconnection):
#         self.preconnection = preconnection
#         self.remotes = dict()
#         self.preconnection.handler = self
#
#     def send_to(self, connection, data):
#         remote_address = connection.remote_endpoint.address
#         remote_port = connection.remote_endpoint.port
#         self.transport.sendto(data, (remote_address, remote_port))
#
#     def connection_made(self, transport):
#         self.transport = transport
#         print_time("New UDP flow", color)
#         return
#
#     def datagram_received(self, data, addr):
#         print_time("Received new datagram", color)
#         if addr in self.remotes:
#             self.remotes[addr].datagram_received(data, addr)
#             return
#         new_connection = Connection(self.preconnection)
#         new_connection.state = ConnectionState.ESTABLISHED
#         new_remote_endpoint = RemoteEndpoint()
#         print_time("Received new connection.", color)
#         new_remote_endpoint.with_address(addr[0])
#         new_remote_endpoint.with_port(addr[1])
#         new_connection.remote_endpoint = new_remote_endpoint
#         print_time("Created new connection object.", color)
#         if new_connection.connection_received:
#             new_connection.loop.create_task(
#                 new_connection.connection_received(new_connection))
#             print_time("Called connection_received cb", color)
#         new_connection.datagram_received(data, addr)
#         self.remotes[addr] = new_connection
#         return
