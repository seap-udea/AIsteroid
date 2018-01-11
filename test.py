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

VPRINT0("Testing AIsteroid.")
#######################################################
#CONFIGURATION TEST
#######################################################
VPRINT0("Checking configuration")
for key in CONF.__dict__.keys():
    VPRINT1("\t%s='%s'"%(key,CONF.__dict__[key]))
VPRINT0("\tDone.")

#######################################################
#CHECKING DIRECTORIES
#######################################################
VPRINT0("Checking directories")
for key in CONF.__dict__.keys():
    if "_DIR" in key:
        mdir=CONF.__dict__[key]
        if os.path.isdir(mdir):
            VPRINT1("\tDirectory %s='%s' checked"%(key,mdir))
        else:
            error("\tDirectory %s='%s' does not exist"%(key,mdir))
VPRINT0("\tDone.")

VPRINT0("All test passed.")
