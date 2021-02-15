from struct import unpack
import numpy as np
import bpy

class Sft:
    def __init__(self, sft, name, ext_pal):

        self.file = sft
        self.name = name.replace(".sft", "")
        self.palette = ext_pal


    def import_Sft(self):
        
        header = unpack("ccccLLLLLLLLLHH", self.file[0:44])

        first_char = header[13]
        last_char = header[14]

        length_char_defs = (last_char - first_char + 1) * 8   # 8 bytes (2 longs) for each char def
        header_bm_start = length_char_defs + 44
        header_bm_end = header_bm_start+76

        header_bm = unpack("ccccLLLLLLLLLLLLLLLLLL", self.file[header_bm_start : header_bm_end])

        PalInc = header_bm[6]                        # 0, 1 or 2 ;  2 = palette included
        NumImages = header_bm[7]                     # number of images in file
        XOffset = header_bm[8]                       # X-offset (for overlaying on other BMs)
        YOffset = header_bm[9]                       # Y-offset (for overlaying on other BMs)
        Transparent = header_bm[10]                  # Transparent colour
        Uk3 = header_bm[11]                          # = 1 in 16-bit BMs, = 0 in 8-bit BMs
        NumBits = header_bm[12]                      # 8 = 8-bit BM, 16 = 16-bit BM
        BlueBits = header_bm[13]                     # = 5 for 16-bit BMs, else = 0
        GreenBits = header_bm[14]                    # = 6 for 16-bit BMs, else = 0
        RedBits = header_bm[15]                      # = 5 for 16-bit BMs, else = 0
        Uk4 = header_bm[16]                          # = 11 in 16-bit BMs, else = 0
        Uk5 = header_bm[17]                          # = 5 in 16-bit BMs, else = 0
        Uk6 = header_bm[18]                          # = 0
        Uk7 = header_bm[19]                          # = 3 in 16-bit BMs, else = 0
        Uk8 = header_bm[20]                          # = 2 in 16-bit BMs, else = 0
        Uk9 = header_bm[21]                          # = 2 in 16-bit BMs, else = 0

        size_x, size_y = unpack("LL", self.file[header_bm_start+128:header_bm_start+136])

        img_start = header_bm_start+136
        img_size = size_x * size_y
        palette_start = img_start + img_size

        image = bpy.data.images.new(name=self.name, width=size_x, height=size_y)

        if NumBits == 16:
            flipped_img16 = np.frombuffer(self.file, dtype=np.uint16 ,count=img_size, offset=img_start).reshape((size_y, size_x))
            img = np.flipud(flipped_img16)
            flat_img16 = img.reshape((img_size, 1))

            r = ((flat_img16 & 0b1111100000000000) >> 11) / 31
            g = ((flat_img16 & 0b0000011111100000) >> 6) / 31
            b = (flat_img16 & 0b0000000000011111) / 31
            a = (flat_img16 != Transparent).astype(int)

            col_image = np.hstack((r, g, b, a))
            pixels = col_image.flatten()

            
        else:
            img = np.frombuffer(self.file, dtype=np.uint8 ,count=img_size, offset=img_start).reshape((size_y, size_x))
            img_matrix = np.flipud(img)

            if PalInc == 2:
                pal = np.frombuffer(self.file, dtype=np.uint8 ,count=256*3, offset=palette_start).reshape((256,3)) / 255
            else:
                pal = np.frombuffer(self.palette, dtype=np.uint8 ,count=256*3, offset=64).reshape((256,3)) / 255
                
            a = np.ones((256,1))
            a[Transparent][0] = 0.0
            pal_alpha_channel = np.hstack((pal, a))

            col_image = pal_alpha_channel[img_matrix]
            pixels = col_image.flatten()


        image.pixels = pixels

