from struct import unpack
from . import jk_flags
import bpy

class Mat:
    def __init__(self, mat, pal, alpha, name, shader, flag):
        '''
        initializes a material, takes material file name and palette file name (currently unused)
        '''
        self.mat = mat
        self.name = name
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
        reads an image from a JK mat file and its corresponding pal file and returns a material with diffuse map
        '''
        self.name = self.name.replace(".mat", "")

        # unpack uint32 from 4 bytes


        Type = unpack("L", self.mat[8:12])[0]     # 0 = colors(TColorHeader) , 1= ?, 2= texture(TTextureHeader)
        NumOfTextures = unpack("L", self.mat[12:16])[0]     # number of textures or colors
        NumOfTextures1 = unpack("L", self.mat[16:20])[0]     # In color MATs, it's 0, in TX ones, it's equal to numOfTextures 

        textype = unpack("L", self.mat[76:80])[0]     #textype   (0=color, 8=texture)
        colornum = unpack("L", self.mat[80:84])[0]     #colornum   (Color index from the CMP palette, only color MATs)

        if Type == 2:



            CurrentTXNum = unpack("L", self.mat[112:116])[0]   #CurrentTXNum

            size_offset = 0
            pixel_offset = 0
            
            if NumOfTextures > 1:
                size_offset = 10*4*(NumOfTextures-1)

            size = unpack("LL", self.mat[116+size_offset:124+size_offset])

            if NumOfTextures > 1:
                pixel_offset = size_offset# -size[0]

            
            numMipMaps = unpack("L", self.mat[136:140])[0]  #NumMipMaps




            image = bpy.data.images.new(self.name, width=size[0], height=size[1])
            
            pixels = [None] * size[0] * size[1]
            for x in range(size[0]):
                for y in range(size[1]):
            	          # 140: start of image array|  end of array |-|end of each line| -x:iterate through each pixel (two minuses go in right pixel direction)     
                    img_value = self.mat[140+pixel_offset+(size[0]*size[1])-((y+1)*size[0]-x)]               
                    r = self.pal[64+(img_value*3)]/256
                    g = self.pal[65+(img_value*3)]/256
                    b = self.pal[66+(img_value*3)]/256
                    if self.alpha:
                        table = 256*1                      # table size 256 * place of 1st transp table (0:color table, 1-63:light level tables, 64-319:transp tables)
                        a = self.pal[832+table+img_value]/64           # 
                    else:
                        a = 1.0
                    pixels[(y * size[0]) + x] = [r, g, b, a]


            # flatten list
            pixels = [chan for px in pixels for chan in px]

            # assign pixels
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

                # # sith engine sky emulation
                # # create nodes
                # mapping = mat.node_tree.nodes.new('ShaderNodeMapping')
                # mapping.vector_type = 'TEXTURE'
                # tex_coord = mat.node_tree.nodes.new('ShaderNodeTexCoord')
                # com_xyz = mat.node_tree.nodes.new('ShaderNodeCombineXYZ')
                # arctan2a = mat.node_tree.nodes.new('ShaderNodeMath')
                # arctan2a.operation = 'ARCTAN2'
                # divide = mat.node_tree.nodes.new('ShaderNodeMath')
                # divide.operation = 'DIVIDE'
                # divide.inputs[0].default_value[1] = -2.0
                # arctan2b = mat.node_tree.nodes.new('ShaderNodeMath')
                # arctan2b.operation = 'ARCTAN2'
                # sep_xyza = mat.node_tree.nodes.new('ShaderNodeSeparateXYZ')
                # sep_xyzb = mat.node_tree.nodes.new('ShaderNodeSeparateXYZ')
                # vec_transa = mat.node_tree.nodes.new('ShaderNodeVectorTransform')
                # vec_transa.convert_from = 'CAMERA'
                # vec_transa.convert_to = 'WORLD'
                # vec_transa.inputs[0].default_value[0] = 1.0
                # vec_transa.inputs[0].default_value[1] = 0.0
                # vec_transa.inputs[0].default_value[2] = 0.0
                # vec_transb = mat.node_tree.nodes.new('ShaderNodeVectorTransform')
                # vec_transb.convert_from = 'WORLD'
                # vec_transb.convert_to = 'CAMERA'
                # vec_transb.inputs[0].default_value[0] = 0.0
                # vec_transb.inputs[0].default_value[1] = 1.0
                # vec_transb.inputs[0].default_value[2] = 0.0
                # # connect sky nodes
                # mat.node_tree.links.new(texImage.inputs[0], mapping.outputs[0])
                # mat.node_tree.links.new(mapping.inputs[0], tex_coord.outputs[5])
                # mat.node_tree.links.new(mapping.inputs[1], com_xyz.outputs[0])
                # mat.node_tree.links.new(com_xyz.inputs[0], divide.outputs[0])
                # mat.node_tree.links.new(divide.inputs[0], arctan2a.outputs[0])
                # mat.node_tree.links.new(arctan2a.inputs[0], sep_xyza.outputs[0])
                # mat.node_tree.links.new(arctan2a.inputs[1], sep_xyza.outputs[1])
                # mat.node_tree.links.new(sep_xyza.inputs[0], vec_transa.outputs[0])
                # mat.node_tree.links.new(com_xyz.inputs[1], arctan2b.outputs[0])
                # mat.node_tree.links.new(arctan2b.inputs[0], sep_xyzb.outputs[1])
                # mat.node_tree.links.new(arctan2b.inputs[1], sep_xyzb.outputs[2])
                # mat.node_tree.links.new(sep_xyzb.inputs[0], vec_transb.outputs[0])


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
