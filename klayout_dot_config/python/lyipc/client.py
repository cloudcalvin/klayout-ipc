''' The client is designed to run in either python or klayout's interpreter
'''
from __future__ import print_function
import socket
from lyipc import PORT, isGSI
import os
import time
from functools import lru_cache


if not isGSI():
    # print('Warning: pya will not be available')
    try:
        import PyQt5.QtNetwork
    except ImportError as e:
        print('Warning: No PyQt5 found. You have to run this script from klayout\'s interpreter')
else:
    import pya


def reload():
    send('reload view')


fast_realpath = lru_cache(maxsize=4)(os.path.realpath)  # Since the argument is going to be the same every time
def load(filename):
    filename = fast_realpath(filename)
    send(f'load {filename}')


def kill():
    send('kill')


def send(message='ping 1234', port=PORT):
    ''' Sends a raw message

        Trick here is that PyQt5 does not do automatic str<->byte encoding, but pya does. Also something weird with the addresses
    '''
    payload = message + '\r\n'
    if isGSI():
        psock = pya.QTcpSocket()
        ha = 'localhost'
    else:
        psock = PyQt5.QtNetwork.QTcpSocket()
        ha = PyQt5.QtNetwork.QHostAddress.LocalHost
        payload = payload.encode()

    psock.connectToHost(ha, port)
    if psock.waitForConnected():
        psock.write(payload)
        if psock.waitForReadyRead(3000):
            ret = psock.readLine()
            if not isGSI():
                ret = bytes(ret).decode('utf-8')
            handle_query(ret)
        else:
            raise Exception('Not acknowledged')
    else:
        print(f'Connection Fail! (tried {ha}:{port})')
    # psock.close()


def handle_query(retString):
    ''' For now all this does is make sure there is handshaking '''
    if retString != 'ACK':
        raise Exception('Not acknowledged, instead: ' + retString)


def trace_pyainsert(layout, file, write_load_delay=0.01):
    ''' Writes to file and loads in the remote instance whenever pya.Shapes.insert is called
        "layout" is what will be written to file and loaded there.

        Intercepts pya.Shapes.insert globally, not just for the argument "layout".
        This is because usually cells are generated before they are inserted into the layout,
        yet we would still like to be able to visualize their creation.
    '''
    import pya
    pya.Shapes.old_insert = pya.Shapes.insert
    def new_insert(self, *args, **kwargs):
        retval = pya.Shapes.old_insert(self, *args, **kwargs)
        layout.write(file)
        time.sleep(write_load_delay)
        load(file)
        return retval
    pya.Shapes.insert = new_insert



def trace_SiEPICplacecell(layout, file, write_load_delay=0.01):
    ''' Uses trace_pyainsert to intercept geometry creation, and also makes Pcells
        place within the parent cell before being created. 
        Normally, pcells are created before they are placed.
    '''
    trace_pyainsert(layout, file, write_load_delay)
    import SiEPIC.utils.pcells as kpc
    kpc.KLayoutPCell.old_place_cell = kpc.KLayoutPCell.place_cell
    def new_place_cell(self, parent_cell, origin, params=None, relative_to=None, transform_into=False):
        layout = parent_cell.layout()
        # Build it to figure out the ports. Don't trace that
        pcell, ports = self.pcell(layout, params=params)
        # layout.delete_cell(pcell.cell_index())
        # Place an empty cell
        new_cell = layout.create_cell(self.name)
        retval = kpc.place_cell(parent_cell, new_cell, ports, origin, relative_to=relative_to, transform_into=transform_into)
        # Build it again, this time in place. Trace it as it builds
        self.pcell(layout, cell=new_cell, params=params)
        return retval
    kpc.KLayoutPCell.place_cell = new_place_cell


def trace_phidladd(device, file, write_load_delay=0.01):
    ''' Writes to file and loads in the remote instance whenever phidl.Device.add is called
    '''
    import phidl
    phidl.device_layout.Device.old_add = phidl.device_layout.Device.add
    def new_add(self, *args, **kwargs):
        retval = phidl.device_layout.Device.old_add(self, *args, **kwargs)
        device.write_gds(file)
        time.sleep(write_load_delay)
        load(file)
        return retval
    phidl.device_layout.Device.add = new_add
