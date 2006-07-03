## vim:ts=4:et:nowrap
##
##---------------------------------------------------------------------------##
##
## PySol -- a Python Solitaire game
##
## Copyright (C) 2003 Markus Franz Xaver Johannes Oberhumer
## Copyright (C) 2002 Markus Franz Xaver Johannes Oberhumer
## Copyright (C) 2001 Markus Franz Xaver Johannes Oberhumer
## Copyright (C) 2000 Markus Franz Xaver Johannes Oberhumer
## Copyright (C) 1999 Markus Franz Xaver Johannes Oberhumer
## Copyright (C) 1998 Markus Franz Xaver Johannes Oberhumer
## All Rights Reserved.
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; see the file COPYING.
## If not, write to the Free Software Foundation, Inc.,
## 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
##
## Markus F.X.J. Oberhumer
## <markus@oberhumer.com>
## http://www.oberhumer.com/pysol
##
##---------------------------------------------------------------------------##

__all__ = ['SoundOptionsDialog']

# imports
import os, sys, string
from Tkinter import *
import traceback

# PySol imports
from pysollib.mfxutil import destruct, kwdefault, KwStruct, Struct, spawnvp
from pysollib.settings import PACKAGE
from pysollib.pysolaudio import pysolsoundserver
from pysollib.settings import MIXERS

# Toolkit imports
from tkconst import EVENT_HANDLED, EVENT_PROPAGATE
from tkwidget import MfxDialog, MfxMessageDialog

# /***********************************************************************
# //
# ************************************************************************/

class SoundOptionsDialog(MfxDialog):
    MIXER = ()

    def __init__(self, parent, title, app, **kw):
        self.app = app
        kw = self.initKw(kw)
        MfxDialog.__init__(self, parent, title, kw.resizable, kw.default)
        top_frame, bottom_frame = self.createFrames(kw)
        self.createBitmaps(top_frame, kw)
        #
        self.saved_opt = app.opt.copy()
        self.sound = BooleanVar()
        self.sound.set(app.opt.sound != 0)
        self.sound_mode = BooleanVar()
        self.sound_mode.set(app.opt.sound_mode != 0)
        self.sample_volume = IntVar()
        self.sample_volume.set(app.opt.sound_sample_volume)
        self.music_volume = IntVar()
        self.music_volume.set(app.opt.sound_music_volume)
        self.samples = [
            ('areyousure',    _('Are You Sure'),   BooleanVar()),

            ('deal',          _('Deal'),           BooleanVar()),
            ('dealwaste',     _('Deal waste'),     BooleanVar()),

            ('turnwaste',     _('Turn waste'),     BooleanVar()),
            ('startdrag',     _('Start drag'),     BooleanVar()),

            ('drop',          _('Drop'),           BooleanVar()),
            ('droppair',      _('Drop pair'),      BooleanVar()),
            ('autodrop',      _('Auto drop'),      BooleanVar()),

            ('flip',          _('Flip'),           BooleanVar()),
            ('autoflip',      _('Auto flip'),      BooleanVar()),
            ('move',          _('Move'),           BooleanVar()),
            ('nomove',        _('No move'),        BooleanVar()),

            ('undo',          _('Undo'),           BooleanVar()),
            ('redo',          _('Redo'),           BooleanVar()),

            ('autopilotlost', _('Autopilot lost'), BooleanVar()),
            ('autopilotwon',  _('Autopilot won'),  BooleanVar()),

            ('gamefinished',  _('Game finished'),  BooleanVar()),
            ('gamelost',      _('Game lost'),      BooleanVar()),
            ('gamewon',       _('Game won'),       BooleanVar()),
            ('gameperfect',   _('Perfect game'),   BooleanVar()),
            ]

        #
        frame = Frame(top_frame)
        frame.pack(expand=1, fill='both', padx=5, pady=5)
        frame.columnconfigure(1, weight=1)
        #
        row = 0
        w = Checkbutton(frame, variable=self.sound,
                                text=_("Sound enabled"), anchor='w')
        w.grid(row=row, column=0, columnspan=2, sticky='ew')
        #
        if os.name == "nt" and pysolsoundserver:
            row += 1
            w = Checkbutton(frame, variable=self.sound_mode,
                                    text=_("Use DirectX for sound playing"),
                                    command=self.mOptSoundDirectX, anchor='w')
            w.grid(row=row, column=0, columnspan=2, sticky='ew')
        #
        if pysolsoundserver and app.startup_opt.sound_mode > 0:
            row += 1
            w = Label(frame, text=_('Sample volume:'))
            w.grid(row=row, column=0, sticky='w')
            w = Scale(frame, from_=0, to=128, resolution=1,
                      orient='horizontal', takefocus=0,
                      length="3i", #label=_('Sample volume'),
                      variable=self.sample_volume)
            w.grid(row=row, column=1, sticky='w', padx=5)
            row += 1
            w = Label(frame, text=_('Music volume:'))
            w.grid(row=row, column=0, sticky='w', padx=5)
            w = Scale(frame, from_=0, to=128, resolution=1,
                      orient='horizontal', takefocus=0,
                      length="3i", #label=_('Music volume'),
                      variable=self.music_volume)
            w.grid(row=row, column=1, sticky='w', padx=5)

        else:
            # remove "Apply" button
            kw.strings[1] = None
        #
        if TkVersion >= 8.4:
            frame = LabelFrame(top_frame, text=_('Enable samles'), padx=5, pady=5)
        else:
            frame = Frame(top_frame)
        frame.pack(expand=1, fill='both', padx=5, pady=5)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        #
        row = 0
        col = 0
        for n, t, v in self.samples:
            v.set(app.opt.sound_samples[n])
            w = Checkbutton(frame, text=t, anchor='w', variable=v)
            w.grid(row=row, column=col, sticky='ew')
            if col == 1:
                col = 0
                row += 1
            else:
                col = 1
        #
        top_frame.columnconfigure(1, weight=1)
        #
        focus = self.createButtons(bottom_frame, kw)
        self.mainloop(focus, kw.timeout)

    def initKw(self, kw):
        strings=[_("&OK"), _("&Apply"), _("&Mixer..."), _("&Cancel"),]
        if self.MIXER is None:
            strings[2] = (_("&Mixer..."), -1)
