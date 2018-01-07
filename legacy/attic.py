    print("Average misalignment:",dm)
    ax.plot(s.loc[sa].X_IMAGE,s.loc[sa].Y_IMAGE,'gs',ms=5,mfc='None')
    ax.set_xlim((0,500))
    ax.set_ylim((2000,2500))
    fig.savefig("tmp/image.png")
    exit(0)

        #Showing misalignment
        if i>0:
            fig,axs=plt.subplots(3,1,sharex=True,sharey=True,figsize=(8,10))
            
            ax=axs[0]
            ax.plot(xy[:,0],xy[:,1],
                    'ro',ms=3,mfc='None')
            ax.plot(images[0]["sourcexxy"]["X_IMAGE"],images[0]["sourcexxy"]["Y_IMAGE"],
                    'bv',ms=3,mfc='None')
            ax.set_title("Misalignment respect to image 0")

            ax=axs[1]
            ax.plot(xy[:,0],xy[:,1],
                    'ro',ms=3,mfc='None')
            ax.plot(xya[:,0],xya[:,1],
                    'bo',ms=3,mfc='None')
            ax.set_title("Transformation")

            ax=axs[2]
            ax.plot(xya[:,0],xya[:,1],
                    'ro',ms=3,mfc='None')
            ax.plot(images[0]["sourcexxy"]["X_IMAGE"],images[0]["sourcexxy"]["Y_IMAGE"],
                    'bv',ms=3,mfc='None')
            ax.set_title("Result")

            fig.tight_layout()
            fig.savefig(OUT_DIR+"misal-%d.png"%i)
            
        if i>0:
            fig,axs=plt.subplots(3,1,sharex=True,sharey=True,figsize=(8,10))
            
            ax=axs[0]
            ax.plot(xy[:,0],xy[:,1],
                    'ro',ms=3,mfc='None')
            ax.plot(images[0]["sourcexxy"]["X_IMAGE"],images[0]["sourcexxy"]["Y_IMAGE"],
                    'bv',ms=3,mfc='None')

            ax.set_xlim((400,600))
            ax.set_ylim((2000,2200))

            ax=axs[1]
            ax.plot(xya[:,0],xya[:,1],
                    'ro',ms=3,mfc='None')
            ax.plot(images[0]["sourcexxy"]["X_IMAGE"],images[0]["sourcexxy"]["Y_IMAGE"],
                    'bv',ms=3,mfc='None')

            ax=axs[2]
            ax.plot(xy[:,0],xy[:,1],
                    'ro',ms=3,mfc='None')
            ax.plot(xya[:,0],xya[:,1],
                    'bo',ms=3,mfc='None')

            fig.savefig("tmp/misal-%d.png"%i)

        
        fig,axs=plt.subplots()
        axs.plot(ta[:,0],ta[:,1],'ro',ms=3,mfc='None')
        axs.plot(sa[:,0],sa[:,1],'bs',ms=5,mfc='None')
        axs.set_title("Image %d"%(i+1))
        axs.invert_yaxis()
        fig.savefig(OUT_DIR+"transform.png")
        input()

