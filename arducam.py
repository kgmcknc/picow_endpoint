
import machine
import hm01b0
import time
import my_i2c

class camera_class:
   def __init__(self):
      self.v_res = 324
      self.h_res = 324
      self.data_bits = 8
      self.image_cpp = 1
      self.image_bpc = 8
      self.i2c = my_i2c.i2c_class()
      self.scl_pin = machine.Pin(5)
      self.sda_pin = machine.Pin(4)
      self.vsync_pin = machine.Pin(16, machine.Pin.IN)
      self.hsync_pin = machine.Pin(15, machine.Pin.IN)
      self.pix_clk_pin = machine.Pin(14, machine.Pin.IN)
      self.data_pin = machine.Pin(6, machine.Pin.IN)
      self.hw_sm: hm01b0.cam_pio_class
   
   def init_camera(self):
      self.i2c.initiate_i2c(self.scl_pin,self.sda_pin,hm01b0.hm01b0_i2c_freq,hm01b0.hm01b0_i2c_address,hm01b0.hm01b0_reg_address_width)
      time.sleep(0.5)
      self.i2c.list_reg_writes(hm01b0.hm01b0_regs_init_324x324_serial, hm01b0.hm01b0_i2c_delay)
      self.hw_sm = hm01b0.cam_pio_class(self.vsync_pin, self.hsync_pin, 0, 125_000_000, self.data_pin)

   def get_frame(self):
      self.hw_sm.get_frame(self.h_res, self.v_res, self.data_bits, 125_000_000, self.data_pin, self.vsync_pin)