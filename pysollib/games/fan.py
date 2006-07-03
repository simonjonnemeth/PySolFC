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
from pysollib.stack import *
from pysollib.game import Game
from pysollib.layout import Layout
from pysollib.hint import AbstractHint, DefaultHint, CautiousDefaultHint
from pysollib.pysoltk import MfxCanvasText


# /***********************************************************************
# //
# ************************************************************************/

class Fan_Hint(CautiousDefaultHint):
    # FIXME: demo is not too clever in this game
    pass


# /***********************************************************************
# // Fan
# ************************************************************************/

class Fan(Game):
    Talon_Class = InitialDealTalonStack
    Foundation_Classes = [SS_FoundationStack]
    ReserveStack_Class = ReserveStack
    RowStack_Class = KingSS_RowStack
    Hint_Class = Fan_Hint

    #
    # game layout
    #

    def createGame(self, rows=(5,5,5,3), playcards=9, reserves=0):
        # create layout
        l, s = Layout(self), self.s

        # set window
        # (set size so that at least 9 cards are fully playable)
        w = max(2*l.XS, l.XS+(playcards-1)*l.XOFFSET)
        w = min(3*l.XS, w)
        w = (w + 1) & ~1
        ##print 2*l.XS, w
        self.setSize(l.XM + max(rows)*w, l.YM + (1+len(rows))*l.YS)

        # create stacks
        if reserves:
            x, y = l.XM, l.YM
            for r in range(reserves):
                s.reserves.append(self.ReserveStack_Class(x, y, self))
                x += l.XS
            x = (self.width - self.gameinfo.decks*4*l.XS - 2*l.XS) / 2
            dx = l.XS
        else:
            dx = (self.width - self.gameinfo.decks*4*l.XS)/(self.gameinfo.decks*4+1)
            x, y = l.XM + dx, l.YM
            dx += l.XS
        for fnd_cls in self.Foundation_Classes:
            for i in range(4):
                s.foundations.append(fnd_cls(x, y, self, suit=i))
                x += dx
        for i in range(len(rows)):
            x, y = l.XM, y + l.YS
            for j in range(rows[i]):
                stack = self.RowStack_Class(x, y, self, max_move=1, max_accept=1)
                stack.CARD_XOFFSET, stack.CARD_YOFFSET = l.XOFFSET, 0
                s.rows.append(stack)
                x += w
        x, y = self.width - l.XS, self.height - l.YS
        s.talon = self.Talon_Class(x, y, self)

        # define stack-groups
        l.defaultStackGroups()
        return l

    #
    # game overrides
    #

    def startGame(self):
        for i in range(2):
            self.s.talon.dealRow(rows=self.s.rows[:17], frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        assert len(self.s.talon.cards) == 0

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.suit == card2.suit and
                (card1.rank + 1 == card2.rank or card2.rank + 1 == card1.rank))

    def getHighlightPilesStacks(self):
        return ()


# /***********************************************************************
# // Scotch Patience
# ************************************************************************/

class ScotchPatience(Fan):
    Foundation_Classes = [AC_FoundationStack]
    RowStack_Class = StackWrapper(RK_RowStack, base_rank=NO_RANK)
    def createGame(self):
        Fan.createGame(self, playcards=8)
    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return abs(card1.rank-card2.rank) == 1


# /***********************************************************************
# // Shamrocks
# ************************************************************************/

class Shamrocks(Fan):
    RowStack_Class = StackWrapper(UD_RK_RowStack, base_rank=NO_RANK, max_cards=3)
    def createGame(self):
        Fan.createGame(self, playcards=4)
    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return abs(card1.rank-card2.rank) == 1


# /***********************************************************************
# // La Belle Lucie (Midnight Oil)
# ************************************************************************/

