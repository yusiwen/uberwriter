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

from .UberwriterTextEditor import TextEditor

import logging
logger = logging.getLogger('uberwriter')

# Spellcheck

import locale
from uberwriter_lib.gtkspellcheck import SpellChecker


from uberwriter_lib import Window
from uberwriter.AboutUberwriterDialog import AboutUberwriterDialog


# gtk_text_view_forward_display_line_end () !! !
# move-viewport signal
# See texteditor_lib.Window.py for more details about how this class works
class UberwriterWindow(Window):

    __gtype_name__ = "UberwriterWindow"

    ITALIC = re.compile(r"\*\w(.+?)\*")
    EMPH = re.compile(r"\*\*\w(.+?)\*\*")
    #STRIKETHROUGH = re.compile(r"-[^ ].+?-")
    
    LIST = re.compile(r"^[\-\*\+] ", re.MULTILINE)
    NUMERICLIST = re.compile(r"^(\d+\.) ", re.MULTILINE)
    HEADINDICATOR = re.compile(r"^(#{1,6}) ", re.MULTILINE)
    HEADLINE = re.compile(r"^(#{1,6}[^\n]+)", re.MULTILINE)

    HORIZONTALRULE = re.compile(r"^([\*\- ]{3,}\n)", re.MULTILINE)

    def markup_buffer(self, mode=0):
        buf = self.TextBuffer

        # Modes:
        # 0 -> start to end
        # 1 -> around the cursor
        # 2 -> n.d.

        if mode == 0:
            context_start = buf.get_start_iter()
            context_end = buf.get_end_iter()
            context_offset = 0
        elif mode == 1:
            pass

    	text = buf.get_slice(context_start, context_end, False).decode("utf-8")
        text = unicode(text)

        #buf._all_tags(buf.get_start_iter(), buf.get_end_iter())

        self.TextBuffer.remove_tag(self.emph, context_start, context_end)

        matches = re.finditer(self.ITALIC, text)
    	for match in matches: 
            startIter = buf.get_iter_at_offset(match.start())
            endIter = buf.get_iter_at_offset(match.end())
            self.TextBuffer.apply_tag(self.italic, startIter, endIter)
        
        self.TextBuffer.remove_tag(self.emph, context_start, context_end)
        matches = re.finditer(self.EMPH, text)
        for match in matches:
            startIter = buf.get_iter_at_offset(match.start())
            endIter = buf.get_iter_at_offset(match.end())
            self.TextBuffer.apply_tag(self.emph, startIter, endIter)

        #matches = re.finditer(self.STRIKETHROUGH, text)
        #for match in matches:
        #    startIter = buf.get_iter_at_offset(match.start())
        #    endIter = buf.get_iter_at_offset(match.end())
        #    self.TextBuffer.apply_tag(self.strikethrough, startIter, endIter)

        for margin in self.leftmargin:
            self.TextBuffer.remove_tag(margin, context_start, context_end)


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
        self.TextBuffer.remove_tag(self.centertext, context_start, context_end)

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
            self.focusmode_highlight()


    def focusmode_highlight(self):
        self.TextBuffer.apply_tag(self.grayfont, 
            self.TextBuffer.get_start_iter(), 
            self.TextBuffer.get_end_iter())
        
        self.TextBuffer.remove_tag(self.blackfont,
            self.TextBuffer.get_start_iter(),
            self.TextBuffer.get_end_iter())

        cursor = self.TextBuffer.get_mark("insert")
        cursor_iter = self.TextBuffer.get_iter_at_mark(cursor)
        
        end_sentence = cursor_iter.copy()
        end_sentence.forward_sentence_end()
        
        start_sentence = cursor_iter.copy()
        start_sentence.backward_sentence_start()
        
        self.TextBuffer.apply_tag(self.blackfont, start_sentence, end_sentence)


    def scrolled(self, widget):
        if self.focusmode:
            if self.textchange == False:
                if self.scroll_count >= 1:
                    self.TextBuffer.apply_tag(
                        self.blackfont, 
                        self.TextBuffer.get_start_iter(), 
                        self.TextBuffer.get_end_iter())
                else:
                    self.scroll_count += 1
            else: 
                self.scroll_count = 0
                self.typewriter()
                self.textchange = False

    def after_modify_text(self, *arg):
        if self.focusmode:
            self.typewriter()

    def init_typewriter(self):

        self.TextBuffer.disconnect(self.TextEditor.delete_event)
        self.TextBuffer.disconnect(self.TextEditor.insert_event)

        ci = self.TextBuffer.get_iter_at_mark(self.TextBuffer.get_mark('insert'))
        co = ci.get_offset()

        fflines = int(round((self.window_height-55)/(2*30)))
        self.fflines = fflines
        self.TextEditor.fflines = fflines

        s = '\n'*fflines

        start_iter =  self.TextBuffer.get_iter_at_offset(0)
        self.TextBuffer.insert(start_iter, s)
        
        end_iter =  self.TextBuffer.get_iter_at_offset(-1)
        self.TextBuffer.insert(end_iter, s)

        ne_ci = self.TextBuffer.get_iter_at_offset(co + fflines)
        self.TextBuffer.place_cursor(ne_ci)

        # Scroll it to the center
        self.TextEditor.scroll_to_mark(self.TextBuffer.get_mark('insert'), 0.0, True, 0.0, 0.5)

        self.TextEditor.insert_event = self.TextBuffer.connect("insert-text",self.TextEditor._on_insert)
        self.TextEditor.delete_event = self.TextBuffer.connect("delete-range",self.TextEditor._on_delete)

        self.typewriter_initiated = True

    def typewriter(self):
        cursor = self.TextBuffer.get_mark("insert")
        cursor_iter = self.TextBuffer.get_iter_at_mark(cursor)
        self.TextEditor.scroll_to_iter(cursor_iter, 0.0, True, 0.0, 0.5)

    def remove_typewriter(self):
        startIter = self.TextBuffer.get_start_iter()
        endLineIter = startIter.copy()
        endLineIter.forward_lines(self.fflines)
        self.TextBuffer.delete(startIter, endLineIter)
        startIter = self.TextBuffer.get_end_iter()
        endLineIter = startIter.copy()
        
        # Move to line before last line
        endLineIter.backward_lines(self.fflines - 1)
        
        # Move to last char in last line
        endLineIter.backward_char()
        self.TextBuffer.delete(startIter, endLineIter)

        self.fflines = 0
        self.TextEditor.fflines = 0

    def get_text(self):
        if self.focusmode == False:
            start_iter = self.TextBuffer.get_start_iter()
            end_iter = self.TextBuffer.get_end_iter()

        else:
            start_iter = self.TextBuffer.get_iter_at_line(self.fflines)
            rbline =  self.TextBuffer.get_line_count() - self.fflines
            end_iter = self.TextBuffer.get_iter_at_line(rbline)

        return self.TextBuffer.get_text(start_iter, end_iter, False)

    def mark_set(self, buffer, location, mark, data=None):
        if self.focusmode and (mark.get_name() == 'insert' or
            mark.get_name() == 'selection_bound'):
            akt_lines = self.TextBuffer.get_line_count()
            lb = self.fflines
            rb = akt_lines - self.fflines
            #print "a %d, lb %d, rb %d" % (akt_lines, lb, rb)
            #lb = self.TextBuffer.get_iter_at_line(self.fflines)
            #rbline =  self.TextBuffer.get_line_count() - self.fflines
            #rb = self.TextBuffer.get_iter_at_line(
            #   rbline)
            #rb.backward_line()
            

            linecount = location.get_line()
            #print "a %d, lb %d, rb %d, lc %d" % (akt_lines, lb, rb, linecount)

            if linecount < lb:
                move_to_line = self.TextBuffer.get_iter_at_line(lb)
                self.TextBuffer.move_mark(mark, move_to_line)
            elif linecount >= rb:
                move_to_line = self.TextBuffer.get_iter_at_line(rb)
                move_to_line.backward_char()
                self.TextBuffer.move_mark(mark, move_to_line)

    def after_mark_set(self, buffer, location, mark, data=None):
        if self.focusmode and mark.get_name() == 'insert':
            self.typewriter()


    def delete_from_cursor(self, editor, typ, count, Data=None):
        if not self.focusmode:
            return
        cursor = self.TextBuffer.get_mark("insert")
        cursor_iter = self.TextBuffer.get_iter_at_mark(cursor)
        if count < 0 and cursor_iter.starts_line():
            lb = self.fflines
            linecount = cursor_iter.get_line()
            #print "lb %d, lc %d" % (lb, linecount)
            if linecount <= lb:
                self.TextEditor.emit_stop_by_name('delete-from-cursor')
        elif count > 0 and cursor_iter.ends_line():
            akt_lines = self.TextBuffer.get_line_count()
            rb = akt_lines - self.fflines
            linecount = cursor_iter.get_line() + 1
            #print "rb %d, lc %d" % (rb, linecount)
            if linecount >= rb:
                self.TextEditor.emit_stop_by_name('delete-from-cursor')

    def backspace(self, data=None):
        if not self.focusmode:
            return

        cursor = self.TextBuffer.get_mark("insert")
        cursor_iter = self.TextBuffer.get_iter_at_mark(cursor)
        if cursor_iter.starts_line():
            lb = self.fflines
            linecount = cursor_iter.get_line()
            print "lb %d, lc %d" % (lb, linecount)

            if linecount <= lb:
                self.TextEditor.emit_stop_by_name('backspace')


    def cursor_moved(self, widget, a, b, data=None):
        pass

    def after_cursor_moved(self, widget, step, count, extend_selection, data=None):
        if self.focusmode:
            self.typewriter()

    def text_changed(self, widget, data=None):
        if self.did_change == False:
            self.did_change = True
            title = self.get_title()
            self.set_title("* " + title)

        self.markup_buffer()

        self.textchange = True

        self.line_count.set_text(str(
            self.TextBuffer.get_line_count() - 
                (2 * self.fflines)))
        self.char_count.set_text(str(self.TextBuffer.get_char_count() - 
                (2 * self.fflines)))

    def toggle_fullscreen(self, widget, data=None):
        if widget.get_active():
            self.fullscreen()
        else:
            self.unfullscreen()
        self.TextEditor.grab_focus()

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
            self.init_typewriter()
            self.focusmode_highlight()
            self.focusmode = True
            self.TextEditor.grab_focus()
            self.SpellChecker.disable()
        else:
            self.remove_typewriter()
            self.focusmode = False
            self.TextBuffer.remove_tag(self.grayfont, 
                self.TextBuffer.get_start_iter(),
                self.TextBuffer.get_end_iter())
            self.TextBuffer.remove_tag(self.blackfont, 
                self.TextBuffer.get_start_iter(),
                self.TextBuffer.get_end_iter())

            self.markup_buffer()
            self.TextEditor.grab_focus()

            self.SpellChecker.enable()            

    def window_resize(self, widget, data=None):
        # To calc padding top / bottom
        self.window_height = widget.get_size()[1]

        # Calculate left / right margin
        lm = (widget.get_size()[0] - 600) / 2
        
        self.TextEditor.set_left_margin(lm)
        self.TextEditor.set_right_margin(lm)


        for i in range(0,6):
            name = "indent_left" + str(i)
            self.leftmargin[i].set_property("left-margin", (lm-10) - 10*(i+1))
            self.leftmargin[i].set_property("indent", - 10*(i+1) - 10)

        if self.focusmode:
            self.remove_typewriter()
            self.init_typewriter()

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
            f.write(self.get_text().decode("utf-8") )
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

                f.write(self.get_text().decode("utf-8") )
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
            f.write(self.get_text().decode("utf-8") )
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
            if filename[-(len(export_type)-1):] == "." + export_type:
                filename = filename[:-(len(export_type)-1)]
            filechooser.destroy()
        else: 
            filechooser.destroy()
            return 

        text = self.get_text()
                
        output_dir = os.path.abspath(os.path.join(filename, os.path.pardir))
        
        basename = os.path.basename(filename)
        
        if export_type == "pdf":
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
        filename = self.export("pdf")

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
        if self.did_change and len(self.get_text()):
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

    def menu_activate_focusmode(self, widget):
        self.focusmode_button.emit('activate')

    def menu_activate_fullscreen(self, widget):
        self.fullscreen_button.emit('activate')

    # Not added as menu button as of now. Standard is typewriter active.
    def toggle_typewriter(self, widget, data=None):
        self.typewriter_active = widget.get_active()

    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(UberwriterWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutUberwriterDialog

        # Code for other initialization actions should be added here.

        #self.set_decorated(False)

        self.focusmode = False

        self.line_count = builder.get_object('line_count')
        self.char_count = builder.get_object('char_count')

        self.fullscreen_button = builder.get_object('togglebutton1')
        self.focusmode_button = builder.get_object('focus_toggle')

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

        self.TextEditor.set_wrap_mode(Gtk.WrapMode.WORD)

        self.TextEditor.show()

        self.ScrolledWindow = builder.get_object('scrolledwindow1')

        self.ScrolledWindow.add(self.TextEditor)

		pangoFont = Pango.FontDescription("Ubuntu Mono 15")
		self.TextEditor.modify_font(pangoFont)
        
        self.TextEditor.set_margin_top(38)
        self.TextEditor.set_margin_bottom(16)

        self.TextEditor.set_pixels_above_lines(5)
        self.TextEditor.set_pixels_below_lines(5)
        self.TextEditor.set_pixels_inside_wrap(10)

        tab_array = Pango.TabArray.new(2, False)
        self.TextEditor.set_tabs(tab_array)


        self.TextBuffer = self.TextEditor.get_buffer()
        self.TextBuffer.set_text('')
        
        self.leftmargin = []
        
        for i in range(0,6):
            name = "indent_left" + str(i)
            self.leftmargin.append(self.TextBuffer.create_tag(name))
            self.leftmargin[i].set_property("left-margin", 90 - 10*(i+1))
            self.leftmargin[i].set_property("indent", - 10*(i+1) - 10)
            #self.leftmargin[i].set_property("background", "gray")

        # Init Window height for top/bottom padding

        self.window_height = self.get_size()[1]

        self.italic = self.TextBuffer.create_tag("italic", 
            style=Pango.Style.ITALIC)

        self.emph = self.TextBuffer.create_tag("emph", 
            weight=Pango.Weight.BOLD,
            style =Pango.Style.NORMAL)

        self.normal_indent = self.TextBuffer.create_tag('normal_indent', indent=100)
        
        self.grayfont = self.TextBuffer.create_tag('graytag', 
            foreground="gray")
        self.blackfont = self.TextBuffer.create_tag('blacktag', 
            foreground="#222")

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

        self.invisibleTag = self.TextBuffer.create_tag("invisible", 
            invisible=True)
        
        self.ineditableTag = self.TextBuffer.create_tag("ineditable", 
            editable=False)

        self.start_mark = self.TextBuffer.create_mark("startmark", 
            self.TextBuffer.get_start_iter(), 
            True)

        self.end_mark =  self.TextBuffer.create_mark("endmark", 
            self.TextBuffer.get_end_iter(), 
            False)
       

        self.TextBuffer.connect('changed', self.text_changed)
        
        self.TextEditor.connect('move-cursor', self.cursor_moved)

        styleProvider = Gtk.CssProvider()

        css = """
        GtkTextView {
            -GtkWidget-cursor-color: #FA5B0F;
            -GtkWidget-cursor-aspect-ratio: 0.05;
            -gtk-tab-size: 2;
            color: #222;
        }"""

        styleProvider.load_from_data(css)

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), styleProvider,     
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.fflines = 0

        #icon_view.get_style_context().add_class(‘transparent’) 
        #window.get_style_context().add_class(‘shelf’)
        #Gtk.CssProvider.load_from_data(css)

        self.TextEditor.set_buffer(self.TextBuffer)
        self.markup_buffer()

        # Scrolling -> Dark or not?
        self.textchange = False
        self.scroll_count = 0


        self.TextBuffer.connect('mark-set', self.mark_set)
        
        self.TextEditor.drag_dest_unset()

        # Events to preserve margin. (To be deleted.)
        self.TextEditor.connect('delete-from-cursor', self.delete_from_cursor)
        self.TextEditor.connect('backspace', self.backspace)

        self.vadjustment = self.TextEditor.get_vadjustment()


        # Events for Typewriter mode
        self.TextBuffer.connect_after('mark-set', self.after_mark_set)
        self.TextBuffer.connect_after('changed', self.after_modify_text)
        self.TextEditor.connect_after('move-cursor', self.after_cursor_moved)
        self.TextEditor.connect_after('insert-at-cursor', self.after_modify_text)

        self.vadjustment.connect('value-changed', self.scrolled)

        # Setting up spellcheck
        self.SpellChecker = SpellChecker(self.TextEditor, locale.getdefaultlocale()[0])


        self.connect("configure-event", self.window_resize)

    def on_destroy(self, widget, data=None):
        """Called when the TexteditorWindow is closed."""
        # Clean up code for saving application state should be added here.
        self.window_close(widget)
        Gtk.main_quit()

