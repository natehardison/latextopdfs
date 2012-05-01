#!/usr/bin/python

import argparse
import csv
import os
import sys
from subprocess import call
from tempfile import mkdtemp, mkstemp
from jinja2 import Environment, FileSystemLoader

# Makes one PDF file by passing "substitutions" through "template"
# and through pdflatex. Stores the PDF file in "destination".
def make_one_pdf(template, substitutions, destination):
    # We're going to throw away this file after we make the PDF
    texfile, texfilename = mkstemp(dir=os.curdir)

    # Pass the TeX template through jinja2 templating engine and into the temp file
    os.write(texfile, template.render(substitutions).encode('utf8'))
    os.close(texfile)

    # Compile the TeX file with PDFLaTeX
    call(['pdflatex', texfilename])

    os.rename(texfilename + '.pdf', destination + '.pdf')

    # These are just trash now
    os.remove(texfilename)
    os.remove(texfilename + '.aux')
    os.remove(texfilename + '.log')


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
        loader = FileSystemLoader(template_dir)
    )

    # Load the template file into the jinja2 engine
    return env.get_template(template_name)


def parse_substitutions(args):
    # Try parsing the args first as a filename
    if (len(args) == 1 and
        os.path.exists(args[0]) and
        os.path.isfile(args[0])):
        return (args[0], True)
    
    # Otherwise, assume that the user passed in a bunch of key=value pairs    
    try:
        return (dict([sub.split('=') for sub in args]), False)
    except:
        subs = ' '.join(args)
        print "Invalid substitutions \"%s\" Please use valid key=value format." % subs
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description='Generate PDF files from LaTeX templates')
    parser.add_argument('template', help='the LaTeX template to use')
    parser.add_argument('substitutions', nargs='+',
        help='the list of substitutions, which can be given either in a CSV file or on the\
              command line as KEY=VALUE pairs')
    parser.add_argument('-o', '--output-directory', default=os.curdir,
        help='the output directory for the PDFs (defaults to current)')
    args = parser.parse_args()

    # Ensure we got a valid template file (should have .tex extension), and
    # it should actually be a file.
    if (os.path.splitext(args.template)[1] != '.tex' or not
        os.path.exists(args.template) or not
        os.path.isfile(args.template)):
        print "Invalid template file \"%s.\" Template must be a valid LaTeX file with .tex extension." % args.template
        sys.exit(1)

    # User might have passed in a relative path for template
    # and we need its parent dir anyway for the jinja2 engine
    template_path = os.path.abspath(args.template)
    template = load_template(template_path)

    substitutions, use_file = parse_substitutions(args.substitutions)
    
    # User might have passed in a relative path for destination
    dest_folder = os.path.abspath(args.output_directory)

    # Make a temp folder to do our dirty work; remember current dir so we can
    # get back here later
    original_dir = os.getcwd()
    tmp_folder = mkdtemp()
    os.chdir(tmp_folder)

    if use_file:
        with open(substitutions, 'rU') as subs_file:
            # DictReader pulls out each row of CSV as a dict and
            # uses first row as keys
            subs_file_reader = csv.DictReader(subs_file)

            # Each row of substitutions in the CSV builds one PDF
            for subs_row in subs_file_reader:
                destination = os.path.join(dest_folder, subs_row['Destination'])
                subs_row['TemplateDir'] = os.path.dirname(template_path)
                make_one_pdf(template, subs_row, destination)

    else:
        if 'Destination' in substitutions:
            dest_file = substitutions['Destination']
        else:
            template_name = os.path.basename(args.template)
            dest_file = os.path.splitext(template_name)[0]
        destination = os.path.join(dest_folder, dest_file)
        substitutions['TemplateDir'] = os.path.dirname(template_path)
        make_one_pdf(template, substitutions, destination)

    os.chdir(original_dir)
    os.rmdir(tmp_folder)

    print "Success! Files stored in %s." % os.path.abspath(dest_folder)


if __name__ == '__main__':
    main()