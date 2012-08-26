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

import mimetypes

from gi.repository import Gtk, Gdk # pylint: disable=E0611
from gi.repository import Pango # pylint: disable=E0611

import re


from MarkupBuffer import MarkupBuffer
from UberwriterTextEditor import TextEditor

import logging
logger = logging.getLogger('uberwriter')

# Spellcheck

import locale
try:
    from gtkspellcheck import SpellChecker
except ImportError:
    from uberwriter_lib.thirdparty.gtkspellcheck import SpellChecker

from uberwriter_lib import Window
from uberwriter_lib import helpers
from uberwriter.AboutUberwriterDialog import AboutUberwriterDialog


# gtk_text_view_forward_display_line_end () !! !
# move-viewport signal
# See texteditor_lib.Window.py for more details about how this class works
class UberwriterWindow(Window):

    __gtype_name__ = "UberwriterWindow"

    def scrolled(self, widget):
        """if window scrolled + focusmode make font black again"""
        if self.focusmode:
            if self.textchange == False:
                if self.scroll_count >= 1:
                    self.TextBuffer.apply_tag(
                        self.M.blackfont, 
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

    def after_insert_at_cursor(self, *arg):
        if self.focusmode:
            self.typewriter()

    def paste_done(self, *args):
        self.M.markup_buffer(0)

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

    WORDCOUNT = re.compile(r"[\s#*\+\-]+", re.UNICODE)
    def update_line_and_char_count(self):
        self.char_count.set_text(str(self.TextBuffer.get_char_count() - 
                (2 * self.fflines)))

        text = self.TextBuffer.get_text(self.TextBuffer.get_start_iter(),
            self.TextBuffer.get_end_iter(), False).decode("utf-8")
        text = unicode(text)
        words = re.split(self.WORDCOUNT, text)
        length = len(words) - 1
        self.word_count.set_text(str(length))

        # TODO rename line_count to word_count

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

        self.M.markup_buffer(1)
        self.textchange = True

        self.update_line_and_char_count()

    def toggle_fullscreen(self, widget, data=None):
        if widget.get_active():
            self.fullscreen()
            widget.set_image(self.fullscreen_active)
            widget.get_image().show()
            key, mod = Gtk.accelerator_parse("Escape")
            self.fullscreen_button.add_accelerator("activate", 
            self.accel_group, key, mod, Gtk.AccelFlags.VISIBLE)
        else:
            self.unfullscreen()
            widget.set_image(self.fullscreen_inactive)
            widget.get_image().show()
            key, mod = Gtk.accelerator_parse("Escape")
            self.fullscreen_button.remove_accelerator(
                self.accel_group, key, mod)
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

    def set_italic(self, widget, data=None):
        cursor_mark = self.TextBuffer.get_insert()
        cursor_iter = self.TextBuffer.get_iter_at_mark(cursor_mark)
        if cursor_iter.starts_word():
            ii = cursor_iter.copy()
            ii.backward_word_starts()
            self.TextBuffer.insert(ii, '*')
            ii.forward_word_starts()
            self.TextBuffer.insert(ii, '*')
    def set_bold(self, widget, data=None):
        pass

    def set_focusmode(self, widget, data=None):
        if widget.get_active():
            self.init_typewriter()
            self.M.focusmode_highlight()
            self.focusmode = True
            self.TextEditor.grab_focus()
            
            if self.spellcheck != False:
                self.SpellChecker._misspelled.set_property('underline', 0)
            
            self.focusmode_button.set_image(self.crosshair_active)
            self.focusmode_button.get_image().show()
        else:
            self.remove_typewriter()
            self.focusmode = False
            self.TextBuffer.remove_tag(self.M.grayfont, 
                self.TextBuffer.get_start_iter(),
                self.TextBuffer.get_end_iter())
            self.TextBuffer.remove_tag(self.M.blackfont, 
                self.TextBuffer.get_start_iter(),
                self.TextBuffer.get_end_iter())

            self.M.markup_buffer(1)
            self.TextEditor.grab_focus()
            self.update_line_and_char_count()
            
            if self.spellcheck != False:
                self.SpellChecker._misspelled.set_property('underline', 4)

            self.focusmode_button.set_image(self.crosshair_inactive)
            self.focusmode_button.get_image().show()

    def window_resize(self, widget, data=None):
        # To calc padding top / bottom
        self.window_height = widget.get_size()[1]

        # Calculate left / right margin
        lm = (widget.get_size()[0] - 600) / 2
            
        self.TextEditor.set_left_margin(lm)
        self.TextEditor.set_right_margin(lm)

        self.M.recalculate(lm)

        if self.focusmode:
            self.remove_typewriter()
            self.init_typewriter()

    def window_close(self, widget, data=None):
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
                self.set_title(os.path.basename(filename) + self.title_end)
                
                filechooser.destroy()

                self.recent_manager.add_item(filename)

                self.did_change = False

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

            filename = filechooser.get_filename()
            if filename[-3:] != ".md":
                filename = filename + ".md"

            f = codecs.open(filename, encoding="utf-8", mode='w')
            f.write(self.get_text().decode("utf-8") )
            f.close()
            
            self.filename = filename
            self.set_title(os.path.basename(filename) + self.title_end)

            self.recent_manager.add_item(filename)

            filechooser.destroy()
            self.did_change = False

        elif response == Gtk.ResponseType.CANCEL:
            print "Cancel clicked"
            filechooser.destroy()

    def export(self, export_type="html"):
        filechooser = Gtk.FileChooserDialog(
            "Export as %s" % export_type.upper(),
            self,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
            )

        filechooser.set_do_overwrite_confirmation(True)
        if self.filename:
            filechooser.set_filename(self.filename[:-2] + export_type.lower())
        
        response = filechooser.run()
        if response == Gtk.ResponseType.OK:
            filename = filechooser.get_filename()
            if filename.endswith("." + export_type):
                filename = filename[:-len(export_type)-1]
            filechooser.destroy()
        else: 
            filechooser.destroy()
            return 

        text = self.get_text()
                
        output_dir = os.path.abspath(os.path.join(filename, os.path.pardir))
        
        basename = os.path.basename(filename)

        args = ['pandoc', '--from=markdown', '--smart']
        
        if export_type == "pdf":
            args.append("-o%s.pdf" % basename) 
        
        elif export_type == "odt":
            args.append("-o%s.odt" % basename)
        
        elif export_type == "html":
            css = helpers.get_media_file('uberwriter.css')
            args.append("-c%s" % css)
            args.append("-o%s.html" % basename)
            args.append("--mathjax")

        p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, cwd=output_dir)
        output = p.communicate(text)[0]
        
        return filename
            
    def export_as_odt(self, widget, data=None):
        self.export("odt")

    def export_as_html(self, widget, data=None):
        self.export("html")

    def export_as_pdf(self, widget, data=None):
        self.export("pdf")

    def copy_html_to_clipboard(self, widget, date=None):
        # TODO connect to item in Menubar, and make new pandoc template for 
        # only HTML, no headers etc.
        
        args = ['pandoc', '--from=markdown', '--smart', '-t html']
        p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, cwd=output_dir)

        cb = Gtk.Clipboard.get()
        cb.set_text('test')
        cb.store()

    def open_document(self, widget):
        cc = self.check_change()
        print cc
        if cc == True:
            return
        filefilter = Gtk.FileFilter.new()
        filefilter.add_mime_type('text/x-markdown')
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
            self.load_file(filename)
            filechooser.destroy()

        elif response == Gtk.ResponseType.CANCEL:
            print "Cancel clicked"
            filechooser.destroy()

    def open_recent(self, widget, data=None):
        pass

    def check_change(self):
        if self.did_change and len(self.get_text()):
            dialog = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                Gtk.MessageType.WARNING, 
                Gtk.ButtonsType.YES_NO,
                "Do you want to save your changes?"
                )
            response = dialog.run()
            if response == Gtk.ResponseType.YES:
                dialog.destroy()
                title = self.get_title()
                self.save_document(None)
                return False
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

    def toggle_spellcheck(self, widget, data=None):
        if widget.get_active():
            self.SpellChecker.enable()
        else:
            self.SpellChecker.disable()


    def on_drag_data_received(self, widget, drag_context, x, y, 
                              data, info, time):
        """Handle drag and drop events"""

        if info == 1:
            # uri target
            uris = data.get_uris()
            for uri in uris: 
                mime = mimetypes.guess_type(uri)

                if mime[0] is not None and mime[0].startswith('image'):
                    text = "![Insert image title here](%s)" % uri
                    ll = 2
                    lr = 23
                else:
                    text = "[Insert link title here](%s)" % uri
                    ll = 1
                    lr = 22

                self.TextBuffer.insert_at_cursor(text)
                insert_mark = self.TextBuffer.get_insert()
                selection_bound = self.TextBuffer.get_selection_bound()
                cursor_iter = self.TextBuffer.get_iter_at_mark(insert_mark)
                cursor_iter.backward_chars(len(text) - ll)
                self.TextBuffer.move_mark(insert_mark, cursor_iter)
                cursor_iter.forward_chars(lr)
                self.TextBuffer.move_mark(selection_bound, cursor_iter)
        
        elif info == 2:
            # Text target
            self.TextBuffer.insert_at_cursor(data.get_text())

        self.present()

    def dark_mode_toggled(self, widget, data=None):
        if widget.get_active():
            # Dark Mode is on
            css = open(helpers.get_media_path('style_dark.css'), 'r')
            css_data = css.read()
            css.close()
            self.style_provider.load_from_data(css_data)

        else: 
            # Dark mode off
            css = open(helpers.get_media_path('style.css'), 'r')
            css_data = css.read()
            css.close()

            self.style_provider.load_from_data(css_data)

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), self.style_provider,     
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

    def load_file(self, filename = None):
        """Open File from command line"""
        if filename:
            self.filename = filename
            print "Open file on start: %s" % filename
            try:
                f = codecs.open(filename, encoding="utf-8", mode='r')
                self.TextBuffer.set_text(f.read())
                f.close()
                self.M.markup_buffer(0)
                self.set_title(os.path.basename(filename) + self.title_end)
            except:
                print "Error Reading File"
            self.did_change = False
        else:
            print "No File arg"

    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(UberwriterWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutUberwriterDialog

        # Code for other initialization actions should be added here.

        self.set_name('UberwriterWindow')

        self.title_end = "  –  UberWriter"
        self.set_title("New File" + self.title_end)

        # Drag and drop
        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        
        self.target_list = Gtk.TargetList.new([])
        self.target_list.add_uri_targets(1)
        self.target_list.add_text_targets(2)

        self.drag_dest_set_target_list(self.target_list)

        self.focusmode = False

        self.word_count = builder.get_object('word_count')
        self.char_count = builder.get_object('char_count')

        self.fullscreen_button = builder.get_object('fullscreen_toggle')
        self.focusmode_button = builder.get_object('focus_toggle')
        self.fullscreen_button.set_name('fullscreen_toggle')
        self.focusmode_button.set_name('focus_toggle')
        
        
        self.crosshair_inactive = Gtk.Image.new_from_file(
                helpers.get_media_path('crh.png')
            )
        self.crosshair_active = Gtk.Image.new_from_file(
                helpers.get_media_path('crh_a.png')
            )

        self.fullscreen_inactive = Gtk.Image.new_from_file(
                helpers.get_media_path('fs.png')
            )
        self.fullscreen_active = Gtk.Image.new_from_file(
                helpers.get_media_path('fs_a.png')
            )

        self.focusmode_button.set_image(self.crosshair_inactive)
        self.focusmode_button.get_image().show()
        self.fullscreen_button.set_image(self.fullscreen_inactive)
        self.fullscreen_button.get_image().show()

        self.accel_group = Gtk.AccelGroup()
        self.add_accel_group(self.accel_group)



        # p = "~/.simpletexter/"
        #p = os.path.expanduser(p)
        #self.temp_dir = p     
        #if not os.path.exists(p):
        #    os.makedirs(p)

        self.TextEditor = TextEditor()

        #self.TextEditor.connect("delete-range",self.check_range)


        base_leftmargin = 100
        self.TextEditor.set_left_margin(base_leftmargin)
        self.TextEditor.set_left_margin(40)

        self.TextEditor.set_wrap_mode(Gtk.WrapMode.WORD)

        self.TextEditor.show()

        self.ScrolledWindow = builder.get_object('scrolledwindow1')

        self.ScrolledWindow.add(self.TextEditor)

		pangoFont = Pango.FontDescription("Ubuntu Mono 14px")
		self.TextEditor.modify_font(pangoFont)
        
        self.TextEditor.set_margin_top(38)
        self.TextEditor.set_margin_bottom(16)

        self.TextEditor.set_pixels_above_lines(5)
        self.TextEditor.set_pixels_below_lines(5)
        self.TextEditor.set_pixels_inside_wrap(10)

        tab_array = Pango.TabArray.new(1, True)
        tab_array.set_tab(0, Pango.TabAlign.LEFT, 20)
        self.TextEditor.set_tabs(tab_array)


        self.TextBuffer = self.TextEditor.get_buffer()
        self.TextBuffer.set_text('')

        self.M = MarkupBuffer(self, self.TextBuffer, base_leftmargin)

        # Init Window height for top/bottom padding

        self.window_height = self.get_size()[1]

        self.TextBuffer.connect('changed', self.text_changed)
        
        self.TextEditor.connect('move-cursor', self.cursor_moved)

        # Recent file filter
        self.recent_manager = Gtk.RecentManager.get_default()

        recent_files_menu = Gtk.RecentChooserMenu.new_for_manager(self.recent_manager)
        recent_filter = Gtk.RecentFilter.new()
        recent_filter.add_mime_type('text/x-markdown')
        recent_files_menu.set_filter(recent_filter)

        recent_files_menu.set_property('show-numbers', True)
        recent_files_menu.show()

        self.builder.get_object('recent-files').set_submenu(recent_files_menu)
        #self.builder.get_object('recent-files').hide()
        self.style_provider = Gtk.CssProvider()

        css = open(helpers.get_media_path('style.css'), 'r')
        css_data = css.read()
        css.close()

        self.style_provider.load_from_data(css_data)

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), self.style_provider,     
            Gtk.STYLE_PROVIDER_PRIORITY_USER
        )


        # Still needed.
        self.fflines = 0

        self.M.markup_buffer()

        # Scrolling -> Dark or not?
        self.textchange = False
        self.scroll_count = 0

        self.TextBuffer.connect('mark-set', self.mark_set)
        
        self.TextEditor.drag_dest_unset()

        # Events to preserve margin. (To be deleted.)
        self.TextEditor.connect('delete-from-cursor', self.delete_from_cursor)
        self.TextEditor.connect('backspace', self.backspace)

        self.TextBuffer.connect('paste-done', self.paste_done)

        self.vadjustment = self.TextEditor.get_vadjustment()

        # Events for Typewriter mode
        self.TextBuffer.connect_after('mark-set', self.after_mark_set)
        self.TextBuffer.connect_after('changed', self.after_modify_text)
        self.TextEditor.connect_after('move-cursor', self.after_cursor_moved)
        self.TextEditor.connect_after('insert-at-cursor', self.after_insert_at_cursor)

        self.vadjustment.connect('value-changed', self.scrolled)

        # Setting up spellcheck
        try:
            self.SpellChecker = SpellChecker(self.TextEditor, locale.getdefaultlocale()[0], collapse=False)
            self.spellcheck = True
        except:
            self.spellcheck = False;


        # Open file from commandline

        self.did_change = False


        # Window resize
        self.connect("configure-event", self.window_resize)

        # Window destroyed??

        self.connect("delete-event", self.on_delete_called)




    def on_delete_called(self, widget, data=None):
        if self.check_change():
            self.save_document(widget)
            ## Handle cancel event
            return False
        return False
 
    def on_destroy(self, widget, data=None):
        """Called when the TexteditorWindow is closed."""
        # Clean up code for saving application state should be added here.
        self.window_close(widget)        
        Gtk.main_quit()

