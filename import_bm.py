from struct import unpack
import numpy as np
import bpy


class Bm:

    def __init__(self, bm, name, ext_pal):

        self.file = bm
        self.name = name.replace(".bm", "")
        self.palette = ext_pal

    def import_Bm(self):

        header = unpack("ccccLLLLLLLLLLLLLLLLLL", self.file[0:76])

        size_x, size_y = unpack("LL", self.file[128:136])

        PalInc = header[6]              # 0, 1 or 2 ;  2 = palette
        NumImages = header[7]           # number of images in file
        XOffset = header[8]             # X-offset (for overlaying other BMs)
        YOffset = header[9]             # Y-offset (for overlaying other BMs)
        Transparent = header[10]        # Transparent colour
        Uk3 = header[11]                # = 1 in 16-bit BMs, = 0 in 8-bit BMs
        NumBits = header[12]            # 8 = 8-bit BM, 16 = 16-bit BM
        BlueBits = header[13]           # = 5 for 16-bit BMs, else = 0
        GreenBits = header[14]          # = 6 for 16-bit BMs, else = 0
        RedBits = header[15]            # = 5 for 16-bit BMs, else = 0
        Uk4 = header[16]                # = 11 in 16-bit BMs, else = 0
        Uk5 = header[17]                # = 5 in 16-bit BMs, else = 0
        Uk6 = header[18]                # = 0
        Uk7 = header[19]                # = 3 in 16-bit BMs, else = 0
        Uk8 = header[20]                # = 2 in 16-bit BMs, else = 0
        Uk9 = header[21]                # = 2 in 16-bit BMs, else = 0

        img_start = 136
        img_size = size_x * size_y
        palette_start = img_start + img_size

        image = bpy.data.images.new(
            name=self.name,
            width=size_x,
            height=size_y
            )

        if NumBits == 16:
            # reshape flat array to 2d matrix for flipping
            flipped_img16 = np.frombuffer(
                self.file,
                dtype=np.uint16,
                count=img_size,
                offset=img_start
                ).reshape((size_y, size_x))

            # image flipped, starts top left in sith engine
            # blender images start bottom left
            img = np.flipud(flipped_img16)
            flat_img16 = img.reshape((img_size, 1))

            # first 5 of 16 bit for red channel
            r = ((flat_img16 & 0b1111100000000000) >> 11) / 31
            # 6 of 16 bit for green channel
            g = ((flat_img16 & 0b0000011111100000) >> 6) / 31
            # last 5 of 16 bit for blue channel
            b = (flat_img16 & 0b0000000000011111) / 31
            # transparency bool for "Transparent" index, recast to int 0 or 1
            a = (flat_img16 != Transparent).astype(int)

            col_image = np.hstack((r, g, b, a))
            pixels = col_image.flatten()

        else:
            img = np.frombuffer(
                self.file,
                dtype=np.uint8,
                count=img_size,
                offset=img_start
                ).reshape((size_y, size_x))
            img_matrix = np.flipud(img)

            if PalInc == 2:
                pal = np.frombuffer(
                    self.file,
                    dtype=np.uint8,
                    count=256*3,
                    offset=palette_start
                    ).reshape((256, 3)) / 255
            else:
                pal = np.frombuffer(
                    self.palette,
                    dtype=np.uint8,
                    count=256*3,
                    offset=64).reshape((256, 3)) / 255

            a = np.ones((256, 1))
            a[Transparent][0] = 0.0
            pal_alpha_channel = np.hstack((pal, a))

            col_image = pal_alpha_channel[img_matrix]
            pixels = col_image.flatten()

        image.pixels = pixels