class LaBelleLucie_Talon(TalonStack):
    def canDealCards(self):
        return self.round != self.max_rounds and not self.game.isGameWon()

    def dealCards(self, sound=0):
        n = self.redealCards1()
        if n == 0:
            return 0
        self.redealCards2()
        if sound:
            self.game.startDealSample()
        self.redealCards3()
        if sound:
            self.game.stopSamples()
        return n

    # redeal step 1) - collect all cards, move them to the Talon
    def redealCards1(self):
        assert len(self.cards) == 0
        num_cards = 0
        for r in self.game.s.rows:
            if r.cards:
                num_cards = num_cards + len(r.cards)
                self.game.moveMove(len(r.cards), r, self, frames=0)
        assert len(self.cards) == num_cards
        return num_cards

    # redeal step 2) - shuffle
    def redealCards2(self):
        assert self.round != self.max_rounds
        assert self.cards
        self.game.shuffleStackMove(self)
        self.game.nextRoundMove(self)

    # redeal step 3) - redeal cards to stacks
    def redealCards3(self, face_up=1):
        # deal 3 cards to each row, and 1-3 cards to last row
        to_stacks = self.game.s.rows
        n = min(len(self.cards), 3*len(to_stacks))
        for i in range(3):
            j = (n/3, (n+1)/3, (n+2)/3) [i]
            frames = (0, 0, 4) [i]
            for r in to_stacks[:j]:
                if self.cards[-1].face_up != face_up:
                    self.game.flipMove(self)
                self.game.moveMove(1, self, r, frames=frames)


class LaBelleLucie(Fan):
    Talon_Class = StackWrapper(LaBelleLucie_Talon, max_rounds=3)
    RowStack_Class = StackWrapper(SS_RowStack, base_rank=NO_RANK)


# /***********************************************************************
# // Super Flower Garden
# ************************************************************************/

class SuperFlowerGarden(LaBelleLucie):
    RowStack_Class = StackWrapper(RK_RowStack, base_rank=NO_RANK)


# /***********************************************************************
# // Three Shuffles and a Draw
# ************************************************************************/

class ThreeShufflesAndADraw_RowStack(SS_RowStack):
    def moveMove(self, ncards, to_stack, frames=-1, shadow=-1):
        game, r = self.game, self.game.s.reserves[0]
        if to_stack is not r:
            SS_RowStack.moveMove(self, ncards, to_stack, frames=frames, shadow=shadow)
            return
        f = self._canDrawCard()
        assert f and game.draw_done == 0 and ncards == 1
        # 1) top card from self to reserve
        game.updateStackMove(r, 2|16)       # update view for undo
        game.moveMove(1, self, r, frames=frames, shadow=shadow)
        game.updateStackMove(r, 3|64)       # update model
        game.updateStackMove(r, 1|16)       # update view for redo
        # 2) second card from self to foundation/row
        if 1 or not game.demo:
            game.playSample("drop", priority=200)
        if frames == 0:
            frames = -1
        game.moveMove(1, self, f, frames=frames, shadow=shadow)
        # 3) from reserve back to self
        #    (need S_FILL because the move is normally not valid)
        old_state = game.enterState(game.S_FILL)
        game.moveMove(1, r, self, frames=frames, shadow=shadow)
        game.leaveState(old_state)

    def _canDrawCard(self):
        if len(self.cards) >= 2:
            pile = self.cards[-2:-1]
            for s in self.game.s.foundations + self.game.s.rows:
                if s is not self and s.acceptsCards(self, pile):
                    return s
        return None


class ThreeShufflesAndADraw_ReserveStack(ReserveStack):
    def acceptsCards(self, from_stack, cards):
        if not ReserveStack.acceptsCards(self, from_stack, cards):
            return 0
        if not from_stack in self.game.s.rows:
            return 0
        if self.game.draw_done or not from_stack._canDrawCard():
            return 0
        return 1

    def updateModel(self, undo, flags):
        assert undo == self.game.draw_done
        self.game.draw_done = not self.game.draw_done

    def updateText(self):
        if self.game.preview > 1 or self.texts.misc is None:
            return
        t = (_("X"), _("Draw")) [self.game.draw_done == 0]
        self.texts.misc.config(text=t)

    def prepareView(self):
        ReserveStack.prepareView(self)
        if not self.is_visible or self.game.preview > 1:
            return
        images = self.game.app.images
        x, y = self.x + images.CARDW/2, self.y + images.CARDH/2
        self.texts.misc = MfxCanvasText(self.game.canvas, x, y,
                                        anchor="center",
                                        font=self.game.app.getFont("canvas_default"))


