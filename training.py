
# coding: utf-8

# # AIsteroid
# [http://bit.ly/aisteroid](http://bit.ly/aisteroid)
# 
# Este notebook esta destinado a mostrar algunas tareas básicas que pueden realizarse sobre un paquete de imágenes en los que se pueden buscar asteroides

# In[1]:


#Aquí hay modulos y paquetes utiles para las tareas propias del análisis
from aisteroid import *

#Esto es para que Jupyter muestre las imágenes a medida que se van ejecutando los comandos
get_ipython().run_line_magic('matplotlib', 'nbagg')


# In[2]:


#Ver los imagesets que están en el servidor
get_ipython().system('make listimages NUM_SETS=20')


# In[3]:


#Desempaca las imagenes: aquí usaremos uno de los scripts de AIsteroid
get_ipython().system('python3.5 unpack.py "SET=\'example\'"')


# In[4]:


#Ver las imágenes desempacadas
get_ipython().system('ls scratch/example/*.fits')


# In[5]:


#Leer una de las imágenes
hd=fits.open("scratch/example/o8009g0075o.1299949.ch.1991737.XY51.p10.fits")


# In[6]:


#Ver el contenido
hd.info()


# In[7]:


#Leer el encabezado
encabezado=hd[0].header


# In[8]:


encabezado


# In[9]:


#Se puede extraer el valor de una de las variables del encabezado
encabezado["DATE-OBS"]


# In[10]:


#Extraer los datos de la imágen
imagen=hd[0].data


# In[11]:


#Tamaño de la imágen
imagen.shape


# In[12]:


#Mostrar la imágen
fig,axs=plt.subplots(1,1)
axs.imshow(imagen,cmap='gray',vmin=100,vmax=500)


# In[53]:


#Mostrar la imágen en negativo
fig,axs=plt.subplots(1,1)
axs.imshow(imagen,cmap='gray_r',vmin=100,vmax=500)


# In[13]:


#Ver un pedazo de la imagen
fig,axs=plt.subplots(1,1)
axs.imshow(imagen[500:1000,1500:2000],cmap='gray_r',vmin=100,vmax=500)


# In[15]:


#Cargar el archivo de configuración
CFG=[line.rstrip('\n') for line in open("data/sets/example.cfg")]


# In[16]:


CFG


# In[17]:


#Extraer una variable
Config(CFG,"MPCCode")


# In[18]:


#Extraer las fuentes de una imagen usando SEXtractor
output,header,data,nsources=SEXtract("scratch/example/",
                                     "o8009g0075o.1299949.ch.1991737.XY51.p10",
                                     DETECT_THRESH=10)


# In[19]:


nsources


# In[71]:


#Mostrar las fuentes superpuestas sobre la imagen
fig,axs=plt.subplots(1,1)

axs.imshow(imagen,cmap='gray_r',vmin=100,vmax=500)
axs.plot(data["X_IMAGE"]-1,data["Y_IMAGE"]-1,'ro',ms=5,mfc='None')


# In[22]:


#Averiguar el campo de vision de la fotografía
ny,nx=imagen.shape


# In[23]:


ny,nx


# In[24]:


#Propiedades del telescopio y la cámara

#Longitud focal en mm
foco=Config(CFG,"FocalLength")

#Ancho del pixel en mm
px=Config(CFG,"PixelWide")

#Alto del pixel en mm
py=Config(CFG,"PixelHigh")

#Tamaño promedio de los pixels
pm=(px+py)/2


# In[25]:


#Calcula el campo de cada pixel en grados
campo_pixel=np.arctan(pm/foco)*RAD


# In[26]:


campo_pixel


# In[27]:


#Campo del pixel en segundos de arco
campo_pixel/ARCSEC


# In[28]:


#Campo total de la foto
ancho_grados=nx*campo_pixel
alto_grados=ny*campo_pixel


# In[29]:


ancho_grados,alto_grados


# In[45]:


#Obtener las coordenadas de la imagen
ra=encabezado["OBJCTRA"]
dec=encabezado["OBJCTDEC"]
ra,dec


# In[31]:


#Descargar todas las estrellas que están en la misma zona de la imagen
columns=['_RAJ2000','_DEJ2000','R1mag']
v=Vizier(columns=columns)
v.ROW_LIMIT=-1

result=v.query_region("%s %s"%(ra,dec),
                      width=Angle(0.2,"deg"),height=Angle(0.2,"deg"),
                      catalog='USNOB1')


# In[32]:


#Muestre los resultados
result


# In[33]:


#Extrae la primera tabla
result[0]


# In[34]:


#Convierte la tabla en un arreglo normal
estrellas=rec2arr(result[0])
estrellas.shape


# In[35]:


#Extrae solo las estrellas que tengan magnitud>0
condicion=estrellas[:,2]>0
aceptadas=estrellas[condicion]


# In[36]:


aceptadas.shape


# In[37]:


#Mostrar las fuentes superpuestas sobre la imagen
fig,axs=plt.subplots(1,1)

axs.plot(data["ALPHA_J2000"],data["DELTA_J2000"],'ro',ms=5,mfc='None')
axs.plot(aceptadas[:,0],aceptadas[:,1],'b*',ms=2)


# In[39]:


#Obtener las estrellas pero cerca al centro del campo
ras=data["ALPHA_J2000"]
decs=data["DELTA_J2000"]

ra_mitad=ras.mean()
dec_mitad=decs.mean()


# In[40]:


ra_mitad,dec_mitad


# In[46]:


#Convierte RA y DEC a formato sexagesimal
ra=dec2sex(ra_mitad/15,format="string")
dec=dec2sex(dec_mitad,format="string")
ra,dec
ra,dec=('21 04 9.17','-15 35 4.36')


# In[47]:


result=v.query_region("%s %s"%(ra,dec),
                      width=Angle(0.2,"deg"),height=Angle(0.2,"deg"),
                      catalog='USNOB1')


# In[49]:


estrellas=rec2arr(result[0])
aceptadas=estrellas[estrellas[:,2]>0]
aceptadas.shape


# In[50]:


#Mostrar las fuentes superpuestas sobre la imagen
fig,axs=plt.subplots(1,1)

axs.plot(data["ALPHA_J2000"],data["DELTA_J2000"],'ro',ms=5,mfc='None')
axs.plot(aceptadas[:,0],aceptadas[:,1],'b*',ms=2)


# In[58]:


#Para crear una version animada de la imagen es necesario leer todos los fits
imagenes=[]
for archivo in sorted(glob.glob("scratch/example/*.fits")):
    print(archivo)
    hd=fits.open(archivo)
    imagenes+=[hd[0].data]


# In[70]:


#Crear una versión animada de la imagen
fig,axs=plt.subplots(figsize=(8,8))

im=plt.imshow(imagenes[0],animated=True,cmap='gray_r',vmin=100,vmax=500)
tx=axs.text(100,100,"0",color='r')
axs.axis("off")
fig.tight_layout()

def updatefig(i):
    im.set_array(imagenes[i])
    tx.set_text("%d"%i)
    return im,

animation.FuncAnimation(fig,updatefig,frames=range(4),
                        interval=1000,repeat_delay=1000,
                        repeat=True,blit=True)


# In[2]:


#Descarga una imagen del cielo
img = SkyView.get_images(position='22:57:00,62:38:00',
                         survey=['DSS2 Red'],
                         pixels='800,800',
                         coordinates='J2000',grid=True,gridlabels=True)


# In[ ]:


fig,axs=plt.subplots(1,1)
axs.imshow(img[0][0].data)

