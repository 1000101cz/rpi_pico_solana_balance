from machine import Pin, SPI
import framebuf
import utime
import urequests
import ujson
import time
import network
import ntptime

# Display resolution
EPD_WIDTH = 128
EPD_HEIGHT = 296

RST_PIN = 12
DC_PIN = 8
CS_PIN = 9
BUSY_PIN = 13

WF_PARTIAL_2IN9 = [
    0x0, 0x40, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x80, 0x80, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x40, 0x40, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x80, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0A, 0x0, 0x0, 0x0, 0x0, 0x0, 0x1,
    0x1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x0, 0x0, 0x0,
    0x22, 0x17, 0x41, 0xB0, 0x32, 0x36,
]

WS_20_30 = [
    0x80, 0x66, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x40, 0x0, 0x0, 0x0,
    0x10, 0x66, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x20, 0x0, 0x0, 0x0,
    0x80, 0x66, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x40, 0x0, 0x0, 0x0,
    0x10, 0x66, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x20, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x14, 0x8, 0x0, 0x0, 0x0, 0x0, 0x2,
    0xA, 0xA, 0x0, 0xA, 0xA, 0x0, 0x1,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x14, 0x8, 0x0, 0x1, 0x0, 0x0, 0x1,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x1,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
    0x44, 0x44, 0x44, 0x44, 0x44, 0x44, 0x0, 0x0, 0x0,
    0x22, 0x17, 0x41, 0x0, 0x32, 0x36
]

ssid = "<<Your_WiFi_SSID>>"
password = "<<Your_WiFi_Password>>"
pubkey = "<<Your_PubKey>>"
fiat_currency = "EUR"
TIMEZONE_OFFSET = 2 * 3600  # Berlin (UTC+2)


def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to network...")
        wlan.connect(ssid, password)
        timeout = 10  # seconds
        start = time.time()
        while not wlan.isconnected():
            if time.time() - start > timeout:
                print("Failed to connect")
                return
            time.sleep(1)
    print("Connected, IP address:", wlan.ifconfig()[0])


def get_solana_price():
    url = f"https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies={fiat_currency.lower()}"
    response = urequests.get(url)
    data = response.json()
    response.close()
    price = data["solana"][fiat_currency.lower()]
    print("Solana price in EUR:", price)
    return price


def get_solana_balance(wallet_address):
    url = "https://api.mainnet-beta.solana.com"
    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBalance",
        "params": [wallet_address]
    }

    response = urequests.post(url, headers=headers, data=ujson.dumps(payload))
    raw = response.text
    # print("Raw response:", raw)
    data = response.json()
    response.close()

    lamports = data["result"]["value"]
    sol = lamports / 1_000_000_000
    print(f"Balance: {sol} SOL")
    return sol


def get_24h_hist_price():
    url = f'https://api.binance.com/api/v3/klines?symbol=SOL{fiat_currency}&interval=15m&limit=96'
    response = urequests.get(url)
    raw = response.text
    # print("Raw response:", raw)
    data = response.json()
    # Each kline = [open time, open, high, low, close, volume, ...]
    return data


def sync_time():
    try:
        ntptime.settime()  # Sync time via NTP
        print("Time synced")
    except Exception as e:
        print("Failed to sync time:", e)


def format_time(t):
    return "{:04}-{:02}-{:02} {:02}:{:02}:{:02}".format(*t[:6])


