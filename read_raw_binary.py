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
    '''Print header and some content of a binary data file.
       BUT first use: xxd file''',
    epilog='''Example:
    read_raw_binary.py -c 20 bamo.00685_320/ID_level_1_proc_88.dat''')
parser.add_argument('-c', metavar='COLUMNS', dest='cols',
        default=20, help="number of columns in data file")
parser.add_argument('--format', metavar='FORMAT', dest='format',
        default='d', help="'d' for double', 'f' for float")
parser.add_argument('--byteorder', metavar='BYTEORDER', dest='byteorder',
        default='=',
        help="'=' is native, '<' is little, '>' is big endian")

parser.add_argument('-r', metavar='ROWS', dest='rows',
        default=3, help="number of binary rows we print")
parser.add_argument('--roff', metavar='ROFFSET', dest='roff',
        default=0, help="first binary row printed (negative if from data end)")
parser.add_argument('--tailbytes', metavar='TAILBYTES', dest='tailbytes',
        default=0, help="number of extra bytes after binary data")

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
def load_data(filename, cols, byteorder, format, rows, roff, tailbytes):
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
        print('#', line.decode('ascii'), end='')
      else:
        f.seek(pos) # go back in file f to start of line
        break
    # once we get here, we have read the header and now the data start
    print('############### binary data starts at pos =', pos,
          '###############')
    ndata = cols
    # read rows lines of bin data:
    #print('roff =', roff)
    if roff >= 0:
      f.seek(ndata*size*roff, 1) #the 1 means seek from current position
    else:
      f.seek(ndata*size*roff-tailbytes, 2) #the 2 means seek from end of file
    pos2 = f.tell()
    if pos2 != pos:
      print('# ...')
      print('############### printing from pos =', pos2,
            '###############')
    for i in range(rows):
      vdata = read_raw_binary(f, ndata, byteorder, format)
      for v in vdata: print('%.16g' % v, end=' ')
      print()
    if roff >=0 or rows < -roff:
      print('# ...')
    f.seek(-(tailbytes), 2) #the 2 means seek from end of file
    pos = f.tell()
    print('############### binary data ends at pos =', pos,
          '###############')
    print('############### each binary data item has size =', size,
          '###############')

#############################################################################

# get args
file = args.file
cols = int(args.cols)
byteorder = args.byteorder
format = args.format
rows = int(args.rows)
roff = int(args.roff)
tailbytes = int(args.tailbytes)


# load and print data
load_data(file, cols, byteorder, format, rows, roff, tailbytes)

#load_data('bamo.00685_320/ID_level_1_proc_88.dat',
#          int(args.cols), args.byteorder, format, rows, roff, tailbytes)
#load_data('BAMSLy_m1.35o.00685_320/ID_level_1_proc_88.dat',
#          int(args.cols), args.byteorder, format, rows, roff, tailbytes)
