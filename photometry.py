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

#############################################################
#PERFORM PHOTOMETRY ON DETECTED OBJECTS
#############################################################

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#PSF FITING
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
objects=pd.DataFrame(columns=["IDOBJ","IDIMG",
                              "SNR","FWHM",
                              "FLUX_AUTO","MAG_AUTO",
                              "X_PSF","Y_PSF",
                              "FLUX_PSF","MAG_PSF",
                              "RA","DEC",
                              "DATE"])
for mobj in range(1,nobj+1):
    cond=allsources.loc[indxs].MOBJ==mobj
    inds=allsources.loc[indxs].index[cond]
    idobj="%s%04d"%(TEAM,mobj)
    n=1
    objp=pd.Series(dict(IDOBJ="",IDIMG="",
             SNR=0,FWHM=0,
             FLUX_AUTO=0,MAG_AUTO=0,
             X_PSF=0,Y_PSF=0,
             FLUX_PSF=0,MAG_PSF=0,
             RA="",DEC="",
             DATE=""))

    for ind in inds:
        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        #GETTING OBJECT INFORMATION
        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        obj=allsources.loc[ind]
        iimg=int(obj.IMG)
        obstime=images[iimg]["obstime"]
        props=imageProps(images[iimg],cfg)
        pxsize=(props[0]+props[1])/2/ARCSEC
        mag=allsources.loc[ind].MAG_AUTO
        flux=allsources.loc[ind].FLUX_AUTO
        ras=dec2sex(allsources.loc[ind].RA/15)
        decs=dec2sex(allsources.loc[ind].DEC)
        idimg=idobj+"."+str(n)
        n+=1

        #DATE
        exptime=float(images[iimg]["header"]["EXPTIME"])
        obstime=images[iimg]["obstime"]
        parts=obstime.split(".")
        dt=datetime.strptime(parts[0],"%Y-%m-%dT%H:%M:%S")
        fday=(dt.hour+dt.minute/60.0+(dt.second+exptime/2+int(parts[1])/1e6)/3600.0)/24.0
        fday=("%.6f"%fday).replace("0.","")
        datet=dt.strftime("%Y %m %d.")+fday

        objp.IDOBJ=idobj
        objp.IDIMG=idimg
        objp.MAG_AUTO=mag
        objp.FLUX_AUTO=flux
        objp.RA=ras
        objp.DEC=decs
        objp.DATE=datet

        data=rec2arr(images[iimg]["data"])
        x=int(obj.X_IMAGE)
        y=int(obj.Y_IMAGE)

        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        #DATA TO FIT
        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        dx=10
        dy=10
        ws=5
        xs=np.arange(x-ws*dx,x+ws*dx,1)
        pxs=data[y,x-ws*dx:x+ws*dx,0]
        ys=np.arange(y-ws*dy,y+ws*dy,1)
        pys=data[y-ws*dy:y+ws*dy,x,0]

        sigmax2=10
        sigmay2=10
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
        g=fit(g_init,X,Y,P,verblevel=1)
        print("Solution:");print(g)

        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        #PLOT FIT 2D
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
        SNR=g.amplitude.value/noise
        print("SNR(2D) = ",SNR)
        objp.SNR=SNR

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

        fig.savefig(OUT_DIR+"psf2d-obj%3d.png"%ind)

        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        #PLOT 1D OF PSF FITTING
        #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
        xc=g.meanx.value
        yc=g.meany.value
        sigmam=np.sqrt(g.sigmax2.value+g.sigmay2.value)
        amplitude=g.amplitude.value
        level=g.level.value
        FWHM=2.355*sigmam

        objp.FWHM=FWHM
        objp.X_PSF=xc
        objp.Y_PSF=yc

        ds=[]
        fs=[]
        ps=[]
        for i,x in enumerate(xs):
            for j,y in enumerate(ys):
                ps+=[P[i,j]]
                d=np.sqrt((x-xc)**2+(y-yc)**2)
                ds+=[d]
        dts=np.linspace(min(ds),max(ds),100)
        gs=amplitude*np.exp(-0.5*(dts**2/sigmam**2))
        fs=gs+level

        fig=plt.figure()
        ax=fig.gca()

        ax.plot(ds,ps,'ko')
        ax.plot(dts,fs,'r-')

        ax.set_xlim((0,max(ds)))
        ax.set_ylim((min(ps),max(ps)))

        ax.axvline(FWHM,color='b',ls='dashed',alpha=0.2)
        ax.axhspan(0,level,color='k',alpha=0.2)

        xls=[]
        for x in ax.get_xticks():
            xls+=["%.1f"%(x*pxsize)]
        ax.set_xticklabels(xls)
        
        ax.set_title(title)
        legend=""
        legend+="SNR = %.2f\n"%SNR
        legend+="FWHM (arcsec) = %.2f\n"%(FWHM*pxsize)
        legend+="MAG = %+.1f\n"%(mag)

        ax.text(0.95,0.95,legend,
                ha='right',va='top',transform=ax.transAxes,color='k',fontsize=12)

        ax.set_xlabel("arcsec")
        ax.set_ylabel("Counts")

        fig.savefig(OUT_DIR+"psf1d-obj%3d.png"%ind)

        #ADD OBJECT
        objects=objects.append(objp,ignore_index=True)
        break
    break

print(objects)

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#FILTER OBJECTS ACCORDING TO MPC THRESHOLDS
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

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
