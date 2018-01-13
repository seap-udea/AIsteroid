include makefile.in
BRANCH=$(shell bash .getbranch)
VERBOSE=0
NUM_SETS=10
CONVERT=$(shell ls *.ipynb)

all:
	@-$(PYTHON) unpack.py "SET='$(SET)'"
	@-$(PYTHON) extract.py "SET='$(SET)'"
	@-$(PYTHON) detect.py "SET='$(SET)'"
	@-$(PYTHON) astrometria.py "SET='$(SET)'"
	@-$(PYTHON) photometry.py "SET='$(SET)'"

branch:
	@-echo $(BRANCH)

convert:
	bash util/convert.sh $(CONVERT)

test:
	@-$(PYTHON) test.py VERBOSE=$(VERBOSE)

%:
	@-$(PYTHON) aisteroid.py NUM_SETS=$(NUM_SETS) $@=1

aisteroid:
	@-$(PYTHON) extract.py
	@-$(PYTHON) detect.py
	@-$(PYTHON) photometry.py
	@-$(PYTHON) astrometry.py
	@-$(PYTHON) report.py

clean:
	find . -name "*~" -exec rm {} \;
	find . -name "#*#" -exec rm {} \;
	@-rm -r __pycache__
	@-rm *.pyc

merge:	
	@echo "Merging branches..."
	@-make master
	@-git merge dev

commit:
	@echo "Commiting..."
	@-git commit -am "Commit"
	@-git push origin $(BRANCH)

pull:
	@echo "Pulling latest version..."
	@-git reset --hard HEAD
	@-git pull origin $(BRANCH)

pack:
	@echo "Packing data..."
	@bash .store/pack.sh pack

unpack:
	@echo "Unpacking data..."
	@bash .store/pack.sh unpack

