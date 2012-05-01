latextopdfs.py
===

Uses a LaTeX template to generate a bunch of PDF files using substitutions
stored in a CSV file or specified on the command line. Helpful for doing a
mail merge since Word doesn't let you save the output to different files.

## Dependencies
  - jinja2: http://jinja.pocoo.org/docs/
  - Only tested on Python 2.7.1

## How to use:

1. Build a LaTeX template, using `\VAR{name}` to indicate where
`latextopdfs.py` should replace text. 

2. Create a CSV file containing the substitutions to make in the LaTeX
template. Each row in the CSV file will produce one PDF.

3. The first row of the CSV file should contain the field names that
correspond to the "name" part of the `\VAR{name}` substitution indicators
in the LaTeX template.

## Help

	$ latextopdfs.py -h