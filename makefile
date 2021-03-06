include makefile.in
BRANCH=$(shell bash .getbranch)

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

