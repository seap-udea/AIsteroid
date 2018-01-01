BRANCH=$(shell bash .getbranch)

clean:
	find . -name "*~" -exec rm {} \;
	find . -name "#*#" -exec rm {} \;

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

