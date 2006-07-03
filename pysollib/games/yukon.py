## vim:ts=4:et:nowrap
##
##---------------------------------------------------------------------------##
##
## PySol -- a Python Solitaire game
##
## Copyright (C) 2000 Markus Franz Xaver Johannes Oberhumer
## Copyright (C) 1999 Markus Franz Xaver Johannes Oberhumer
## Copyright (C) 1998 Markus Franz Xaver Johannes Oberhumer
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

__all__ = []

# imports
import sys

# PySol imports
from pysollib.gamedb import registerGame, GameInfo, GI
from pysollib.util import *
from pysollib.mfxutil import kwdefault
from pysollib.stack import *
from pysollib.game import Game
from pysollib.layout import Layout
from pysollib.hint import AbstractHint, DefaultHint, CautiousDefaultHint
from pysollib.hint import YukonType_Hint
from pysollib.pysoltk import MfxCanvasText

from spider import Spider_SS_Foundation

# /***********************************************************************
# //
# ************************************************************************/

class Yukon_Hint(YukonType_Hint):
    BONUS_FLIP_CARD = 9000
    BONUS_CREATE_EMPTY_ROW = 100

    ## FIXME: this is only a rough approximation and doesn't seem to help
    ##        for Russian Solitaire
    def _getMovePileScore(self, score, color, r, t, pile, rpile):
        s, color = YukonType_Hint._getMovePileScore(self, score, color, r, t, pile, rpile)
        bonus = s - score
        assert 0 <= bonus <= 9999
        # We must take care when moving piles that we won't block cards,
        # i.e. if there is a card in pile which would be needed
        # for a card in stack t.
        tpile = t.getPile()
        if tpile:
            for cr in pile:
                rr = self.ClonedStack(r, stackcards=[cr])
                for ct in tpile:
                    if rr.acceptsCards(t, [ct]):
                        d = bonus / 1000
                        bonus = (d * 1000) + bonus % 100
                        break
        return score + bonus, color


# /***********************************************************************
# // Yukon
# ************************************************************************/

class Yukon(Game):
    Layout_Method = Layout.yukonLayout
    Talon_Class = InitialDealTalonStack
    Foundation_Class = SS_FoundationStack
    RowStack_Class = StackWrapper(Yukon_AC_RowStack, base_rank=KING)
    Hint_Class = Yukon_Hint


    def createGame(self, **layout):
        # create layout
        l, s = Layout(self), self.s
        kwdefault(layout, rows=7, texts=0, playcards=25)
        apply(self.Layout_Method, (l,), layout)
        self.setSize(l.size[0], l.size[1])
        # create stacks
        s.talon =self.Talon_Class(l.s.talon.x, l.s.talon.y, self)
        for r in l.s.foundations:
            s.foundations.append(self.Foundation_Class(r.x, r.y, self, suit=r.suit,
                                                       max_move=0))
        for r in l.s.rows:
            s.rows.append(self.RowStack_Class(r.x, r.y, self))
        # default
        l.defaultAll()
        return l

    def startGame(self):
        for i in range(1, len(self.s.rows)):
            self.s.talon.dealRow(rows=self.s.rows[i:], flip=0, frames=0)
        for i in range(4):
            self.s.talon.dealRow(rows=self.s.rows[1:], flip=1, frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        assert len(self.s.talon.cards) == 0

    def getHighlightPilesStacks(self):
        return ()

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.color != card2.color and
                (card1.rank + 1 == card2.rank or card2.rank + 1 == card1.rank))


# /***********************************************************************
# // Russian Solitaire (like Yukon, but build down by suit)
# ************************************************************************/

class RussianSolitaire(Yukon):
    RowStack_Class = StackWrapper(Yukon_SS_RowStack, base_rank=KING)

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.suit == card2.suit and
                (card1.rank + 1 == card2.rank or card2.rank + 1 == card1.rank))


# /***********************************************************************
# // Moosehide (build down in any suit but the same)
# ************************************************************************/

