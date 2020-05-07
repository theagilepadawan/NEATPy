***********************
Client-server example
***********************

Let us create a simple client and server with NEATPy!

Our server is going to reply :guilabel:`"Hello from server"` to all
incoming messages, while our client will simply send a message, wait for a reply, then terminate the connection.

Import *NEATPy* and let us start with the server!

.. code-block:: python

    import neatpy

Server
-------------------

First we need to create a :py:class:`local_endpoint` and specify which port we want to listen to:

.. code-block:: python

    local_specifier = LocalEndpoint()
    local_specifier.with_port(5000)

We want a transport that is reliable and stream-oriented.
To specify this we need to create a :py:class:`transport_properties` object and set a :py:class:`preference_level` for a couple of :py:class:`selection_properties`:

.. code-block:: python

    transport_properties = TransportProperties()
    # Selection properties can be set with the add call...
    transport_properties.add(SelectionProperties.RELIABILITY, PreferenceLevel.REQUIRE)
    # Or one of the convenient functions:
    transport_properties.prohibit(SelectionProperties.PRESERVE_MSG_BOUNDARIES)


The next step is to create a :py:class:`preconnection`, passing our local endpoint and transport properties as arguments. Next, we call :py:meth:`.listen`

.. code-block:: python

    new_preconnection = Preconnection(local_endpoint=local_specifier, transport_properties=tp)
    new_listener: Listener = new_preconnection.listen()


To reply `Hello from server` to new incoming messages, and then terminate the connection we need to register two event handlers:

- One event handler that is registered for the listener, called when a new connection is established. This is registered with the member `HANDLE_CONNECTION_RECEIVED` of the listener class.

- We pass our second event handler with the send call for our reply, being fired with the 'sent' event.

The signatures of these event is listed in the documentation. The event handlers could be either full fledged
functions or anonymous functions (in essence all objects that are callable), let us create one of each for demonstration:

.. code-block:: python

    def simple_connection_received_handler(connection, message, context, is_end, error):
        anon_func = lambda connection: connection.close()
        connection.send(b"Hello from server", anon_func)

The last step will be to register the event handler and call :py:meth:`preconnection.Preconnection.start`.

.. code-block:: python

    new_listener.HANDLE_CONNECTION_RECEIVED = new_connection_received
    new_preconnection.start()


.. Note:: Calling start on the Preconnection starts the inner event loop of the transport system and does not return. Further interaction is achieved through the various events,
          e.g. the event signaling a Connection is received, manifested in the :py:attr:`.HANDLE_CONNECTION_RECEIVED` member of the :py:class:`listener` class.

That is it! Assuming we are running our program from the command line and using a main function, the typed out server looks like the following:

.. code-block:: python

    import neatpy

    def simple_connection_received_handler(connection, message, context, is_end, error):
        anon_func = lambda connection: connection.close()
        connection.send(b"Hello from server", anon_func)

    def main():
        local_specifier = LocalEndpoint()
        local_specifier.with_port(5000)

        transport_properties = TransportProperties()
        transport_properties.add(SelectionProperties.RELIABILITY, PreferenceLevel.REQUIRE)
        transport_properties.prohibit(SelectionProperties.PRESERVE_MSG_BOUNDARIES)

        new_preconnection = Preconnection(local_endpoint=local_specifier, transport_properties=tp)
        new_listener: Listener = new_preconnection.listen()

        new_listener.HANDLE_CONNECTION_RECEIVED = new_connection_received
        new_preconnection.start()

    if __name__ == "__main__":
        main()

-------------------------------------------------------------------------------------------------------------------

Client
-------------------

To establish a connection to our server, we will first need to create a Remote Endpoint and specify the remote port and address:

.. code-block:: python

    remote_specifier = RemoteEndpoint()
    remote_specifier.with_address("127.0.0.1")
    remote_specifier.with_port(5000)

Following we create a :py:class:`transport_properties` object, but this time we will use one of the :py:class:`transport_profiles`. These functions
as a convenience objects, pre-configured with frequently used sets of properties, and are passed on when initializing a :py:class:`transport_properties` object:

.. code-block:: python

    transport_properties = TransportProperties(TransportPropertyProfiles.RELIABLE_INORDER_STREAM)

Next, just like with the server, we create a :py:class:`preconnection` and pass out Remote Endpoint and Transport Properties:

.. code-block:: python

    new_preconnection = Preconnection(remote_endpoint=remote_specifier, transport_properties=transport_properties)
    new_connection = new_preconnection.initiate()

The last thing we need to do is to register our event handler for when the initiated connection is successfully established, and then start the transport
system with


.. code-block:: python

    new_connection.HANDLE_STATE_READY = ready_handler
    new_preconnection.start()

With our client we have two event handlers. One for handling when the Connection is successfully established while the last one is passed when calling
:py:meth:`.receive`, handling a receive event:

.. code-block:: python

    def receive_handler(connection, message, message_context, is_end_of_message, error):
        print(f"Got message {len(message.data)}: {message.data.decode()}")
        connection.stop()

    def ready_handler(connection: Connection):
        connection.send(b"Hello server", None)
        connection.receive(receive_handler)

Our client in full looks like the following:

.. code-block:: python

    def receive_handler(connection, message, message_context, is_end_of_message, error):
        print(f"Got message {len(message.data)}: {message.data.decode()}")
        connection.stop()

    def ready_handler(connection: Connection):
        connection.send(b"Hello server", None)
        connection.receive(receive_handler)

    def main():
        remote_specifier = RemoteEndpoint()
        remote_specifier.with_address("127.0.0.1")
        remote_specifier.with_port(5000)

        transport_properties = TransportProperties(TransportPropertyProfiles.RELIABLE_INORDER_STREAM)

        new_preconnection = Preconnection(remote_endpoint=remote_specifier, transport_properties=transport_properties)
        new_connection = new_preconnection.initiate()
        new_connection.HANDLE_STATE_READY = ready_handler
        new_preconnection.start()

    if __name__ == "__main__":
        main()
