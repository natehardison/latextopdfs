latextopdfs.py
===

Uses a LaTeX template to generate a bunch of PDF files using substitutions
stored in a CSV file or specified on the command line. Helpful for doing a mail
merge since Word doesn't let you save the output to different files.

## Dependencies
- jinja2: http://jinja.pocoo.org/docs/ 
- Python 2.7.1 (not tested on anything else)

## How to use:

1. Build a LaTeX template using modified Jinja syntax (so that it
plays nicely with LaTeX syntax). The syntax changes are as follows:

* `\VAR{foo}` specifies a variable called `foo`.
* `\BLOCK{}` defines a block of Jinja template code.
* `\#{}` defines a comment; `%#` turns the whole line into a comment
* Refer to the Jinja docs at http://jinja.pocoo.org/docs/ for more info.

2. Create a CSV file containing the variable to make in the LaTeX template.
Each row in the CSV file will produce one PDF.

3. For every variable named `foo`, there should be a corresponding substitution
in the CSV file. The first row of the CSV file should contain the names of all
of the variables in the template file (e.g. if the template has variables
`FullName` and `Address`, the CSV file's first row should have columns titled
FullName and Address). These names need not be in any particular order.

4. Make sure to include a column called Destination that specifies the output
filename for each PDF!

5. Each subsequent row in the CSV file should contain the variable
substitutions for a single PDF.

6. Run the code as follows:

	./latextopdfs.py <template-file> <substitutions-file>

6. You can also specify the fields directly on the command line using
`key=value` syntax. This only works for generating one file from your template
though!

	./latextopdfs.py <template-file> <key1=val1> <key2=val2> ...

## Help

	$ latextopdfs.py -h
