# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2012, Wolf Vollprecht <w.vollprecht@gmail.com>
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

import re
import http.client
import urllib
from urllib.error import URLError, HTTPError
import webbrowser
import locale

import threading

from gi.repository import Gtk, Gdk, GdkPixbuf, GObject
from uberwriter_lib import LatexToPNG

from .MarkupBuffer import MarkupBuffer

from locale import gettext as _
locale.textdomain('uberwriter')

import logging
logger = logging.getLogger('uberwriter')

GObject.threads_init()

def check_url(url, item, spinner):
    logger.debug("thread started, checking url")
    error = False
    try:
        response = urllib.request.urlopen(url)
    except URLError as e:
        error = True
        text = "Error! Reason: %s" % e.reason

    if not error:
        if (response.code / 100) >= 4:
            logger.debug("Website not available")
            text = _("Website is not available")
        else:
            text = _("Website is available")
    logger.debug("Response: %s" % text)
    spinner.destroy()
    item.set_label(text)

class UberwriterInlinePreview():

    def __init__(self, view, text_buffer):
        self.TextView = view
        self.TextBuffer = text_buffer
        self.LatexConverter = LatexToPNG.LatexToPNG()
        cursor_mark = self.TextBuffer.get_insert()
        cursor_iter = self.TextBuffer.get_iter_at_mark(cursor_mark)
        self.ClickMark = self.TextBuffer.create_mark('click', cursor_iter)
        # Events for popup menu
        self.TextView.connect_after('populate-popup', self.populate_popup)
        self.TextView.connect_after('popup-menu', self.move_popup)
        self.TextView.connect('button-press-event', self.click_move_button)

    def click_move_button(self, widget, event):
        if event.button == 3:
            x, y = self.TextView.window_to_buffer_coords(2,
                                                         int(event.x),
                                                         int(event.y))
            self.TextBuffer.move_mark(self.ClickMark,
                                      self.TextView.get_iter_at_location(x, y))

    def populate_popup(self, editor, menu, data=None):

        item = Gtk.MenuItem.new()
        item.set_name("PreviewMenuItem")
        separator = Gtk.SeparatorMenuItem.new()

        start_iter = self.TextBuffer.get_iter_at_mark(self.ClickMark)
        # Line offset of click mark
        line_offset = start_iter.get_line_offset()
        end_iter = start_iter.copy()
        start_iter.set_line_offset(0)
        end_iter.forward_to_line_end()

        text = self.TextBuffer.get_text(start_iter, end_iter, False)

        math = MarkupBuffer.regex["MATH"]
        link = MarkupBuffer.regex["LINK"]

        footnote = re.compile('\[\^([^\s]+?)\]')
        image = re.compile("!\[(.+?)\]\((.+?)\)")

        buf = self.TextBuffer
        context_offset = 0

        matchlist = []

        found_match = False

        matches = re.finditer(math, text)
        for match in matches:
            logger.debug(match.group(1))
            if match.start() < line_offset and match.end() > line_offset:
                latex_image = self.LatexConverter.generatepng(match.group(1))
                image = Gtk.Image.new_from_file(latex_image)
                image.show()
                item.add(image)
                item.set_property('width-request', 50)
                item.show()
                menu.prepend(separator)
                separator.show()
                menu.prepend(item)
                menu.show()
                found_match = True
                break

        if not found_match:
            matches = re.finditer(link, text)
            for match in matches:
                if match.start() < line_offset and match.end() > line_offset:
                    text = text[text.find("http://"):-1]
                    
                    item.connect("activate", lambda w: webbrowser.open(text))                    

                    # spinner = Gtk.Spinner()

                    # # get off brackets and other text
                    # # print text
                    # url = urllib.parse.urlparse(text)
                    # # netloc = url.netloc
                    # # path = url.path
                    # conn = http.client.HTTPConnection(url.netloc)
                    # conn.request("HEAD", url.path)
                    # code = conn.getresponse().status
                    # # print code
                    logger.debug(text)

                    statusitem = Gtk.MenuItem.new()
                    statusitem.show()


                    spinner = Gtk.Spinner.new()
                    spinner.start()
                    statusitem.add(spinner)
                    spinner.show()
                    
                    thread = threading.Thread(target=check_url, args=(text, statusitem, spinner))
                    thread.start()

                    item.set_label(_("Open Link in Webbrowser"))
                    item.show()
                    # # print menu, item
                    # conn.close()
                    menu.prepend(separator)
                    separator.show()
                    menu.prepend(item)
                    menu.show()
                    menu.prepend(statusitem)
                    found_match = True
                    break
        
        if not found_match:
            matches = re.finditer(image, text)
            for match in matches:
                if match.start() < line_offset and match.end() > line_offset:
                    path = match.group(2)
                    if path.startswith("file://"):
                        path = path[7:]
                    logger.info(path)
                    pb = GdkPixbuf.Pixbuf.new_from_file_at_size(path, 400, 300)
                    image = Gtk.Image.new_from_pixbuf(pb)
                    image.show()
                    item.add(image)
                    item.set_property('width-request', 50)
                    item.show()
                    menu.prepend(separator)
                    separator.show()
                    menu.prepend(item)
                    menu.show()
                    found_match = True
                    break

        if not found_match:
            matches = re.finditer(footnote, text)
            for match in matches:
                if match.start() < line_offset and match.end() > line_offset:
                    logger.debug(match.group(1))
                    footnote_match = re.compile("\[\^" + match.group(1) + "\]: (.+(?:\n|\Z)(?:^[\t].+(?:\n|\Z))*)", re.MULTILINE)
                    replace = re.compile("^\t", re.MULTILINE)
                    start, end = self.TextBuffer.get_bounds()
                    fn_match = re.search(footnote_match, self.TextBuffer.get_text(start, end, False))
                    label = Gtk.Label()
                    logger.debug(fn_match)
                    if fn_match:
                        result = re.sub(replace, "", fn_match.group(1))
                        if result.endswith("\n"):
                            result = result[:-1]
                    else: 
                        result = _("No matching footnote found")
                    label.set_max_width_chars(40)
                    label.set_line_wrap(True)
                    label.set_text(result)
                    label.show()
                    item.add(label)
                    item.show()
                    # # print menu, item
                    # conn.close()
                    menu.prepend(separator)
                    separator.show()
                    menu.prepend(item)
                    menu.show()
                    found_match = True
                    break
        return

    def move_popup(self):
        pass
