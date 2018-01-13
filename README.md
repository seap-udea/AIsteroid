# AIsteroid

This project is aimed at assiting and eventually automatizing the
process of searching for asteroids in image sets provided by
observatories.

Let's suppose for instance that you have the following set of
observations (credit:
[Pan-STARRS](https://panstarrs.stsci.edu/)/[IASC](http://iasc.hsutx.edu/)):

![alt text](https://github.com/seap-udea/AIsteroid/blob/edu/doc/images/example-raw.gif)

How many moving objects do you dectect in this image? 

If your answer is one, you are a good obsever.  However, if you see
between 2 and 3 objects, you seem to have a trained eye.  But if you
see more than 4, probably you are a machine! (to see the actual number
of moving objects see the image in [this
link](https://raw.githubusercontent.com/seap-udea/AIsteroid/edu/doc/images/example-detection.gif)).

This is precisely the purpose of **AIsteroid**. 

Searching for moving objects in a noisy images (most astronomical
images are very noisy) is a task normally intended for human
brains. With our *super power* to notice small changes in visual
patterns, the task is very well suited for us. This is the way as most
of the asteroids have been discovered in the past and are being
discovered today.

With the advent of powerful computers and clever computational
algorithms such as those belonging to the broad class of **artificial
intelligence** (neural networks, decision trees, deep learning, etc.),
we can now teach machines to perform this kind of task.

In this simple package you will find a series of python scripts (and
ipython notebooks) intended to assist and automatize the searching
process, not for replacing entirely the role of humans, but at least
for easing this process.

Quickstart
----------

If you already have the package and its dependencies (see section
Installation below) the automatized detection is performed in three
simple steps:

1. Get an image set.  They are normally provided in the form of a zip
   file containing 4 or more images in FITS format.  

   **AIsteroid** is provided with at least one image set
   (``data/sets/example.zip``).  Sets must be installed in the
   ``data/sets/`` directory.

   If you are working on a campaign (e.g. All Colombia IASC campaign),
   the campaign coordinator may have provided you a location where
   many image sets are available. 

   To list all the image sets available, run:

   ```
	make listimages
   ```
   
   If you want to list more of them, run:

   ```
	make listimages NUM_SETS=100
   ```

2. Unpack the image set:

   ```
      python unpack.py
   ```

      **NOTE**: Remind that you may run the script in Jupyter using
      the notebook with the same name, ``unpack.ipynb``.

   This command will execute the action in the default image set
   (``example``) or equivalently the set defined in the `file
   ``aisteroid.cfg``.  If you want to change the image set use:

   ```
      python unpack.py "SET='ps1-20181_1_000'"
   ```

   Where the double and single quotation marks should be respected.

3. Extract the position and basic photometric properties of the point
   sources in the image:

   ```
      python extract.py
   ```

4. Detect any moving objects in the image and check which of them may be
   actually asteroids:

   ```
      python detect.py
   ```

5. Perform an astrometric analysis of the image to determine the
   precise position (RA and DEC) of the sources:

   ```
      python astrometry.py
   ```

6. Perform an advanced photometric analysis on the image:

   ```
      python photometry.py
   ```

You may perform all the previous actions at once for a given set using
the abbreviated command:

   ```
      make all
   ```
    
If you want to use a set different to the default one:

   ```
      make all SET=ps1-20181_1_000
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

2. Copy configuration files from templates in ``util/makefile.in`` and
   ``util/aisteroid.cfg``:

   ```
   cp util/makefile.in .
   cp util/aisteroid.cfg .
   ```
   
3. Modify the variables in the file ``makefile.in`` to adjust it to
   your system preferences:

   ```
   PYTHON=python3.5
   ```
   
4. Install the prerequisites:

   a. [Astrometry.net](http://astrometry.net/use.html): download and
      compile from the sources.

   a. [SEXtractor](https://www.astromatic.net/software/sextractor):
      download and compile from the sources.

   b. Python dependencies: using your preferred python run the
      following command to install python dependencies
   
      ```
      python pip -m install astropy matplotlib scikit-image
      ```

6. Test it:
   
   ```
   make test
   ```

   If you want additional details in your test run:

   ```
   make VERBOSE=1 test
   ```

If all the tests are passed you are ready to use **AIsteroid**.

IPython Notebooks
-----------------

You want to run all the procedures using a graphical controled
environment, we have provided several iPython notebook (see for
instance [this
link](https://github.com/seap-udea/AIsteroid/blob/master/AIsteroid.ipynb)). The
difference between the comman line scripts (``*.py`` files) and the
notebooks are that in the latests you will find everything more
explicitely.  Notebooks are great educational tools.

The notebook could be outdated with respect to the main scripts

Known problems
--------------

The package is not perfect.  This are some of the known problems of
the package in the present release.

Releases 
--------

As the package evolves we will report here some of the changes
performed on their components.  Most of these changes attempt to solve
the problems mentioned in the "Known problems" section.

- *Release 0.1*: 
  
  * Initial release.
  * This is a non-usable release.

- *Release 0.2*:
 
  * Educational branch is realeased, ``edu``.  It is intended for
    teaching how to deal with images.

Contributors
------------

- Jorge I. Zuluaga, main developer.
- Sergio Lopez, contributor
- Jonathan Ospina, preparation of training sets.
- Ivan Dario Moreno, preparation of training sets.
- Liliana Piedrahita, preparation of training sets.

Acknowledgements
----------------

The development of this package have been possible thanks to the
participation in the International Asteroid Search Campaign that
provided the example image sets required to test the algorithms.

Special thanks to Enrique Torres from Medellin Planetarium for
introducing the Campaign in Medellin and provided the initial training
and data required to understand the process.

It would be impossible to create this package if the following
previous packages did not exist: astrometry.net, Astrometrica,
astropy.

Copyleft
--------

Jorge I. Zuluaga et al. [)] 2017
