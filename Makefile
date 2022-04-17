.PHONY: clean build upload

clean:
	rm -rf dist/ rear.egg-info/

build:
	python -m build

upload:
	twine upload dist/*
