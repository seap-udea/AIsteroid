import numpy as np
from astropy.io import fits
from sys import argv,exit

#READ SOURCES
try:
    basename=argv[1]
    hdul_xy=fits.open('%s.axy'%basename)
except:
    print("You must provide a valid file basename")
    exit(1)

print("Number of detected objects: ",hdul_xy[1].data.shape[0])
hdul_xy.close()

#IDENTIFIED OBJECTS
hdul_objs=fits.open('%s-indx.xyls'%basename)
data_objs=hdul_objs[1].data
objs=[]
for obj in hdul_objs[1].data:
    objs+=[[obj[0],obj[1]]]
objs=np.array(objs)
hdul_objs.close()

#COORDINATE OF OBJECTS
hdul_crd=fits.open('%s.rdls'%basename)
crds=[]
for i,crd in enumerate(hdul_crd[1].data):
    crds+=[[crd[0]/15,crd[1]]]
crds=np.array(crds)
hdul_crd.close()

print("Number of identified objects:",len(objs))

for i in range(len(objs)):
    print("Object %d: (%.2f,%.2f), ra = %.5f, def = %.5f"%(i,objs[i,0],objs[i,1],crds[i,0],crds[i,1]))

