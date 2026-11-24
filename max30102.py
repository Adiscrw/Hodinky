import time
from ucollections import deque

# I2C adresa senzoru MAX30102
MAX30102_I2C_ADDR = 0x57

# Registr mapování
REG_INTR_STATUS_1 = 0x00
REG_INTR_STATUS_2 = 0x01
REG_INTR_ENABLE_1 = 0x02
REG_INTR_ENABLE_2 = 0x03
REG_FIFO_WR_PTR = 0x04
REG_OVF_COUNTER = 0x05
REG_FIFO_RD_PTR = 0x06
REG_FIFO_DATA = 0x07
REG_FIFO_CONFIG = 0x08
REG_MODE_CONFIG = 0x09
REG_SPO2_CONFIG = 0x0A
REG_LED1_PA = 0x0C       # Červená LED (RED)
REG_LED2_PA = 0x0D       # Infračervená LED (IR)
REG_MULTI_LED_CTRL1 = 0x11
REG_MULTI_LED_CTRL2 = 0x12
REG_REV_ID = 0xFE
REG_PART_ID = 0xFF

# Konstanty jasu LED diod
MAX30105_PULSE_AMP_LOWEST = 0x02   # ~0.4 mA
MAX30105_PULSE_AMP_LOW = 0x1F      # ~6.4 mA
MAX30105_PULSE_AMP_MEDIUM = 0x3F   # ~12.5 mA
MAX30105_PULSE_AMP_HIGH = 0x7F     # ~25.4 mA
MAX30105_PULSE_AMP_MAX = 0xFF      # ~50.0 mA

# Konstanty režimů
MODE_REDONLY = 0x02
MODE_REDIRONLY = 0x03
MODE_MULTILED = 0x07

# Očekávané ID čipu MAX30102
EXPECTED_PART_ID = 0x15


