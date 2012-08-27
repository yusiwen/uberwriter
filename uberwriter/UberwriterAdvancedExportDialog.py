# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2012 <Wolf Vollprecht> <w.vollprecht@googlemail.com>
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

from gi.repository import Gtk
import os
import subprocess
import gettext
from gettext import gettext as _
gettext.textdomain('uberwriter')

import logging
logger = logging.getLogger('uberwriter')

from uberwriter_lib.AdvancedExportDialog import AdvancedExportDialog

# See uberwriter_lib.AboutDialog.py for more details about how this class works.
class UberwriterAdvancedExportDialog(AdvancedExportDialog):
    __gtype_name__ = "UberwriterAdvancedExportDialog"
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the about dialog"""
        super(UberwriterAdvancedExportDialog, self).finish_initializing(builder)

        # Code for other initialization actions should be added here.

        self.builder.get_object("highlight_style").set_active(0)

        format_store = Gtk.ListStore(int, str)
        for el in self.export_formats:
            format_store.append(el)
        self.format_field = builder.get_object('choose_format')
        self.format_field.set_model(format_store)
        self.format_field.connect("changed", self.on_name_combo_changed)

        format_renderer = Gtk.CellRendererText()
        self.format_field.pack_start(format_renderer, True)
        self.format_field.add_attribute(format_renderer, "text", 1)
        self.format_field.set_active(0)
        self.show_all()

    def on_name_combo_changed(self, combo, data=None):
        tree_iter = combo.get_active_iter()
        if tree_iter != None:
            model = combo.get_model()
            row_id, name = model[tree_iter][:2]
            print "Selected: ID=%d, name=%s" % (row_id, name)
        else:
            entry = combo.get_child()
            print "Entered: %s" % entry.get_text()

    formats_dict = {
        1: {
            "name": "Latex Source",
            "ext": "tex",
            "to": "latex"
        },
        2: {
            "name": "HTML",
            "ext": "html",
            "to": "html"
        },
        "odt": {
            "ext": "odt",
            "to": "odt"
        },
        "pdf": {
            "ext": "pdf"
        },
        "rst": {
            "format": "rst"
        },
        "beamer_tex": {
            "format": "tex"
        },
        "beamer_pdf": {
            "format": "pdf"
        },
        "context": {
            "format": "tex"
        },
        "s5": {
            "format": "html"
        },
        "man": {
            "format": "man"
        },
        "mediawiki": {
            "format": "txt"
        },
        "textile": {
            "format": "txt"
        },
        "docx": {
            "format": "docx"
        }
    }

    export_formats = [
    	[1, "Latex source"],
    	[2, "Latex PDF"], 
    	[3, "Beamer PDF"],
    	[4, "Beamer Latex Source"],
    	[5, "HTML"],
    	[6, "Textile"]
    ]
    def advanced_export(self, text = ""):
    	export_type = "html"
        tree_iter = self.format_field.get_active_iter()
        if tree_iter != None:
            model = self.format_field.get_model()
            row_id, name = model[tree_iter][:2]

        fmt = self.formats_dict[row_id]
        print fmt
        filechooser = Gtk.FileChooserDialog(
            "Export as %s" % fmt["name"],
            self,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
            )

        filechooser.set_do_overwrite_confirmation(True)
        
        response = filechooser.run()
        if response == Gtk.ResponseType.OK:
            filename = filechooser.get_filename()
            if filename.endswith("." + export_type):
                filename = filename[:-len(export_type)-1]
            filechooser.destroy()
        else: 
            filechooser.destroy()
            return 
                
        output_dir = os.path.abspath(os.path.join(filename, os.path.pardir))
        
        basename = os.path.basename(filename)

        args = ['pandoc', '--from=markdown']
        
        to = "-t%s" % fmt["to"]
        
        output_file = "-o%s.%s" % (basename, fmt["ext"])
        
        if self.builder.get_object("toc").get_active():
            args.append('--toc')
        if self.builder.get_object("normalize").get_active():
            args.append('--normalize')
        if self.builder.get_object("smart").get_active():
            args.append('--smart')
        if self.builder.get_object("highlight").get_active == False:
            args.append('--no-highlight')
        else:
            hs = self.builder.get_object("highlight_style").get_active_text()
            args.append("--highlight-style=%s" % hs)
        args.append(to)
        args.append(output_file)

        print args

        p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, cwd=output_dir)
        output = p.communicate(text)[0]
        
        return filename