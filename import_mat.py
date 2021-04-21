from struct import unpack
from . import jk_flags
import numpy as np
import bpy
from pathlib import Path


class Mat:
    def __init__(self, mat, pal, alpha, name, shader, flag):
        '''
        initializes a material, takes material file name
        and palette file name (currently unused)
        '''
        self.mat = mat
        self.name = name.replace(".mat", "")
        self.pal = pal
        self.transp = False
        self.alpha = alpha
        self.anim = False
        self.shader = shader
        self.flag = flag

    def __str__(self):
        print(self.mat, self.pal)

    def import_Mat(self):
        '''
        reads an image from a JK mat file and its corresponding pal file
        and returns a material with diffuse map
        '''

        # read in header

        t_mat_header = unpack("ccccLLLLLLLLLLLLLLLLLLLLLLLL", self.mat[0:100])
        ver = t_mat_header[4]
        ttype = t_mat_header[5]
        NumOfTextures = t_mat_header[6]
        NumOfTextures1 = t_mat_header[7]
        textype = t_mat_header[22]
        colornum = t_mat_header[23]

        # Header lengths

        TMAT_HEADER_LEN = 76  # for every mat file
        TTEX_HEADER_LEN = 40  # for every mat file * NumOfTextures
        TTEX_DATA_LEN = 24 # goes before every pixel data

        # Textures #

        if ttype == 2:

            t_tex_header = unpack("LLLLLLLL", self.mat[100:132])

            header_offset = TMAT_HEADER_LEN + TTEX_HEADER_LEN * NumOfTextures
            pixel_offset = header_offset + TTEX_DATA_LEN

            size = unpack("LL", self.mat[header_offset:header_offset+8])

            image = bpy.data.images.new(self.name, width=size[0], height=size[1]*NumOfTextures)

            # create numpy pixel data

            img = np.frombuffer(self.mat, dtype=np.uint8, count=(size[1] * size[0] * NumOfTextures) + (TTEX_DATA_LEN * NumOfTextures), offset=header_offset).reshape((NumOfTextures, size[0]*size[1]+TTEX_DATA_LEN))
            img_del = np.delete(img, np.s_[0:TTEX_DATA_LEN], axis=1)
            img_headless = img_del.reshape((size[1]*NumOfTextures, size[0]))
            img_matrix = np.flipud(img_headless)
            col_pal = np.frombuffer(self.pal, dtype=np.uint8, count=256*3, offset=64).reshape((256, 3)) / 255
            trans_pal = np.frombuffer(self.pal, dtype=np.uint8, count=256, offset=64 + (256*3)).reshape((256, 1)) / 63
            if self.alpha:
                pal_add_channel = np.hstack((col_pal, trans_pal))
            else:
                pal_add_channel = np.hstack((col_pal, np.ones((256, 1))))
            col_image = pal_add_channel[img_matrix]
            pixels = col_image.flatten()

            image.pixels = pixels

            # save image temporarily

            prefs = bpy.context.preferences.addons["import_jkl"].preferences
            temp_path = Path(prefs.temp_folder)
            if temp_path != "":
                joined_path = temp_path.joinpath(self.name + ".png")
                image.filepath_raw = str(joined_path)
                image.file_format = 'PNG'
                image.save()
            else:
                self.report({'INFO'}, "Missing temp folder, check add-on preferences!")

            # create material

            mat = bpy.data.materials.new(name=self.name)
            mat.use_nodes = True

            if self.alpha:
                mat.use_backface_culling = True
            else:
                mat.use_backface_culling = False

            bsdf = mat.node_tree.nodes["Principled BSDF"]

            if self.shader == "BSDF":
                bsdf.inputs[5].default_value = 0.0      # Specular
                bsdf.inputs[7].default_value = 1.0      # Roughness
                texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
                texImage.image = image
                mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
                if self.alpha:
                    mat.node_tree.links.new(bsdf.inputs['Alpha'], texImage.outputs['Alpha'])
                    mat.blend_method = 'CLIP'

            else:
                mat.node_tree.nodes.remove(bsdf)
                output = mat.node_tree.nodes["Material Output"]
                texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')

                vertexColor = mat.node_tree.nodes.new('ShaderNodeAttribute')
                vertexColor.attribute_name = 'Intensities'
                vertexColor.location = -500, -50

                mixColor = mat.node_tree.nodes.new('ShaderNodeMixRGB')
                mixColor.blend_type = 'MULTIPLY'
                mixColor.inputs[0].default_value = 0.98
                mixColor.location = -250, 150

                texImage.image = image
                texImage.location = -600, 250
                mat.node_tree.links.new(output.inputs['Surface'], mixColor.outputs['Color'])
                mat.node_tree.links.new(mixColor.inputs['Color1'], texImage.outputs['Color'])
                mat.node_tree.links.new(mixColor.inputs['Color2'], vertexColor.outputs['Color'])

        # Color Mat #

        else:
            mat = bpy.data.materials.new(name=self.name)
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes["Principled BSDF"]
            mat.node_tree.nodes.remove(bsdf)
            output = mat.node_tree.nodes["Material Output"]
            # bsdf.inputs[5].default_value = 0.0      # Specular
            # bsdf.inputs[7].default_value = 1.0      # Roughness
            colorNode = mat.node_tree.nodes.new('ShaderNodeRGB')
            r = self.pal[64+(colornum*3)]/255
            g = self.pal[65+(colornum*3)]/255
            b = self.pal[66+(colornum*3)]/255
            colorNode.outputs[0].default_value = (r, g, b, 1)
            colorNode.location = -400, 250
            mat.node_tree.links.new(output.inputs['Surface'], colorNode.outputs['Color'])
