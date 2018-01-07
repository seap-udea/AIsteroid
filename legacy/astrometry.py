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
#LOADING DETECTION RESULTS
#######################################################
if not os.path.isfile(AIA):
    error("You have not performed the astrometry on this set.")

print("Loading astrometry results...")
analysis=pickle.load(open(AIA,"rb"))
images=analysis["images"]
allsources=analysis["allsources"]
nimgs=len(images)

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
#DETECTING
#######################################################
if "sourcesxy" in analysis.keys() and not CONF.OVERWRITE:
    print("Loading extraction results...")
else:
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #1-PERFORMING ASTROMETRY
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    print("Astrometry analysis...")
    for i,image in enumerate(images):
        file=image["file"]
        header=image["header"]

        #GET COORDINATES
        ra=sex2dec(header["OBJCTRA"])*15
        dec=sex2dec(header["OBJCTDEC"])

        #ASTROMETRY.NET COMMAND
        print("\tRunning astrometry over %s..."%file)
        opts=""
        opts+=" "+"--use-sextractor --sextractor-path "+CONF.SEX_DIR+"bin/sex"
        opts+=" "+"--no-plots"
        opts+=" "+"--ra %.7f --dec %.7f --radius 1"%(ra,dec)
        #opts+=" "+"--scale-units arcsecperpix --scale-low %.2f --scale-high %.2f"%(PXSIZE/ARCSEC,2*PXSIZE/ARCSEC)
        opts+=" "+"--guess-scale --overwrite"
        cmd=CONF.AST_DIR+"bin/solve-field "+opts+" "+file+".fits"
        sys="cd "+OUT_DIR+";"+cmd
        out=System(sys,True)
        exit(0)
        if out[-1][0]!=0:
            print("\t\tError processing image")
            print(out[-1][1])
        else:
            print("\t\tAstrometry processing successful")
            #STORE RESULTS
            image["astro_output"]="\n".join(out[:-1])

            #SOURCE XY AND MAG
            hdul=fits.open(OUT_DIR+"%s.axy"%file)
            image["sourcesxy_header"]=hdul[1].header
            image["sourcesxy"]=hdul[1].data
            hdul.close()

            #TRANSFORM
            data=rec2arr(image["sourcesxy"])
            xy=data[:,:2]
            if i>0:
                tr=image["transform"]
                xya=[]
                for j in range(xy.shape[0]):xya+=tr(xy[j,:]).tolist()
                xya=np.array(xya)
            else:xya=xy
            image["sourcesxy_aligned"]=xya

            #SOURCES RA,DEC
            cmd=CONF.AST_DIR+"bin/wcs-xy2rd -X 'X_IMAGE' -Y 'Y_IMAGE' -w %s.wcs -i %s.axy -o %s.ard"%(file,file,file)
            sys="cd "+OUT_DIR+";"+cmd
            out=System(sys,False)

            hdul=fits.open(OUT_DIR+"%s.ard"%file)
            image["sourcesrd_header"]=hdul[1].header
            image["sourcesrd"]=hdul[1].data
            hdul.close()

            #STARS X,Y
            hdul=fits.open(OUT_DIR+"%s-indx.xyls"%file)
            image["starsxy_header"]=hdul[1].header
            image["starsxy"]=hdul[1].data
            hdul.close()

            #STARS RA,DEC
            hdul=fits.open(OUT_DIR+"%s.rdls"%file)
            image["starsrd_header"]=hdul[1].header
            image["starsrd"]=hdul[1].data
            hdul.close()
    print("\tDone.")
    exit(0)
    
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #5-CALIBRATING STARS
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    print("Calibrating photometry...")

    for i,image in enumerate(images):
        print("\tCalibrating image ",i)
        starsrd=image["starsrd"]
        starsxy=image["starsxy"]
        sourcesxy=image["sourcesxy"]
        zeros=[]
        ifound=0
        for istar in range(starsrd.shape[0]):
            #print("Testing star %d"%istar)
            starxy=starsxy[istar]
            starrd=starsrd[istar]
            #print("\tXY pos:",starxy)
            #print("\tRA,DEC:",starrd)

            #Search for close sources
            ds=np.sqrt((sourcesxy["X_IMAGE"]-starxy[0])**2+(sourcesxy["Y_IMAGE"]-starxy[1])**2)
            ids=np.argsort(ds)
            if ds[ids[0]]<1:
                #print("\tSource found at %.2f px"%ds[ids[0]])
                source=sourcesxy[ids[0]]
                mag=source["MAG_AUTO"]
                #print("\tPhotometric magnitude source:",mag)
                ra=dec2sex(starrd[0]/15)
                dec=dec2sex(starrd[1])
                ras="%d %d %.2f"%(int(ra[0]),int(ra[1]),ra[2])
                des="%d %d %.2f"%(int(dec[0]),int(dec[1]),dec[2])
                v=Vizier(columns=['_RAJ2000', '_DEJ2000','R1mag'])
                result=v.query_region("%s %s"%(ras,des),radius=Angle(0.1,"arcmin"),catalog='USNOB1')
                R=result[0]["R1mag"][0]
                #print("\tActual magnitude:",R)
                zeros+=[R-mag]
                #print("\tZero point:",zeros[-1])
                ifound+=1
            else:
                pass
                #print("\tNo source found")
        zeros=np.array(zeros)
        image["zero"]=zeros.mean()
        image["dzero"]=zeros.std()
        print("\t\tZero = %.2f +/- %.2f (%d)"%(image["zero"],image["dzero"],ifound))

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #4-COMPILING ALL SOURCES
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    print("Compiling all sources...")
    allsources=pd.DataFrame()
    for i,image in enumerate(images):
        srcxys=pd.DataFrame(image["sourcesxy"])
        srcals=pd.DataFrame(image["sourcesxy_aligned"],columns=["X_ALIGN","Y_ALIGN"])
        srcrds=pd.DataFrame(image["sourcesrd"])
        alls=pd.concat([srcxys,srcals,srcrds],axis=1)
        alls["IMG"]=i #In which image is the source
        alls["OBJ"]=0 #To which object it belongs
        alls["NIMG"]=1 #In how many images is the object present
        alls["MOBJ"]=0 #To which moving object it belongs
        allsources=allsources.append(alls)
    allsources.sort_values(by="MAG_AUTO",ascending=True,inplace=True)
    allsources.reset_index(inplace=True)
    print("\tTotal number of sources:",len(allsources))
    print("\tDone.")

    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    #5-STORING RESULTS
    #%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 
    print("Saving astrometry results...")
    analysis=dict(images=images,allsources=allsources)
    pickle.dump(analysis,open(AIA,"wb"))
    print("\tDone.")

