from struct import unpack
import bpy

class Bm:

    def __init__(self, bm, name):

        self.file = bm
        self.name = name

    def import_Bm(self):

        header = unpack("ccccLLLLLLLLLLLLLLLLLL", self.file[0:76])

        size_x, size_y = unpack("LL", self.file[128:136])

        PalInc = header[6]                        # 0, 1 or 2 ;  2 = palette included
        NumImages = header[7]                     # number of images in file
        XOffset = header[8]                       # X-offset (for overlaying on other BMs)
        YOffset = header[9]                       # Y-offset (for overlaying on other BMs)
        Transparent = header[10]                  # Transparent colour
        Uk3 = header[11]                          # = 1 in 16-bit BMs, = 0 in 8-bit BMs
        NumBits = header[12]                      # 8 = 8-bit BM, 16 = 16-bit BM
        BlueBits = header[13]                     # = 5 for 16-bit BMs, else = 0
        GreenBits = header[14]                    # = 6 for 16-bit BMs, else = 0
        RedBits = header[15]                      # = 5 for 16-bit BMs, else = 0
        Uk4 = header[16]                          # = 11 in 16-bit BMs, else = 0
        Uk5 = header[17]                          # = 5 in 16-bit BMs, else = 0
        Uk6 = header[18]                          # = 0
        Uk7 = header[19]                          # = 3 in 16-bit BMs, else = 0
        Uk8 = header[20]                          # = 2 in 16-bit BMs, else = 0
        Uk9 = header[21]                          # = 2 in 16-bit BMs, else = 0

        img_start = 136
        palette_start = img_start + size_x * size_y

        print(header)
        print("NumBits: ", NumBits)
        print(size_x, size_y)




        palette = [None]
        if PalInc == 2:
            palette_flat = self.file[palette_start : palette_start + 256 * 3]
            print(palette_flat)

        image = bpy.data.images.new(name=self.name, width=size_x, height=size_y)

        pixels = [None] * size_x * size_y
        for x in range(size_x):
            for y in range(size_y):
                pixel = (size_x * size_y) - (y * size_x) + x - size_x
                image_value =  self.file[pixel + img_start]
                r = self.file[palette_start + image_value * 3]/256
                g = self.file[palette_start + 1 + image_value * 3]/256
                b = self.file[palette_start + 2 + image_value * 3]/256
                a = 1.0
                pixels[(y * size_x) + x] = [r, g, b, a]

        pixels = [chan for px in pixels for chan in px]


        image.pixels = pixels