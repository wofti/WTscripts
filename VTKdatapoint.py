#!/usr/bin/env python

import numpy as np
import struct
import argparse


# use python's arg parser
parser = argparse.ArgumentParser(description=
    '''Get data closest to point x0,y0,z0.''',
    epilog='''Example:
    VTKdatapoint.py -x 1 -y 2 -z 3 file.vtk''')
parser.add_argument('-x', metavar='x0', dest='x0', help='x-coord')
parser.add_argument('-y', metavar='y0', dest='y0', help='y-coord')
parser.add_argument('-z', metavar='z0', dest='z0', help='z-coord')
parser.add_argument('file', metavar='FILE', nargs='?', help='name of VTK file')

args = parser.parse_args()
filename = args.file
if args.x0 == None:
  x0 = 0.
else:
  x0 = float(args.x0)
if args.y0 == None:
  y0 = 0.
else:
  y0 = float(args.y0)
if args.z0 == None:
  z0 = 0.
else:
  z0 = float(args.z0)

################################################################
# Functions needed

################################################################
# find and get value of a parameter
def getparameter(line, par):
  val = ''
  ok = 0
  EQsign = 0
  p = line.find(par)
  # make sure there is no letter in front the par name we find
  if p > 0:
    before = line[p-1:p]
    if before.isalpha():
      p=-1
  if p >= 0:
    ok = 1
    afterpar = line[p+len(par):]
    # strip white space at end and beginning
    afterpar  = afterpar.rstrip()
    afterpar2 = afterpar.lstrip()
    if len(afterpar2) > 0:
      # if '=' is there
      if afterpar2[0] == '=':
        afterpar2 = afterpar2[1:]
        val = afterpar2.lstrip()
        EQsign = 1
      # if we have a space instead
      elif afterpar[0].isspace():
        val = afterpar.lstrip()
        EQsign = 0

  return (val , ok, EQsign)


################################################################
# is line data or comment or time = ...
def linetype(line, timestr='time'):
  iscomment = 0
  foundtime = 0
  time = ''
  # look for comments
  lstart = line.lstrip()
  if len(lstart) == 0:
    lstart = line
  if lstart[0] == '#' or lstart[0] == '"' or lstart[0] == '%':
    iscomment = 1
  # look for time value
  (time, ok, EQ) = getparameter(line.lower(), timestr)
  if len(time) > 0:
    time = time.split()[0]
  # see if we found time
  # if ok==1 and EQ==1:
  if ok==1:
    foundtime = 1
    # look for junk and cut it out
    l = len(time)
    p1 = time.find('"')
    p2 = time.find(',')
    if p1 < 0:
      p1 = l
    if p2 < 0:
      p2 = l
    pm = min(p1, p2)
    time = time[:pm]
  else:
    fondtime = 0

  return (iscomment, foundtime, time)

################################################################
# convert a string to float similar to C's atof
def WT_atof(str, strfl=0.0):
  fl = float(strfl)
  if len(str) == 0:
    return fl
  list = str.split()
  str1 = list[0]
  while len(str1)>0:
    try:
      fl = float(str1)
      break
    except:
      str1 = str1[:-1]
  return fl


################################################################
# functions to read simple VTK files

# find out what kind of vtk file we have
def determine_vtk_DATASET_type(filename):
  with open(filename, 'rb') as f:
    # go over lines until DATASET
    while True:
      line = f.readline()
      if not line:
        break
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'DATASET')
      if ok == 1:
        DATASET = val
        break
    return DATASET


