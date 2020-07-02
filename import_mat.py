from struct import *
import bpy

class Mat:
    def __init__(self, mat, pal):
        '''
        initializes a material, takes material file name and palette file name (currently unused)
        '''
        self.mat = mat
        self.pal = pal
        self.transp = False
        self.alpha = False
        self.anim = False

    def __str__(self):
        print(self.mat, self.pal)

    def importMat(mat, pal, alpha, name, shader):
        '''
        reads an image from a JK mat file and its corresponding pal file and returns a material with diffuse map
        '''
        name = name.replace(".mat", "")

        # unpack uint32 from 4 bytes

        NumOfTextures = unpack("L", mat[12:16])[0]     #NumOfTextures

        textype = unpack("L", mat[76:80])[0]     #textype   (0=color, 8=texture)
        colornum = unpack("L", mat[80:84])[0]     #colornum   (Color index from the CMP palette, only color MATs)

        CurrentTXNum = unpack("L", mat[112:116])[0]   #CurrentTXNum

        size_offset = 0
        pixel_offset = 0
        
        if NumOfTextures > 1:
            size_offset = 10*4*(NumOfTextures-1)

        size = unpack("LL", mat[116+size_offset:124+size_offset])

        if NumOfTextures > 1:
            pixel_offset = size_offset# -size[0]

        
        numMipMaps = unpack("L", mat[136:140])[0]  #NumMipMaps


        if textype == 8:

            image = bpy.data.images.new(name, width=size[0], height=size[1])
            
            pixels = [None] * size[0] * size[1]
            for x in range(size[0]):
                for y in range(size[1]):
            	          # 140: start of image array|  end of array |-|end of each line| -x:iterate through each pixel (two minuses go in right pixel direction)     
                    img_value = mat[140+pixel_offset+(size[0]*size[1])-((y+1)*size[0]-x)]               
                    r = pal[64+(img_value*3)]/255
                    g = pal[65+(img_value*3)]/255
                    b = pal[66+(img_value*3)]/255
                    if alpha:
                        table = 256*1                      # table size 256 * place of 1st transp table (0:color table, 1-63:light level tables, 64-319:transp tables)
                        a = pal[832+table+img_value]/64           # 
                    else:
                        a = 1.0
                    pixels[(y * size[0]) + x] = [r, g, b, a]


            # flatten list
            pixels = [chan for px in pixels for chan in px]

            # assign pixels
            image.pixels = pixels


            # write image
            # image.filepath_raw = "/tmp/" + name + ".png"
            # image.file_format = 'PNG'
            # image.save()

            # create material

            mat = bpy.data.materials.new(name=name)
            mat.use_nodes = True


            if alpha:
                mat.use_backface_culling = True
            else:
                mat.use_backface_culling = False

            bsdf = mat.node_tree.nodes["Principled BSDF"]

            if shader == "BSDF":
                bsdf.inputs[5].default_value = 0.0      # Specular
                bsdf.inputs[7].default_value = 1.0      # Roughness
                texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
                texImage.image = image
                mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
                if alpha:
                    mat.node_tree.links.new(bsdf.inputs['Alpha'], texImage.outputs['Alpha'])

            else:
                mat.node_tree.nodes.remove(bsdf)
                output = mat.node_tree.nodes["Material Output"]
                texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
                
                vertexColor = mat.node_tree.nodes.new('ShaderNodeAttribute')
                vertexColor.attribute_name = 'Intensities'
                vertexColor.location = -500, 400

                mixColor = mat.node_tree.nodes.new('ShaderNodeMixRGB')
                mixColor.blend_type = 'MULTIPLY'
                mixColor.inputs[0].default_value = 0.98
                mixColor.location = -250, 300

                # # assign texture
                
                texImage.image = image
                texImage.location = -600,250
                mat.node_tree.links.new(output.inputs['Surface'], mixColor.outputs['Color'])
                mat.node_tree.links.new(mixColor.inputs['Color1'], texImage.outputs['Color'])
                mat.node_tree.links.new(mixColor.inputs['Color2'], vertexColor.outputs['Color'])



            
        else:
            
            # create color MAT
            
            mat = bpy.data.materials.new(name=name)
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes["Principled BSDF"]
            mat.node_tree.nodes.remove(bsdf)
            output = mat.node_tree.nodes["Material Output"]
            # bsdf.inputs[5].default_value = 0.0      # Specular
            # bsdf.inputs[7].default_value = 1.0      # Roughness
            colorNode = mat.node_tree.nodes.new('ShaderNodeRGB')
            r = pal[64+(colornum*3)]/255
            g = pal[65+(colornum*3)]/255
            b = pal[66+(colornum*3)]/255
            colorNode.outputs[0].default_value = (r,g,b,1)
            colorNode.location = -400,250
            mat.node_tree.links.new(output.inputs['Surface'], colorNode.outputs['Color'])
