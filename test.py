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
# Alignment procedure
#######################################################
from aisteroid import *

#######################################################
#AUXILIAR VARIABLES
#######################################################
OUT_DIR=CONF.SCR_DIR+CONF.SET+"/"

#######################################################
#SCRIPT
#######################################################
for fimgfile in sorted(glob.glob(OUT_DIR+"*.fits")):
    imgfile=os.path.basename(fimgfile).split(".fits")[0]
    
    dts=[]
    ns=[]
    for dt in range(1,10):
        output,header,data,nsources=SEXtract(OUT_DIR,imgfile,
                                             DETECT_THRESH=dt)
        dts+=[dt]
        ns+=[nsources]

    #Determine 
    m=(np.log10(ns[-1])-np.log10(ns[-5]))/(np.log10(dts[-1])-np.log10(dts[-5]))
    b=np.log10(ns[-1])-m*(np.log10(dts[-1]))

    xs=np.linspace(1,10,10)
    ys=10**(m*np.log10(xs)+b)

    noise_levels=ns[0]-ys[0]
    print(noise_levels)

    fig,axs=plt.subplots()

    axs.plot(dts,ns,'ko')
    axs.plot(xs,ys,'r-')

    axs.set_yscale("log")
    axs.set_xscale("log")
    fig.savefig("detection.png")
    break
