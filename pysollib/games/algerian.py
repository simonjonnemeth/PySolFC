##---------------------------------------------------------------------------##
##
## PySol -- a Python Solitaire game
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


# /***********************************************************************
# // Carthage
# ************************************************************************/

class Carthage_Talon(DealRowTalonStack):
    def dealCards(self, sound=0):
        if sound:
            self.game.startDealSample()
        if len(self.cards) == len(self.game.s.rows):
            n = self.dealRowAvail(rows=self.game.s.rows, sound=0)
        else:
            n = self.dealRowAvail(rows=self.game.s.reserves, sound=0)
            n += self.dealRowAvail(rows=self.game.s.reserves, sound=0)
        if sound:
            self.game.stopSamples()
        return n


class Carthage(Game):

    Hint_Class = CautiousDefaultHint
    Talon_Class = Carthage_Talon
    Foundation_Classes = (SS_FoundationStack,
                          SS_FoundationStack)
    RowStack_Class = StackWrapper(SS_RowStack, max_move=1)

    #
    # game layout
    #

    def createGame(self, rows=8, reserves=6, playcards=12):
        # create layout
        l, s = Layout(self), self.s

        # set window
        decks = self.gameinfo.decks
        foundations = decks*4
        max_rows = max(foundations, rows)
        w, h = l.XM+(max_rows+1)*l.XS, l.YM+3*l.YS+playcards*l.YOFFSET
        self.setSize(w, h)

        # create stacks
        x, y = l.XM+l.XS+(max_rows-foundations)*l.XS/2, l.YM
        for fclass in self.Foundation_Classes:
            for i in range(4):
                s.foundations.append(fclass(x, y, self, suit=i))
                x += l.XS

        x, y = l.XM+l.XS+(max_rows-rows)*l.XS/2, l.YM+l.YS
        for i in range(rows):
            s.rows.append(self.RowStack_Class(x, y, self,
                                              max_move=1, max_accept=1))
            x += l.XS
        self.setRegion(s.rows, (-999, y-l.CH/2, 999999, h-l.YS-l.CH/2))

        d = (w-reserves*l.XS)/reserves
        x, y = l.XM, h-l.YS
        for i in range(reserves):
            stack = ReserveStack(x, y, self)
            stack.CARD_XOFFSET, stack.CARD_YOFFSET = 2, 0
            s.reserves.append(stack)
            x += l.XS+d

        s.talon = self.Talon_Class(l.XM, l.YM, self)
        l.createText(s.talon, "ss")

        # define stack-groups
        l.defaultStackGroups()

    #
    # game overrides
    #

    def startGame(self):
        self.s.talon.dealRow(rows=self.s.rows, frames=0)
        for i in range(5):
            self.s.talon.dealRow(rows=self.s.reserves, frames=0)
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.reserves)

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.suit == card2.suit and
                ((card1.rank + 1) % 13 == card2.rank or
                 (card2.rank + 1) % 13 == card1.rank))


# /***********************************************************************
# // Algerian Patience
# ************************************************************************/

class AlgerianPatience(Carthage):

    Foundation_Classes = (SS_FoundationStack,
                          StackWrapper(SS_FoundationStack, base_rank=KING, dir=-1))
    RowStack_Class = StackWrapper(UD_SS_RowStack, mod=13)

    def _shuffleHook(self, cards):
        # move 4 Kings to top of the Talon
        return self._shuffleHookMoveToTop(cards,
               lambda c: (c.rank == KING and c.deck == 0, c.suit))

    def startGame(self):
        self.s.talon.dealRow(rows=self.s.foundations[4:], frames=0)
        Carthage.startGame(self)


class AlgerianPatience3(Carthage):
    Foundation_Classes = (SS_FoundationStack,
                          SS_FoundationStack,
                          SS_FoundationStack)
    RowStack_Class = StackWrapper(UD_SS_RowStack, mod=13)

    def createGame(self):
        Carthage.createGame(self, rows=8, reserves=8, playcards=20)

    def _shuffleHook(self, cards):
        return self._shuffleHookMoveToTop(cards,
               lambda c: (c.rank == ACE, (c.deck, c.suit)))

    def startGame(self):
        self.s.talon.dealRow(rows=self.s.foundations, frames=0)
        Carthage.startGame(self)



# register the game
registerGame(GameInfo(321, Carthage, "Carthage",
                      GI.GT_2DECK_TYPE, 2, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(322, AlgerianPatience, "Algerian Patience",
                      GI.GT_2DECK_TYPE, 2, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(457, AlgerianPatience3, "Algerian Patience (3 decks)",
                      GI.GT_3DECK_TYPE | GI.GT_ORIGINAL, 3, 0, GI.SL_MOSTLY_SKILL))
