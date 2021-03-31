from struct import unpack
from . import jk_flags
import numpy as np
import bpy


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
        t_mat_header = unpack("ccccLLLLLLLLLLLLLLLLLLLLLLLL", self.mat[0:100])

        ver = t_mat_header[4]
        Type = t_mat_header[5]
        NumOfTextures = t_mat_header[6]
        NumOfTextures1 = t_mat_header[7]

        textype = t_mat_header[22]
        colornum = t_mat_header[23]

        if Type == 2:

            t_tex_header = unpack("LLLLLLLL", self.mat[100:132])

            CurrentTXNum = unpack("L", self.mat[112:116])[0]   #CurrentTXNum

            size_offset = 0
            pixel_offset = 0

            if NumOfTextures > 1:
                size_offset = 10*4*(NumOfTextures-1)

            size = unpack("LL", self.mat[116+size_offset:124+size_offset])

            if NumOfTextures > 1:
                pixel_offset = size_offset


            numMipMaps = unpack("L", self.mat[136:140])[0]  #NumMipMaps


            image = bpy.data.images.new(self.name, width=size[0], height=size[1])


            img = np.frombuffer(self.mat, dtype=np.uint8 ,count=size[1] * size[0], offset=140+pixel_offset).reshape((size[1], size[0]))
            img_matrix = np.flipud(img)
            col_pal = np.frombuffer(self.pal, dtype=np.uint8 ,count=256*3, offset=64).reshape((256,3)) / 255
            trans_pal = np.frombuffer(self.pal, dtype=np.uint8 ,count=256, offset=64 + (256*3)).reshape((256,1)) / 63
            if self.alpha:
                pal_add_channel = np.hstack((col_pal, trans_pal))
            else:
                pal_add_channel = np.hstack((col_pal, np.ones((256,1))))
            col_image = pal_add_channel[img_matrix]
            pixels = col_image.flatten()

            
            image.pixels = pixels


            # write image

            image.filepath_raw = "/tmp/" + self.name + ".png"
            image.file_format = 'PNG'
            image.save()

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

                # # assign texture
                
                texImage.image = image
                texImage.location = -600,250
                mat.node_tree.links.new(output.inputs['Surface'], mixColor.outputs['Color'])
                mat.node_tree.links.new(mixColor.inputs['Color1'], texImage.outputs['Color'])
                mat.node_tree.links.new(mixColor.inputs['Color2'], vertexColor.outputs['Color'])



        
        else:
            
            # create color MAT
            
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
            colorNode.outputs[0].default_value = (r,g,b,1)
            colorNode.location = -400,250
            mat.node_tree.links.new(output.inputs['Surface'], colorNode.outputs['Color'])
