#! /usr/bin/env python3

"""
    Class Communicator
    This contains communicator to get and send msg each other,
        - Using ZeroMQ to connect, especially using PUB/SUB method.
        - Our Communicator model uses one Brocker intermediate.
        - Assume that all agents always 'broadcasting' their msg to everyone.

    Func proxy
    This describes our intermediate broker.
        - Using ZeroMQ to receive and send msg, sockets are consist of XPUB/XSUB.
        - Before start connection, proxy() must be called first.
"""

import zmq
import time
import logging

FORMAT = '%(asctime)s %(module)s %(levelname)s %(lineno)d %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)


# Broker's addresses
proxy_addr_in = 'tcp://127.0.0.1:5555'
proxy_addr_out = 'tcp://127.0.0.1:5556'

class Communicator(object):
    def __init__(self,core=False):
        self.core=core
        self.context = zmq.Context.instance()

        # connect subscriber to broker's XPUB socket
        self.subscriber = self.context.socket(zmq.SUB)
        if self.core is True:
            self.subscriber.setsockopt(zmq.SUBSCRIBE, b'core')
        else:
            self.subscriber.setsockopt(zmq.SUBSCRIBE, b'')
            self.subscriber.setsockopt(zmq.UNSUBSCRIBE, b'core')

        self.subscriber.connect(proxy_addr_out)

        # connect publisher to broker's XSUB socket
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.connect(proxy_addr_in)

        time.sleep(1)

    def read(self):
        message = ''
        try:
            # zmq.NOBLOCK makes the process not wait for msg.
            # When it is waiting for msg, if there is no msg, just continue the process.
            message = self.subscriber.recv_string(flags=zmq.NOBLOCK)

        except zmq.error.Again:
            pass
        return message

    def send(self, message):

        if self.core is True:
            self.publisher.send_string("%s %s"%('agent',message))
        else:
            self.publisher.send_string("%s %s"%('core',message))


    def close(self):
        self.publisher.close()
        self.subscriber.close()

# Proxy server acts Broker to transfer msg from all agents to all agents.
def proxy():
    addr_in = proxy_addr_in
    addr_out = proxy_addr_out

    context = zmq.Context.instance()
    socket_in = context.socket(zmq.XSUB)
    socket_in.bind(addr_in)
    socket_out = context.socket(zmq.XPUB)
    socket_out.bind(addr_out)

    try:
        logger.info("proxy is started.")
        zmq.proxy(socket_in, socket_out)
    except zmq.ContextTerminated:
        print("proxy terminated")
        socket_in.close()
        socket_out.close()