# load data from bam vtk file for Cartesian grids
def load_vtk_STRUCTURED_POINTS_data(filename, timestr):
  with open(filename, 'rb') as f:
    varname = ''
    time = '0'
    BINARY = 0
    DATASET = ''
    nx = 1
    ny = 1
    nz = 1
    x0 = 0.0
    y0 = 0.0
    z0 = 0.0
    dx = 1.0
    dy = 1.0
    dz = 1.0
    double_prec = 0
    # go over lines until LOOKUP_TABLE
    while True:
      line = f.readline()
      if not line:
        break
      (val,ok,EQsign) = getparameter(line.lower().decode('ascii'), 'variable')
      if ok == 1:
        varname = val
        p = val.find(',')
        if p >= 1:
          varname = val[:p-1]
      (val,ok,EQsign) = getparameter(line.lower().decode('ascii'), timestr)
      if ok == 1:
        time = val
        p = val.find(',')
        if p >= 1:
          time = val[:p-1]
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'BINARY')
      if ok == 1:
        BINARY = 1
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'DATASET')
      if ok == 1:
        DATASET = val
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'DIMENSIONS')
      if ok == 1:
        slist = val.split()
        nx = int(slist[0])
        ny = int(slist[1])
        nz = int(slist[2])
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'ORIGIN')
      if ok == 1:
        slist = val.split()
        x0 = float(slist[0])
        y0 = float(slist[1])
        z0 = float(slist[2])
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'SPACING')
      if ok == 1:
        slist = val.split()
        dx = float(slist[0])
        dy = float(slist[1])
        dz = float(slist[2])
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'SCALARS')
      if ok == 1:
        p = val.find('double')
        if p >= 0:
          double_prec = 1
      p = line.decode('ascii').find('LOOKUP_TABLE')
      if p >= 0:
        break
    # once we get here, we have read the ASCII header and now the data start
    npoints = nx*ny*nz
    if BINARY == 1:
      vdata = read_raw_binary_vtk(f, npoints, double_prec)
    else:
      vdata = read_raw_text_vtk(f, npoints)
    # now make x,y,z coords for all points
    # xr = np.linspace(x0, x0 + dx*(nx-1), nx)
    # yr = np.linspace(y0, y0 + dy*(ny-1), ny)
    # zr = np.linspace(z0, z0 + dz*(nz-1), nz)
    # first make empty numpy array of the correct type
    if double_prec == 1:
      xyzdata = np.empty(3*npoints)
    else:
      xyzdata = np.empty(3*npoints, dtype=np.float32)
    # now insert coords
    ijk = 0
    for k in range(0,nz):
      z = z0 + k*dz
      for j in range(0,ny):
        y = y0 + j*dy
        for i in range(0,nx):
          xyzdata[ijk]   = x0 + i*dx
          xyzdata[ijk+1] = y
          xyzdata[ijk+2] = z
          ijk += 3
    xyzdata = xyzdata.reshape(-1,3)
    # figure out blocking for mesh grid
    if nz == 1:
      blocks = ny
    elif ny == 1 or nx == 1:
      blocks = nz
    else:
      blocks = nz
    data = np.concatenate((xyzdata , vdata.reshape(-1,1)), axis=1)
    return (data, WT_atof(time), blocks)


