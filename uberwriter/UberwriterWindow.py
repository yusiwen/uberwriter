# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import gettext
from gettext import gettext as _
gettext.textdomain('uberwriter')

from gi.repository import Gtk # pylint: disable=E0611
import logging
logger = logging.getLogger('uberwriter')

from uberwriter_lib import Window
from uberwriter.AboutUberwriterDialog import AboutUberwriterDialog
from uberwriter.PreferencesUberwriterDialog import PreferencesUberwriterDialog

# See uberwriter_lib.Window.py for more details about how this class works
class UberwriterWindow(Window):
    __gtype_name__ = "UberwriterWindow"
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(UberwriterWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutUberwriterDialog
        self.PreferencesDialog = PreferencesUberwriterDialog

        # Code for other initialization actions should be added here.

