from gi.repository import Gtk, Gdk, GObject

class FadeLabel(Gtk.Label):
    """ Gtk Label with timed fade out effect """

    active_duration = 3000  # Fade start after this time
    fade_duration = 1500.0  # Fade duration

    def __init__(self, message='', active_color=None, inactive_color=None):
        Gtk.Label.__init__(self, message)
        if not active_color:
            active_color = '#ffffff'
        self.active_color = active_color
        if not inactive_color:
            inactive_color = '#000000'
        self.fade_level = 0
        self.inactive_color = inactive_color
        self.idle = 0

    def set_text(self, message, duration=None):
        """change text that is displayed
        @param message: message to display
        @param duration: duration in miliseconds"""
        if not duration:
            duration = self.active_duration
        self.modify_fg(Gtk.StateFlags.NORMAL,
                       Gdk.color_parse(self.active_color))
        Gtk.Label.set_text(self, message)
        if self.idle:
            GObject.source_remove(self.idle)
        self.idle = GObject.timeout_add(duration, self.fade_start)

    def fade_start(self):
        """start fading timer"""
        self.fade_level = 1.0
        if self.idle:
            GObject.source_remove(self.idle)
        self.idle = GObject.timeout_add(25, self.fade_out)

    def fade_out(self):
        """now fade out"""
        print "fadeout"
        color = Gdk.color_parse(self.inactive_color)
        (red1, green1, blue1) = (color.red, color.green, color.blue)
        color = Gdk.color_parse(self.active_color)
        (red2, green2, blue2) = (color.red, color.green, color.blue)
        red = red1 + int(self.fade_level * (red2 - red1))
        green = green1 + int(self.fade_level * (green2 - green1))
        blue = blue1 + int(self.fade_level * (blue2 - blue1))
        self.modify_fg(Gtk.StateFlags.NORMAL, Gdk.Color(red, green, blue))
        self.fade_level -= 1.0 / (self.fade_duration / 25)
        if self.fade_level > 0:
            return True
        self.idle = 0
        return False