"""
Classical algorithm for extraction and identification of moving objects in an image set
"""
from aisteroid import *

#############################################################
#BASIC CONFIGURATION
#############################################################
SET="ps1-20170913_1_set142"
OUT_DIR=SCR_DIR+SET+"/"
AIA=OUT_DIR+"analysis.aia"
CFG=SET.split("-")[0]+".cfg"
cfg=[line.rstrip('\n') for line in open(SETS_DIR+CFG)]
NOW=datetime.now()
NOW=NOW.strftime("%Y.%m.%d %H:%M:%S")
MPCCODE=Config(cfg,"MPCCode")
TEAM="NEA"

#############################################################
#RECOVER DATA
#############################################################
print("Loading pickled analysis results...")
analysis=pickle.load(open(AIA,"rb"))
images=analysis["images"]
allsources=analysis["allsources"]
try:
    indxs=analysis["indxs"]
except:
    print("You must first run detect.py")

nobj=len(np.unique(allsources.loc[indxs].MOBJ.values))
objs=pd.read_csv(OUT_DIR+"objects-%s.csv"%SET)
print(len(objs))
nobj=len(objs)
exit(0)

#############################################################
#GENERATE REPORT
#############################################################
f=open(OUT_DIR+"report-%s.txt"%SET,"w")

f.write("""COD %s
OBS N. Primak, A. Schultz, S. Watters, J. Thiel, T. Goggia
MEA J.Ospina, L. Piedraita, I.Moreno, S.Lopez, J. Zuluaga (NEA, Colombia)
TEL 1.8-m f/4.4 Ritchey-Chretien + CCD
ACK MPCReport file updated %s
NET PPMXL

Image set: %s

"""%(MPCCODE,NOW,SET))

pref="NEA"
typo="C"
mago="R"
lines=""
for mobj in range(1,nobj+1):
    cond=allsources.loc[indxs].MOBJ==mobj
    inds=allsources.loc[indxs].index[cond]
    for ind in inds:
        mag=allsources.loc[ind].MAG_AUTO
        ras=dec2sex(allsources.loc[ind].RA/15)
        decs=dec2sex(allsources.loc[ind].DEC)

        iimg=int(allsources.loc[ind].IMG)
        
        exptime=float(images[iimg]["header"]["EXPTIME"])
        obstime=images[iimg]["obstime"]
        parts=obstime.split(".")
        dt=datetime.strptime(parts[0],"%Y-%m-%dT%H:%M:%S")
        fday=(dt.hour+dt.minute/60.0+(dt.second+exptime/2+int(parts[1])/1e6)/3600.0)/24.0
        fday=("%.6f"%fday).replace("0.","")
        datet=dt.strftime("%Y %m %d.")+fday

        idobj="%s%04d"%(pref,mobj)
        line="%12s%3s%s%02d %02d %6.3f%03d %02d %5.2f%13.1f%2s%9s\n"%\
            (idobj,
             typo,
             datet,
             int(ras[0]),int(ras[1]),ras[2],
             int(decs[0]),int(decs[1]),decs[2],
             mag,
             mago,
             MPCCODE)
        
        lines+=line

if nobj==0:
    f.write("NO MOVING OBJECTS DETECTED\n\n")

f.write(lines)
f.write("----- end -----\n")
f.close()
