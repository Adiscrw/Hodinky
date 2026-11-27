import gc
from machine import Pin, SPI, freq  #I2C
from machine import I2C

freq(240_000_000)  # ESP32-S3 na plny vykon

from drivers.gc9a01.gc9a01 import GC9A01 as SSD  # 4bitovy ovladac, framebuffer ~28,8 kB


# Piny displeje
pcs = Pin(2, Pin.OUT, value=1)    # D1
pdc = Pin(4, Pin.OUT, value=0)    # D3
prst = Pin(21, Pin.OUT, value=1)  # pomocny pin - RST na desce neni vyveden (GPIO21 = LED na XIAO)
pbl = Pin(43, Pin.OUT, value=1)   # D6 - podsvit, 1 = zapnuto

spi = SPI(1, baudrate=30_000_000, sck=Pin(7), mosi=Pin(9), miso=Pin(8))

i2c = I2C(0, scl=Pin(6), sda=Pin(5), freq=400_000)

gc.collect()  # Opatreni pred vytvorenim framebufferu
ssd = SSD(spi, pcs, pdc, prst)  # vychozi 240x240, pripadne: usd=True / mirror=True / lscape=True

# Import musi nasledovat az po vytvoreni ssd
from gui.core.ugui import Display, quiet

# quiet()  # odkomentovat pro potlaceni diagnostickych hlasek

# Ovladaci tlacitka - UPRAVTE podle toho, co fyzicky pripojite (aspon nxt a sel):
# nxt = Pin(1, Pin.IN, Pin.PULL_UP)  # D0 (GPIO1) - dalsi widget
# sel = Pin(3, Pin.IN, Pin.PULL_UP)  # D2 (GPIO3) - potvrdit (pozor: D2 je CS SD karty na Round Display)
# prev = Pin(7,Pin.IN,Pin.PULL_UP)

ex = Pin(9, Pin.IN, Pin.PULL_UP)          # Enkodér Pin A (D10 / GPIO 9)[cite: 8]
ey = Pin(21, Pin.IN, Pin.PULL_UP)         # Enkodér Pin B (GPIO 21)[cite: 8]
btn_sel = Pin(1, Pin.IN, Pin.PULL_UP)     # Tlačítko SELECT (D0 / GPIO 1)[cite: 5]
btn_switch = Pin(44, Pin.IN, Pin.PULL_UP) # Tlačítko SWITCH_TO_CHANGE (D7 / GPIO 44)[cite: 5]

# Režim Encoder-only: enkodér posouvá fokus, btn_sel potvrzuje[cite: 4]
display = Display(ssd, nxt=ex, sel=btn_sel, prev=ey, incr=False, encoder=4)


