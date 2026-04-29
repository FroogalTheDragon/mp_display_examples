print("elegoo_cyd_2432s028r.py initialization")
"""
Elegoo 2.8" Cheap Yellow Display (ESP32-2432S028R)
    https://github.com/witnessmenow/ESP32-Cheap-Yellow-Display
    https://www.lcdwiki.com/2.8inch_ESP32-32E_Display

Hardware:
 * ESP32 WROOM (no SPIRAM, 4MB flash)
 * Display: ILI9341 320x240 (SPI on HSPI bus, GPIO 13/12/14/15/2)
 * Touch: XPT2046 resistive (separate SPI bus on VSPI, GPIO 32/39/25/33, IRQ=36)
 * RGB LED (active low): R=4, G=16, B=17
 * Light sensor: GPIO 34
 * Speaker: GPIO 26

Key fix for memory fragmentation:
 * lcd_bus, machine, and SPI bus init happen FIRST
 * Frame buffers are allocated BEFORE heavy module imports fragment the heap
 * Then the rest of the drivers are imported
"""

import gc
import time
import machine
import lcd_bus
from machine import Pin, ADC
from micropython import const

# --- Display SPI (HSPI = host 1) ---
SPI_HOST    = const(1)
SPI_FREQ    = const(8_000_000)   # 8MHz is safe max for ILI9341 over SPI
LCD_SCK     = const(14)
LCD_MOSI    = const(13)
LCD_MISO    = const(12)
LCD_DC      = const(2)
LCD_CS      = const(15)
LCD_BL      = const(21)
LCD_TYPE    = const(2)           # ILI9341 type 2

# --- Touch SPI (VSPI = host 2, completely separate pins on CYD) ---
TOUCH_HOST  = const(2)
TOUCH_FREQ  = const(1_000_000)
TOUCH_SCK   = const(25)
TOUCH_MOSI  = const(32)
TOUCH_MISO  = const(39)
TOUCH_CS    = const(33)
TOUCH_IRQ   = const(36)

# --- Display resolution ---
DISPLAY_W   = const(320)
DISPLAY_H   = const(240)

# --- RGB LED (active low) ---
LED_RED     = const(4)
LED_GREEN   = const(16)
LED_BLUE    = const(17)

# --- Other hardware ---
LIGHTSENSOR_PIN = const(34)
SPEAKER_PIN     = const(26)
BUTTON_BOOT     = const(0)

# --- SD Card (VSPI, shared with touch physically but different CS) ---
SDCARD_SCK  = const(18)
SDCARD_MOSI = const(23)
SDCARD_MISO = const(19)
SDCARD_CS   = const(5)

# =============================================================
# STEP 1: Init SPI bus and allocate frame buffers EARLY
# This must happen before heavy imports (lvgl, mpos.ui, etc.)
# fragment the internal heap — those imports eat RAM and leave
# no room for a contiguous DMA buffer afterward.
# =============================================================

gc.collect()

print("elegoo_cyd: SPI bus init")
try:
    display_spi = machine.SPI.Bus(
        host=SPI_HOST,
        sck=LCD_SCK,
        mosi=LCD_MOSI,
        miso=LCD_MISO,
    )
except Exception as e:
    print(f"Display SPI bus init failed: {e} — resetting in 3s")
    time.sleep(3)
    machine.reset()

display_bus = lcd_bus.SPIBus(
    spi_bus=display_spi,
    freq=SPI_FREQ,
    dc=LCD_DC,
    cs=LCD_CS,
)

# Allocate frame buffers NOW, while heap is still contiguous.
# 320 * 15 * 2 = 9600 bytes each (19200 total). Leaves ~113KB free.
# 15 rows = 16 render passes instead of 24 — less pixelation, safe on RAM.
_BUF_SIZE = const(DISPLAY_W * 15 * 2)
print(f"elegoo_cyd: allocating frame buffers ({_BUF_SIZE} bytes each, free={gc.mem_free()})")
try:
    fb1 = display_bus.allocate_framebuffer(
        _BUF_SIZE, lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA
    )
    fb2 = display_bus.allocate_framebuffer(
        _BUF_SIZE, lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA
    )
except MemoryError as e:
    print(f"Frame buffer allocation failed: {e}")
    print(f"Free RAM: {gc.mem_free()}")
    print("Try reducing _BUF_SIZE (e.g. 320*5*2=3200) or run gc.collect() earlier.")
    raise

print(f"elegoo_cyd: frame buffers allocated, free={gc.mem_free()}")

# =============================================================
# STEP 2: Now import the heavy modules
# =============================================================

import drivers.display.ili9341 as ili9341
import lvgl as lv
import mpos.ui
from drivers.indev.xpt2046 import XPT2046
from mpos import InputManager

# =============================================================
# STEP 3: RGB LED — light up during init
# =============================================================

red_led   = Pin(LED_RED,   Pin.OUT)
green_led = Pin(LED_GREEN, Pin.OUT)
blue_led  = Pin(LED_BLUE,  Pin.OUT)
red_led.on()    # active low = on
green_led.on()
blue_led.on()

# =============================================================
# STEP 4: Display init
# =============================================================

print("elegoo_cyd: display init")
try:
    mpos.ui.main_display = ili9341.ILI9341(
        data_bus=display_bus,
        display_width=DISPLAY_W,
        display_height=DISPLAY_H,
        frame_buffer1=fb1,
        frame_buffer2=fb2,
        color_space=lv.COLOR_FORMAT.RGB565,
        color_byte_order=ili9341.BYTE_ORDER_BGR,
        rgb565_byte_swap=True,
        backlight_pin=LCD_BL,
        backlight_on_state=ili9341.STATE_PWM,
    )
except Exception as e:
    print(f"ILI9341 init failed: {e}")
    time.sleep(3)
    machine.reset()

mpos.ui.main_display.init(LCD_TYPE)
mpos.ui.main_display.set_power(True)
mpos.ui.main_display.set_color_inversion(False)
mpos.ui.main_display.set_backlight(100)

# =============================================================
# STEP 5: Touch init (separate SPI bus with correct CYD pins)
# =============================================================

print("elegoo_cyd: touch init")
touch_spi = machine.SPI.Bus(
    host=TOUCH_HOST,
    sck=TOUCH_SCK,
    mosi=TOUCH_MOSI,
    miso=TOUCH_MISO,
)
touch_dev = machine.SPI.Device(
    spi_bus=touch_spi,
    freq=TOUCH_FREQ,
    cs=TOUCH_CS,
)

indev = XPT2046(
    touch_dev,
    lcd_cs=LCD_CS,
    touch_cs=TOUCH_CS,
    display_width=DISPLAY_W,
    display_height=DISPLAY_H,
    startup_rotation=lv.DISPLAY_ROTATION._0,
)

group = lv.group_create()
group.set_default()
indev.set_group(group)
indev.enable(True)
InputManager.register_indev(indev)

# =============================================================
# STEP 6: Light sensor
# =============================================================

lightsensor = ADC(LIGHTSENSOR_PIN, atten=ADC.ATTN_0DB)
print(f"elegoo_cyd: light sensor = {lightsensor.read_uv()} uV")

# =============================================================
# DONE
# =============================================================

# LEDs off = init complete
red_led.off()
green_led.off()
blue_led.off()

gc.collect()
print(f"elegoo_cyd: init done, free RAM = {gc.mem_free()}")
