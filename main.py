# hello.py - micro-gui "Hello world" upraveny pro kulaty displej 240x240
# (rohy displeje jsou oriznute kruhem, proto je obsah umisten ke stredu)
from hardware_setup import ssd  # Vytvori displej - musi byt prvni import
from hardware_setup import i2c
from gui.core.ugui import Screen
from gui.core.writer import CWriter
from gui.core.colors import *
import time
import asyncio
import cmath

from gui.widgets import Label, Button,CloseButton,Dial,Pointer
import gui.fonts.freesans20 as freesans20
import gui.fonts.arial10 as arial10

from max30102 import MAX30102, MAX30105_PULSE_AMP_MEDIUM


class BaseScreen(Screen):

    def __init__(self):
        super().__init__()
        wri = CWriter(ssd, freesans20, GREEN, BLACK, verbose=False)
        Label(wri, 95, 55, 'Hello world!')
        #Button je active widget (Screen potrebuje aspon jeden) - ukonci aplikaci
        Button(wri, 140, 85, text='Konec', callback=lambda b: Screen.change(AnalogWatchScreen))
        # Button(wri, 140, 125, width=70, text="Dalsi ->", fgcolor=BLUE,
        #         callback=lambda _: Screen.change(AnalogWatchScreen, mode=Screen.REPLACE))
        # Button(wri, 140, 45, width=70, text="<- Zpet", fgcolor=YELLOW,
        #         callback=lambda _: Screen.change(HeartScreen, mode=Screen.REPLACE))

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
        Button(wri, 140, 85, text='Konec', callback=lambda _: Screen.change(HealthScreen))
        #CloseButton(self.wri)
        #Button(wri, 140, 125, width=70, text="Dalsi ->", fgcolor=BLUE,
        #         callback=lambda _: Screen.change(HeartScreen, mode=Screen.REPLACE))
        # Button(wri, 140, 45, width=70, text="<- Zpet", fgcolor=YELLOW,
        #         callback=lambda _: Screen.change(BaseScreen, mode=Screen.REPLACE))

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

class HealthScreen(Screen):
    def __init__(self):
        super().__init__()
        wri_big = CWriter(ssd, freesans20, WHITE, BLACK, verbose=False)
        wri_lbl = CWriter(ssd, arial10, GREEN, BLACK, verbose=False)
        wri_btn = CWriter(ssd, arial10, WHITE, BLACK, verbose=False)

        # Nadpis obrazovky
        Label(wri_lbl, 25, 75, "ZDRAVI & TEP")

        # Dynamické popisky pro hodnoty (pevně definovaná šířka pro čisté překreslení)
        self.lbl_bpm = Label(wri_big, 55, 45, 150, justify=Label.CENTRE, fgcolor=RED)
        self.lbl_bpm.value("Tep: -- BPM")

        self.lbl_spo2 = Label(wri_big, 90, 45, 150, justify=Label.CENTRE, fgcolor=BLUE)
        self.lbl_spo2.value("SpO2: -- %")

        self.lbl_status = Label(wri_lbl, 125, 35, 170, justify=Label.CENTRE, fgcolor=YELLOW)
        self.lbl_status.value("Prilozte prst...")

        # Navigační tlačítka (stejná logika jako u hodin)
        Button(wri_btn, 160, 125, width=70, text="Dalsi ->", fgcolor=BLUE,
               callback=lambda _: Screen.change(AnalogWatchScreen, mode=Screen.REPLACE))
        Button(wri_btn, 160, 45, width=70, text="<- Zpet", fgcolor=YELLOW,
               callback=lambda _: Screen.change(AnalogWatchScreen, mode=Screen.REPLACE))

        # Spuštění měření na pozadí (on_change=True úlohu ukončí při odchodu z obrazovky)
        self.reg_task(self.measure_health(), on_change=True)

    async def measure_health(self):
        sensor = MAX30102(i2c=i2c)
        
        # Kontrola, zda je senzor připojen
        if not sensor.check_part_id():
            self.lbl_status.value("Chyba senzoru!")
            return

        # Nastavení senzoru (střední jas LED, 100 vzorků za sekundu)
        sensor.setup_sensor()
        sensor.set_sample_rate(100)
        sensor.set_fifo_average(4)
        sensor.set_active_leds_amplitude(MAX30105_PULSE_AMP_MEDIUM)

        ir_avg = 0
        last_beat = time.ticks_ms()
        beats = []

        try:
            while True:
                sensor.check()  # Načte nová data z FIFO paměti senzoru
                
                while sensor.available():
                    red = sensor.pop_red_from_storage()
                    ir = sensor.pop_ir_from_storage()

                    # 1. Detekce přiloženého prstu (IR hodnota vyskočí nad 50 000)
                    if ir < 50000:
                        self.lbl_status.value("Prilozte prst...")
                        self.lbl_bpm.value("Tep: -- BPM")
                        self.lbl_spo2.value("SpO2: -- %")
                        beats.clear()
                    else:
                        self.lbl_status.value("Merim...")
                        
                        # 2. Jednoduchý filtr a detekce úderu srdce
                        if ir_avg == 0:
                            ir_avg = ir
                        
                        # Zjištění lokálního vrcholu pulzní vlny
                        diff = ir - ir_avg
                        ir_avg = ir_avg * 0.95 + ir * 0.05  # Klouzavý průměr (DC složka)

                        now = time.ticks_ms()
                        delta = time.ticks_diff(now, last_beat)

                        # Pokud signál prudce stoupne a od posledního tepu uběhlo min. 300 ms (max 200 BPM)
                        if diff > 400 and delta > 300:
                            last_beat = now
                            bpm = 60000 / delta
                            if 40 < bpm < 190:
                                beats.append(bpm)
                                if len(beats) > 5:
                                    beats.pop(0)
                                avg_bpm = int(sum(beats) / len(beats))
                                self.lbl_bpm.value(f"Tep: {avg_bpm} BPM")

                                # 3. Orientační výpočet SpO2 z poměru RED a IR
                                ratio = (red / ir)
                                spo2 = int(max(85, min(100, 110 - 15 * ratio)))
                                self.lbl_spo2.value(f"SpO2: {spo2} %")

                # Uvolnění procesoru pro vykreslování GUI a čtení tlačítek (20 ms = 50 Hz)
                await asyncio.sleep_ms(20)
        finally:
            # Při opuštění obrazovky uspí senzor a zhasne červenou LED
            sensor.shutdown()
            
            





Screen.change(BaseScreen)

