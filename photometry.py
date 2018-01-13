
# coding: utf-8

# # AIsteroid
# [http://bit.ly/aisteroid](http://bit.ly/aisteroid)

# In[1]:


from aisteroid import *
get_ipython().run_line_magic('matplotlib', 'nbagg')


# ## Task: Perform astrometry of images

# ### Choose the image set

# In[2]:


if QIPY:
    #listImages() ##See the list of imagesets
    CONF.SET="example" ##Choose your preferred imageset
    #CONF.CFG="example" ##You choose your preferred observatory configuration (example.cfg)
    CONF.OVERWRITE=1 ##Overwrite all previous actions
    CONF.VERBOSE=1 ## Show all outputs
    CONF.SET='ps1-20180107_1_set045'


# #### DO NOT TOUCH IF YOU ARE NOT SURE

# In[3]:


#DO NOT MODIFY THIS LINES
print0("*"*60+"\nPHOTOMETRY OF OBJECTS FOUND IN SET '%s'\n"%CONF.SET+"*"*60)
OUT_DIR=CONF.SCR_DIR+CONF.SET+"/"
CFG=[line.rstrip('\n') for line in open(CONF.SETS_DIR+CONF.CFG+".cfg")]
AIA=dict()
AIA_FILE=OUT_DIR+CONF.SET+".aia"
SET_FILE=CONF.SETS_DIR+CONF.SET+".zip"
PLOT_DIR=OUT_DIR+"plots/"
FLOG=open(OUT_DIR+"photometry.log","a")
SYSOPTS=dict(qexit=[True,FLOG])
if not os.path.isfile(AIA_FILE):
    error("Set '%s' has not been unpacked"%CONF.SET)
else:
    System("cp "+CONF.INPUT_DIR+"analysis/* "+OUT_DIR)
    AIA=pickle.load(open(AIA_FILE,"rb"))
    images=AIA["images"]
    borders=AIA["borders"]
    sources=AIA["sources"]
    objects=AIA["objects"]
    detector=AIA["detector"]
    nimgs=len(images)
    nobj=len(objects)


# ### Photometry & results of photometry

# In[6]:


print0("Photometry of objects")