class ThreeShufflesAndADraw(LaBelleLucie):
    RowStack_Class = StackWrapper(ThreeShufflesAndADraw_RowStack, base_rank=NO_RANK)

    def createGame(self):
        l = LaBelleLucie.createGame(self)
        s = self.s
        # add a reserve stack
        x, y = s.rows[3].x, s.rows[-1].y
        s.reserves.append(ThreeShufflesAndADraw_ReserveStack(x, y, self))
        # redefine the stack-groups
        l.defaultStackGroups()
        # extra settings
        self.draw_done = 0

    def startGame(self):
        self.draw_done = 0
        self.s.reserves[0].updateText()
        LaBelleLucie.startGame(self)

    def _restoreGameHook(self, game):
        self.draw_done = game.loadinfo.draw_done

    def _loadGameHook(self, p):
        self.loadinfo.addattr(draw_done=p.load())

    def _saveGameHook(self, p):
        p.dump(self.draw_done)


# /***********************************************************************
# // Trefoil
# ************************************************************************/

class Trefoil(LaBelleLucie):
    GAME_VERSION = 2
    Foundation_Classes = [StackWrapper(SS_FoundationStack, min_cards=1)]

    def createGame(self):
        return Fan.createGame(self, rows=(5,5,5,1))

    def _shuffleHook(self, cards):
        # move Aces to bottom of the Talon (i.e. last cards to be dealt)
        return self._shuffleHookMoveToBottom(cards, lambda c: (c.rank == 0, c.suit))

    def startGame(self):
        for i in range(2):
            self.s.talon.dealRow(frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealRow(rows=self.s.foundations)


# /***********************************************************************
# // Intelligence
# ************************************************************************/

class Intelligence_Talon(LaBelleLucie_Talon):
    # all Aces go to Foundations
    dealToStacks = TalonStack.dealToStacksOrFoundations

    # redeal step 1) - collect all cards, move them to the Talon (face down)
    def redealCards1(self):
        assert len(self.cards) == 0
        r = self.game.s.reserves[0]
        num_cards = len(r.cards)
        if num_cards > 0:
            self.game.moveMove(len(r.cards), r, self, frames=0)
        for r in self.game.s.rows:
            num_cards = num_cards + len(r.cards)
            while r.cards:
                self.game.moveMove(1, r, self, frames=0)
                self.game.flipMove(self)
        assert len(self.cards) == num_cards
        return num_cards

    # redeal step 3) - redeal cards to stacks
    def redealCards3(self, face_up=1):
        for r in self.game.s.rows:
            while len(r.cards) < 3:
                self.dealToStacks([r], frames=4)
                if not self.cards:
                    return
        # move all remaining cards to the reserve
        self.game.moveMove(len(self.cards), self, self.game.s.reserves[0], frames=0)


# up or down in suit
class Intelligence_RowStack(UD_SS_RowStack):
    def fillStack(self):
        if not self.cards:
            r = self.game.s.reserves[0]
            if r.cards:
                r.dealRow((self,self,self), sound=1)


class Intelligence_ReserveStack(ReserveStack, DealRow_StackMethods):
    # all Aces go to Foundations (used in r.dealRow() above)
    dealToStacks = DealRow_StackMethods.dealToStacksOrFoundations

    def canFlipCard(self):
        return 0


class Intelligence(Fan):

    Foundation_Classes = [SS_FoundationStack, SS_FoundationStack]
    Talon_Class = StackWrapper(Intelligence_Talon, max_rounds=3)
    RowStack_Class = StackWrapper(Intelligence_RowStack, base_rank=NO_RANK)

    def createGame(self, rows=(5,5,5,3)):
        l = Fan.createGame(self, rows)
        s = self.s
        # add a reserve stack
        x, y = s.talon.x - l.XS, s.talon.y
        s.reserves.append(Intelligence_ReserveStack(x, y, self, max_move=0, max_accept=0, max_cards=UNLIMITED_CARDS))
        l.createText(s.reserves[0], "sw")
        # redefine the stack-groups
        l.defaultStackGroups()

    def startGame(self):
        talon = self.s.talon
        for i in range(2):
            talon.dealRow(frames=0)
        self.startDealSample()
        talon.dealRow()
        # move all remaining cards to the reserve
        self.moveMove(len(talon.cards), talon, self.s.reserves[0], frames=0)


class IntelligencePlus(Intelligence):
    def createGame(self):
        Intelligence.createGame(self, rows=(5,5,5,4))


# /***********************************************************************
# // House in the Wood
# // House on the Hill
# //   (2 decks variants of Fan)
# ************************************************************************/

class HouseInTheWood(Fan):
    Foundation_Classes = [SS_FoundationStack, SS_FoundationStack]
    RowStack_Class = StackWrapper(UD_SS_RowStack, base_rank=NO_RANK)

    def createGame(self):
        Fan.createGame(self, rows=(6,6,6,6,6,5))

    def startGame(self):
        self.s.talon.dealRow(rows=self.s.rows[:34], frames=0)
        self.s.talon.dealRow(rows=self.s.rows[:35], frames=0)
        self.startDealSample()
        self.s.talon.dealRow(rows=self.s.rows[:35])
        assert len(self.s.talon.cards) == 0


class HouseOnTheHill(HouseInTheWood):
    Foundation_Classes = [SS_FoundationStack,
                          StackWrapper(SS_FoundationStack, base_rank=KING, dir=-1)]


# /***********************************************************************
# // Clover Leaf
# ************************************************************************/

class CloverLeaf_RowStack(UD_SS_RowStack):
    def acceptsCards(self, from_stack, cards):
        if not UD_SS_RowStack.acceptsCards(self, from_stack, cards):
            return False
        if not self.cards:
            return cards[0].rank in (ACE, KING)
        return True


class CloverLeaf(Game):

    Hint_Class = Fan_Hint

    #
    # game layout
    #

    def createGame(self):
        # create layout
        l, s = Layout(self), self.s

        # set window
        playcards = 7
        w, h = l.XM+l.XS+4*(l.XS+(playcards-1)*l.XOFFSET), l.YM+4*l.YS
        self.setSize(w, h)

        # create stacks
        x, y = l.XM, l.YM
        for i in range(2):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i))
            y += l.YS
        for i in range(2):
            s.foundations.append(SS_FoundationStack(x, y, self, suit=i+2,
                                                    base_rank=KING, dir=-1))
            y += l.YS

        x = l.XM+l.XS
        for i in range(4):
            y = l.YM
            for j in range(4):
                stack = CloverLeaf_RowStack(x, y, self,
                                            max_move=1, max_accept=1)
                s.rows.append(stack)
                stack.CARD_XOFFSET, stack.CARD_YOFFSET = l.XOFFSET, 0
                y += l.YS
            x += l.XS+(playcards-1)*l.XOFFSET

        s.talon = InitialDealTalonStack(w-l.XS, h-l.YS, self)

        # default
        l.defaultAll()

    #
    # game overrides
    #

    def startGame(self):
        for i in range(2):
            self.s.talon.dealRow(frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealRow(rows=self.s.foundations)

    def _shuffleHook(self, cards):
        return self._shuffleHookMoveToBottom(cards,
                   lambda c: ((c.rank == ACE and c.suit in (0,1)) or
                              (c.rank == KING and c.suit in (2,3)),
                              c.suit))

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.suit == card2.suit and
                abs(card1.rank-card2.rank) == 1)