class Moosehide_RowStack(Yukon_AC_RowStack):
    def _isSequence(self, c1, c2):
        return (c1.suit != c2.suit and c1.rank == c2.rank+1)
    def getHelp(self):
        return _('Row. Build down in any suit but the same, can move any face-up cards regardless of sequence.')

class Moosehide(Yukon):
    RowStack_Class = StackWrapper(Moosehide_RowStack, base_rank=KING)

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.suit != card2.suit and
                abs(card1.rank-card2.rank) == 1)


# /***********************************************************************
# // Odessa (just like Russian Solitaire, only a different initial
# // card layout)
# ************************************************************************/

class Odessa(RussianSolitaire):
    def startGame(self):
        for i in range(3):
            self.s.talon.dealRow(flip=0, frames=0)
        for i in range(2):
            self.s.talon.dealRow(frames=0)
        for i in range(2):
            self.s.talon.dealRow(rows=self.s.rows[1:6], frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        assert len(self.s.talon.cards) == 0


# /***********************************************************************
# // Grandfather
# ************************************************************************/

class Grandfather(RussianSolitaire):
    def startGame(self):
        n = 1
        for i in (2,4,6,5,3,1):
            self.s.talon.dealRow(rows=[self.s.rows[n]]*i, flip=0, frames=0)
            n += 1
        n = 0
        self.startDealSample()
        for i in (1,5,5,5,5,5,5):
            self.s.talon.dealRow(rows=[self.s.rows[n]]*i)
            n += 1
        assert len(self.s.talon.cards) == 0


# /***********************************************************************
# // Alaska (like Russian Solitaire, but build up or down in suit)
# ************************************************************************/

class Alaska_RowStack(Yukon_SS_RowStack):
    def _isSequence(self, c1, c2):
        return (c1.suit == c2.suit and
                ((c1.rank + self.cap.dir) % self.cap.mod == c2.rank or
                 (c2.rank + self.cap.dir) % self.cap.mod == c1.rank))
    def getHelp(self):
        return _('Row. Build up or down by suit, can move any face-up cards regardless of sequence.')


class Alaska(RussianSolitaire):
    RowStack_Class = StackWrapper(Alaska_RowStack, base_rank=KING)


# /***********************************************************************
# // Roslin (like Yukon, but build up or down by alternate color)
# ************************************************************************/

class Roslin_RowStack(Yukon_AC_RowStack):
    def _isSequence(self, c1, c2):
        return (c1.color != c2.color and
                ((c1.rank + self.cap.dir) % self.cap.mod == c2.rank or
                 (c2.rank + self.cap.dir) % self.cap.mod == c1.rank))
    def getHelp(self):
        return _('Row. Build up or down by alternate color, can move any face-up cards regardless of sequence.')


class Roslin(Yukon):
    RowStack_Class = StackWrapper(Roslin_RowStack, base_rank=KING)


# /***********************************************************************
# // Chinese Discipline
# // Chinese Solitaire
# ************************************************************************/

class ChineseDiscipline(Yukon):
    Layout_Method = Layout.klondikeLayout
    Talon_Class = DealRowTalonStack

    def createGame(self):
        return Yukon.createGame(self, waste=0, texts=1)

    def startGame(self):
        for i in (3, 3, 3, 4, 5, 6):
            self.s.talon.dealRow(rows=self.s.rows[:i], flip=1, frames=0)
            self.s.talon.dealRow(rows=self.s.rows[i:], flip=0, frames=0)
        self.startDealSample()
        self.s.talon.dealRow()


class ChineseSolitaire(ChineseDiscipline):
    RowStack_Class = Yukon_AC_RowStack      # anything on an empty space


# /***********************************************************************
# // Queenie
# ************************************************************************/

class Queenie(Yukon):
    Layout_Method = Layout.klondikeLayout
    Talon_Class = DealRowTalonStack

    def createGame(self):
        return Yukon.createGame(self, waste=0, texts=1)

    def startGame(self, flip=1, reverse=1):
        for i in range(1, len(self.s.rows)):
            self.s.talon.dealRow(rows=self.s.rows[i:], flip=flip, frames=0, reverse=reverse)
        self.startDealSample()
        self.s.talon.dealRow(reverse=reverse)


# /***********************************************************************
# // Rushdike (like Queenie, but built down by suit)
# ************************************************************************/

class Rushdike(RussianSolitaire):
    Layout_Method = Layout.klondikeLayout
    Talon_Class = DealRowTalonStack

    def createGame(self):
        return RussianSolitaire.createGame(self, waste=0, texts=1)

    def startGame(self, flip=0, reverse=1):
        for i in range(1, len(self.s.rows)):
            self.s.talon.dealRow(rows=self.s.rows[i:], flip=flip, frames=0, reverse=reverse)
        self.startDealSample()
        self.s.talon.dealRow(reverse=reverse)


# /***********************************************************************
# // Russian Point (Rushdike in a different layout)
# ************************************************************************/

class RussianPoint(Rushdike):
    def startGame(self):
        r = self.s.rows
        for i in (1, 1, 2, 2, 3, 3):
            self.s.talon.dealRow(rows=r[i:len(r)-i], flip=0, frames=0)
        self.startDealSample()
        self.s.talon.dealRow()


# /***********************************************************************
# // Abacus
# ************************************************************************/

class Abacus_Foundation(SS_FoundationStack):
    def __init__(self, x, y, game, suit, **cap):
        kwdefault(cap, base_rank=suit, mod=13, dir=suit+1, max_move=0)
        apply(SS_FoundationStack.__init__, (self, x, y, game, suit), cap)


class Abacus_RowStack(Yukon_SS_RowStack):
    def _isSequence(self, c1, c2):
        dir, mod = -(c1.suit + 1), 13
        return c1.suit == c2.suit and (c1.rank + dir) % mod == c2.rank


class Abacus(Rushdike):
    Foundation_Class = Abacus_Foundation
    RowStack_Class = Abacus_RowStack

    def createGame(self):
        l = Rushdike.createGame(self)
        help = (_('''\
Club:    A 2 3 4 5 6 7 8 9 T J Q K
Spade:   2 4 6 8 T Q A 3 5 7 9 J K
Heart:   3 6 9 Q 2 5 8 J A 4 7 T K
Diamond: 4 8 Q 3 7 J 2 6 T A 5 9 K'''))
        self.texts.help = MfxCanvasText(self.canvas,
                                        l.XM, self.height - l.YM, text=help,
                                        anchor="sw",
                                        font=self.app.getFont("canvas_fixed"))

    def _shuffleHook(self, cards):
        # move Twos to top of the Talon (i.e. first cards to be dealt)
        return self._shuffleHookMoveToTop(cards, lambda c: (c.id in (0, 14, 28, 42), c.suit))

    def startGame(self, flip=1, reverse=1):
        self.s.talon.dealRow(rows=self.s.foundations, frames=0)
        for i in range(1, len(self.s.rows)):
            self.s.talon.dealRow(rows=self.s.rows[i:], flip=flip, frames=0, reverse=reverse)
        self.startDealSample()
        self.s.talon.dealRow(reverse=reverse)

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        dir, mod = -(card1.suit + 1), 13
        return (card1.suit == card2.suit and
                ((card1.rank + dir) % mod == card2.rank or
                 (card2.rank + dir) % mod == card1.rank))


# /***********************************************************************
# // Double Yukon
# // Double Russian Solitaire
# ************************************************************************/

class DoubleYukon(Yukon):
    def createGame(self):
        Yukon.createGame(self, rows=10)
    def startGame(self):
        for i in range(1, len(self.s.rows)-1):
            self.s.talon.dealRow(rows=self.s.rows[i:], flip=0, frames=0)
        #self.s.talon.dealRow(rows=self.s.rows, flip=0, frames=0)
        for i in range(5):
            self.s.talon.dealRow(flip=1, frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        assert len(self.s.talon.cards) == 0


class DoubleRussianSolitaire(DoubleYukon):
    RowStack_Class = StackWrapper(Yukon_SS_RowStack, base_rank=KING)

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.suit == card2.suit and
                (card1.rank + 1 == card2.rank or card2.rank + 1 == card1.rank))


# /***********************************************************************
# // Triple Yukon
# // Triple Russian Solitaire
# ************************************************************************/

class TripleYukon(Yukon):
    def createGame(self):
        Yukon.createGame(self, rows=13, playcards=34)
    def startGame(self):
        for i in range(1, len(self.s.rows)):
            self.s.talon.dealRow(rows=self.s.rows[i:], flip=0, frames=0)
        for i in range(5):
            self.s.talon.dealRow(rows=self.s.rows, flip=1, frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        assert len(self.s.talon.cards) == 0


class TripleRussianSolitaire(TripleYukon):
    RowStack_Class = StackWrapper(Yukon_SS_RowStack, base_rank=KING)

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.suit == card2.suit and
                (card1.rank + 1 == card2.rank or card2.rank + 1 == card1.rank))


# /***********************************************************************
# // Ten Across
# ************************************************************************/

class TenAcross(Yukon):

    Foundation_Class = Spider_SS_Foundation
    RowStack_Class = StackWrapper(Yukon_SS_RowStack, base_rank=KING)
    Layout_Method = Layout.freeCellLayout

    #
    # game layout
    #

    def createGame(self, **layout):
        # create layout
        l, s = Layout(self), self.s
        kwdefault(layout, rows=10, reserves=2, texts=0)
        apply(self.Layout_Method, (l,), layout)
        self.setSize(l.size[0], l.size[1])
        # create stacks
        s.talon = InitialDealTalonStack(l.s.talon.x, l.s.talon.y, self)
        for r in l.s.foundations:
            self.s.foundations.append(self.Foundation_Class(r.x, r.y, self, suit=r.suit))
        for r in l.s.rows:
            s.rows.append(self.RowStack_Class(r.x, r.y, self))
        for r in l.s.reserves:
            self.s.reserves.append(ReserveStack(r.x, r.y, self))
        # default
        l.defaultAll()

    #
    # game overrides
    #

    def startGame(self):
        n = 1
        for i in range(4):
            self.s.talon.dealRow(rows=self.s.rows[:n], frames=0)
            self.s.talon.dealRow(rows=self.s.rows[n:-n], frames=0, flip=0)
            self.s.talon.dealRow(rows=self.s.rows[-n:], frames=0)
            n += 1
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealRow(rows=self.s.reserves)
        assert len(self.s.talon.cards) == 0

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.suit == card2.suit and
                (card1.rank + 1 == card2.rank or card2.rank + 1 == card1.rank))


