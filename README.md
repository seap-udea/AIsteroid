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

