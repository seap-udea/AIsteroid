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

#######################################################
#LOADING DECTECTION RESULTS
#######################################################
if not os.path.isfile(AIA):
    error("You have not performed the astrometry on this set.")

print("Loading astrometry results...")
analysis=pickle.load(open(AIA,"rb"))
images=analysis["images"]
allsources=analysis["allsources"]
nimgs=len(images)

try:
    indxs=analysis["indxs"]
    nobj=len(np.unique(allsources.loc[indxs].MOBJ.values))
    print("\tNumber of detected objects:",nobj)
except:
    error("The detection has not been performed.")

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

#############################################################
#PERFORM PHOTOMETRY ON DETECTED OBJECTS
#############################################################
print("PSF fitting for objects")
columns=allsources.columns.tolist()+["IDOBJ","IDIMG",
                                     "SNR","FWHM",
                                     "X_PSF","Y_PSF",
                                     "DATE","GO","REASON"]
objects=pd.DataFrame(columns=columns)
for mobj in range(1,nobj+1):
    #Get sources corresponding to object mobj
    cond=allsources.loc[indxs].MOBJ==mobj
    inds=allsources.loc[indxs].index[cond]

    #Create an index for this object
    idobj="%04d"%(mobj)

    n=1
    for ind in inds:
        #Get object information
        objp=allsources.loc[ind]
        iimg=int(objp.IMG)
        image=images[iimg]
        zero=image["zero"]
        READOUT=image["header"]["HIERARCH CELL.READNOISE"]

        idimg=idobj+"."+str(n)
        objp["IDIMG"]=idimg
        objp["IDOBJ"]=idobj
        objp["MAG_AUTO"]+=zero

        print("\tPSF fitting for image of object OBJ%s"%idimg)
        n+=1

        #DATE
        obstime=images[iimg]["obstime"]
        exptime=float(images[iimg]["header"]["EXPTIME"])
        parts=obstime.split(".")
        dt=datetime.strptime(parts[0],"%Y-%m-%dT%H:%M:%S")
        fday=(dt.hour+dt.minute/60.0+(dt.second+exptime/2+int(parts[1])/1e6)/3600.0)/24.0
        fday=("%.6f"%fday).replace("0.","")
        objp["DATE"]=dt.strftime("%Y %m %d.")+fday

        #GET DATA IMAGE
        data=rec2arr(images[iimg]["data"])
        x=int(objp.X_IMAGE)
        y=int(objp.Y_IMAGE)
        print("\t\tExpected position:",x,y)
        
        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        #2D PSH FIT
        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        dx=10 #Error in photometry
        dy=10 #Error in photometry
        ws=5  #Number of errors to select for fitting
        xs=np.arange(x-ws*dx,x+ws*dx,1)
        pxs=data[y,x-ws*dx:x+ws*dx,0]
        ys=np.arange(y-ws*dy,y+ws*dy,1)
        pys=data[y-ws*dy:y+ws*dy,x,0]

        sigmax2=10 #Estimated error in X
        sigmay2=10 #Estimated error in y
        meanx=x
        meany=y
        X,Y=np.meshgrid(xs,ys)
        P=data[y-ws*dy:y+ws*dy,x-ws*dx:x+ws*dx,0]

        def gaussianLevel2(tx,ty,level=0.0,amplitude=1.0,
                           meanx=meanx,meany=meany,
                           sigmax2=sigmax2,sigmay2=sigmay2):
            g=amplitude*np.exp(-0.5*((tx-meanx)**2/sigmax2+(ty-meany)**2/sigmay2))
            f=g+level
            return f

        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        #FIT RESULTS
        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        g_init=custom_model(gaussianLevel2)()
        fit=fitting.SLSQPLSQFitter()
        g=fit(g_init,X,Y,P,verblevel=0)
        #print("\t\tResults (level,amplitude,meanx,meany,sigmax,sigmay):\n\t\t\t%s"%str(g.parameters))

        xc=g.meanx.value
        yc=g.meany.value
        sigmam=np.sqrt(g.sigmax2.value+g.sigmay2.value)
        amplitude=g.amplitude.value
        level=g.level.value
        objp["FWHM"]=2.355*sigmam
        objp["X_PSF"]=xc
        objp["Y_PSF"]=yc

        print("\t\tPSF position:",xc,yc)
        print("\t\tFWHM:",objp.FWHM)

        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        #COMPUTE SNR
        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        title="Object %d, %s, %s"%(ind,idimg,obstime)

        ws=5
        x=int(g.meanx.value)
        y=int(g.meany.value)
        dx=int(np.sqrt(g.sigmax2.value))
        dy=int(np.sqrt(g.sigmay2.value))
        xs=np.arange(x-ws*dx,x+ws*dx,1)
        ys=np.arange(y-ws*dy,y+ws*dy,1)
        X,Y=np.meshgrid(xs,ys)
        P=data[y-ws*dy:y+ws*dy,x-ws*dx:x+ws*dx,0]
        Pth=gaussianLevel2(X,Y,
                           level=g.level.value,amplitude=g.amplitude.value,
                           meanx=g.meanx.value,meany=g.meany.value,
                           sigmax2=g.sigmax2.value,sigmay2=g.sigmay2.value)
        D=P-Pth
        noise=D.std()
        objp["SNR"]=g.amplitude.value/noise
        print("\t\tSNR = ",objp.SNR)
        print("\t\tMAG = ",objp.MAG_AUTO)

        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        #PLOT 2D FIT
        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        fig = plt.figure()
        ax3d = fig.add_subplot(111, projection='3d')
        ax3d.plot_wireframe(X,Y,P,lw=0.5)
        ngrid=50
        Xs,Ys=np.meshgrid(np.linspace(xs[0],xs[-1],ngrid),
                          np.linspace(ys[0],ys[-1],ngrid))
        Zs=gaussianLevel2(Xs,Ys,
                          level=g.level.value,amplitude=g.amplitude.value,
                          meanx=g.meanx.value,meany=g.meany.value,
                          sigmax2=g.sigmax2.value,sigmay2=g.sigmay2.value)
        ax3d.plot_surface(Xs,Ys,Zs,cmap='hsv',alpha=0.2)
        ax3d.set_title(title,position=(0.5,1.05),fontsize=10)
        fig.savefig(OUT_DIR+"psf2d-%s.png"%idimg)

        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        #1D PLOT OF PSF FITTING
        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        xs=np.arange(x-ws*dx,x+ws*dx,1)
        pxs=data[y,x-ws*dx:x+ws*dx,0]
        pxts=level+amplitude*np.exp(-0.5*((xs-x)**2/g.sigmax2.value))
        rxs=pxs-pxts

        ys=np.arange(y-ws*dy,y+ws*dy,1)
        pys=data[y-ws*dy:y+ws*dy,x,0]
        pyts=level+amplitude*np.exp(-0.5*((ys-y)**2/g.sigmay2.value))
        rys=pys-pyts

        xt=np.linspace(xs[0],xs[-1],100)
        pt=level+amplitude*np.exp(-0.5*((xt-x)**2/g.sigmax2.value))

        fig,axs=plt.subplots(2,1,sharex=True,gridspec_kw={'height_ratios':[2,1]})
        ax=axs[0]
        ax.plot((xs-x)/np.sqrt(g.sigmax2.value),pxs,'ko')
        ax.plot((ys-y)/np.sqrt(g.sigmay2.value),pys,'ko')
        ax.plot((xt-x)/np.sqrt(g.sigmax2.value),pt,'r-')
        ax.set_xlim((-ws,+ws))
        ax.set_ylim((min(pxs.min(),pys.min()),max(pxs.max(),pys.max())))
        ax.axvspan(-objp.FWHM/2/sigmam,+objp.FWHM/2/sigmam,color='b',alpha=0.2)
        ax.axhspan(0,level,color='k',alpha=0.2)
        ax.set_xticks([])
        legend=""
        legend+="SNR = %.2f\n"%objp.SNR
        legend+="FWHM (arcsec) = %.2f\n"%(objp.FWHM*PXSIZE/ARCSEC)
        legend+="MAG = %+.1f\n"%(objp.MAG_AUTO)
        ax.text(0.95,0.95,legend,
                ha='right',va='top',transform=ax.transAxes,color='k',fontsize=12)
        ax.set_ylabel("Counts")
        ax.set_title("Object %s"%idimg)
        waterMark(ax)

        ax=axs[1]
        ax.plot((xs-x)/np.sqrt(g.sigmax2.value),rxs,'ko')
        ax.plot((ys-y)/np.sqrt(g.sigmay2.value),rys,'ko')
        ax.set_ylim((-level,level))
        ax.axhspan(-noise,noise,color='k',alpha=0.2)
        ax.set_ylabel("Residual (count)")

        fig.tight_layout()
        fig.subplots_adjust(hspace=0)
        fig.savefig(OUT_DIR+"psf1d-%s.png"%idimg)

        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        #EVALUATE IF OBJECT GO
        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        objp["GO"]=1
        objp["REASON"]="Nice"

        #ADD OBJECT
        objects=objects.append(objp,ignore_index=True)

        #break
    #break

objects.to_csv(OUT_DIR+"objects-%s.csv"%CONF.SET,index=False)