# /***********************************************************************
# // Free Fan
# ************************************************************************/

class FreeFan(Fan):
    def createGame(self):
        Fan.createGame(self, reserves=2)


# /***********************************************************************
# // Box Fan
# ************************************************************************/

class BoxFan(Fan):

    RowStack_Class = KingAC_RowStack

    def createGame(self):
        Fan.createGame(self, rows=(4,4,4,4))

    def startGame(self):
        for i in range(2):
            self.s.talon.dealRow(frames=0)
        self.startDealSample()
        self.s.talon.dealRow()
        self.s.talon.dealRow(rows=self.s.foundations)

    def _shuffleHook(self, cards):
        # move Aces to bottom of the Talon (i.e. last cards to be dealt)
        return self._shuffleHookMoveToBottom(cards, lambda c: (c.rank == 0, c.suit))

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return (card1.color != card2.color and
                (card1.rank + 1 == card2.rank or card2.rank + 1 == card1.rank))


# /***********************************************************************
# // Troika
# ************************************************************************/

class Troika(Fan):

    RowStack_Class = StackWrapper(RK_RowStack, dir=0, base_rank=NO_RANK, max_cards=3)

    def createGame(self):
        Fan.createGame(self, rows=(6, 6, 6), playcards=4)

    def shallHighlightMatch(self, stack1, card1, stack2, card2):
        return card1.rank == card2.rank

    def startGame(self, ncards=3):
        self.startDealSample()
        for r in self.s.rows:
            for i in range(ncards):
                if not self.s.talon.cards:
                    break
                c = self.s.talon.cards[-1]
                t = r
                if c.rank == ACE:
                    t = self.s.foundations[c.suit]
                self.s.talon.dealRow(rows=[t], frames=4)