class MAX30102:
    def __init__(self, i2c, address=MAX30102_I2C_ADDR, max_buffer_len=32):
        self.i2c = i2c
        self.address = address
        self._active_leds = 2
        self._red_buffer = deque((), max_buffer_len)
        self._ir_buffer = deque((), max_buffer_len)

    def _read_reg(self, reg, nbytes=1):
        return self.i2c.readfrom_mem(self.address, reg, nbytes)

    def _write_reg(self, reg, val):
        self.i2c.writeto_mem(self.address, reg, bytes([val]))

    def _bitmask(self, reg, mask, thing):
        orig = self._read_reg(reg)[0]
        orig &= mask
        self._write_reg(reg, orig | thing)

    def check_part_id(self):
        """Ověří, zda na adrese 0x57 skutečně odpovídá čip MAX30102."""
        try:
            part_id = self._read_reg(REG_PART_ID)[0]
            return part_id == EXPECTED_PART_ID
        except OSError:
            return False

    def soft_reset(self):
        """Provede softwarový reset senzoru a vyčká na jeho dokončení."""
        self._bitmask(REG_MODE_CONFIG, 0xBF, 0x40)
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < 100:
            if (self._read_reg(REG_MODE_CONFIG)[0] & 0x40) == 0:
                break
            time.sleep_ms(1)

    def shutdown(self):
        """Uspí senzor a zhasne LED diody pro úsporu baterie."""
        try:
            self._bitmask(REG_MODE_CONFIG, 0x7F, 0x80)
        except OSError:
            pass

    def wakeup(self):
        """Probudí senzor z úsporného režimu."""
        self._bitmask(REG_MODE_CONFIG, 0x7F, 0x00)

    def set_led_mode(self, mode):
        self._bitmask(REG_MODE_CONFIG, 0xF8, mode)
        if mode == MODE_REDONLY:
            self._active_leds = 1
        elif mode == MODE_REDIRONLY:
            self._active_leds = 2

    def set_adc_range(self, adc_range):
        # Rozsah ADC: 2048, 4096, 8192, 16384 nA
        if adc_range == 2048:
            val = 0x00
        elif adc_range == 4096:
            val = 0x20
        elif adc_range == 8192:
            val = 0x40
        else:
            val = 0x60
        self._bitmask(REG_SPO2_CONFIG, 0x9F, val)

    def set_sample_rate(self, sample_rate):
        # Vzorkovací frekvence: 50, 100, 200, 400, 800, 1000, 1600, 3200 Hz
        rates = {
            50: 0x00, 100: 0x04, 200: 0x08, 400: 0x0C,
            800: 0x10, 1000: 0x14, 1600: 0x18, 3200: 0x1C
        }
        val = rates.get(sample_rate, 0x04)
        self._bitmask(REG_SPO2_CONFIG, 0xE3, val)

    def set_pulse_width(self, pulse_width):
        # Šířka pulzu LED (rozlišení ADC): 69 (15b), 118 (16b), 215 (17b), 411 (18b) us
        widths = {69: 0x00, 118: 0x01, 215: 0x02, 411: 0x03}
        val = widths.get(pulse_width, 0x03)
        self._bitmask(REG_SPO2_CONFIG, 0xFC, val)

    def set_fifo_average(self, samples):
        # Hardwarové průměrování vzorků ve FIFO: 1, 2, 4, 8, 16, 32
        avgs = {1: 0x00, 2: 0x20, 4: 0x40, 8: 0x60, 16: 0x80, 32: 0xA0}
        val = avgs.get(samples, 0x40)
        self._bitmask(REG_FIFO_CONFIG, 0x1F, val)

    def enable_fifo_rollover(self):
        self._bitmask(REG_FIFO_CONFIG, 0xEF, 0x10)

    def set_pulse_amplitude_red(self, amplitude):
        self._write_reg(REG_LED1_PA, amplitude)

    def set_pulse_amplitude_ir(self, amplitude):
        self._write_reg(REG_LED2_PA, amplitude)

    def set_active_leds_amplitude(self, amplitude):
        self.set_pulse_amplitude_red(amplitude)
        self.set_pulse_amplitude_ir(amplitude)

    def clear_fifo(self):
        self._write_reg(REG_FIFO_WR_PTR, 0x00)
        self._write_reg(REG_OVF_COUNTER, 0x00)
        self._write_reg(REG_FIFO_RD_PTR, 0x00)

    def setup_sensor(self, led_mode=MODE_REDIRONLY, adc_range=4096,
                     sample_rate=100, pulse_width=411, fifo_avg=4,
                     led_power=MAX30105_PULSE_AMP_MEDIUM):
        """Výchozí konfigurace senzoru pro měření tepu a SpO2."""
        self.soft_reset()
        self.set_fifo_average(fifo_avg)
        self.enable_fifo_rollover()
        self.set_led_mode(led_mode)
        self.set_adc_range(adc_range)
        self.set_sample_rate(sample_rate)
        self.set_pulse_width(pulse_width)
        self.set_active_leds_amplitude(led_power)
        self.clear_fifo()

    def check(self):
        """Vyčte všechny nové vzorky z FIFO paměti senzoru do interní fronty."""
        read_ptr = self._read_reg(REG_FIFO_RD_PTR)[0]
        write_ptr = self._read_reg(REG_FIFO_WR_PTR)[0]

        if read_ptr == write_ptr:
            return 0

        num_samples = write_ptr - read_ptr
        if num_samples < 0:
            num_samples += 32

        bytes_per_sample = self._active_leds * 3
        raw_data = self._read_reg(REG_FIFO_DATA, num_samples * bytes_per_sample)

        for i in range(0, len(raw_data), bytes_per_sample):
            red = ((raw_data[i] << 16) | (raw_data[i + 1] << 8) | raw_data[i + 2]) & 0x03FFFF
            self._red_buffer.append(red)

            if self._active_leds > 1:
                ir = ((raw_data[i + 3] << 16) | (raw_data[i + 4] << 8) | raw_data[i + 5]) & 0x03FFFF
                self._ir_buffer.append(ir)

        return num_samples

    def available(self):
        """Vrátí počet nepřečtených vzorků ve frontě."""
        return len(self._ir_buffer) if self._active_leds > 1 else len(self._red_buffer)

    def pop_red_from_storage(self):
        """Odebere a vrátí nejstarší hodnotu červené (RED) složky."""
        if len(self._red_buffer) == 0:
            return 0
        return self._red_buffer.popleft()

    def pop_ir_from_storage(self):
        """Odebere a vrátí nejstarší hodnotu infračervené (IR) složky."""
        if len(self._ir_buffer) == 0:
            return 0
        return self._ir_buffer.popleft()