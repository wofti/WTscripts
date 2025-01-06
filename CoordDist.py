#!/usr/bin/env python

import numpy as np
import argparse


# use python's arg parser
parser = argparse.ArgumentParser(description=
    '''Find the distance b''',
    epilog='''Example:
    CoordDist.py -c1 2:3:4 -c2 2:3:4 file1 file2''')
parser.add_argument('-ct', metavar='TCOL', dest='ct',
    help='column with time for 1st object')
parser.add_argument('-c1', metavar='XCOL1:YCOL1:ZCOL1', dest='c1',
    help='columns with x,y,z of 1st object')
parser.add_argument('-c2', metavar='XCOL2:YCOL2:ZCOL2', dest='c2',
    help='columns with x,y,z of 2nd object')
parser.add_argument('file', metavar='FILE', nargs='+',
    help='name of position files')

args = parser.parse_args()

# get the 2 file names
filename1 = args.file[0]
if(len(args.file)>1):
    filename2 = args.file[1]
else:
    filename2 = filename1

# time and position columns
if args.ct == None:
    ct = 1
else:
    ct = int(args.ct)
if args.c1 == None:
    c1 = '2:3:4'
else:
    c1 = str(args.c1)
if args.c2 == None:
    c2 = c1
else:
    c2 = str(args.c2)

# get indices of x,y,z positions
cols1 = c1.split(':')
x1i = int(cols1[0])-1
y1i = int(cols1[1])-1
z1i = int(cols1[2])-1
cols2 = c2.split(':')
x2i = int(cols2[0])-1
y2i = int(cols2[1])-1
z2i = int(cols2[2])-1

# get index for times
ti = ct-1

####################################################################

# load the 2 files
dat1 = np.loadtxt(filename1)
dat2 = np.loadtxt(filename2)

# compute and print distances
print('# time distance')
for i in range(len(dat1)):
    x1 = dat1[i][x1i]
    y1 = dat1[i][y1i]
    z1 = dat1[i][z1i]
    x2 = dat2[i][x2i]
    y2 = dat2[i][y2i]
    z2 = dat2[i][z2i]
    dx = x1-x2
    dy = y1-y2
    dz = z1-z2
    d = np.sqrt(dx*dx + dy*dy + dz*dz)
    print(dat1[i][ti], d)
