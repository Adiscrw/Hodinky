# from machine import Pin, SPI
# import gc
# from drivers.gc9a01.gc9a01 import GC9A01 as SSD
# from gui.core.ugui import Display

# # 1. Zapnutí podsvícení pro Round Display for XIAO (GPIO 43)
# bl = Pin(43, Pin.OUT)
# bl.value(1)

# # 2. Inicializace SPI pro displej GC9A01
# pdc = Pin(4, Pin.OUT, value=0)   # D3
# pcs = Pin(2, Pin.OUT, value=1)   # D1
# prst = Pin(9, Pin.OUT, value=1)

# spi = SPI(1, baudrate=30_000_000, sck=Pin(8), mosi=Pin(10))
# gc.collect()
# ssd = SSD(spi, pcs, pdc, prst, height=240, width=240)

# # 3. Povinná inicializace Display objektu pro micro-gui
# nxt = Pin(1, Pin.IN, Pin.PULL_UP)
# sel = Pin(3, Pin.IN, Pin.PULL_UP)
# display = Display(ssd, nxt, sel)





# from machine import Pin, SPI
# import gc
# from drivers.gc9a01.gc9a01 import GC9A01 as SSD

# # 1. Zapnutí podsvícení (D6 = GPIO 43 na XIAO ESP32-S3 skutečně existuje)
# bl = Pin(43, Pin.OUT)
# bl.value(1)

# # 2. Prázdný reset pin (Round Display nemá samostatný RST pin)
# class DummyPin:
#     def __call__(self, val):
#         pass
#     def value(self, val=None):
#         pass

# pdc = Pin(4, Pin.OUT, value=0)   # D3 = GPIO 4
# pcs = Pin(2, Pin.OUT, value=1)   # D1 = GPIO 2
# prst = DummyPin()

# # 3. Inicializace SPI(1) včetně MISO (D9 = GPIO 9), aby sběrnice na ESP32-S3 korektně vysílala
# spi = SPI(1, baudrate=10_000_000, sck=Pin(8), mosi=Pin(10), miso=Pin(9))
# gc.collect()
# ssd = SSD(spi, pcs, pdc, prst, height=240, width=240)

# # 4. Povinná inicializace Display objektu pro micro-gui
# from gui.core.ugui import Display, quiet
# quiet()

# # Tlačítka na volné piny (D0 = GPIO 1, D7 = GPIO 44)
# nxt = Pin(1, Pin.IN, Pin.PULL_UP)
# sel = Pin(44, Pin.IN, Pin.PULL_UP)
# display = Display(ssd, nxt, sel)




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
nxt = Pin(1, Pin.IN, Pin.PULL_UP)  # D0 (GPIO1) - dalsi widget
sel = Pin(3, Pin.IN, Pin.PULL_UP)  # D2 (GPIO3) - potvrdit (pozor: D2 je CS SD karty na Round Display)
#prev = Pin(7,Pin.IN,Pin.PULL_UP)


display = Display(ssd, nxt, sel)


