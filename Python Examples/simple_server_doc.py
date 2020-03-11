from endpoint import *
from preconnection import *
from transport_properties import *
from enumerations import *
import framer

local_specifier = LocalEndpoint()
local_specifier.with_port(5000)

tp = TransportProperties(TransportPropertyProfiles.UNRELIABLE_DATAGRAM)

def simple_receive_handler(connection, message, context, is_end, error):
    shim_print(f"Got msg {len(message.data)}: {message.data.decode()}", level='msg')
    connection.send(b"Simple server hello", None)
    connection.receive(simple_receive_handler)


def new_connection_received(connection: Connection):
    connection.receive(simple_receive_handler)


preconnection = Preconnection(local_endpoint=local_specifier, transport_properties=tp)
preconnection.add_framer(framer.TestFramer())

new_listener: Listener = preconnection.listen()
new_listener.HANDLE_CONNECTION_RECEIVED = new_connection_received

preconnection.start()