# load data from sgrid vtk file for grids with non-uniform spacing
def load_vtk_RECTILINEAR_GRID_data(filename, timestr):
  with open(filename, 'rb') as f:
    varname = ''
    time = '0'
    BINARY = 0
    DATASET = ''
    nx = 1
    ny = 1
    nz = 1
    double_prec = 0
    # go over lines until LOOKUP_TABLE
    while True:
      line = f.readline()
      if not line:
        break
      (val,ok,EQsign) = getparameter(line.lower().decode('ascii'), 'variable')
      if ok == 1:
        varname = val
        p = val.find(',')
        if p >= 1:
          varname = val[:p-1]
      (val,ok,EQsign) = getparameter(line.lower().decode('ascii'), timestr)
      if ok == 1:
        time = val
        p = val.find(',')
        if p >= 1:
          time = val[:p-1]
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'BINARY')
      if ok == 1:
        BINARY = 1
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'DATASET')
      if ok == 1:
        DATASET = val
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'DIMENSIONS')
      if ok == 1:
        slist = val.split()
        nx = int(slist[0])
        ny = int(slist[1])
        nz = int(slist[2])
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'X_COORDINATES')
      if ok == 1:
        slist = val.split()
        nX = int(slist[0])
        p = val.find('double')
        if p >= 0:
          double_prec = 1
        if BINARY == 1:
          Xdata = read_raw_binary_vtk(f, nX, double_prec)
        else:
          Xdata = read_raw_text_vtk(f, nX)
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'Y_COORDINATES')
      if ok == 1:
        slist = val.split()
        nY = int(slist[0])
        p = val.find('double')
        if p >= 0:
          double_prec = 1
        if BINARY == 1:
          Ydata = read_raw_binary_vtk(f, nY, double_prec)
        else:
          Ydata = read_raw_text_vtk(f, nY)
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'Z_COORDINATES')
      if ok == 1:
        slist = val.split()
        nZ = int(slist[0])
        p = val.find('double')
        if p >= 0:
          double_prec = 1
        if BINARY == 1:
          Zdata = read_raw_binary_vtk(f, nZ, double_prec)
        else:
          Zdata = read_raw_text_vtk(f, nZ)
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'SCALARS')
      if ok == 1:
        p = val.find('double')
        if p >= 0:
          double_prec = 1
      p = line.decode('ascii').find('LOOKUP_TABLE')
      if p >= 0:
        break
    # once we get here, we have read the ASCII header and now the data start
    npoints = nx*ny*nz
    if BINARY == 1:
      vdata = read_raw_binary_vtk(f, npoints, double_prec)
    else:
      vdata = read_raw_text_vtk(f, npoints)
    # now make x,y,z coords for all points
    # first make empty numpy array of the correct type
    if double_prec == 1:
      xyzdata = np.empty(3*npoints)
    else:
      xyzdata = np.empty(3*npoints, dtype=np.float32)
    # now insert coords
    ijk = 0
    for k in range(0,nZ):
      for j in range(0,nY):
        for i in range(0,nX):
          xyzdata[ijk]   = Xdata[i]
          xyzdata[ijk+1] = Ydata[j]
          xyzdata[ijk+2] = Zdata[k]
          ijk += 3
    xyzdata = xyzdata.reshape(-1,3)
    # figure out blocking for mesh grid
    if nz == 1:
      blocks = ny
    elif ny == 1 or nx == 1:
      blocks = nz
    else:
      blocks = nz
    data = np.concatenate((xyzdata , vdata.reshape(-1,1)), axis=1)
    return (data, WT_atof(time), blocks)


# load data from bam vtk file for STRUCTURED_GRID (e.g. polar) grids
def load_vtk_STRUCTURED_GRID_data(filename, timestr):
  with open(filename, 'rb') as f:
    varname = ''
    time = '0'
    BINARY = 0
    DATASET = ''
    nx = 1
    ny = 1
    nz = 1
    double_prec = 0
    nPOINTS = 0

    # go over lines until POINTS
    while True:
      line = f.readline()
      if not line:
        break
      (val,ok,EQsign) = getparameter(line.lower().decode('ascii'), 'variable')
      if ok == 1:
        varname = val
        p = val.find(',')
        if p >= 1:
          varname = val[:p-1]
      (val,ok,EQsign) = getparameter(line.lower().decode('ascii'), timestr)
      if ok == 1:
        time = val
        p = val.find(',')
        if p >= 1:
          time = val[:p-1]
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'BINARY')
      if ok == 1:
        BINARY = 1
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'DATASET')
      if ok == 1:
        DATASET = val
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'DIMENSIONS')
      if ok == 1:
        slist = val.split()
        nx = int(slist[0])
        ny = int(slist[1])
        nz = int(slist[2])
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'POINTS')
      if ok == 1:
        nPOINTS = int( WT_atof(val) )
        p = val.find('double')
        if p >= 0:
          double_prec = 1
      p = line.decode('ascii').find('POINTS')
      if p >= 0:
        break
    # once we get here, we have read the ASCII header for the points
    # and now the data for the grid points start
    npoints = nx*ny*nz
    if(nPOINTS>0):
      npoints = nPOINTS
    ncoords = npoints * 3   # there x,y,z coords for each point
    if BINARY == 1:
      vdata = read_raw_binary_vtk(f, ncoords, double_prec)
    else:
      vdata = read_raw_text_vtk(f, ncoords)
    # now read x,y,z coords for all points from vdata
    # e.g. xyzdata[11,0] is x-coord of point 11
    xyzdata = vdata.reshape(-1,3)
    # figure out blocking for mesh grid
    if nz == 1:
      blocks = ny
    elif ny == 1 or nx == 1:
      blocks = nz
    else:
      blocks = nz

    # go over data text lines until LOOKUP_TABLE
    while True:
      line = f.readline()
      if not line:
        break
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'BINARY')
      if ok == 1:
        BINARY = 1
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'ASCII')
      if ok == 1:
        BINARY = 0
      (val,ok,EQsign) = getparameter(line.decode('ascii'), 'SCALARS')
      if ok == 1:
        p = val.find('double')
        if p >= 0:
          double_prec = 1
        else:
          double_prec = 0
      p = line.decode('ascii').find('LOOKUP_TABLE')
      if p >= 0:
        break
    # once we get here, we have read the ASCII header and now the data start
    vdata = []
    if BINARY == 1:
      vdata = read_raw_binary_vtk(f, npoints, double_prec)
    else:
      vdata = read_raw_text_vtk(f, npoints)
    data = np.concatenate((xyzdata , vdata.reshape(-1,1)), axis=1)
    return (data, WT_atof(time), blocks)



