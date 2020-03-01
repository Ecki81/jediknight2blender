from struct import *
import bpy
import re
import pathlib

def import_mat(matfile, cmpfile):
    '''
    reads an image from a JK mat file and its corresponding cmp file and returns a material with diffuse map
    '''
    #filename="C:/Program Files (x86)/GOG Galaxy/Games/Star Wars Jedi Knight - Dark Forces 2/Resource/Res2/3do/mat/tiebpit.mat"
    #imagefile="D:/GalaxyClient/Games/Star Wars Jedi Knight - Dark Forces 2/Resource/Res2/mat/" + matfile
    # imagefile="D:/GalaxyClient/Games/Star Wars Jedi Knight - Dark Forces 2/Resource/Res2/3do/mat/" + matfile
    # palettefile="D:/GalaxyClient/Games/Star Wars Jedi Knight - Dark Forces 2/Resource/Res2/misc/cmp/" + cmpfile                       # @home dir
    # palettefile="C:/Program Files (x86)/GOG Galaxy/Games/Star Wars Jedi Knight - Dark Forces 2/Resource/Res2/misc/cmp/" + cmpfile       # @work dir
    palettefile=cmpfile       # @work dir


    imagefile = matfile

    f=open(palettefile,'rb') # open file for reading
    f.seek(0)
    cmp = f.read()

    fullpath = pathlib.Path(matfile)
    name = fullpath.parts[-1].replace(".mat", "")

    f=open(imagefile,'rb') # open file for reading
    f.seek(0)
    mat = f.read()

    # unpack uint32 from 4 bytes

    type = unpack("L", mat[8:12])[0]      #Type
    NumOfTextures = unpack("L", mat[12:16])[0]     #NumOfTextures
    #unpack("L", mat[16:20])[0]     #NumOfTextures1
    #unpack("L", mat[20:24])[0]     #Longint
    #unpack("L", mat[24:28])[0]     #LongInt

    textype = unpack("L", mat[76:80])[0]     #textype   (0=color, 8=texture)
    colornum = unpack("L", mat[80:84])[0]     #colornum   (Color index from the CMP palette, only color MATs)

    #unpack("L", mat[108:112])[0]   #Longint (0xBFF78482)
    CurrentTXNum = unpack("L", mat[112:116])[0]   #CurrentTXNum

    sizeX = unpack("L", mat[116:120])[0]   #SizeX
    sizeY = unpack("L", mat[120:124])[0]   #SizeY

    #unpack("L", mat[136:140])[0]  #NumMipMaps



    ###



    size = sizeX, sizeY


    # blank image
    image = bpy.data.images.new(name, width=size[0], height=size[1])

    ## For white image
    # pixels = [1.0] * (4 * size[0] * size[1])

    # is type texture? (2)
    
    if textype == 8:
        
        pixels = [None] * size[0] * size[1]
        for x in range(size[0]):
            for y in range(size[1]):
                # assign RGBA to something useful
    # 140: start of image array    |  end of array |-|end of each line| -x:iterate through each pixel (two minuses go in right pixel direction)     
                cmp_index = mat[140+(size[0]*size[1])-((y+1)*size[0]-x)]
                r = cmp[64+(cmp_index*3)]/255
                g = cmp[65+(cmp_index*3)]/255
                b = cmp[66+(cmp_index*3)]/255
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
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs[5].default_value = 0.0      # Specular
        bsdf.inputs[7].default_value = 1.0      # Roughness
        texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
        
        # assign texture
        
        texImage.image = image
        texImage.location = -400,250
        mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
        
    else:
        
        # create color MAT
        

        
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs[5].default_value = 0.0      # Specular
        bsdf.inputs[7].default_value = 1.0      # Roughness
        colorNode = mat.node_tree.nodes.new('ShaderNodeRGB')
        r = cmp[64+(colornum*3)]/255
        g = cmp[65+(colornum*3)]/255
        b = cmp[66+(colornum*3)]/255
        colorNode.outputs[0].default_value = (r,g,b,1)
        colorNode.location = -400,250
        mat.node_tree.links.new(bsdf.inputs['Base Color'], colorNode.outputs['Color'])
    


class Mat:
     def importMat(matfile, cmpfile):
         import_mat(matfile, cmpfile)