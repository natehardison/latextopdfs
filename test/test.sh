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

for template in ${templates[@]} ; do
  ../latextopdfs.py "../../letters/${template}.tex" test_substitutions > /dev/null
  check
done

echo "All good!"