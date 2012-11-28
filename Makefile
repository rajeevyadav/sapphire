.PHONY: gh-pages

gh-pages:
ifeq (`git status --porcelain | wc -l`, 0)
	git checkout gh-pages
	git rm -rf .
	git clean -dxf
	git checkout HEAD .nojekyll
	git checkout master doc sapphire
	make -C doc/ html
	mv -fv doc/_build/html/* .
	rm -rf doc/ sapphire/
	git add -A
	git commit -m "Generated gh-pages for `git log master -1 --pretty=short --abbrev-commit`"
	git checkout master
else
	$(error Working tree is not clean, please commit all changes.)
endif
