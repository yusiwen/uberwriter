import re
import http.client, urllib


from gi.repository import Gtk
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
			x, y = self.TextView.window_to_buffer_coords(2, int(event.x), int(event.y))
			self.TextBuffer.move_mark(self.ClickMark, self.TextView.get_iter_at_location(x, y))

	def populate_popup(self, editor, menu,  data=None):
		## Begin vovvvk

		item = Gtk.MenuItem.new()

		start_iter = self.TextBuffer.get_iter_at_mark(self.ClickMark)
		end_iter = start_iter.copy()
		start_iter.set_line_offset(0)
		end_iter.forward_to_line_end()

		text = self.TextBuffer.get_text(start_iter, end_iter, False)


		math = MarkupBuffer.regex["MATH"]
		link = MarkupBuffer.regex["LINK"]

		buf = self.TextBuffer
		context_offset = 0

		matches = re.findall(math, text)
		for match in matches:
			logger.debug(match)
			latex_image = self.LatexConverter.generatepng(match)
			image = Gtk.Image.new_from_file(latex_image)
			image.show()
			item.add(image)
			item.set_property('width-request', 50)
			item.show()
			# print menu, item
			menu.prepend(item)
			menu.show()

		matches = re.finditer(link, text)
		for match in matches:
			text = text[text.find("http://"):-1] # get off brackets and other text
			# print text
			url = urllib.parse.urlparse(text)
			# netloc = url.netloc
			# path = url.path
			conn = http.client.HTTPConnection(url.netloc)
			conn.request("HEAD", url.path)
			code = conn.getresponse().status
			# print code
			label = Gtk.Label()
			label.set_text(str(code))
			label.show()
			item.add(label)
			item.show()
			# print menu, item
			menu.prepend(item)
			menu.show()
			conn.close()

		### END
		# item = Gtk.MenuItem.new()

		# start_iter = self.TextBuffer.get_iter_at_mark(self.ClickMark)
		# end_iter = start_iter.copy()
		# start_iter.set_line_offset(0)
		# end_iter.forward_to_line_end()

		# text = self.TextBuffer.get_text(start_iter, end_iter, False)
		# #print text
		# latex_image = self.LatexConverter.generatepng('$\\frac{d}{dx}\\left( \\int_{0}^{x} f(u)\\,du\\right)=f(x).$')

		# image = Gtk.Image.new_from_file(latex_image)
		# image.show()
		# item.add(image)
		# item.set_property('width-request', 50)
		# item.show()
		# #print menu, item
		# menu.prepend(item)
		# menu.show()

	def move_popup(self):
		pass