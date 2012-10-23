"""
Based on latex2png.py from Stuart Rackham

AUTHOR
	Written by Stuart Rackham, <srackham@gmail.com>
	The code was inspired by Kjell Magne Fauske's code:
	http://fauskes.net/nb/htmleqII/

	See also:
	http://www.amk.ca/python/code/mt-math
	http://code.google.com/p/latexmath2png/

COPYING
	Copyright (C) 2010 Stuart Rackham. Free use of this software is
	granted under the terms of the MIT License.
"""

import os, sys, tempfile, hashlib

class LatexToPNG():

	TEX_HEADER = r'''\documentclass{article}
	\usepackage{amsmath}
	\usepackage{amsthm}
	\usepackage{amssymb}
	\usepackage{bm}
	\newcommand{\mx}[1]{\mathbf{\bm{#1}}} % Matrix command
	\newcommand{\vc}[1]{\mathbf{\bm{#1}}} % Vector command
	\newcommand{\T}{\text{T}}			 % Transpose
	\pagestyle{empty}
	\begin{document}'''
	
	TEX_FOOTER = r'''\end{document}'''

	def __init__(self):
		self.temp_result = tempfile.NamedTemporaryFile(suffix='.png')

	def run(self, cmd):
		cmd += ' >/dev/null 2>&1'
		if os.system(cmd):
			raise 'failed command: %s' % cmd


	def latex2png(self, tex, outfile, dpi, modified):
		'''Convert LaTeX input file infile to PNG file named outfile.'''
		outfile = os.path.abspath(outfile)
		outdir = os.path.dirname(outfile)
		#if not os.path.isdir(outdir):
		#	raise EApp, 'directory does not exist: %s' % outdir
		texfile = tempfile.mktemp(suffix='.tex', dir=os.path.dirname(outfile))
		basefile = os.path.splitext(texfile)[0]
		dvifile = basefile + '.dvi'
		temps = [basefile + ext for ext in ('.tex','.dvi', '.aux', '.log')]
		skip = False
		
		tex = '%s\n%s\n%s\n' % (self.TEX_HEADER, tex.strip(), self.TEX_FOOTER)

		open(texfile, 'w').write(tex)
		saved_pwd = os.getcwd()

		os.chdir(outdir)
		try:
			# Compile LaTeX document to DVI file.
			self.run('latex %s' % texfile)
			# Convert DVI file to PNG.
			cmd = 'dvipng'
			if dpi:
				cmd += ' -D %s' % dpi
			cmd += ' -T tight -x 1000 -z 9 -bg Transparent -o "%s" "%s"' \
					% (outfile,dvifile)
			self.run(cmd)
		finally:
			os.chdir(saved_pwd)
		for f in temps:
			if os.path.isfile(f):
				os.remove(f)

	def generatepng(self, formula):
		self.temp_result = tempfile.NamedTemporaryFile(suffix='.png')
		self.latex2png(formula, self.temp_result.name, 300, False)
		return self.temp_result.name