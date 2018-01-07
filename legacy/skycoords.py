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
#SKY COORDS
#######################################################
#if "RA" in allsources.keys()!=None and not CONF.OVERWRITE:
#    print("Skycoords completed")
#else:
if not os.path.isfile(OUT_DIR+"rds.dat") or CONF.OVERWRITE:

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #1-EXTRACTING BRIGHTEST OBJECTS COORDINATES
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    print("Coordinates of the brightest sources...")
    rds=dict()
    for i,image in enumerate(images):
        file=image["file"]
        #Brightest coordinates
        print("Image %d"%i,image["file"])
        sources=allsources[allsources.IMG==i]
        print("\tAll sources:",len(sources))
        sc=isolateSources(sources,radius=50*CONF.RADIUS)
        print("\tSeparate sources:",len(sc))

        fig,axs=plt.subplots()
        axs.plot(sources["X_ALIGN"],sources["Y_ALIGN"],'ko',ms=0.5,mfc='None')
        axs.plot(sc["X_ALIGN"],sc["Y_ALIGN"],'b+',ms=3,mfc='None')
        axs.set_title("Image %d"%(i+1))
        axs.invert_yaxis()
        fig.savefig(OUT_DIR+"separate.png")

        #Search for matches in Vizier
        print("\tSearching for close sources (it may take a while)...")
        freq=int(len(sc)/10)
        rds[file]=[]
        qnomag=0
        qnoclose=0
        for i,ind in enumerate(sc.index):
            if (i%freq)==0:print("\t\tSearching source %d..."%i)
            obj=sources.loc[ind]
            ra=dec2sex(obj["ALPHA_J2000"]/15)
            dec=dec2sex(obj["DELTA_J2000"])
            ras="%d %d %.2f"%(int(ra[0]),int(ra[1]),ra[2])
            des="%d %d %.2f"%(int(dec[0]),int(dec[1]),dec[2])
            v=Vizier(columns=['_RAJ2000', '_DEJ2000','R1mag'])
            result=v.query_region("%s %s"%(ras,des),
                                  radius=Angle(0.1,"arcmin"),
                                  catalog='USNOB1')
            if len(result)>0:
                Rmag=float(result[0]["R1mag"][0])
                if not np.isnan(Rmag):
                    RA=result[0]["_RAJ2000"][0]
                    DEC=result[0]["_DEJ2000"][0]
                    rds[file]+=[[ind,RA,DEC,Rmag]]
                else:
                    qnomag+=1
            else:
                qnoclose+=1

        print("\t\tNumber of sources matching:",len(rds[file]))
        print("\t\tNumber of unsuitable sources:",qnomag)
        print("\t\tNumber of undetectd counterpart:",qnoclose)
        rds[file]=np.array(rds[file])

    print("Saving skycoord results...")
    pickle.dump(rds,open(OUT_DIR+"rds.dat","wb"))
    print("\tDone.")

rds=pickle.load(open(OUT_DIR+"rds.dat","rb"))
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
#1-ALIGNMENT
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
for i,image in enumerate(images):
    file=image["file"]

    print("Coordinates transformation for image %d (%s)..."%(i,file))
    inds=[int(ind) for ind in rds[file][:,0]]

    sources=allsources[allsources.IMG==i].loc[inds][["ALPHA_J2000",
                                                     "DELTA_J2000"]].values
    targets=rds[file][:,1:3]
    print("\t\tAverage distance before alignment:",np.abs(sources-targets).mean()/ARCSEC)

    #Alignment
    tr=SimilarityTransform()
    status=tr.estimate(sources,targets)

    #Plot detection
    #Test alignment
    src=[]
    for j in range(sources.shape[0]):src+=tr(sources[j,:]).tolist()
    src=np.array(src)
    print("\t\tAverage distance after alignment:",np.abs(src-targets).mean()/ARCSEC)
            

    fig,axs=plt.subplots(2,1,sharex=True,sharey=True)

    ax=axs[0]
    ax.plot(sources[:,0],sources[:,1],'ro',ms=3,mfc='None')
    ax.plot(targets[:,0],targets[:,1],'b+',ms=3,mfc='None')

    ax=axs[1]
    ax.plot(src[:,0],src[:,1],'ro',ms=3,mfc='None')
    ax.plot(targets[:,0],targets[:,1],'b+',ms=3,mfc='None')

    fig.savefig(OUT_DIR+"coordinates.png")
