''' Automatically launches a subprocess klayout and drops into debug shell
'''
from os.path import join, dirname
import sys
# sys.path.append(join(dirname(__file__), '..', 'python'))

import lyipc.client as ipc
import os
import time
import phidl

import linecache

import pya
from SiEPIC_IME_Lightwave import Ring_Filter_DB_Refactored

from SiEPIC.utils import get_technology_by_name
TECHNOLOGY = get_technology_by_name('SiEPIC_IME')

class SetTrace(object):
    def __init__(self, func):
        self.func = func

    def __enter__(self):
        sys.settrace(self.func)
        return self

    def __exit__(self, ext_type, exc_value, traceback):
        sys.settrace(None)


def monitorWrap(layout):
    global i
    i = 0
    def monitor(frame, event, arg):
        if event == "line":
            lineno = frame.f_lineno
            filename = frame.f_globals["__file__"]
            line = linecache.getline(filename, lineno)
            usesGeometry = 'cell' in line or 'shapes' in line
            # if 'nc_devices' in filename or 'nc_library' in filename:
            # global i
            # i += 1
            if usesGeometry:
                print('>>', line.rstrip())
                # layout.write(DglobFile)
                # ipc.reload()
                # time.sleep(.05)
        return monitor
    return monitor


def foo():
   print('bar')
   print('barbar')
   print('barbarbar')


layout = pya.Layout()
layout.dbu = 0.001
# TOP = layout.create_cell('TOP')

DglobFile = os.path.realpath('Dglob.gds')
layout.write(DglobFile)
ipc.load(DglobFile)
time.sleep(2)

c = Ring_Filter_DB_Refactored()
with SetTrace(monitorWrap(layout)):
    nh = test_ntron_with_htron(D=Dglob)