if nobj>0:
    
    if not "photometry" in AIA.keys() or CONF.OVERWRITE:

        moving=sources[sources.NIMG<2]    
        columns=moving.columns.tolist()+["IDOBJ","IDIMG","DATE"
                                         "SNR","FWHM",
                                         "X_PSF","Y_PSF",
                                         "MAG_MEAN","MAG_MIN","MAG_MAX","MAG_RANGE","MAG_VAR",
                                         "SNR_MEAN","SNR_MIN","SNR_MAX","SNR_RANGE","SNR_VAR"]
        
        photometry=pd.DataFrame(columns=columns)
        iobj=0
        for mobj in range(1,nobj+1):

            #Get sources corresponding to object mobj
            indxs=objects[iobj]
            iobj+=1
            cond=moving.loc[indxs].MOBJ==mobj
            inds=moving.loc[indxs].index[cond]

            #Create an index for this object
            idobj="%04d"%(mobj)

            print1("\tObject %s:"%idobj)
            n=1
            mags=[]
            snrs=[]
            nrel=0
            for ind in inds:

                #Get object information
                objp=sources.loc[ind]
                iimg=int(objp.IMG)
                image=images[iimg]

                idimg=idobj+"."+str(n)
                objp["IDIMG"]=idimg
                objp["IDOBJ"]=idobj
                n+=1

                print1("\t\tPSF fitting for image of object OBJ%s"%idimg)

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
                x=int(objp.X_IMAGE)-1
                y=int(objp.Y_IMAGE)-1
                print1("\t\t\tExpected position:",x,y)

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

                def gaussianLevel2(tx,ty,level=100.0,amplitude=100.0,
                                   meanx=meanx,meany=meany,
                                   sigmax2=sigmax2,sigmay2=sigmay2):
                    g=amplitude*np.exp(-0.5*((tx-meanx)**2/sigmax2+(ty-meany)**2/sigmay2))
                    f=g+level
                    return f

                #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                #FIT RESULTS
                #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                try:
                    g_init=custom_model(gaussianLevel2)()
                    fit=fitting.SLSQPLSQFitter()
                    g=fit(g_init,X,Y,P,verblevel=0)
                except:
                    print1("\t\t\tFit has failed. Skipping")
                    continue

                xc=g.meanx.value
                yc=g.meany.value
                sigmam=np.sqrt(g.sigmax2.value+g.sigmay2.value)

                #If sigmam is too large abort
                amplitude=g.amplitude.value
                level=g.level.value
                objp["FWHM"]=2.355*sigmam
                
                if objp["FWHM"]>10*CONF.RADIUS:
                    print1("\t\t\tThis is an spurious image. skipping.")
                    continue
                
                objp["X_PSF"]=xc
                objp["Y_PSF"]=yc

                print1("\t\t\tPSF position:",xc,yc)
                print1("\t\t\tFWHM:",objp.FWHM)
                
                #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                #COMPUTE SNR
                #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                title="Object %d, %s, %s"%(ind,idimg,obstime)

                try:
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
                    print1("\t\t\tSNR = ",objp.SNR)
                    print1("\t\t\tMAG = %.1f +/- %.2f"%(objp.MAG_ASTRO,objp.ERR_MAG_ASTRO))
                except:
                    objp.SNR=-1.0
                mags+=[objp.MAG_ASTRO]
                snrs+=[objp.SNR]

                if objp.SNR<0:
                    print1("\t\t\tThis is an spurious image. skipping.")
                    continue
                    
                nrel+=1
                
                #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                #PLOT 2D FIT
                #&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
                if CONF.QPLOT and objp.SNR>0:
                    plt.ioff()
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
                    fig.savefig(PLOT_DIR+"psf2d-%s.png"%idimg)

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
                    legend+="FWHM (arcsec) = %.2f\n"%(objp.FWHM*detector.PXSIZE/ARCSEC)
                    legend+="MAG = %+.1f\n"%(objp.MAG_ASTRO)
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
                    fig.savefig(PLOT_DIR+"psf1d-%s.png"%idimg)

                #ADD OBJECT
                photometry=photometry.append(objp,ignore_index=True)
                
            if len(photometry)>0:
                mags=np.array(mags)
                snrs=np.array(snrs)

                #Storing object properties
                photometry.loc[photometry.IDOBJ==idobj,"MAG_MIN"]=mags.min()
                photometry.loc[photometry.IDOBJ==idobj,"MAG_MAX"]=mags.max()
                photometry.loc[photometry.IDOBJ==idobj,"MAG_RANGE"]=mags.max()-mags.min()
                photometry.loc[photometry.IDOBJ==idobj,"MAG_MEAN"]=mags.mean()
                photometry.loc[photometry.IDOBJ==idobj,"MAG_VAR"]=mags.std()

                photometry.loc[photometry.IDOBJ==idobj,"SNR_MIN"]=snrs.min()
                photometry.loc[photometry.IDOBJ==idobj,"SNR_MAX"]=snrs.max()
                photometry.loc[photometry.IDOBJ==idobj,"SNR_RANGE"]=snrs.max()-snrs.min()
                photometry.loc[photometry.IDOBJ==idobj,"SNR_MEAN"]=snrs.mean()
                photometry.loc[photometry.IDOBJ==idobj,"SNR_VAR"]=snrs.std()

                print1("\t\tMag: [%.1f,%.1f:%.1f] %.1f +/- %.2f"%(mags.min(),mags.max(),
                                                                 mags.max()-mags.min(),
                                                                 mags.mean(),mags.std()))
                print1("\t\tSNR: [%.1f,%.1f:%.1f] %.1f +/- %.2f"%(snrs.min(),snrs.max(),
                                                                 snrs.max()-snrs.min(),
                                                                 snrs.mean(),snrs.std()))
                photometry.to_csv(OUT_DIR+"photometry-%s.csv"%CONF.SET,index=False)
                print0("\t\tPhotometry for object %d completed"%n)
                print0("\t\tNumber of images relevant:%d"%nrel)
            else:
                print1("\t\tNo significative image of object %d detected."%n)
                
        AIA["photometry"]=photometry
        pickle.dump(AIA,open(AIA_FILE,"wb"))
    else:
        print("\tPhotometry already performed")
        photometry=AIA["photometry"]
else:
    error("\tNo objects detected")


# ### Save objects

# In[5]:


selfile=OUT_DIR+"select-%s.txt"%CONF.SET

print0("Generating selection file")

if len(photometry)>0:
    if not os.path.isfile(selfile) or CONF.OVERWRITE:
        f=open(selfile,"w")

        typo="C"
        mago="R"
        MPCCODE=Config(CFG,"MPCCode")

        lines=""
        header="%-5s|%-68s|%-10s|%-10s|\n"%("ID","REPORT","SNR","MAG_RANGE")
        f.write(header)
        f.write("-"*len(header)+"\n")
        for ind in photometry.index:
            objp=photometry.loc[ind]
            parts=str(objp.IDIMG).split(".")
            idimg="%04d.%1d"%(int(parts[0]),int(parts[1]))
            idobj="%s%s"%(CONF.TEAM,objp.IDOBJ)

            mag=objp.MAG_ASTRO
            ras=dec2sex(objp.RA/15)
            decs=dec2sex(objp.DEC)

            entry="%3s%1s%02d %02d %6.3f%02d %02d %5.2f%13.1f%2s%9s"%                (typo,
                 objp.DATE,
                 int(ras[0]),int(ras[1]),ras[2],
                 int(decs[0]),int(decs[1]),decs[2],
                 mag,
                 mago,
                 MPCCODE
                )

            line="%-5s|%-68s|%-10.2f|%-10.2f|\n"%                (objp.IDOBJ,
                 entry,
                 objp.SNR,
                 objp.MAG_RANGE
                )
            lines+=line

        if len(photometry.index)==0:
            f.write("NO MOVING OBJECTS DETECTED\n\n")
        else:
            f.write(lines)
        f.close()
    else:
        print("\tSelection file already generated")
    out=System("cat "+selfile,True)
    print("Done.")
else:
    print("\tNo significative object detected")


# In[41]:


print0("Task completed.")
FLOG.close()

