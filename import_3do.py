import re
import bpy, bmesh
from math import *
import pathlib

class Thing:

    def __init__(self, file, x, y, z, pitch, yaw, roll):
        '''
        Initializes a Thing with name (filename.3do), xyz position and rotation offset
        '''
        self.file = file
        self.xOffs = x
        self.yOffs = y
        self.zOffs = z
        self.pitchOffs = pitch
        self.yawOffs = yaw
        self.rollOffs = roll
        self.name = ""

    def import_Thing(self):
        # import_3do(self.name, self.x, self.y, self.z, self.pitch, self.yaw, self.roll)
        f=open(self.file,'r') # open file for reading
        lines=f.readlines()  # store the entire file in a variable
        f.close()

        #filepath = re.split("/", filename)
        #name = filepath[-1].replace(".3do", "")

        motsflag = True
        path = pathlib.Path(self.file)
        if path.parts[-3] == "JKMRES":
            motsflag = True
            # print("motsflag true")
        else:
            motsflag = False
            # print("motsflag false")

        # get the number of materials #######################################

        matPos = 0
        matCount = 0
        i = 0
        while i < len(lines):
                i += 1
                if re.search("^MATERIALS ", lines[i]) != None:
                    materialsString = re.split("\s", lines[i])
                    materialCount = int(materialsString[1])
                    matPos = i+1
                    break

        # get a material name list, for easy mesh appliance later

        i=0
        matLine = ""
        matList = []
        while i < materialCount:

            if motsflag:
                matLine = re.split("\s+", lines[i+matPos],)
                matLine[1] = matLine[1].replace(".MAT", "")          # :P
                matList.append(matLine[1].replace(".mat", ""))
            else:
                matLine = re.split("\s+", lines[i+matPos+1],)
                matLine[2] = matLine[2].replace(".MAT", "")
                matList.append(matLine[2].replace(".mat", ""))

            i+=1



        # get the number of meshes ##########################################

        meshCount = 0
        i=0
        while i < len(lines):
            i+=1
            if re.search("MESHES ",lines[i])!=None:
                meshesString = re.split("\s", lines[i])
                meshCount = int(meshesString[1])
                break

        # TODO: read in mesh positions in text file #####################

        meshPos=[]
        for idx, line in enumerate(lines):
            if re.search("^MESH ",line)!=None and len(meshPos)<meshCount:
                meshPos.append(idx)
        # print(meshPos)


        # get to the hierarchy ##########################################

        hiPos = 0
        hierarchyNodes = 0
        i=0
        while i < len(lines):
            i+=1
            if re.search("HIERARCHY NODES ",lines[i])!=None:
                hierarchyString = re.split("\s", lines[i])
                hierarchyNodes = int(hierarchyString[2])
                hiPos = i+2
                break   


        vc_pos = 0
        scPos = 0
        uvPos = 0

        # print(str(hierarchyNodes))

        # go through every mesh #############################################


        midx = 0
        while midx < meshCount:
            # print("mesh ", midx)
            
            # get the vertex count ##########################################

            vertex_count = 0
            i=meshPos[midx]
            while i < len(lines):
                i+=1
                if re.search("^VERTICES ",lines[i])!=None:
                    vcString = re.split("\s+", lines[i])
                    vertex_count = int(vcString[-2])
                    vc_pos = i+1
                    break
            #print("vc_pos: " + str(vc_pos) + ", vertex count: " + str(vertex_count))

            # get the UV count ##############################################

            uvCount = 0
            i=meshPos[midx]
            while i < len(lines):
                i+=1
                if re.search("^TEXTURE VERTICES ",lines[i])!=None:
                    uvString = re.split("\s+", lines[i])
                    uvCount = int(uvString[-2])
                    uvPos = i+1
                    break

            # get the surface count #########################################

            #scPos = 0
            surfaceCount = 0
            i=meshPos[midx]
            while i < len(lines):
                i+=1
                if re.search("FACES ",lines[i],re.I)!=None:
                    scString = re.split("\s+", lines[i])
                    surfaceCount = int(scString[-2])
                    scPos = i+1
                    break



            # read in mesh names ###################################################
            
            # read in hierarchy definition #########################################
            
            x = 0.0
            y = 0.0
            z = 0.0
            
            pitch = 0.0
            yaw = 0.0
            roll = 0.0
            
            pivot_x = 0.0
            pivot_y = 0.0
            pivot_z = 0.0

            
            i=0
            while i < int(hierarchyNodes):
                hier_line=""
                if motsflag:
                    hier_line=re.split("\s+", lines[i+hiPos])
                else:
                    hier_line=re.split("\s+", lines[i+hiPos+1])
                #hier_line=re.split("\s+", lines[i+hiPos+1])
                hier_line=list(filter(None, hier_line))
                if int(hier_line[3]) != midx:
                    #print("Name not found: " + hier_line[3] + " != " + str(midx))
                    i+=1
                else:
                    #print("Name found: " + hier_line[17])
                    self.name = hier_line[17]
                    x = float(hier_line[8])
                    y = float(hier_line[9])
                    z = float(hier_line[10])
                    pitch = float(hier_line[11])
                    yaw = float(hier_line[12])
                    roll = float(hier_line[13])
                    pivot_x = float(hier_line[14])
                    pivot_y = float(hier_line[15])
                    pivot_z = float(hier_line[16])
                    i+=1
                #verts=int(hier_line[8])                          # count of vertexes needed for surfaces (nverts)
                #geomode=int(hier_line[4]) 
                #print(hier_line)
                #i+=1


            # read in vertices ###############################################

            vert_array = []  # 2D array with vertices x, y, z


            i=0
            while i < int(vertex_count):
                vert_line=""
                if motsflag:
                    vert_line=re.split("\s+", lines[i+vc_pos+1])
                    del vert_line[0]
                    del vert_line[3]
                    del vert_line[3]
                    #print(vert_line)
                else:
                    vert_line=re.split("\s+", lines[i+vc_pos+2])
                    del vert_line[0]
                    del vert_line[0]
                    del vert_line[3]
                    del vert_line[3]
                    #print(vert_line)
                # del vert_line[0]
                # del vert_line[0]
                # del vert_line[3]
                # del vert_line[3]
                vert_line[0]=float(vert_line[0])
                vert_line[1]=float(vert_line[1])
                vert_line[2]=float(vert_line[2])
                vert_array.append(vert_line)
                i+=1

            #print(vert_array)

            j = 0
            while j < int(vertex_count):
                vert_array[j][0] += pivot_x
                vert_array[j][1] += pivot_y
                vert_array[j][2] += pivot_z
                j+=1


            # read in UVs #####################################################

            uvArray = []  # 2D array with vertices x, y, z


            i=0
            while i < int(uvCount):
                uvLine=""
                if motsflag:
                    uvLine=re.split("\s+", lines[i+uvPos])
                    del uvLine[0]
                    del uvLine[-1]
                else:
                    uvLine=re.split("\s+", lines[i+uvPos+1])
                    del uvLine[-1]
                    del uvLine[0]
                    del uvLine[0]

                uvArray.append(uvLine)
                i+=1


            # read in surfaces ################################################

            surf_array = []
            surf_vertices = []
            surf_material = []
            uv_index_list = []
            uv_indices = []

            i=0
            while i < int(surfaceCount):
                surfLine=""
                verts=0

                if motsflag:
                    surfLine=re.split("\s+|,", lines[i+scPos+1])
                    verts=int(surfLine[7])
                else:
                    surfLine=re.split("\s+|,", lines[i+scPos+2])
                    verts=int(surfLine[8])


                surfLine=list(filter(None, surfLine))           # delete every empty element in list
            
                j=0

                while j < verts*2:

                    vIdx = surfLine[j+8]
                    uvIdx = surfLine[j+9]
                    surf_vertices.append(int(vIdx))
                    uv_index_list.append(int(uvIdx))
                    j+=2


                surf_array.append(surf_vertices)
                surf_material.append(int(surfLine[1]))
                uv_indices.append(uv_index_list)
                surf_vertices = []
                uv_index_list = []

                i+=1

            # create the mesh ##################################################

            # Create mesh and object
            me = bpy.data.meshes.new(self.name+'Mesh')
            ob = bpy.data.objects.new(self.name, me)
            ob.show_name = False

            # Add materials to meshes
            for material in matList:
                try:
                    ob.data.materials.append(bpy.data.materials[material.lower()])
                except:
                    pass

            # TODO parenting
            # offset has to be applied to root object
            ob.location = (x + self.xOffs, y + self.yOffs, z + self.zOffs)     # wrong! translation has to be relative to parent object. this only works in hierarchy with depth of 1

            ob.rotation_euler.rotate_axis("X", radians(pitch + self.pitchOffs))              # Correct order of local rotation axes (pitch, yaw, roll)
            ob.rotation_euler.rotate_axis("Z", radians(yaw + self.yawOffs))
            ob.rotation_euler.rotate_axis("Y", radians(roll + self.rollOffs))

            # rotate localy (matrix transform)
            
            # Link object to scene
            scene = bpy.context.scene
            scene.collection.objects.link(ob)
            me.from_pydata(vert_array, [], surf_array)


            # add uv map
            me.uv_layers.new(name="UVMap")
            uvMap = me.uv_layers["UVMap"]

            # assign every needed material to faces
            for isrf, surface in enumerate(surf_array):
                polygon = me.polygons[isrf]
                polygon.material_index = surf_material[isrf]
                currenttexture = matList[surf_material[isrf]].lower()
                textureSize = bpy.data.images[currenttexture].size
                # add uv data
                for jsrf, loop in enumerate(uv_indices[isrf]):
                    uvMap.data[polygon.loop_indices[jsrf]].uv = (float(uvArray[uv_indices[isrf][jsrf]][0])/textureSize[0], float(uvArray[uv_indices[isrf][jsrf]][1])/-textureSize[1])


            # Update mesh with new data
            me.update()

            midx+=1

    def copy_Thing(self):
        path = pathlib.Path(self.file)
        obj_string = path.parts[-1]
        print("object", obj_string, "with name", self.name, "is already existing.")

    def name(self):
        return self.name


    #   return {'FINISHED'}

    
#import_3do("at.3do")