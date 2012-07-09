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

import gettext
import subprocess
import os
import codecs
from gettext import gettext as _
gettext.textdomain('uberwriter')

from gi.repository import Gtk, Gdk # pylint: disable=E0611
from gi.repository import Pango # pylint: disable=E0611
import re

from quickly.widgets.text_editor import TextEditor

import logging
logger = logging.getLogger('uberwriter')

from uberwriter_lib import Window
from uberwriter.AboutUberwriterDialog import AboutUberwriterDialog
from uberwriter.PreferencesUberwriterDialog import PreferencesUberwriterDialog


# gtk_text_view_forward_display_line_end () !! !
# See texteditor_lib.Window.py for more details about how this class works
class UberwriterWindow(Window):
    __gtype_name__ = "UberwriterWindow"

    EMPHASIS = re.compile(r"\*\w(.+?)\*")
    UNDERLINE = re.compile(r"\*\*\w(.+?)\*\*")
    #STRIKETHROUGH = re.compile(r"-[^ ].+?-")
    
    LIST = re.compile(r"^[\-\*\+] ", re.MULTILINE)
    NUMERICLIST = re.compile(r"^(\d+\.) ", re.MULTILINE)
    HEADINDICATOR = re.compile(r"^(#{1,6}) ", re.MULTILINE)
    HEADLINE = re.compile(r"^(#{1,6}[^\n]+)", re.MULTILINE)

    HORIZONTALRULE = re.compile(r"^([\*\- ]{3,})", re.MULTILINE)

    def markup_buffer(self):
    	buf = self.TextBuffer
    	text = buf.get_slice(buf.get_start_iter(), buf.get_end_iter(), False).decode("utf-8")
        text = unicode(text)

        buf.remove_all_tags(buf.get_start_iter(), buf.get_end_iter())

        matches = re.finditer(self.EMPHASIS, text)
    	for match in matches: 
            startIter = buf.get_iter_at_offset(match.start())
            endIter = buf.get_iter_at_offset(match.end())
            self.TextBuffer.apply_tag(self.emph, startIter, endIter)

        matches = re.finditer(self.UNDERLINE, text)
        for match in matches:
            startIter = buf.get_iter_at_offset(match.start())
            endIter = buf.get_iter_at_offset(match.end())
            self.TextBuffer.apply_tag(self.underline, startIter, endIter)

        #matches = re.finditer(self.STRIKETHROUGH, text)
        #for match in matches:
        #    startIter = buf.get_iter_at_offset(match.start())
        #    endIter = buf.get_iter_at_offset(match.end())
        #    self.TextBuffer.apply_tag(self.strikethrough, startIter, endIter)


        matches = re.finditer(self.LIST, text) 
        for match in matches:
            startIter = buf.get_iter_at_offset(match.start())
            endIter = buf.get_iter_at_offset(match.end())
            self.TextBuffer.apply_tag(self.leftmargin[0], startIter, endIter)
       
        matches = re.finditer(self.NUMERICLIST, text)
        for match in matches:
            startIter = buf.get_iter_at_offset(match.start())
            endIter = buf.get_iter_at_offset(match.end())
            index = len(match.group(1)) - 1
            margin = self.leftmargin[index]
            self.TextBuffer.apply_tag(margin, startIter, endIter)

        matches = re.finditer(self.HEADINDICATOR, text) 
        for match in matches:
            startIter = buf.get_iter_at_offset(match.start())
            endIter = buf.get_iter_at_offset(match.end())
            index = len(match.group(1)) - 1
            margin = self.leftmargin[index]
            self.TextBuffer.apply_tag(margin, startIter, endIter)

        matches = re.finditer(self.HORIZONTALRULE, text)
        for match in matches:
            startIter = buf.get_iter_at_offset(match.start())
            endIter = buf.get_iter_at_offset(match.end())
            self.TextBuffer.apply_tag(self.centertext, startIter, endIter)

        matches = re.finditer(self.HEADLINE, text) 
        for match in matches:
            startIter = buf.get_iter_at_offset(match.start())
            endIter = buf.get_iter_at_offset(match.end())
            self.TextBuffer.apply_tag(self.emph, startIter, endIter)

        if self.focusmode:
            buf.apply_tag(self.grayfont, buf.get_start_iter(), buf.get_end_iter())
            cursor = buf.get_mark("insert")
            cursor_iter = buf.get_iter_at_mark(cursor)
            end_sentence = cursor_iter.copy()
            end_sentence.forward_sentence_end()
            start_sentence = cursor_iter.copy()
            start_sentence.backward_sentence_start()
            self.TextBuffer.apply_tag(self.blackfont, start_sentence, end_sentence)
            mark = buf.create_mark('centermark', cursor_iter)
            #self.TextEditor.scroll_to_mark(mark, True, True, 0.4, 0.4)
            

    def text_changed(self, widget, data=None):
        if self.did_change == False:
            self.did_change = True
            title = self.get_title()
            self.set_title("* " + title)

        self.markup_buffer()
        self.line_count.set_text(str(self.TextBuffer.get_line_count()))
        self.char_count.set_text(str(self.TextBuffer.get_char_count()))

    def toggle_fullscreen(self, widget, data=None):
        if widget.get_active():
            self.fullscreen()
        else:
            self.unfullscreen()

    def delete_text(self, widget):
        pass

    def cut_text(self, widget, data=None):
        self.TextEditor.cut()

    def paste_text(self, widget, data=None):
        self.TextEditor.paste()

    def copy_text(self, widget, data=None):
        self.TextEditor.copy()

    def undo(self, widget, data=None):
        self.TextEditor.undo()

    def redo(self, widget, data=None):
        self.TextEditor.redo()

    def set_focusmode(self, widget, data=None):
        if widget.get_active():
            self.focusmode = True
        else:
            self.focusmode = False
        self.markup_buffer()

    def window_resize(self, widget, data=None):
        lm = (widget.get_size()[0] - 600) / 2
        self.TextEditor.set_left_margin(lm)
        self.TextEditor.set_right_margin(lm)
        for i in range(0,6):
            name = "indent_left" + str(i)
            self.leftmargin[i].set_property("left-margin", (lm-10) - 10*(i+1))
            self.leftmargin[i].set_property("indent", - 10*(i+1) - 10)

    def window_close(self, widget, data=None):
        if self.check_change():
            self.save_document(widget)
            return True
        return True


    def save_document(self, widget, data=None):
        if self.filename:
            print "saving"
            filename = self.filename
            f = codecs.open(filename, encoding="utf-8", mode='w')
            startIter = self.TextBuffer.get_start_iter()
            endIter = self.TextBuffer.get_end_iter()
            f.write(self.TextBuffer.get_text(startIter, endIter, False).decode("utf-8"))
            f.close()
            if self.did_change:
                self.did_change = False
                title = self.get_title()
                self.set_title(title[2:])

        else:
            filechooser = Gtk.FileChooserDialog(
                "Save your File",
                self,
                Gtk.FileChooserAction.SAVE,
                (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                 Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
                )
            filechooser.set_do_overwrite_confirmation(True)
            response = filechooser.run()
            if response == Gtk.ResponseType.OK:
                print "Open clicked"
                print "File selected: " + filechooser.get_filename()
                filename = filechooser.get_filename()
                if filename[-3:] != ".md":
                    filename = filename + ".md"
                f = codecs.open(filename, encoding="utf-8", mode='w')
                startIter = self.TextBuffer.get_start_iter()
                endIter = self.TextBuffer.get_end_iter()
                text = self.TextBuffer.get_text(startIter, endIter, False)
                text = text.decode("utf-8")
                print text
                f.write(text)
                f.close()
                self.filename = filename
                filechooser.destroy()
                self.did_change = False
                title = self.get_title()
                self.set_title(title[2:])

            elif response == Gtk.ResponseType.CANCEL:
                print "Cancel clicked"
                filechooser.destroy()

    def save_document_as(self, widget, data=None):
        filechooser = Gtk.FileChooserDialog(
            "Save your File",
            self,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
            )
        filechooser.set_do_overwrite_confirmation(True)
        if self.filename:
            filechooser.set_filename(self.filename)
        response = filechooser.run()
        if response == Gtk.ResponseType.OK:
            print "Open clicked"
            print "File selected: " + filechooser.get_filename()
            filename = filechooser.get_filename()
            if filename[-3:] != ".md":
                filename = filename + ".md"
            f = codecs.open(filename, encoding="utf-8", mode='w')
            startIter = self.TextBuffer.get_start_iter()
            endIter = self.TextBuffer.get_end_iter()
            text = self.TextBuffer.get_text(startIter, endIter, False)
            text = text.decode("utf-8")
            f.write(text)
            f.close()
            self.filename = filename
            filechooser.destroy()
            self.did_change = False
            title = self.get_title()
            self.set_title(title[2:])

        elif response == Gtk.ResponseType.CANCEL:
            print "Cancel clicked"
            filechooser.destroy()

    def export(self, export_type="rtf"):
        filechooser = Gtk.FileChooserDialog(
            "Save your File",
            self,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
            )
        filechooser.set_do_overwrite_confirmation(True)
        if self.filename:
            filechooser.set_filename(self.filename)
        response = filechooser.run()
        if response == Gtk.ResponseType.OK:
            filename = filechooser.get_filename()
            filechooser.destroy()
        else: 
            filechooser.destroy()
            return 

        startIter = self.TextBuffer.get_start_iter()
        endIter = self.TextBuffer.get_end_iter()

        text = self.TextBuffer.get_text(startIter, endIter, False).decode("utf-8")
                
        output_dir = os.path.abspath(os.path.join(filename, os.path.pardir))
        
        basename = os.path.basename(filename)
        
        if export_type == "latex":
            args = ['pandoc', '--from=markdown', "-o %s.pdf" % basename] 
        elif export_type == "rtf":
            args = ['pandoc', '--from=markdown', "-o %s.rtf" % basename]
        elif export_type == "html":
            args = ['pandoc', '--from=markdown', "-o %s.html" % basename]

        p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, cwd=output_dir)
        output = p.communicate(text)[0]
        
        return filename

            
    def export_as_rtf(self, widget, data=None):
        self.export("rtf")

    def export_as_html(self, widget, data=None):
        self.export("html")

    def export_as_pdf(self, widget, data=None):
        filename = self.export("latex")

    def open_document(self, widget):
        if self.check_change() == False:
            return
        filechooser = Gtk.FileChooserDialog(
            "Open a .md-File",
            self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
            )
        response = filechooser.run()
        if response == Gtk.ResponseType.OK:
            print "File selected: " + filechooser.get_filename()
            filename = filechooser.get_filename()
            f = codecs.open(filename, encoding="utf-8", mode='r')
            self.TextBuffer.set_text(f.read())
            f.close()
            self.filename = filename
            filechooser.destroy()

        elif response == Gtk.ResponseType.CANCEL:
            print "Cancel clicked"
            filechooser.destroy()

    def check_change(self):
        if self.did_change:
            dialog = Gtk.MessageDialog(self, 0,
                Gtk.MessageType.WARNING, 
                Gtk.ButtonsType.OK_CANCEL,
                "The document has changed and you didn't save it. Save it now?"
                )
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                dialog.destroy()
                title = self.get_title()
                self.set_title(title[2:])
                return True
            else:
                dialog.destroy()
                return False

    def new_document(self, widget):
        if self.check_change() == False:
            return
        else:      
            self.did_change = False
            self.filename = None
            self.TextBuffer.set_text('')

    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(UberwriterWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutUberwriterDialog
        self.PreferencesDialog = PreferencesUberwriterDialog

        # Code for other initialization actions should be added here.

        #self.set_decorated(False)

        self.focusmode = False

        self.line_count = builder.get_object('line_count')
        self.char_count = builder.get_object('char_count')

        self.did_change = False
        self.filename = None

       # p = "~/.simpletexter/"
       #p = os.path.expanduser(p)
       #self.temp_dir = p     
       #if not os.path.exists(p):
       #    os.makedirs(p)

        self.TextEditor = TextEditor()

        self.TextEditor.set_left_margin(100)
        self.TextEditor.set_left_margin(40)

        #self.TextEditor.set_indent(100)

        self.TextEditor.set_wrap_mode(Gtk.WrapMode.WORD)
        self.TextEditor.show()

        builder.get_object('scrolledwindow1').add(self.TextEditor)

        print self.get_size()[0]

		pangoFont = Pango.FontDescription("Ubuntu Mono 15")
		self.TextEditor.modify_font(pangoFont)
        self.TextEditor.set_margin_top(38)
        self.TextEditor.set_margin_bottom(16)

        self.TextEditor.set_pixels_above_lines(5)
        self.TextEditor.set_pixels_below_lines(5)

        #tabs = self.TextEditor.get_tabs()
        #tabs.resize(4)
        #tabs = Pango.TabArray()
        #tabs.set_tab(0, Pango.TAB_LEFT, 4)
        #self.TextEditor.set_tab(tabs)

        #self.TextEditor.modify_cursor(Gdk.Color(100,0,0), Gdk.Color(200,0,0))

        self.TextBuffer = self.TextEditor.get_buffer()
        self.TextBuffer.set_text('')
        
        self.leftmargin = []
        for i in range(0,6):
            name = "indent_left" + str(i)
            self.leftmargin.append(self.TextBuffer.create_tag(name))
            self.leftmargin[i].set_property("left-margin", 90 - 10*(i+1))
            self.leftmargin[i].set_property("indent", - 10*(i+1) - 10)
            #self.leftmargin[i].set_property("background", "gray")


        self.emph = self.TextBuffer.create_tag("emph", weight=Pango.Weight.BOLD)

        self.normal_indent = self.TextBuffer.create_tag('normal_indent', indent=100)
        
        self.grayfont = self.TextBuffer.create_tag('graytag', foreground="gray")
        self.blackfont = self.TextBuffer.create_tag('blacktag', foreground="black")

        self.underline = self.TextBuffer.create_tag(
            "underline", 
            underline=Pango.Underline.SINGLE
            )
        self.underline.set_property('weight', Pango.Weight.BOLD)
        
        self.strikethrough = self.TextBuffer.create_tag(
            "strikethrough", 
            strikethrough=True
            )

        self.centertext = self.TextBuffer.create_tag(
            "centertext", 
            justification=Gtk.Justification.CENTER
        )

        self.TextBuffer.apply_tag(
            self.normal_indent, 
            self.TextBuffer.get_start_iter(),
            self.TextBuffer.get_end_iter()
            )


        self.TextBuffer.connect('changed', self.text_changed)

        self.TextEditor.set_buffer(self.TextBuffer)
        self.markup_buffer()

        self.connect("configure-event", self.window_resize)

    def on_destroy(self, widget, data=None):
        """Called when the TexteditorWindow is closed."""
        # Clean up code for saving application state should be added here.
        self.window_close(widget)
        Gtk.main_quit()