class EPD_2in9_Landscape(framebuf.FrameBuffer):
    def __init__(self):
        self.balance = 0.1
        self.sol_price = 0.1
        self.reset_pin = Pin(RST_PIN, Pin.OUT)
        self.price_history = {}

        self.busy_pin = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(CS_PIN, Pin.OUT)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

        self.partial_lut = WF_PARTIAL_2IN9
        self.full_lut = WS_20_30

        self.spi = SPI(1)
        self.spi.init(baudrate=4000_000)
        self.dc_pin = Pin(DC_PIN, Pin.OUT)

        self.buffer = bytearray(self.height * self.width // 8)
        super().__init__(self.buffer, self.height, self.width, framebuf.MONO_VLSB)
        self.init()

    def digital_write(self, pin, value):
        pin.value(value)

    def digital_read(self, pin):
        return pin.value()

    def delay_ms(self, delaytime):
        utime.sleep(delaytime / 1000.0)

    def delay_min(self, delaytime):
        utime.sleep(delaytime * 60)

    def spi_writebyte(self, data):
        self.spi.write(bytearray(data))

    def module_exit(self):
        self.digital_write(self.reset_pin, 0)

    # Hardware reset
    def reset(self):
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(50)
        self.digital_write(self.reset_pin, 0)
        self.delay_ms(2)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(50)

    def send_command(self, command):
        self.digital_write(self.dc_pin, 0)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([command])
        self.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi_writebyte([data])
        self.digital_write(self.cs_pin, 1)

    def send_data1(self, buf):
        self.digital_write(self.dc_pin, 1)
        self.digital_write(self.cs_pin, 0)
        self.spi.write(bytearray(buf))
        self.digital_write(self.cs_pin, 1)

    def ReadBusy(self):
        print("e-Paper busy")
        while (self.digital_read(self.busy_pin) == 1):  # 0: idle, 1: busy
            self.delay_ms(10)
        print("e-Paper busy release")

    def TurnOnDisplay(self):
        self.send_command(0x22)  # DISPLAY_UPDATE_CONTROL_2
        self.send_data(0xC7)
        self.send_command(0x20)  # MASTER_ACTIVATION
        self.ReadBusy()

    def TurnOnDisplay_Partial(self):
        self.send_command(0x22)  # DISPLAY_UPDATE_CONTROL_2
        self.send_data(0x0F)
        self.send_command(0x20)  # MASTER_ACTIVATION
        self.ReadBusy()

    def lut(self, lut):
        self.send_command(0x32)
        self.send_data1(lut[0:153])
        self.ReadBusy()

    def SetLut(self, lut):
        self.lut(lut)
        self.send_command(0x3f)
        self.send_data(lut[153])
        self.send_command(0x03)  # gate voltage
        self.send_data(lut[154])
        self.send_command(0x04)  # source voltage
        self.send_data(lut[155])  # VSH
        self.send_data(lut[156])  # VSH2
        self.send_data(lut[157])  # VSL
        self.send_command(0x2c)  # VCOM
        self.send_data(lut[158])

    def SetWindow(self, x_start, y_start, x_end, y_end):
        self.send_command(0x44)  # SET_RAM_X_ADDRESS_START_END_POSITION
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self.send_data((x_start >> 3) & 0xFF)
        self.send_data((x_end >> 3) & 0xFF)
        self.send_command(0x45)  # SET_RAM_Y_ADDRESS_START_END_POSITION
        self.send_data(y_start & 0xFF)
        self.send_data((y_start >> 8) & 0xFF)
        self.send_data(y_end & 0xFF)
        self.send_data((y_end >> 8) & 0xFF)

    def SetCursor(self, x, y):
        self.send_command(0x4E)  # SET_RAM_X_ADDRESS_COUNTER
        self.send_data(x & 0xFF)

        self.send_command(0x4F)  # SET_RAM_Y_ADDRESS_COUNTER
        self.send_data(y & 0xFF)
        self.send_data((y >> 8) & 0xFF)
        self.ReadBusy()

    def init(self):
        # EPD hardware init start
        self.reset()

        self.ReadBusy()
        self.send_command(0x12)  # SWRESET
        self.ReadBusy()

        self.send_command(0x01)  # Driver output control
        self.send_data(0x27)
        self.send_data(0x01)
        self.send_data(0x00)

        self.send_command(0x11)  # data entry mode
        self.send_data(0x07)

        self.SetWindow(0, 0, self.width - 1, self.height - 1)

        self.send_command(0x21)  # Display update control
        self.send_data(0x00)
        self.send_data(0x80)

        self.SetCursor(0, 0)
        self.ReadBusy()

        self.SetLut(self.full_lut)
        # EPD hardware init end
        return 0

    def display(self, image):
        if (image == None):
            return
        self.send_command(0x24)  # WRITE_RAM
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])
        self.TurnOnDisplay()

    def display_Base(self, image):
        if (image == None):
            return
        self.send_command(0x24)  # WRITE_RAM
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])

        self.send_command(0x26)  # WRITE_RAM
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])

        self.TurnOnDisplay()

    def display_Partial(self, image):
        if (image == None):
            return

        self.digital_write(self.reset_pin, 0)
        self.delay_ms(2)
        self.digital_write(self.reset_pin, 1)
        self.delay_ms(2)

        self.SetLut(self.partial_lut)
        self.send_command(0x37)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x40)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x3C)  # BorderWaveform
        self.send_data(0x80)

        self.send_command(0x22)
        self.send_data(0xC0)
        self.send_command(0x20)
        self.ReadBusy()

        self.SetWindow(0, 0, self.width - 1, self.height - 1)
        self.SetCursor(0, 0)

        self.send_command(0x24)  # WRITE_RAM
        for j in range(int(self.width / 8) - 1, -1, -1):
            for i in range(0, self.height):
                self.send_data(image[i + j * self.height])
        self.TurnOnDisplay_Partial()

    def Clear(self, color):
        self.send_command(0x24)  # WRITE_RAM
        self.send_data1([color] * self.height * int(self.width / 8))
        self.send_command(0x26)  # WRITE_RAM
        self.send_data1([color] * self.height * int(self.width / 8))
        self.TurnOnDisplay()

    def sleep(self):
        self.send_command(0x10)  # DEEP_SLEEP_MODE
        self.send_data(0x01)

        self.delay_ms(2000)
        self.module_exit()

    def get_graph(self, current_time):
        x_start = 50
        x_end = 295
        x_diff = x_end - x_start

        y_start = 60
        y_end = 120
        y_diff = y_end - y_start

        max_price = float('-inf')
        min_price = float('inf')

        day_before = time.mktime(current_time) - (24 * 60 * 60)  # this is 24h
        # day_before = time.mktime(current_time) - (10 * 60)  # this is last 10min

        now = time.mktime(current_time)
        time_diff = now - day_before

        # remove old data
        keys = list(self.price_history.keys())
        for key in keys:
            if time.mktime(key) < day_before:
                self.price_history.pop(key)
            else:
                max_price = max(max_price, self.price_history[key])
                min_price = min(min_price, self.price_history[key])

        price_diff = max_price - min_price
        if price_diff == 0:
            return

        self.hline(x_start, y_end, x_diff, 0x00)
        self.vline(x_start, y_start, y_diff, 0x00)

        self.text(f"{max_price:.2f}", 0, y_start, 0x00)
        self.text(f"{min_price:.2f}", 0, y_end, 0x00)

        keys = list(self.price_history.keys())
        keys = sorted(keys)

        last_x = None
        last_y = None

        for idx, key in enumerate(keys):
            key_time = time.mktime(key)
            x_coord = x_start + int(((key_time - day_before) / time_diff) * x_diff)
            y_coord = y_start + int(((max_price - self.price_history[key]) / price_diff) * y_diff)

            if last_x is not None:
                self.line(last_x, last_y, x_coord, y_coord, 0x00)

            last_x = x_coord
            last_y = y_coord

        if len(keys) >= 2:
            price_before = self.price_history[keys[0]]
            price_now = self.price_history[keys[-1]]
            diff = 100.0 * ((price_now - price_before) / price_before)
            if diff > 0:
                self.text(f"+{diff:.2f}%", 160, 50, 0x00)
            else:
                self.text(f"{diff:.2f}%", 160, 50, 0x00)

    def init_fetch(self):
        data = get_24h_hist_price()

        for k in data:
            timestamp = k[0]
            key_time = time.localtime(k[0] // 1000 + TIMEZONE_OFFSET)
            # open_price = float(k[1])
            # high_price = float(k[2])
            # low_price = float(k[3])
            close_price = float(k[4])
            # print(f"{timestamp}: O:{open_price} H:{high_price} L:{low_price} C:{close_price}")
            self.price_history[key_time] = close_price

    def fetch_data(self):

        self.sol_price = get_solana_price()
        self.balance = get_solana_balance(pubkey)

        current_time = time.localtime(time.time() + TIMEZONE_OFFSET)

        self.price_history[current_time] = self.sol_price

        self.Clear(0xff)
        self.fill(0xff)

        graph = self.get_graph(current_time)

        self.update_display(current_time)

    def update_display(self, current_time):

        formatted_time = format_time(current_time)
        self.text(f"{formatted_time}", 5, 0, 0x00)
        self.hline(0, 10, 296, 0x00)
        self.text(f"Balance: {self.balance:.3f} SOL", 5, 15, 0x00)
        self.text(f"SOL price: {self.sol_price:.2f} {fiat_currency}", 5, 25, 0x00)
        worth = self.balance * self.sol_price
        self.text(f"Wallet worth: {worth:.3f} {fiat_currency}", 5, 35, 0x00)
        self.hline(0, 45, 296, 0x00)
        self.text("                            Last 24h", 5, 50, 0x00)
        self.display(epd.buffer)


if __name__ == '__main__':
    connect()

    sync_time()

    epd = EPD_2in9_Landscape()
    epd.init_fetch()
    while True:
        epd.fetch_data()
        epd.delay_min(15)

    # epd.Clear(0xff)

    # epd.fill(0xff)
    # epd.text("Solana", 5, 10, 0x00)
    # epd.text(f"{pubkey[:36]}", 5, 20, 0x00)
    # epd.text(f"{pubkey[36:]}", 5, 30, 0x00)
    # epd.display(epd.buffer)
    # epd.delay_ms(2000)

    # epd.vline(10, 40, 60, 0x00)
    # epd.vline(120, 40, 60, 0x00)
    # epd.hline(10, 40, 110, 0x00)
    # epd.hline(10, 100, 110, 0x00)
    # epd.line(10, 40, 120, 100, 0x00)
    # epd.line(120, 40, 10, 100, 0x00)
    # epd.display(epd.buffer)
    # epd.delay_ms(2000)

    # epd.rect(150, 5, 50, 55, 0x00)
    # epd.fill_rect(150, 65, 50, 115, 0x00)
    # epd.display_Base(epd.buffer)
    # epd.delay_ms(2000)

    # for i in range(0, 10):
    #     epd.fill_rect(220, 60, 10, 10, 0xff)
    #     epd.text(str(i), 222, 62, 0x00)
    #     epd.display_Partial(epd.buffer)
