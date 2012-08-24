import re
from gi.repository import Gtk, Gdk # pylint: disable=E0611
from gi.repository import Pango # pylint: disable=E0611


class MarkupBuffer():
 
    def __init__(self, Parent, TextBuffer, base_leftmargin):
    	self.parent = Parent
    	self.TextBuffer = TextBuffer
        
        # Styles 

        self.italic = self.TextBuffer.create_tag("italic", 
            style=Pango.Style.ITALIC)

        self.emph = self.TextBuffer.create_tag("emph", 
            weight=Pango.Weight.BOLD,
            style =Pango.Style.NORMAL)

        self.normal_indent = self.TextBuffer.create_tag('normal_indent', indent=100)
        
        self.green_text = self.TextBuffer.create_tag(
            "greentext",
            foreground="#00364C"
           	)

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

        self.rev_leftmargin = []
        
        for i in range(0,6):
            name = "rev_marg_indent_left" + str(i)
            self.rev_leftmargin.append(self.TextBuffer.create_tag(name))
            self.rev_leftmargin[i].set_property("left-margin", 90 - 10*(i+1))
            self.rev_leftmargin[i].set_property("indent", - 10*(i+1) - 10)
            #self.leftmargin[i].set_property("background", "gray")

        self.leftmargin = []

        for i in range(0,6):
            name = "marg_indent_left" + str(i)
            self.leftmargin.append(self.TextBuffer.create_tag(name))
            self.leftmargin[i].set_property("left-margin", base_leftmargin + 10 + 10 * (i+1))
            self.leftmargin[i].set_property("indent", - 10*(i+1) - 10)

        self.leftindent = []

        for i in range(0,15):
            name = "indent_left" + str(i)
            self.leftindent.append(self.TextBuffer.create_tag(name))
            self.leftindent[i].set_property("indent", - 10*(i+1) - 20)

        self.table_env = self.TextBuffer.create_tag('table_env')
        self.table_env.set_property('wrap-mode', Gtk.WrapMode.NONE)


    # *asdasd* // _asdasd asd asd_ 
    ITALIC = re.compile(r"\*\w(.+?)\*| _\w(.+?)_ ")
    
    # **as das** // __asdasdasd asd ad a__
    EMPH = re.compile(r"\*{2}\w(.+?)\*{2}| [_]{2}\w(.+?)[_]{2} ")
    
    #ITALICEMPH = re.compile(r"\*{3}\w(.+?)\*{3}| [_]{3}\w(.+?)[_]{3} ")
    

    BLOCKQUOTE = re.compile(r"^([\>]+ )", re.MULTILINE)
    
    STRIKETHROUGH = re.compile(r"~~[^ `~\n].+?~~")
    
    LIST = re.compile(r"^[\-\*\+] ", re.MULTILINE)
    NUMERICLIST = re.compile(r"^((\d|[a-z]|\#)+[\.\)]) ", re.MULTILINE)
    INDENTEDLIST = re.compile(r"^(\t{1,6})((\d|[a-z]|\#)+[\.\)]|[\-\*\+]) ", re.MULTILINE)

    HEADINDICATOR = re.compile(r"^(#{1,6}) ", re.MULTILINE)
    HEADLINE = re.compile(r"^(#{1,6} [^\n]+)", re.MULTILINE)

    MATH = re.compile(r"\${1,2}[^` ](.+?)[^`\\ ]\${1,2}")

    HORIZONTALRULE = re.compile(r"(\n\n[\*\- ]{3,}\n)", re.MULTILINE)

    TABLE = re.compile(r"^:table:\n(.+?)\n:endtable:", re.DOTALL)


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
            cursor_mark = buf.get_insert()
            context_start = buf.get_iter_at_mark(cursor_mark)
            context_start.backward_lines(2)
            context_end = buf.get_iter_at_mark(cursor_mark)
            context_end.forward_lines(2)
            context_offset = context_start.get_offset()

    	text = buf.get_slice(context_start, context_end, False).decode("utf-8")
        text = unicode(text)

        self.TextBuffer.remove_tag(self.italic, context_start, context_end)

        matches = re.finditer(self.ITALIC, text)
    	for match in matches: 
            startIter = buf.get_iter_at_offset(context_offset + match.start())
            endIter = buf.get_iter_at_offset(context_offset + match.end())
            self.TextBuffer.apply_tag(self.italic, startIter, endIter)
        
        self.TextBuffer.remove_tag(self.emph, context_start, context_end)

        matches = re.finditer(self.EMPH, text)
        for match in matches:
            startIter = buf.get_iter_at_offset(context_offset + match.start())
            endIter = buf.get_iter_at_offset(context_offset + match.end())
            self.TextBuffer.apply_tag(self.emph, startIter, endIter)

        self.TextBuffer.remove_tag(self.strikethrough, context_start, context_end)

        matches = re.finditer(self.STRIKETHROUGH, text)
        for match in matches:
            startIter = buf.get_iter_at_offset(context_offset + match.start())
            endIter = buf.get_iter_at_offset(context_offset + match.end())
            self.TextBuffer.apply_tag(self.strikethrough, startIter, endIter)

        self.TextBuffer.remove_tag(self.green_text, context_start, context_end)

        matches = re.finditer(self.MATH, text) 
        for match in matches:
            startIter = buf.get_iter_at_offset(context_offset + match.start())
            endIter = buf.get_iter_at_offset(context_offset + match.end())
            self.TextBuffer.apply_tag(self.green_text, startIter, endIter)

        for margin in self.rev_leftmargin:
            self.TextBuffer.remove_tag(margin, context_start, context_end)

        matches = re.finditer(self.LIST, text) 
        for match in matches:
            startIter = buf.get_iter_at_offset(context_offset + match.start())
            endIter = buf.get_iter_at_offset(context_offset + match.end())
            self.TextBuffer.apply_tag(self.rev_leftmargin[0], startIter, endIter)
   
        matches = re.finditer(self.NUMERICLIST, text)
        for match in matches:
            startIter = buf.get_iter_at_offset(context_offset + match.start())
            endIter = buf.get_iter_at_offset(context_offset + match.end())
            index = len(match.group(1)) - 1
            if index < len(self.rev_leftmargin):
                margin = self.rev_leftmargin[index]
                self.TextBuffer.apply_tag(margin, startIter, endIter)

        matches = re.finditer(self.BLOCKQUOTE, text) 
        for match in matches:
            startIter = buf.get_iter_at_offset(context_offset + match.start())
            endIter = buf.get_iter_at_offset(context_offset + match.end())
            index = len(match.group(1)) - 2
            if index < len(self.leftmargin):
                self.TextBuffer.apply_tag(self.leftmargin[index], startIter, endIter)

        for leftindent in self.leftindent:
            self.TextBuffer.remove_tag(leftindent, context_start, context_end)

        matches = re.finditer(self.INDENTEDLIST, text)
        for match in matches:
            startIter = buf.get_iter_at_offset(context_offset + match.start())
            endIter = buf.get_iter_at_offset(context_offset + match.end())
            index = (len(match.group(1)) - 1)*2 + len(match.group(2))
            if index < len(self.leftindent):
                self.TextBuffer.apply_tag(self.leftindent[index], startIter, endIter)

        matches = re.finditer(self.HEADINDICATOR, text) 
        for match in matches:
            startIter = buf.get_iter_at_offset(context_offset + match.start())
            endIter = buf.get_iter_at_offset(context_offset + match.end())
            index = len(match.group(1)) - 1
            if index < len(self.rev_leftmargin):
                margin = self.rev_leftmargin[index]
                self.TextBuffer.apply_tag(margin, startIter, endIter)

        matches = re.finditer(self.HORIZONTALRULE, text)
        self.TextBuffer.remove_tag(self.centertext, context_start, context_end)

        for match in matches:
            startIter = buf.get_iter_at_offset(context_offset + match.start())
            startIter.forward_chars(2)
            endIter = buf.get_iter_at_offset(context_offset + match.end())
            self.TextBuffer.apply_tag(self.centertext, startIter, endIter)

        matches = re.finditer(self.HEADLINE, text) 
        for match in matches:
            startIter = buf.get_iter_at_offset(context_offset + match.start())
            endIter = buf.get_iter_at_offset(context_offset + match.end())
            self.TextBuffer.apply_tag(self.emph, startIter, endIter)
        

        matches = re.finditer(self.TABLE, text) 
        for match in matches:
            startIter = buf.get_iter_at_offset(context_offset + match.start())
            endIter = buf.get_iter_at_offset(context_offset + match.end())
            self.TextBuffer.apply_tag(self.table_env, startIter, endIter)


        if self.parent.focusmode:
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

    def recalculate(self, lm):
    	for i in range(0,6):
    	    name = "rev_indent_left" + str(i)
    	    self.rev_leftmargin[i].set_property("left-margin", (lm-10) - 10*(i+1))
    	    self.rev_leftmargin[i].set_property("indent", - 10*(i+1) - 10)

    	for i in range(0,6):
    	    self.leftmargin[i].set_property("left-margin", (lm-10) + 10 + 10 * (i+1))
    	    self.leftmargin[i].set_property("indent", - 9*(i+1) - 10) ## Was - 10 ...