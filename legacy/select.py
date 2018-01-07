#######################################################
#           _____     _                 _     _       #
#     /\   |_   _|   | |               (_)   | |      # 
#    /  \    | |  ___| |_ ___ _ __ ___  _  __| |      #
#   / /\ \   | | / __| __/ _ \ '__/ _ \| |/ _` |      #
#  / ____ \ _| |_\__ \ ||  __/ | | (_) | | (_| |      #
# /_/    \_\_____|___/\__\___|_|  \___/|_|\__,_|      #
# Artificial Intelligence in the Search for Asteroids #
# Jorge I. Zuluaga [)] 2017                           #
# http://bit.ly/aisteroid                             #
#######################################################
# Photometry procedure
#######################################################
from aisteroid import *

#######################################################
#LOCAL CONFIGURATION
#######################################################
#Output directory
OUT_DIR=CONF.SCR_DIR+CONF.SET+"/"

#File to pickle analysis results
AIA=OUT_DIR+"analysis.aia"

#Observatory configuration file
CFG=[line.rstrip('\n') for line in open(CONF.SETS_DIR+CONF.CFG+".cfg")]

#MPCCODE
MPCCODE=Config(CFG,"MPCCode")
OBSERVER=Config(CFG,"Observer")
TELESCOPE=Config(CFG,"Telescope")[0]

#Time of report
NOW=datetime.now()
NOW=NOW.strftime("%Y.%m.%d %H:%M:%S")

#############################################################
#LOAD ASTROMETRY RESULTS
#############################################################
if not os.path.isfile(AIA):
    error("You have not performed the astrometry on this set.")

print("Loading astrometry results...")
analysis=pickle.load(open(AIA,"rb"))
images=analysis["images"]
allsources=analysis["allsources"]
nimgs=len(images)
objects=pd.read_csv(OUT_DIR+"objects-%s.csv"%CONF.SET)

#############################################################
#GENERATE REPORT
#############################################################
f=open(OUT_DIR+"select-%s.txt"%CONF.SET,"w")
print("Generating selection report...")
typo="C"
mago="R"
lines=""
header="%-5s|%-68s|%-10s|%-10s|\n"%("ID","REPORT","SNR","RA")
f.write(header)
f.write("-"*len(header)+"\n")
for ind in objects.index:
    objp=objects.loc[ind]
    if objp.GO<1:continue
    parts=str(objp.IDIMG).split(".")
    idimg="%04d.%1d"%(int(parts[0]),int(parts[1]))
    idobj="%s%04d"%(CONF.TEAM,objp.IDOBJ)
    print("\tReport for image %s"%idimg)
    
    mag=objp.MAG_BEST
    ras=dec2sex(objp.RA/15)
    decs=dec2sex(objp.DEC)

    entry="%3s%1s%02d%03d%7.3f%03d%03d%6.2f%13.1f%2s%9s"%\
        (typo,
         objp.DATE,
         int(ras[0]),int(ras[1]),ras[2],
         int(decs[0]),int(decs[1]),decs[2],
         mag,
         mago,
         MPCCODE
        )

    line="%-5d|%-68s|%-10.2f|%-10.2f|\n"%\
        (objp.IDOBJ,
         entry,
         objp.SNR,
         objp.RA
        )
    lines+=line

if len(objects.index)==0:
    f.write("NO MOVING OBJECTS DETECTED\n\n")
else:
    f.write(lines)
f.close()