# /***********************************************************************
# // Panopticon
# ************************************************************************/

class Panopticon(TenAcross):

    Foundation_Class = SS_FoundationStack

    def createGame(self):
        TenAcross.createGame(self, rows=8, reserves=4)

    def startGame(self):
        self.s.talon.dealRow(frames=0, flip=0)
        n = 1
        for i in range(3):
            self.s.talon.dealRow(rows=self.s.rows[:n], frames=0)
            self.s.talon.dealRow(rows=self.s.rows[n:-n], frames=0, flip=0)
            self.s.talon.dealRow(rows=self.s.rows[-n:], frames=0)
            n += 1
        self.s.talon.dealRow(frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealRow(rows=self.s.reserves)


# /***********************************************************************
# // Australian Patience
# // Raw Prawn
# // Bim Bom
# ************************************************************************/

class AustralianPatience(RussianSolitaire):

    RowStack_Class = StackWrapper(Yukon_SS_RowStack, base_rank=KING)

    def createGame(self, rows=7):
        l, s = Layout(self), self.s
        Layout.klondikeLayout(l, rows=rows, waste=1)
        self.setSize(l.size[0], l.size[1])
        s.talon = WasteTalonStack(l.s.talon.x, l.s.talon.y, self, max_rounds=1)
        s.waste = WasteStack(l.s.waste.x, l.s.waste.y, self)
        for r in l.s.foundations:
            s.foundations.append(SS_FoundationStack(r.x, r.y, self, suit=r.suit))
        for r in l.s.rows:
            s.rows.append(self.RowStack_Class(r.x, r.y, self))
        l.defaultAll()

    def startGame(self):
        for i in range(3):
            self.s.talon.dealRow(frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealCards()


class RawPrawn(AustralianPatience):
    RowStack_Class = Yukon_SS_RowStack


class BimBom(AustralianPatience):
    RowStack_Class = Yukon_SS_RowStack
    def createGame(self):
        AustralianPatience.createGame(self, rows=8)
    def startGame(self):
        for i in range(4):
            self.s.talon.dealRow(frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealCards()


# /***********************************************************************
# // Geoffrey
# ************************************************************************/

class Geoffrey(Yukon):
    Layout_Method = Layout.klondikeLayout
    RowStack_Class = StackWrapper(Yukon_SS_RowStack, base_rank=KING)

    def createGame(self):
        Yukon.createGame(self, rows=8, waste=0)

    def startGame(self):
        for i in (4, 4, 4, 4, 8):
            self.s.talon.dealRow(rows=self.s.rows[:i], flip=1, frames=0)
            self.s.talon.dealRow(rows=self.s.rows[i:], flip=0, frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealRow(rows=self.s.rows[:4])

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return card1.suit == card2.suit and abs(card1.rank-card2.rank) == 1



# register the game
registerGame(GameInfo(19, Yukon, "Yukon",
                      GI.GT_YUKON, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(20, RussianSolitaire, "Russian Solitaire",
                      GI.GT_YUKON, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(27, Odessa, "Odessa",
                      GI.GT_YUKON, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(278, Grandfather, "Grandfather",
                      GI.GT_YUKON, 1, 0, GI.SL_MOSTLY_LUCK))
registerGame(GameInfo(186, Alaska, "Alaska",
                      GI.GT_YUKON, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(187, ChineseDiscipline, "Chinese Discipline",
                      GI.GT_YUKON | GI.GT_XORIGINAL, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(188, ChineseSolitaire, "Chinese Solitaire",
                      GI.GT_YUKON | GI.GT_XORIGINAL, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(189, Queenie, "Queenie",
                      GI.GT_YUKON | GI.GT_XORIGINAL, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(190, Rushdike, "Rushdike",
                      GI.GT_YUKON | GI.GT_XORIGINAL, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(191, RussianPoint, "Russian Point",
                      GI.GT_YUKON | GI.GT_XORIGINAL, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(192, Abacus, "Abacus",
                      GI.GT_YUKON | GI.GT_XORIGINAL, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(271, DoubleYukon, "Double Yukon",
                      GI.GT_YUKON, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(272, TripleYukon, "Triple Yukon",
                      GI.GT_YUKON, 3, 0, GI.SL_BALANCED))
registerGame(GameInfo(284, TenAcross, "Ten Across",
                      GI.GT_YUKON, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(285, Panopticon, "Panopticon",
                      GI.GT_YUKON | GI.GT_ORIGINAL, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(339, Moosehide, "Moosehide",
                      GI.GT_YUKON, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(387, Roslin, "Roslin",
                      GI.GT_YUKON, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(447, AustralianPatience, "Australian Patience",
                      GI.GT_YUKON, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(450, RawPrawn, "Raw Prawn",
                      GI.GT_YUKON, 1, 0, GI.SL_BALANCED))
registerGame(GameInfo(456, BimBom, "Bim Bom",
                      GI.GT_YUKON | GI.GT_ORIGINAL, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(466, DoubleRussianSolitaire, "Double Russian Solitaire",
                      GI.GT_YUKON, 2, 0, GI.SL_BALANCED))
registerGame(GameInfo(488, TripleRussianSolitaire, "Triple Russian Solitaire",
                      GI.GT_YUKON, 3, 0, GI.SL_BALANCED))
registerGame(GameInfo(492, Geoffrey, "Geoffrey",
                      GI.GT_YUKON, 1, 0, GI.SL_MOSTLY_SKILL))
