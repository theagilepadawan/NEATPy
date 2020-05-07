.. NEATpy documentation master file, created by
   sphinx-quickstart on Sat Feb 29 18:59:34 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Master thesis documentation - Michae Gundersen
***********************************************

This is the documentation for NEATPy: a transport system conforming to the specification of a transport system
specified by the `TAPS WG`_.
While written in Python, it utilizes the NEAT_ codebase with the help of language bindings created by SWIG_. In this way this transport system
is logically divided in a front-end and back-end; the Python front-end presents a standards conforming API to the end user,
while under the hood, it uses NEAT to handle all protocol machinery.

Missing implementation details:

The implementation of NEATPy is mostly based on version 4 and 5 of the interface draft by the TAPS. It implements
all major objects, actions and events. However some implementations details are left out. The reason for this, is that
successful implementation of these would require changes to NEAT, which was outside the scope of the thesis:

**Selection Properties:**

+--------------------------------------+
| Interface Instance or Type           |
+--------------------------------------+
| Provisioning Domain Instance or Type |
+--------------------------------------+
| Use Temporary Local Address          |
+--------------------------------------+

**Connection Properties:**

+-----------------------------------------------------------------------+
| Retransmission Threshold Before Excessive Retransmission Notification |
+-----------------------------------------------------------------------+
| Connection Group Transmission Scheduler                               |
+-----------------------------------------------------------------------+

**Events:**

+---------------------------+
| Soft Errors               |
+---------------------------+
| Excessive retransmissions |
+---------------------------+

**Security Parameters:**

NEATPy provides secure connections, with **TLS/TCP | DTLS/UDP | DTLS/SCTP**, but further customization, as specified in the interface draft is not implemented,
due to constraints in  NEAT. For the transport system to be fully security-conformant, further implementation
of security within NEAT is needed.

**Rendezvous Action:**

Currently, the TAPS description is not very clear, and the full specification for the action is yet to be finalized.

Deviations:

:py:meth:`.Preconnection.start`:

The method is added to fulfill the methods :py:meth:`.Preconnection.initiate` and
:py:meth:`.Preconnection.listen`, which respectively returns a Connection and Listener. The reason for this addition to
NEATPy's interface is to facilitate the start of the event loop running in the within NEAT. This function starting the event
loop does not return. To be able to return Connection and Listener objects this method is needed to start the transport system
and with it the event loop.

.. _TAPS WG: https://github.com/ietf-tapswg/api-drafts
.. _SWIG: http://www.swig.org/
.. _NEAT: https://www.neat-project.org/

.. toctree::
   :caption: API documentation
   :maxdepth: 3

   subdir/API

.. toctree::
   :caption: Examples
   :maxdepth: 1

   subdir/Client-server example
