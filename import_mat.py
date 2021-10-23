from struct import unpack
from . import jk_flags
import numpy as np
import bpy
from pathlib import Path
from os.path import basename, dirname


class Mat:
    def __init__(self, mat, pal, alpha, name, shader, emission, faceflags):
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
        self.emission = emission
        self.flags = faceflags

    def __str__(self):
        print(self.mat, self.pal)

    def import_Mat(self):
        '''
        reads an image from a JK mat file and its corresponding pal file
        and returns a material with diffuse and emission (optional) map
        '''

        # read in header

        t_mat_header = unpack("ccccLLLLLLLLLLLLLLLLLLLLLLLL", self.mat[0:100])
        ver = t_mat_header[4]
        ttype = t_mat_header[5]
        NumOfTextures = t_mat_header[6]
        NumOfTextures1 = t_mat_header[7]
        textype = t_mat_header[22]
        colornum = t_mat_header[23]

        # Header byte lengths

        TMAT_HEADER_LEN = 76  # for every mat file
        TTEX_HEADER_LEN = 40  # for every mat file * NumOfTextures
        TTEX_DATA_LEN = 24  # goes before every pixel data block
        TCMP_HEADER_LEN = 64

        # if Solid colors, overide texture type flag with color type

        if self.shader == "SOLID":
            ttype = 1
        else:
            pass

        # Textures #

        if ttype == 2:

            t_tex_header = unpack("LLLLLLLL", self.mat[100:132])

            header_offset = TMAT_HEADER_LEN + TTEX_HEADER_LEN * NumOfTextures

            size_x, size_y = unpack("LL", self.mat[header_offset:header_offset+8])

            image = bpy.data.images.new(self.name, width=size_x, height=size_y*NumOfTextures)

            # create numpy pixel data

            # matrix shape: frames * length of pixel data incl. header
            img = np.frombuffer(
                self.mat,
                dtype=np.uint8,
                count=(size_y * size_x * NumOfTextures) + (TTEX_DATA_LEN * NumOfTextures),
                offset=header_offset
                ).reshape((NumOfTextures, size_x*size_y+TTEX_DATA_LEN))

            # remove TTextureData columns
            img_del = np.delete(img, np.s_[0:TTEX_DATA_LEN], axis=1)

            # reshape to image dimensions
            img_headless = img_del.reshape((size_y*NumOfTextures, size_x))

            # flip upside down to blender pixel direction (0,0 = bottom left)
            img_matrix = np.flipud(img_headless)

            # read in color values to RGB table shape
            col_pal = np.frombuffer(self.pal, dtype=np.uint8, count=256*3, offset=64).reshape((256, 3)) / 255

            # read in alpha values from last light level table
            trans_pal = np.frombuffer(self.pal, dtype=np.uint8, count=256, offset=64 + (256*3) + (256*63)).reshape((256, 1)) / 63

            # concat alpha values to RGB table
            if self.alpha:
                pal_rgba = np.hstack((col_pal, trans_pal))
            else:
                pal_rgba = np.hstack((col_pal, np.ones((256, 1))))

            # assign rgba values to image
            col_image = pal_rgba[img_matrix]

            # flatten image matrix to R,G,B,A,R,G,B,A,....
            pixels = col_image.flatten()

            image.pixels = pixels

            # # emissive map
            has_em_map = False
            if self.emission:
                light_levels = np.frombuffer(self.pal, dtype=np.uint8, count=256, offset=64 + (256*3))
                emission_pal = col_pal[light_levels]

                # check, if emission is all black
                em_image = emission_pal[img_matrix]
                em_image_sum = np.sum(em_image)
                if em_image_sum > 0.0:
                    print(self.name, "has emission")

                    # add alpha layer to image matrix
                    alpha_pixels = np.ones((size_y*NumOfTextures, size_x, 1))
                    em_image_rgba = np.concatenate((em_image, alpha_pixels), axis=2)
                    em_pixels = em_image_rgba.flatten()

                    emission_image = bpy.data.images.new(self.name + "_E", width=size_x, height=size_y*NumOfTextures, alpha=False)
                    emission_image.pixels = em_pixels
                    has_em_map = True
                else:
                    has_em_map = False
            else:
                pass

            # save image temporarily

            this_addon = basename(dirname(__file__))
            prefs = bpy.context.preferences.addons[this_addon].preferences
            temp_path = Path(prefs.temp_folder)
            if temp_path != "":
                joined_path = temp_path.joinpath(self.name + ".png")
                joined_path_e = temp_path.joinpath(self.name + "_E.png")
                image.filepath_raw = str(joined_path)
                image.file_format = 'PNG'
                image.save()
                if has_em_map:
                    emission_image.filepath_raw = str(joined_path_e)
                    emission_image.file_format = 'PNG'
                    emission_image.save()
            else:
                self.report({'INFO'}, "Missing temp folder, check add-on preferences!")

            # create material

            mat = bpy.data.materials.new(name=self.name)
            mat.use_nodes = True

            double_sided = (self.flags & 0x01) != 0
            alpha_blend  = (self.flags & 0x02) != 0
            if self.alpha or not double_sided:
                mat.use_backface_culling = True
            else:
                mat.use_backface_culling = False

            if alpha_blend:
                mat.blend_method = 'BLEND'

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
                if self.emission and has_em_map:
                    emTexImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
                    emTexImage.image = emission_image
                    multiply = mat.node_tree.nodes.new('ShaderNodeMixRGB')
                    multiply.blend_type = 'MULTIPLY'
                    multiply.inputs[0].default_value = 1.0
                    multiply.inputs[2].default_value = (4.95385, 4.95385, 4.95385, 1.0)
                    mat.node_tree.links.new(bsdf.inputs['Emission'], multiply.outputs[0])
                    mat.node_tree.links.new(multiply.inputs[1], emTexImage.outputs['Color'])
                if NumOfTextures > 1:
                    mapping = mat.node_tree.nodes.new('ShaderNodeMapping')
                    mapping.vector_type = 'TEXTURE'
                    coord = mat.node_tree.nodes.new('ShaderNodeTexCoord')
                    combine = mat.node_tree.nodes.new('ShaderNodeCombineXYZ')
                    divide = mat.node_tree.nodes.new('ShaderNodeMath')
                    divide.operation = 'DIVIDE'
                    value_frame = mat.node_tree.nodes.new('ShaderNodeValue')
                    value_frame.label = 'frame'
                    frame_driver = value_frame.outputs[0].driver_add("default_value")
                    frame_driver.driver.expression = "frame"
                    value_divisor = mat.node_tree.nodes.new('ShaderNodeValue')
                    value_divisor.label = 'NumOfTextures'
                    value_divisor.outputs[0].default_value = NumOfTextures

                    mat.node_tree.links.new(texImage.inputs[0], mapping.outputs[0])
                    mat.node_tree.links.new(mapping.inputs[1], combine.outputs[0])
                    mat.node_tree.links.new(mapping.inputs[0], coord.outputs[2])
                    mat.node_tree.links.new(combine.inputs[1], divide.outputs[0])
                    mat.node_tree.links.new(divide.inputs[0], value_frame.outputs[0])
                    mat.node_tree.links.new(divide.inputs[1], value_divisor.outputs[0])
                    if self.emission and has_em_map:
                        mat.node_tree.links.new(emTexImage.inputs[0], mapping.outputs[0])

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

                if self.emission and has_em_map:
                    emTexImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
                    emTexImage.image = emission_image
                    addition = mat.node_tree.nodes.new('ShaderNodeMixRGB')
                    addition.blend_type = 'ADD'
                    addition.inputs[0].default_value = 1.0

                    mat.node_tree.links.new(output.inputs['Surface'], addition.outputs['Color'])
                    mat.node_tree.links.new(addition.inputs['Color1'], mixColor.outputs['Color'])
                    mat.node_tree.links.new(addition.inputs['Color2'], emTexImage.outputs['Color'])

                # flip book animation nodes
                if NumOfTextures > 1:
                    mapping = mat.node_tree.nodes.new('ShaderNodeMapping')
                    mapping.vector_type = 'TEXTURE'
                    coord = mat.node_tree.nodes.new('ShaderNodeTexCoord')
                    combine = mat.node_tree.nodes.new('ShaderNodeCombineXYZ')
                    divide = mat.node_tree.nodes.new('ShaderNodeMath')
                    divide.operation = 'DIVIDE'
                    value_frame = mat.node_tree.nodes.new('ShaderNodeValue')
                    value_frame.label = 'frame'
                    frame_driver = value_frame.outputs[0].driver_add("default_value")
                    frame_driver.driver.expression = "frame"
                    value_divisor = mat.node_tree.nodes.new('ShaderNodeValue')
                    value_divisor.label = 'NumOfTextures'
                    value_divisor.outputs[0].default_value = NumOfTextures

                    mat.node_tree.links.new(texImage.inputs[0], mapping.outputs[0])
                    mat.node_tree.links.new(mapping.inputs[1], combine.outputs[0])
                    mat.node_tree.links.new(mapping.inputs[0], coord.outputs[2])
                    mat.node_tree.links.new(combine.inputs[1], divide.outputs[0])
                    mat.node_tree.links.new(divide.inputs[0], value_frame.outputs[0])
                    mat.node_tree.links.new(divide.inputs[1], value_divisor.outputs[0])
                    if self.emission and has_em_map:
                        mat.node_tree.links.new(emTexImage.inputs[0], mapping.outputs[0])

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
            vertexColor = mat.node_tree.nodes.new('ShaderNodeAttribute')
            vertexColor.attribute_name = 'Intensities'
            vertexColor.location = -500, -50
            mixColor = mat.node_tree.nodes.new('ShaderNodeMixRGB')
            mixColor.blend_type = 'MULTIPLY'
            mixColor.inputs[0].default_value = 0.98
            mixColor.location = -250, 150
            mat.node_tree.links.new(output.inputs['Surface'], mixColor.outputs[0])
            mat.node_tree.links.new(mixColor.inputs['Color1'], colorNode.outputs[0])
            mat.node_tree.links.new(mixColor.inputs['Color2'], vertexColor.outputs['Color'])