class TroikaPlus_RowStack(RK_RowStack):
    def getBottomImage(self):
        return self.game.app.images.getReserveBottom()

class TroikaPlus(Troika):
    RowStack_Class = StackWrapper(TroikaPlus_RowStack, dir=0,
                                  ##base_rank=NO_RANK,
                                  max_cards=4)
    def createGame(self):
        Fan.createGame(self, rows=(5, 5, 3), playcards=5)

    def startGame(self):
        Troika.startGame(self, ncards=4)
##         for i in range(3):
##             self.s.talon.dealRow(rows=self.s.rows[:-1], frames=0)
##         self.startDealSample()
##         self.s.talon.dealRow(rows=self.s.rows[:-1])


# register the game
registerGame(GameInfo(56, Fan, "Fan",
                      GI.GT_FAN_TYPE | GI.GT_OPEN, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(87, ScotchPatience, "Scotch Patience",
                      GI.GT_FAN_TYPE | GI.GT_OPEN, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(57, Shamrocks, "Shamrocks",
                      GI.GT_FAN_TYPE | GI.GT_OPEN, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(901, LaBelleLucie, "La Belle Lucie",      # was: 32, 82
                      GI.GT_FAN_TYPE | GI.GT_OPEN, 1, 2, GI.SL_MOSTLY_SKILL,
                      altnames=("Fair Lucy", "Midnight Oil") ))
registerGame(GameInfo(132, SuperFlowerGarden, "Super Flower Garden",
                      GI.GT_FAN_TYPE | GI.GT_OPEN, 1, 2, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(128, ThreeShufflesAndADraw, "Three Shuffles and a Draw",
                      GI.GT_FAN_TYPE | GI.GT_OPEN, 1, 2, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(88, Trefoil, "Trefoil",
                      GI.GT_FAN_TYPE | GI.GT_OPEN, 1, 2, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(227, Intelligence, "Intelligence",
                      GI.GT_FAN_TYPE, 2, 2, GI.SL_BALANCED))
registerGame(GameInfo(340, IntelligencePlus, "Intelligence +",
                      GI.GT_FAN_TYPE, 2, 2, GI.SL_BALANCED))
registerGame(GameInfo(268, HouseInTheWood, "House in the Wood",
                      GI.GT_FAN_TYPE | GI.GT_OPEN, 2, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(317, HouseOnTheHill, "House on the Hill",
                      GI.GT_FAN_TYPE | GI.GT_OPEN, 2, 0, GI.SL_MOSTLY_SKILL,
                      rules_filename='houseinthewood.html'))
registerGame(GameInfo(320, CloverLeaf, "Clover Leaf",
                      GI.GT_FAN_TYPE | GI.GT_OPEN, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(347, FreeFan, "Free Fan",
                      GI.GT_FAN_TYPE | GI.GT_OPEN, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(385, BoxFan, "Box Fan",
                      GI.GT_FAN_TYPE | GI.GT_OPEN, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(516, Troika, "Troika",
                      GI.GT_FAN_TYPE | GI.GT_OPEN, 1, 0, GI.SL_MOSTLY_SKILL))
registerGame(GameInfo(517, TroikaPlus, "Troika +",
                      GI.GT_FAN_TYPE | GI.GT_OPEN, 1, 0, GI.SL_MOSTLY_SKILL))