################################################################
# functions to read big endian doubles or floats from binary
# or text files

# read doubles or floats from file and return in numpy array
def read_raw_binary_vtk(file, npoints, double_prec):
  if double_prec == 1:
    # read data into a byte string
    bstr = file.read(8*npoints)
    # unpack bstr into tuple of C-doubles, assuming big-endian (>) byte order
    fmt = '>%dd' % (npoints)
    dtuple = struct.unpack(fmt, bstr)
    # convert tuple dtuple into numpy array
    vdata = np.array(dtuple)
  else:
    # read data into a byte string
    bstr = file.read(4*npoints)
    # unpack bstr into tuple of C-floats, assuming big-endian (>) byte order
    fmt = '>%df' % (npoints)
    dtuple = struct.unpack(fmt, bstr)
    # convert tuple dtuple into numpy array
    vdata = np.array(dtuple, dtype=np.float32)
  return vdata

# read data from text file
def read_raw_text_vtk(file, npoints):
  dat = []
  i = 0
  while i<npoints:
    line = file.readline()
    if not line:
      print(file)
      print('read_raw_text_vtk: npoints =', npoints,
            '. But EOF already at i = ', i)
      print('appending zeros...')
      for k in range(i, npoints):
        dat.append(0.0)
      break
    # split line into a list li and append each element of li as float to dat
    li = line.split()
    for l in li:
      dat.append(float(l))
    i = i + len(li)
  vdata = np.array(dat)
  return vdata




####################################################################


timestr = 'time'

DATASET = determine_vtk_DATASET_type(filename)
# print(DATASET)
if DATASET.find('STRUCTURED_GRID')>=0:
  (dat, time, bl) = load_vtk_STRUCTURED_GRID_data(filename, timestr)
elif DATASET.find('RECTILINEAR_GRID')>=0:
  (dat, time, bl) = load_vtk_RECTILINEAR_GRID_data(filename, timestr)
else:
  (dat, time, bl) = load_vtk_STRUCTURED_POINTS_data(filename, timestr)

# find x0,y0,z0
dist_ijk0 = 1e300
for ijk in range(len(dat)):
  x = dat[ijk][0]
  y = dat[ijk][1]
  z = dat[ijk][2]
  dist = (x-x0)**2 + (y-y0)**2 + (z-z0)**2
  if dist < dist_ijk0:
    dist_ijk0 = dist
    ijk0 = ijk

#print(data)
#print('blocks =', blocks)
#print('# nx ny nz =', nx,ny,nz)
print('# point x,y,z closest to x0,y0,z0 in',filename)
print('# x0 y0 z0 =',x0,y0,z0)
print('# time =', time)
print('# x y z value')
for ent in dat[ijk0]:
  print(ent, end=' ')
print()
 
