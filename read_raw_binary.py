#!/usr/bin/env python

# read_raw_binary.py
# Copyright (C) 2017 Wolfgang Tichy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import print_function

#import numpy as np
import struct
import argparse

# use pythons arg parser
parser = argparse.ArgumentParser(description=
    '''Print header and some content of a binary data file''',
    epilog='''Example:
    read_raw_binary.py -c 20 bamo.00685_320/ID_level_1_proc_88.dat''')
parser.add_argument('--byteorder', metavar='BYTEORDER', dest='byteorder',
        default='=',
        help="'=' is native, '<' is little, '>' is big endian")
parser.add_argument('--format', metavar='FORMAT', dest='format',
        default='d', help="'d' for double', 'f' for float")
parser.add_argument('-c', metavar='COLUMNS', dest='cols',
        default=20, help="number of columns in data file")
parser.add_argument('file', help='filename')

args = parser.parse_args()


#############################################################################
# function to read big or little endian doubles or floats from binary files
# read doubles or floats from file and return in vdata
def read_raw_binary(file, ndata, byteorder, format):
  """byteorder is '=', '>' or '<' for native, big-endian and little-endian
     format is 'd' or 'f' for double of float"""
  # read data into a byte string
  size = struct.calcsize(format)
  bstr = file.read(size*ndata)
  # unpack bstr into tuple of C-floats, assuming big-endian (>) byte order
  fmt = byteorder + ('%d' % (ndata)) + format 
  dtuple = struct.unpack(fmt, bstr)
  ## convert tuple dtu into numpy array
  #vdata = np.array(dtuple)
  vdata = dtuple
  return vdata


# figure out if a line is actually text or binary
def is_text(line):
  try:
    text = line.decode('utf_8')
    istext = 1
  except:
    istext = 0
  return istext

# load data from e.g. a bam vtk file
def load_data(filename, cols, byteorder, format):
  size = struct.calcsize(format)
  with open(filename, 'rb') as f:
    # print all text header lines
    print('############### text header at begining of file ###############')
    while True:
      pos = f.tell()
      # print('S pos =', pos)
      line = f.readline()
      if not line: break
      if is_text(line) == 1:
        print('#', line.decode('utf_8'), end='')
      else:
        f.seek(pos) # go back in file f to start of line
        break
    # once we get here, we have read the header and now the data start
    print('############### binary data starts now at pos =', pos, 
          '###############')
    ndata = cols
    # read 3 lines from the beginning of bin data:
    vdata = read_raw_binary(f, ndata, byteorder, format)
    for v in vdata: print('%.16g' % v, end=' ')
    print()
    vdata = read_raw_binary(f, ndata, byteorder, format)
    for v in vdata: print('%.16g' % v, end=' ')
    print()
    vdata = read_raw_binary(f, ndata, byteorder, format)
    for v in vdata: print('%.16g' % v, end=' ')
    print()
    print('# ...')
    # read 2 lines from before the end:
    f.seek(-ndata*size*2, 2)  # the last 2 means seek from end of file
    vdata = read_raw_binary(f, ndata, byteorder, format)
    for v in vdata: print('%.16g' % v, end=' ')
    print()
    vdata = read_raw_binary(f, ndata, byteorder, format)
    for v in vdata: print('%.16g' % v, end=' ')
    print()
    pos = f.tell()
    print('############### binary data ends at pos =', pos, 
          '###############')
    print('############### each binary data item has size =', size, 
          '###############')

#############################################################################

load_data(args.file, int(args.cols), args.byteorder, args.format)

#load_data('bamo.00685_320/ID_level_1_proc_88.dat',
#          int(args.cols), args.byteorder, format)
#load_data('BAMSLy_m1.35o.00685_320/ID_level_1_proc_88.dat',
#          int(args.cols), args.byteorder, format)
