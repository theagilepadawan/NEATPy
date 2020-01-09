import copy
from utils import *

class Listner():
    def __init__(self, preconnection):
        self.preconnection = preconnection
        self.props = copy.deepcopy(self.preconnection.transport_properties)
        shim_print(self.props)
        shim_print(preconnection.transport_properties)
