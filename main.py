# hello.py - micro-gui "Hello world" upraveny pro kulaty displej 240x240
# (rohy displeje jsou oriznute kruhem, proto je obsah umisten ke stredu)
from hardware_setup import ssd  # Vytvori displej - musi byt prvni import
from gui.core.ugui import Screen
from gui.core.writer import CWriter
from gui.core.colors import *
import time
import asyncio
import cmath

from gui.widgets import Label, Button,CloseButton,Dial,Pointer
import gui.fonts.freesans20 as freesans20
import gui.fonts.arial10 as arial10


class BaseScreen(Screen):

    def __init__(self):
        super().__init__()
        wri = CWriter(ssd, freesans20, GREEN, BLACK, verbose=False)
        Label(wri, 95, 55, 'Hello world!')
        #Button je active widget (Screen potrebuje aspon jeden) - ukonci aplikaci
        Button(wri, 140, 85, text='Konec', callback=lambda b: Screen.change(AnalogWatchScreen))
        Button(wri, 140, 125, width=70, text="Dalsi ->", fgcolor=BLUE,
                callback=lambda _: Screen.change(AnalogWatchScreen, mode=Screen.REPLACE))
        Button(wri, 140, 45, width=70, text="<- Zpet", fgcolor=YELLOW,
                callback=lambda _: Screen.change(HeartScreen, mode=Screen.REPLACE))

class AnalogWatchScreen(Screen):
    def __init__(self):
        super().__init__()
        wri = CWriter(ssd, arial10, WHITE, BLACK, verbose=False)

        # Kruhový ciferník vycentrovaný na displeji 240x240 px (průměr 200 px)
        self.dial = Dial(wri, 20, 20, height=200, ticks=12, bdcolor=WHITE, pip=RED)
        
        # Vytvoření hodinové, minutové a vteřinové ručičky[cite: 4]
        self.ptr_hrs = Pointer(self.dial)
        self.ptr_mins = Pointer(self.dial)
        self.ptr_secs = Pointer(self.dial)
        # Skryté zavírací tlačítko pro stisk fyzického SEL[cite: 5]
        #Button(wri, 140, 85, text='Konec', callback=lambda _: Screen.back())
        #CloseButton(self.wri)
        Button(wri, 140, 125, width=70, text="Dalsi ->", fgcolor=BLUE,
                callback=lambda _: Screen.change(HeartScreen, mode=Screen.REPLACE))
        Button(wri, 140, 45, width=70, text="<- Zpet", fgcolor=YELLOW,
                callback=lambda _: Screen.change(BaseScreen, mode=Screen.REPLACE))

        self.reg_task(self.update_hands(),on_change=False)
        

    async def update_hands(self):
        while True:
            
            t = time.localtime()
            hrs = t[3] % 12
            mins = t[4]
            secs = t[5]

            # Výpočet úhlů (12 hodin je nahoře = úhel pi/2 v komplexní rovině)
            angle_s = (cmath.pi / 2) - (secs / 60) * 2 * cmath.pi
            angle_m = (cmath.pi / 2) - ((mins + secs / 60) / 60) * 2 * cmath.pi
            angle_h = (cmath.pi / 2) - ((hrs + mins / 60) / 12) * 2 * cmath.pi

            # Nastavení délky (0.5 až 0.9) a barvy jednotlivých ručiček[cite: 4]
            self.ptr_hrs.value(cmath.rect(0.55, angle_h), WHITE)
            self.ptr_mins.value(cmath.rect(0.80, angle_m), YELLOW)
            self.ptr_secs.value(cmath.rect(0.90, angle_s), RED)

            await asyncio.sleep(1)

class StopWach(Screen):
    def __init__(self):
        pass


class HeartScreen(Screen):
    def __init__(self):
        super().__init__()
        wri = CWriter(ssd, freesans20, GREEN, BLACK, verbose=False)
        wri_btn = CWriter(ssd, arial10, WHITE, BLACK, verbose=False)

        Label(wri, 75, 55, "Tep: 72 BPM")

        Button(wri_btn, 140, 125, width=70, text="Dalsi ->", fgcolor=BLUE,
               callback=lambda _: Screen.change(BaseScreen, mode=Screen.REPLACE))
        Button(wri_btn, 140, 45, width=70, text="<- Zpet", fgcolor=YELLOW,
               callback=lambda _: Screen.change(AnalogWatchScreen, mode=Screen.REPLACE))
            
            





Screen.change(BaseScreen)

