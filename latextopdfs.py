#!/usr/bin/python

import argparse
import csv
import os
import sys
from subprocess import call
from tempfile import mkdtemp, mkstemp
from jinja2 import Environment, FileSystemLoader, StrictUndefined, UndefinedError

# Makes one PDF file by passing "substitutions" through "template"
# and through pdflatex.
def make_one_pdf(template, substitutions, original_dir):
    # We're going to throw away this file after we make the PDF
    texfile, texfilename = mkstemp(dir=os.curdir)

    # Add in the template file directory as a variable so that the template
    # can locate any resources referenced from it (e.g. image files)
    substitutions['TemplateDirectory'] = os.path.dirname(template.filename)

    # Pass the TeX template through jinja2 templating engine and into the temp file
    # Raises an error if there's an undefined variable in the template
    try:
        os.write(texfile, template.render(substitutions).encode('utf8'))
    except UndefinedError as error:
        print "Error processing template: %s." % error.message
        sys.exit(0)
        
    os.close(texfile)
    
    call(['pdflatex', texfilename])

    # There's got to be a better way to do this...
    if 'Destination' in substitutions:
        destination = os.path.expanduser(substitutions['Destination'])
    else:
        destination = template.name

    if not os.path.isabs(destination):
        destination = os.path.normpath(os.path.join(original_dir, destination))

    destination = os.path.splitext(destination)[0]

    os.rename(texfilename + '.pdf', destination + '.pdf')

    # These are just trash now
    os.remove(texfilename)
    os.remove(texfilename + '.aux')
    os.remove(texfilename + '.log')

    return destination


def load_template(template_path):
    # Split path into name/dir for jinja2
    template_name = os.path.basename(template_path)
    template_dir = os.path.dirname(template_path)

    # Set up the jinja2 environment so that it doesn't get
    # confused with other LaTeX markup
    # Credit: http://e6h.de/post/11/
    env = Environment(
        block_start_string = '\BLOCK{',
        block_end_string = '}',
        variable_start_string = '\VAR{',
        variable_end_string = '}',
        comment_start_string = '\#{',
        comment_end_string = '}',
        line_statement_prefix = '%-',
        line_comment_prefix = '%#',
        trim_blocks = True,
        autoescape = False,
        undefined = StrictUndefined,
        loader = FileSystemLoader(template_dir)
    )

    # Load the template file into the jinja2 engine
    return env.get_template(template_name)


def parse_substitution_args(sub_args):
    # Try parsing the args first as a filename
    if (len(sub_args) == 1 and
        os.path.exists(sub_args[0]) and
        os.path.isfile(sub_args[0])):
        return (sub_args[0], True)
    
    # Otherwise, assume that the user passed in a bunch of key=value pairs    
    try:
        return (dict([arg.split('=') for arg in sub_args]), False)
    except:
        print "Invalid substitutions \"%s\" Please use valid key=value format." % ' '.join(sub_args)
        sys.exit(1)

def validate_template_file(template):
    return (os.path.splitext(template)[1] == '.tex' and
            os.path.exists(template) and
            os.path.isfile(template))

def main():
    parser = argparse.ArgumentParser(description='Generate PDF files from LaTeX templates')
    parser.add_argument('template', help='the LaTeX template to use')
    parser.add_argument('substitutions', nargs='+',
        help='the list of substitutions, which can be given either in a CSV\
              file or on the command line as key=value pairs. Use\
              Destination=path/to/file to specify the destination of the output\
              file relative to the current directory')
    args = parser.parse_args()

    # Ensure we got a valid template file (should have .tex extension), and it
    # should actually be a file.
    if not validate_template_file(args.template):
        print "Invalid template file \"%s.\" Template must be a valid LaTeX file with the .tex extension." % args.template
        sys.exit(1)

    # User might have passed in a relative path for template and we need its
    # parent dir anyway for the jinja2 engine
    template = load_template(os.path.abspath(args.template))

    # If use_fule = True, then substitutions will be a CSV file containing the
    # substitutions. Otherwise, substitutions is a dict containing the args
    # passed in on the command line.
    substitutions, use_file = parse_substitution_args(args.substitutions)

    # Make a temp folder to do our dirty work; remember current dir so we can
    # get back here later
    original_dir = os.getcwd()
    tmp_folder = mkdtemp()
    os.chdir(tmp_folder)

    if use_file:
        with open(substitutions, 'rU') as subs_file:
            subs_file_reader = csv.DictReader(subs_file)
            for subs_row in subs_file_reader:
                destination = make_one_pdf(template, subs_row, original_dir)
    else:
        destination = make_one_pdf(template, substitutions, original_dir)

    os.chdir(original_dir)
    os.rmdir(tmp_folder)

    print "File(s) stored in %s." % os.path.dirname(destination)    


if __name__ == '__main__':
    main()