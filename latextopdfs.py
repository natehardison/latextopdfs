#!/usr/bin/python

import argparse
import csv
import jinja2
import os
import re
import subprocess
import sys
from tempfile import mkdtemp, mkstemp

class PDFGenerator:
    """Generates PDF files from a jinja2 template"""
    def __init__(self, template_path):
        # Split path into dir/name for jinja2
        template_dir, template_name = os.path.split(os.path.abspath(template_path))

        # Set up the jinja2 environment so that it doesn't get confused with other LaTeX markup
        # Credit: http://e6h.de/post/11/
        env = jinja2.Environment(
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
            undefined = jinja2.StrictUndefined,
            loader = jinja2.FileSystemLoader(template_dir)
        )

        # Provide a filter to allow templates to resolve paths relative to their
        # own location in the filesystem
        env.filters['abspath'] = lambda path: os.path.join(template_dir, path)

        # Load the template file into the jinja2 engine
        try:
            self._template = env.get_template(template_name)
        except jinja2.exceptions.TemplateNotFound:
            raise PDFGenerator.Error("%s: No such file or directory" % template_path)
        except jinja2.exceptions.TemplateSyntaxError as e:
            raise PDFGenerator.Error("%s:%d: error: %s" % (e.filename, e.lineno, e.message))

    def generate_pdf(self, substitutions, destination):
        """Makes one PDF file by passing "substitutions" through "template" and
           through pdflatex. Saves the resulting PDF as "destination"."""
        # Pass the LaTeX template through jinja2 templating engine and into the temp file
        # Raises an error if there's an undefined variable in the template
        try:
            tex_source = self._template.render(substitutions).encode('utf8')
        except jinja2.UndefinedError as e:
            raise PDFGenerator.Error("%s: error: %s" % (self._template.filename, e.message))

        # We're going to throw away this file after we make the PDF
        texfile, texfilename = mkstemp(dir=os.curdir)
        os.write(texfile, tex_source)
        os.close(texfile)

        # This is a hack because Python < 3 doesn't support subprocess.DEVNULL
        with open("/dev/null", 'w') as devnull:
            try:
                subprocess.check_call(["pdflatex", "-halt-on-error", texfilename], stdout=devnull)
            except subprocess.CalledProcessError as e:
                os.rename(texfilename + ".log", destination + ".log")
                error_message = "Command 'pdflatex' returned non-zero exit code %d." % e.returncode
                error_message += " Error log saved as %s" % (destination + ".log")
                raise PDFGenerator.Error(error_message)
            else:
                os.rename(texfilename + ".pdf", destination + ".pdf")
            finally:
                os.remove(texfilename)
                if os.path.exists(texfilename + ".aux"):
                    os.remove(texfilename + ".aux")
                if os.path.exists(texfilename + ".log"):
                    os.remove(texfilename + ".log")

    class Error(Exception):
        def __init__(self, message):
            self.message = message
        def __str__(self):
            return repr(self.message)
    # end class Error
# end class PDFGenerator

def csv_substitutions_reader(substitutions_file):
    csv_reader = csv.DictReader(substitutions_file)
    for row in csv_reader:
        yield row

def key_value_substitutions_reader(substitutions_file):
    r = re.compile('("[^"]+"|[^ =]+)\s*=\s*("[^"]*"|[^ ]*)')
    for line_number, line in enumerate(substitutions_file):
        try:
            substitutions = dict([(k.strip('"'), v.strip('"')) for k, v in r.findall(line)])
        except ValueError:
            print >> sys.stderr, "%s:%d: error: Invalid key=value format %s" % (substitutions_file.name, line_number, line)
        else:
            yield substitutions

def main():
    parser = argparse.ArgumentParser(description='Generate PDF files from LaTeX templates')
    parser.add_argument('template', help='the LaTeX template to use')
    parser.add_argument('substitutions', nargs='?', type=argparse.FileType('r'),
        default=sys.stdin, help='the list of substitutions, which can be given\
                                 either in a CSV file or via stdin as key=value\
                                 pairs. Use OutputFile to designate the desired\
                                 destination for each PDF file.')
    args = parser.parse_args()

    try:
        pdf_generator = PDFGenerator(args.template)
    except PDFGenerator.Error as e:
        print >> sys.stderr, e.message
        sys.exit(1)

    # In case the user didn't put in a default destination for each PDF file
    default_destination = os.path.splitext(os.path.basename(args.template))[0]

    # Make a temp folder to do our dirty work; remember current dir so we can
    # get back here later
    original_dir = os.getcwd()
    tmp_folder = mkdtemp()
    os.chdir(tmp_folder)

    if args.substitutions == sys.stdin:
        print "Enter substitutions as key=value pairs. Each line should specify\
 all of the substitutions necessary to create one PDF file."

    if os.path.splitext(args.substitutions.name)[1] == ".csv":
        substitutions_reader = csv_substitutions_reader(args.substitutions)
    else:
        substitutions_reader = key_value_substitutions_reader(args.substitutions)

    for line_number, substitutions in enumerate(substitutions_reader):
        if "OutputFile" in substitutions:
            destination = os.path.splitext(os.path.expanduser(substitutions["OutputFile"]))[0]
        else:
            destination = default_destination + "_%d" % line_number
        destination = os.path.normpath(os.path.join(original_dir, destination))
        try:
            pdf_generator.generate_pdf(substitutions, destination)
        except PDFGenerator.Error as e:
            print >> sys.stderr, e.message + " (from substitutions line %d)" % line_number
        else:
            print "Created %s.pdf" % destination

    os.chdir(original_dir)
    os.rmdir(tmp_folder)

if __name__ == '__main__':
    main()
