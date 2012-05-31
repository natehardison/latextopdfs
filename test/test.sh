#!/bin/bash

templates=( ca grader producer simultaneous statistician tf )

check ()
{
  if [ -e "Nate Hardison.pdf" ] ; then
    rm -f "Nate Hardison.pdf"
  else
    echo "Uh oh! Something went wrong..."
    exit 1
  fi
}

# TODO: check the following:
# (no arguments) ../latextopdfs.py
# (bad template filename) ../latextopdfs.py nonexistenttemplate
# (bad subs filename) ../latextopdfs.py sample.tex nonexistentsubsfile
# (empty subs file) ../latextopdfs.py sample.tex empty.txt
# (malformed CSV subs file) ../latextopdfs.py sample.tex bad.csv
# (malformed generic subs file) ../latextopdfs.py sample.tex bad.txt

for template in ${templates[@]} ; do
  ../latextopdfs.py "../../letters/${template}.tex" test_substitutions > /dev/null
  check
done

echo "All good!"