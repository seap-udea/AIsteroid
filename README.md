# AIsteroid

This project is aimed at automatizing the process of searching for
asteroids in image sets provided by observatories.

Let's suppose for instance that you have the following set of
observations (credit:
[Pan-STARRS](https://panstarrs.stsci.edu/)/[IASC](http://iasc.hsutx.edu/)):

![alt text](https://raw.githubusercontent.com/seap-udea/AIsteroid/master/images/example-raw.gif)

How many moving objects do you dectect in this image? 

If your answer is one, you are a good obsever.  However, if you see
between 1 and 3 objects, you seem to have a trained eye.  But if you
see 4, probably you are a machine! (to see the actual number of moving
objects see the image in [this
link](https://raw.githubusercontent.com/seap-udea/AIsteroid/master/images/example-detection.gif)).

This is precisely the purpose of **AIsteroid**. 

Searching for moving objects in a noisy images (most astronomical
images are very noisy) is a task normally intended for human
brains. With our super-power to notice small changes in visual
patterns, the task is very well suited for us. This is the way as most
of the asteroids have been discovered in the past and are being
discovered today.

With the advent of powerful computers and clever computational
algorithms such as those belonging to the broad class of **artificial
intelligence** (neural networks, decision trees, deep learning, etc.),
we can now teach machines to perform this kind of task.

In this simple package you will find a series of python scripts (and
ipython notebooks) intended to automatize the searching process, not
for replacing entirely the role of humans, but at least for ease this
process.

Quickstart
----------

If you already have the package and its dependencies (see section
Installation below) the automatized detection is performed in three
simple steps:

1. Get an image set.  They are normally provided in the form of a zip
   file containing 4 or more images in FITS format.  The package is
   provided with at least one image set (``data/sets/example.zip``).
   Sets must be installed in the ``data/sets/`` directory.

2. Provide a configuration file for the observations.  This file is in
   the format of [astrometrica](http://www.astrometrica.at).  The
   package is provided with an example file,
   ``data/sets/example.cfg``, corresponding to Pan-STARRS telescope.

3. Edit the configuration file, ``aisteroid.cfg``:

   ```
      SET="example" #Name of the zip file containing the observation set
      CFG="example" #Name of the configuration file
      TEAM="NEA" #Name of the team performing the observations
   ```

4. Run the astrometry procedure:
   
   ```
   python astometry.py
   ```
   
5. Run the detection procedure:

   ```
   python detect.py
   ```

5. Run the photometry procedure:

   ```
   python photometry.py
   ```
   
6. Create a MPC report:

   ```
   python report.py
   ```
   
If your are confident of your data you may perform the whole procedure
at once using:

```
make aisteroid
```

And voila! your asteroids must be detected!. The main output of this
procedure is the following image:

![alt text](https://raw.githubusercontent.com/seap-udea/AIsteroid/master/images/example-detection.gif)

Additionally the package prepare an MPC report
``data/reports/example-MPCReport.txt`` looking like this:

```
COD F51
OBS N. Primak, A. Schultz, S. Watters, J. Thiel, T. Goggia
MEA J.Ospina, L. Piedraita, I.Moreno, S.Lopez, J. Zuluaga (NEA, Colombia)
TEL 1.8-m f/4.4 Ritchey-Chretien + CCD
ACK MPCReport file updated 2018.01.03 20:35:29
NET PPMXL

Image set: ps1-20170913_1_set142

     NEA0001  C2017 09 13.31597121 03 57.251-15 33 47.80         -9.5 R      F51
     NEA0001  C2017 09 13.32958521 03 56.806-15 33 45.55         -9.1 R      F51
     NEA0001  C2017 09 13.34318521 03 56.395-15 33 43.21         -9.0 R      F51
     NEA0001  C2017 09 13.35677121 03 55.994-15 33 40.71         -8.8 R      F51
     NEA0002  C2017 09 13.31597121 04 14.300-15 33 49.07        -10.2 R      F51
     NEA0002  C2017 09 13.32958521 04 13.933-15 33 51.06        -10.1 R      F51
     NEA0002  C2017 09 13.34318521 04 13.590-15 33 53.18        -10.1 R      F51
     NEA0002  C2017 09 13.35677121 04 13.275-15 33 55.24        -10.1 R      F51
     NEA0003  C2017 09 13.31597121 03 57.134-15 31 44.66         -8.6 R      F51
     NEA0003  C2017 09 13.32958521 03 56.751-15 31 46.68         -8.1 R      F51
     NEA0003  C2017 09 13.34318521 03 56.416-15 31 49.01         -8.1 R      F51
     NEA0003  C2017 09 13.35677121 03 56.066-15 31 51.37         -8.0 R      F51
     NEA0004  C2017 09 13.31597121 04 12.090-15 31 23.98         -9.7 R      F51
     NEA0004  C2017 09 13.32958521 04 11.596-15 31 25.73         -9.6 R      F51
     NEA0004  C2017 09 13.34318521 04 11.132-15 31 27.58         -9.6 R      F51
     NEA0004  C2017 09 13.35677121 04 10.694-15 31 29.46         -9.7 R      F51
     NEA0005  C2017 09 13.31597121 03 57.118-15 29 59.50        -10.6 R      F51
     NEA0005  C2017 09 13.32958521 03 56.733-15 30  2.86        -10.5 R      F51
     NEA0005  C2017 09 13.34318521 03 56.371-15 30  6.46        -10.5 R      F51
     NEA0005  C2017 09 13.35677121 03 55.992-15 30 10.47        -10.4 R      F51
----- end -----
```

Downloading and installating
----------------------------

In order to get the package you need to download it and installing all
the required prerrequisites.  For this purpose follow the procedure
below:

1. Clone the package:

   ```
   git clone https://github.com/seap-udea/AIsteroid.git   
   ```

2. Create a ``makefile.in`` from the provided template:

   ```
   cp makefile.in.temp makefile.in
   ```
   
3. Modify the variables in the file ``makefile.in`` to adjust it to
   your system preferences:

   ```
   PYTHON=python3.5
   ```
   
4. Install the prerequisites:

   a. [Astrometry.net](http://astrometry.net/use.html): download and
      compile from the sources.

   b. Python dependencies: using your preferred python run the
      following command to install python dependencies
   
      ```
      python pip -m install astropy matplotlib 
      ```

5. Unpack large data sets:

   ```
   make unpack
   ```

6. Test:
   
   ```
   make test
   ```

If all the tests are passed you are ready to use **AIsteroid**.

Known problems
--------------

The package is not entirely perfect.

Acknowledgements
----------------

The development of this package have been possible thanks to the
participation in the International Asteroid Search Campaign that
provided the example image sets required to test the algorithms.

Special thanks to Enrique Torres from Medellin Planetarium for
introducing the Campaign in Medellin and provided the initial training
and data required to understand the process.

Copyleft
--------

Jorge I. Zuluaga [)] 2017
