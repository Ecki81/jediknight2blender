from struct import unpack
import numpy as np
import bpy


class Cmp:

    def __init__(self, cmp, name):
        self.file = cmp
        self.name = name.replace(".cmp", "")

    def import_Cmp(self):

        header = unpack("ccccLL", self.file[0:12])

        Transparency = header[5]

        image = bpy.data.images.new(
            name=self.name,
            width=16,
            height=16
            )

        pixels = np.frombuffer(
                self.file,
                dtype=np.uint8,
                count=256*3,
                offset=64
                ).reshape((256,3)) / 255

        image.pixels = np.hstack((pixels, np.ones((256, 1)))).flatten()
