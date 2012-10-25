import re
import http.client
import urllib
import webbrowser

from gi.repository import Gtk, Gdk
from uberwriter_lib import LatexToPNG

from .MarkupBuffer import MarkupBuffer

import logging
logger = logging.getLogger('uberwriter')


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
        ## Begin vovvvk

        item = Gtk.MenuItem.new()
        item.set_name("PreviewMenuItem")
        separator = Gtk.SeparatorMenuItem.new()

        start_iter = self.TextBuffer.get_iter_at_mark(self.ClickMark)
        # Line offset of Click Marke
        line_offset = start_iter.get_line_offset()
        end_iter = start_iter.copy()
        start_iter.set_line_offset(0)
        end_iter.forward_to_line_end()

        text = self.TextBuffer.get_text(start_iter, end_iter, False)

        math = MarkupBuffer.regex["MATH"]
        link = MarkupBuffer.regex["LINK"]

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
                    label = Gtk.Label()
                    label.set_text("Open Link in Webbrowser")
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
