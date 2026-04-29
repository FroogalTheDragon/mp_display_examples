import lvgl_micropython.lib.micropython
import lvgl_micropython.lib.lvgl as lv

lv.init()

from machine import Pin

print("CrowPanel 7 Inch")

class CrowPenel7:
    # Define our data pins
    DE = const(41)
    VSYNC = const(40)
    HSYNC = const(39)

    # Blue Pins
    B7 = const(4)
    B6 = const(5)
    B5 = const(6)
    B4 = const(7)
    B3 = const(15) # B2-B0 are hooked up to gnd for some reason

    # Green Pins
    G7 = const(1)
    G6 = const(16)
    G5 = const(8)
    G4 = const(3)
    G3 = const(46)
    G2 = const(9) # G1 - G0 are hooked up to gnd

    # Red Pins
    R7 = const(45)
    R6 = const(48)
    R5 = const(47)
    R4 = const(21)
    R3 = const(14) # R2 - R0 hooked up to gne
    
    BOOT_CLOCK = const(0)
    
    hsync_polarity = 0
    hsync_front_porch = 40
    hsync_pulse_width = 48
    hsync_back_porch = 40

    vsync_polarity = 0
    vsync_front_porch = 1
    vsync_pulse_width = 31
    vsync_back_porch = 13

    pclk_active_neg = 1
    de_idle_high = 0
    pclk_idle_high = 0
    
    freq_write  = 14000000
    def __init__(self):
        pass
    
    def setup(self):
        pass


