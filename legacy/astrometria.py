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
# Astrometry procedure
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

#######################################################
#LOADING PREVIOUS RESULTS
#######################################################
if not os.path.isfile(AIA):
    error("You have not performed the extraction procedure.")

print("Loading results...")
analysis=pickle.load(open(AIA,"rb"))
images=analysis["images"];nimgs=len(images)
allsources=analysis["allsources"]

#######################################################
#CCD PROPERTIES
#######################################################
print("Telescope & CCD Properties:")
FOCAL=Config(CFG,"FocalLength") #mm
PW=Config(CFG,"PixelWide") #mm
PH=Config(CFG,"PixelHigh") #mm
SIZEX=images[0]["header"]["NAXIS1"]
SIZEY=images[0]["header"]["NAXIS2"]
PWD=np.arctan(PW/FOCAL)*RAD
PHD=np.arctan(PW/FOCAL)*RAD
PXSIZE=(PWD+PHD)/2
print("\tFocal lenght (mm) :",FOCAL)
print("\tPixel size (x mm,y mm) :",PW,PH)
print("\tImage size (x px,y px) :",SIZEX,SIZEY)
print("\tPixel size (arcsec):",PXSIZE/ARCSEC)
print("\tCamera field (x deg,y deg) :",SIZEX*PWD,SIZEY*PHD)

#######################################################
#ASTROMETRIA
#######################################################
#if "RA" in allsources.keys()!=None and not CONF.OVERWRITE:
#    print("Skycoords completed")
#else:
if not os.path.isfile(OUT_DIR+"rds.dat") or CONF.OVERWRITE:

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #1-BUILD DATABASE OF CLOSE SOURCES
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    print("Looking for star in the field covered by the images...")
    rmin=allsources["ALPHA_J2000"].min()
    rmax=allsources["ALPHA_J2000"].max()
    dmin=allsources["DELTA_J2000"].min()
    dmax=allsources["DELTA_J2000"].max()
    rmean=(rmin+rmax)/2;dr=(rmax-rmin)/2
    dmean=(dmin+dmax)/2;dd=(dmax-dmin)/2
    ra=dec2sex(rmean/15)
    dec=dec2sex(dmean)
    ras="%d %d %.2f"%(int(ra[0]),int(ra[1]),ra[2])
    des="%d %d %.2f"%(int(dec[0]),int(dec[1]),dec[2])
    radius=np.sqrt(dr**2+dd**2)

    columns=['_RAJ2000','_DEJ2000','R1mag']
    v=Vizier(columns=columns)
    v.ROW_LIMIT=-1
    result=v.query_region("%s %s"%(ras,des),
                          radius=Angle(radius,"deg"),
                          catalog='USNOB1')[0]
    cond=result["R1mag"]>0
    stars=pd.DataFrame(rec2arr(result[cond][columns[:2]]),
                       columns=["ALPHA_J2000","DELTA_J2000"])
    print("\tNumber of reference stars found:",len(stars))

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #2-MATCH IMAGE AND STAR DATABASE
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    print("Matching stars...")
    for i,image in enumerate(images):
        file=image["file"]

        #Well isolated sources
        print("\tImage %d"%i,image["file"])
        sources=allsources[allsources.IMG==i]
        print("\t\tAll sources:",len(sources))
        sc=isolateSources(sources,radius=50*CONF.RADIUS)
        print("\t\tWell isolated sources:",len(sc))

        fig,axs=plt.subplots()
        axs.plot(sources["X_ALIGN"],sources["Y_ALIGN"],'ko',ms=0.5,mfc='None')
        axs.plot(sc["X_ALIGN"],sc["Y_ALIGN"],'b+',ms=3,mfc='None')
        axs.set_title("Image %d"%(i+1))
        axs.invert_yaxis()
        fig.savefig(OUT_DIR+"separate.png")

        #Matches
        sr,st=matchSources(sc[["ALPHA_J2000","DELTA_J2000"]],
                           stars,
                           x="ALPHA_J2000",y="DELTA_J2000",
                           risol=0,radius=0.1/60.0)
        print("\t\tNumber of Matched stars:",len(st))
        print("\t\tAverage distance before alignment:",
              np.abs(sr-st).mean()/ARCSEC)
        
        #Alignment
        print("\t\tAligning")
        tr=SimilarityTransform()
        status=tr.estimate(sr,st)

        sp=[]
        for j in range(sr.shape[0]):sp+=tr(sr[j,:]).tolist()
        sp=np.array(sp)
        print("\t\tAverage distance after alignment:",np.abs(sp-st).mean()/ARCSEC)

        fig,axs=plt.subplots(2,1,sharex=True,sharey=True)

        ax=axs[0]
        ax.plot(sr[:,0],sr[:,1],'ro',ms=3,mfc='None')
        ax.plot(st[:,0],st[:,1],'b+',ms=3,mfc='None')

        ax=axs[1]
        ax.plot(sp[:,0],sp[:,1],'ro',ms=3,mfc='None')
        ax.plot(st[:,0],st[:,1],'b+',ms=3,mfc='None')

        fig.savefig(OUT_DIR+"coordinates-%d.png"%(i))

