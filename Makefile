.PHONY: clean build upload

clean:
	rm -rf build/ dist/ rear.egg-info/

build:
	python setup.py sdist bdist_wheel

upload:
	twine upload dist/*
