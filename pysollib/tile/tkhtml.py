#!/usr/bin/env python
# -*- mode: python; coding: utf-8; -*-
##---------------------------------------------------------------------------##
##
## Copyright (C) 1998-2003 Markus Franz Xaver Johannes Oberhumer
## Copyright (C) 2003 Mt. Hood Playing Card Co.
## Copyright (C) 2005-2009 Skomoroh
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
##---------------------------------------------------------------------------##

__all__ = ['HTMLViewer']

# imports
import os, sys
import formatter
import Tkinter
import ttk

if __name__ == '__main__':
    d = os.path.abspath(os.path.join(sys.path[0], '..', '..'))
    sys.path.append(d)
    import gettext
    gettext.install('pysol', d, unicode=True)

# PySol imports
from pysollib.mygettext import _, n_
from pysollib.mfxutil import Struct, openURL
from pysollib.settings import TITLE

# Toolkit imports
from pysollib.ui.tktile.tkutil import bind, unbind_destroy
from tkwidget import MfxMessageDialog
from statusbar import HtmlStatusbar

from pysollib.ui.tktile.tkhtml import REMOTE_PROTOCOLS, tkHTMLWriter, tkHTMLParser

# ************************************************************************
# *
# ************************************************************************

class HTMLViewer:
    symbols_fn = {}  # filenames, loaded in Application.loadImages3
    symbols_img = {}

    def __init__(self, parent, app=None, home=None):
        self.parent = parent
        self.app = app
        self.home = home
        self.url = None
        self.history = Struct(
            list = [],
            index = 0,
        )
        self.visited_urls = []
        self.images = {}    # need to keep a reference because of garbage collection
        self.defcursor = parent["cursor"]
        ##self.defcursor = 'xterm'
        self.handcursor = "hand2"

        frame = ttk.Frame(parent, width=640, height=440)
        frame.pack(expand=True, fill='both')
        frame.grid_propagate(False)

        # create buttons
        button_width = 8
        self.homeButton = ttk.Button(frame, text=_("Index"),
                                     width=button_width,
                                     command=self.goHome)
        self.homeButton.grid(row=0, column=0, sticky='w')
        self.backButton = ttk.Button(frame, text=_("Back"),
                                     width=button_width,
                                     command=self.goBack)
        self.backButton.grid(row=0, column=1, sticky='w')
        self.forwardButton = ttk.Button(frame, text=_("Forward"),
                                        width=button_width,
                                        command=self.goForward)
        self.forwardButton.grid(row=0, column=2, sticky='w')
        self.closeButton = ttk.Button(frame, text=_("Close"),
                                      width=button_width,
                                      command=self.destroy)
        self.closeButton.grid(row=0, column=3, sticky='e')

        # create text widget
        text_frame = ttk.Frame(frame)
        text_frame.grid(row=1, column=0, columnspan=4,
                        sticky='nsew', padx=1, pady=1)
        vbar = ttk.Scrollbar(text_frame)
        vbar.pack(side='right', fill='y')
        self.text = Tkinter.Text(text_frame,
                                 fg='black', bg='white',
                                 bd=1, relief='sunken',
                                 cursor=self.defcursor,
                                 wrap='word', padx=10)
        self.text.pack(side='left', fill='both', expand=True)
        self.text["yscrollcommand"] = vbar.set
        vbar["command"] = self.text.yview

        # statusbar
        self.statusbar = HtmlStatusbar(frame, row=2, column=0, columnspan=4)

        frame.columnconfigure(2, weight=1)
        frame.rowconfigure(1, weight=1)

        # load images
        for name, fn in self.symbols_fn.items():
            self.symbols_img[name] = self.getImage(fn)

        self.initBindings()

    def initBindings(self):
        w = self.parent
        bind(w, "WM_DELETE_WINDOW", self.destroy)
        bind(w, "<Escape>", self.destroy)
        bind(w, "<KeyPress-Prior>", self.page_up)
        bind(w, "<KeyPress-Next>", self.page_down)
        bind(w, "<KeyPress-Up>", self.unit_up)
        bind(w, "<KeyPress-Down>", self.unit_down)
        bind(w, "<KeyPress-Begin>", self.scroll_top)
        bind(w, "<KeyPress-Home>", self.scroll_top)
        bind(w, "<KeyPress-End>", self.scroll_bottom)
        bind(w, "<KeyPress-BackSpace>", self.goBack)

    def destroy(self, *event):
        unbind_destroy(self.parent)
        try:
            self.parent.wm_withdraw()
        except: pass
        try:
            self.parent.destroy()
        except: pass
        self.parent = None

    def _yview(self, *args):
        self.text.yview(*args)
        return 'break'

    def page_up(self, *event):
        return self._yview('scroll', -1, 'page')
    def page_down(self, *event):
        return self._yview('scroll', 1, 'page')
    def unit_up(self, *event):
        return self._yview('scroll', -1, 'unit')
    def unit_down(self, *event):
        return self._yview('scroll', 1, 'unit')
    def scroll_top(self, *event):
        return self._yview('moveto', 0)
    def scroll_bottom(self, *event):
        return self._yview('moveto', 1)

    # locate a file relative to the current self.url
    def basejoin(self, url, baseurl=None, relpath=1):
        if baseurl is None:
            baseurl = self.url
        if 0:
            import urllib
            url = urllib.pathname2url(url)
            if relpath and self.url:
                url = urllib.basejoin(baseurl, url)
        else:
            url = os.path.normpath(url)
            if relpath and baseurl and not os.path.isabs(url):
                h1, t1 = os.path.split(url)
                h2, t2 = os.path.split(baseurl)
                if cmp(h1, h2) != 0:
                    url = os.path.join(h2, h1, t1)
                url = os.path.normpath(url)
        return url

    def normurl(self, url, with_protocol=True):
        for p in REMOTE_PROTOCOLS:
            if url.startswith(p):
                break
        else:
            url = self.basejoin(url)
            if with_protocol:
                if os.name == 'nt':
                    url = url.replace('\\', '/')
                url = 'file://'+url
        return url

    def openfile(self, url):
        if url[-1:] == "/" or os.path.isdir(url):
            url = os.path.join(url, "index.html")
        url = os.path.normpath(url)
        return open(url, "rb"), url

    def display(self, url, add=1, relpath=1, xview=0, yview=0):
        # for some reason we have to stop the PySol demo
        # (is this a multithread problem with Tkinter ?)
        if self.app and self.app.game:
            self.app.game.stopDemo()
            ##self.app.game._cancelDrag()
            ##pass

        # ftp: and http: would work if we use urllib, but this widget is
        # far too limited to display anything but our documentation...
        for p in REMOTE_PROTOCOLS:
            if url.startswith(p):
                if not openURL(url):
                    self.errorDialog(TITLE + _('''HTML limitation:
The %s protocol is not supported yet.

Please use your standard web browser
to open the following URL:
%s
''') % (p, url))
                return

        # locate the file relative to the current url
        url = self.basejoin(url, relpath=relpath)

        # read the file
        try:
            file = None
            if 0:
                import urllib
                file = urllib.urlopen(url)
            else:
                file, url = self.openfile(url)
            data = file.read()
            file.close()
            file = None
        except Exception, ex:
            if file: file.close()
            self.errorDialog(_("Unable to service request:\n") + url + "\n\n" + str(ex))
            return
        except:
            if file: file.close()
            self.errorDialog(_("Unable to service request:\n") + url)
            return

        self.url = url
        if self.home is None:
            self.home = self.url
        if add:
            self.addHistory(self.url, xview=xview, yview=yview)

        ##print self.history.index, self.history.list
        if self.history.index > 1:
            self.backButton.config(state="normal")
        else:
            self.backButton.config(state="disabled")
        if self.history.index < len(self.history.list):
            self.forwardButton.config(state="normal")
        else:
            self.forwardButton.config(state="disabled")

        old_c1, old_c2 = self.defcursor, self.handcursor
        self.defcursor = self.handcursor = "watch"
        self.text.config(cursor=self.defcursor)
        self.text.update_idletasks()
        ##self.frame.config(cursor=self.defcursor)
        ##self.frame.update_idletasks()
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        ##self.images = {}
        writer = tkHTMLWriter(self.text, self, self.app)
        fmt = formatter.AbstractFormatter(writer)
        parser = tkHTMLParser(fmt)
        parser.feed(data)
        parser.close()
        self.text.config(state="disabled")
        if 0.0 <= xview <= 1.0:
            self.text.xview_moveto(xview)
        if 0.0 <= yview <= 1.0:
            self.text.yview_moveto(yview)
        self.parent.wm_title(parser.title)
        self.parent.wm_iconname(parser.title)
        self.defcursor, self.handcursor = old_c1, old_c2
        self.text.config(cursor=self.defcursor)
        ##self.frame.config(cursor=self.defcursor)

    def addHistory(self, url, xview=0, yview=0):
        if url not in self.visited_urls:
            self.visited_urls.append(url)
        if self.history.index > 0:
            u, xv, yv = self.history.list[self.history.index-1]
            if cmp(u, url) == 0:
                self.updateHistoryXYView()
                return
        del self.history.list[self.history.index : ]
        self.history.list.append((url, xview, yview))
        self.history.index = self.history.index + 1

    def updateHistoryXYView(self):
        if self.history.index > 0:
            url, xview, yview = self.history.list[self.history.index-1]
            xview = self.text.xview()[0]
            yview = self.text.yview()[0]
            self.history.list[self.history.index-1] = (url, xview, yview)

    def goBack(self, *event):
        if self.history.index > 1:
            self.updateHistoryXYView()
            self.history.index = self.history.index - 1
            url, xview, yview = self.history.list[self.history.index-1]
            self.display(url, add=0, relpath=0, xview=xview, yview=yview)

    def goForward(self, *event):
        if self.history.index < len(self.history.list):
            self.updateHistoryXYView()
            url, xview, yview = self.history.list[self.history.index]
            self.history.index = self.history.index + 1
            self.display(url, add=0, relpath=0, xview=xview, yview=yview)

    def goHome(self, *event):
        if self.home and cmp(self.home, self.url) != 0:
            self.updateHistoryXYView()
            self.display(self.home, relpath=0)

    def errorDialog(self, msg):
        d = MfxMessageDialog(self.parent, title=TITLE+" HTML Problem",
                             text=msg,
                             ##bitmap="warning", # FIXME: this interp don't have images
                             strings=(_("&OK"),), default=0)

    def getImage(self, fn):
        if fn in self.images:
            return self.images[fn]
        try:
            img = Tkinter.PhotoImage(master=self.parent, file=fn)
        except:
            img = None
        self.images[fn] = img
        return img

    def showImage(self, src, alt, ismap, align, width, height):
        url = self.basejoin(src)
        img = self.getImage(url)
        if img:
            self.text.image_create(index="insert", image=img, padx=0, pady=0)



# ************************************************************************
# *
# ************************************************************************


def tkhtml_main(args):
    try:
        url = args[1]
    except:
        url = os.path.join(os.pardir, os.pardir, "data", "html", "index.html")
    top = Tkinter.Tk()
    top.tk.call("package", "require", "tile")
    top.wm_minsize(400, 200)
    viewer = HTMLViewer(top)
    viewer.app = None
    viewer.display(url)
    top.mainloop()
    return 0

if __name__ == "__main__":
    sys.exit(tkhtml_main(sys.argv))


