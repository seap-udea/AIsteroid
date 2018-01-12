#######################################################
#           _____     _                 _     _       #
#     /\   |_   _|   | |               (_)   | |      # 
#    /  \    | |  ___| |_ ___ _ __ ___  _  __| |      #
#   / /\ \   | | / __| __/ _ \ '__/ _ \| |/ _` |      #
#  / ____ \ _| |_\__ \ ||  __/ | | (_) | | (_| |      #
# /_/    \_\_____|___/\__\___|_|  \___/|_|\__,_|      #
# Artificial Intelligence in the Search for Asteroids #
# Jorge I. Zuluaga et al. [)] 2017                    #
# http://bit.ly/aisteroid                             #
#######################################################
# Test package
#######################################################
from aisteroid import *

print0("Testing AIsteroid.")

#######################################################
#CONFIGURATION TEST
#######################################################
print0("Checking configuration")
for key in CONF.__dict__.keys():
    print1("\t%s='%s'"%(key,CONF.__dict__[key]))
print0("\tDone.")

#######################################################
#CHECKING DIRECTORIES
#######################################################
print0("Checking directories")
for key in CONF.__dict__.keys():
    if "_DIR" in key:
        mdir=CONF.__dict__[key]
        if os.path.isdir(mdir):
            print1("\tDirectory %s='%s' checked"%(key,mdir))
        else:
            error("\tDirectory %s='%s' does not exist"%(key,mdir))
print0("\tDone.")

print0("All test passed.")