##        if os.name != "nt" and not self.app.debug:
##            strings[2] = None
        kw = KwStruct(kw,
                      strings=strings,
                      default=0,
                      resizable=1,
                      padx=10, pady=10,
                      buttonpadx=1, buttonpady=5,
                      )
        return MfxDialog.initKw(self, kw)

    def mDone(self, button):
        if button == 0 or button == 1:
            self.app.opt.sound = self.sound.get()
            self.app.opt.sound_mode = self.sound_mode.get()
            self.app.opt.sound_sample_volume = self.sample_volume.get()
            self.app.opt.sound_music_volume = self.music_volume.get()
            for n, t, v in self.samples:
                self.app.opt.sound_samples[n] = v.get()
        elif button == 2:
            for name, args in MIXERS:
                try:
                    f = spawnvp(name, args)
                    if f:
                        self.MIXER = (f, args)
                        return
                except:
                    if traceback: traceback.print_exc()
                    pass
            self.MIXER = None
        elif button == 3:
            self.app.opt = self.saved_opt
        if self.app.audio:
            self.app.audio.updateSettings()
            if button == 1:
                self.app.audio.playSample("drop", priority=1000)
        if button == 1:
            return EVENT_HANDLED
        return MfxDialog.mDone(self, button)

    def mCancel(self, *event):
        return self.mDone(2)

    def wmDeleteWindow(self, *event):
        return self.mDone(0)

    def mOptSoundDirectX(self, *event):
        ##print self.sound_mode.get()
        d = MfxMessageDialog(self.top, title=_("Sound preferences info"),
                      text=_("Changing DirectX settings will take effect\nthe next time you restart ")+PACKAGE,
                      bitmap="warning",
                      default=0, strings=(_("&OK"),))
