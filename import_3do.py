import re
import bpy
from math import *
from os.path import basename, dirname
from .import_gob import Gob
from .import_mat import Mat

class Thing:

    def __init__(self, file, x, y, z, pitch, yaw, roll, scale, name, motsflag, import_textures):
        '''
        Initializes a Thing with name (filename.3do), xyz position and rotation offset
        '''
        self.file = file
        self.xOffs = x * scale
        self.yOffs = y * scale
        self.zOffs = z * scale
        self.pitchOffs = pitch
        self.yawOffs = yaw
        self.rollOffs = roll
        self.name = name
        self.scale = scale
        self.motsflag = motsflag
        self.import_textures = import_textures


    def tree(self, hierarchy):
        '''reads in hierarchy, returns absolute x, y, z transforms'''

        new_hierarchy = []

        def has_parent(node, transf):
            parent = int(hierarchy[node][4])
            node_name = hierarchy[parent][-1]
            if parent != -1:                                                # If it is a child
                transf[0] = transf[0] + float(hierarchy[node][8])           # loc
                transf[1] = transf[1] + float(hierarchy[node][9])
                transf[2] = transf[2] + float(hierarchy[node][10])
                has_parent(parent, transf)
            else:                                                           # If it is the root
                transf[0] = transf[0] + float(hierarchy[node][8])           # loc
                transf[1] = transf[1] + float(hierarchy[node][9])
                transf[2] = transf[2] + float(hierarchy[node][10])
            return transf

        for i, line in enumerate(hierarchy):
            new_hierarchy_line = []
            node_text = line[-1]
            default_transforms = [0.0, 0.0, 0.0]
            new_transforms = has_parent(i, default_transforms)
            for j, element in enumerate(line):
                if j == 8:
                    element = new_transforms[0]
                elif j == 9:
                    element = new_transforms[1]
                elif j == 10:
                    element = new_transforms[2]
                else:
                    element = line[j]
                new_hierarchy_line.append(element)
            new_hierarchy.append(new_hierarchy_line)


        return new_hierarchy


    def import_Thing(self):
        '''read in and build 3do mesh'''
        ungobed_string = self.file.decode("ISO-8859-1")
        lines = re.split('\n', ungobed_string)
        del ungobed_string


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

            if self.motsflag:
                matLine = re.split("\s+", lines[i+matPos],)
                matLine[1] = matLine[1].replace(".MAT", "")          # :P
                matList.append(matLine[1].replace(".mat", ""))
            else:
                matLine = re.split("\s+", lines[i+matPos+1],)
                matLine[2] = matLine[2].replace(".MAT", "")
                matList.append(matLine[2].replace(".mat", ""))

            i+=1

        if self.import_textures:
            this_addon = basename(dirname(__file__))
            prefs = bpy.context.preferences.addons[this_addon].preferences
            gob = Gob(prefs.jkdf_path + "\Res2.gob")
            ungobed_palette = gob.ungob("01narsh.cmp")
            for texture in matList:
                if bpy.data.materials.get(texture):
                    continue
                else:
                    ungobed_file = gob.ungob(texture.lower()+".mat")
                    mat = Mat(ungobed_file, ungobed_palette, False, texture.lower(), "BSDF", True, None)
                    mat.import_Mat()



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
        hierarchy_nodes = 0
        i=0
        while i < len(lines):
            i+=1
            if re.search("HIERARCHY NODES ",lines[i])!=None:
                hierarchy_string = re.split("\s", lines[i])
                hierarchy_nodes = int(hierarchy_string[2])
                hiPos = i+2
                break   


        vc_pos = 0
        scPos = 0
        uvPos = 0

        # put hierarchy in 2d-array #########################################

        hier_array = []  # 2D array with vertices x, y, z


        i=0
        while i < hierarchy_nodes:
            if self.motsflag:
                hier_line=re.split("\s+", lines[i+hiPos])
                del hier_line[-1]
            else:
                hier_line=re.split("\s+", lines[i+hiPos+1])
                del hier_line[0]
                del hier_line[-1]

            hier_array.append(hier_line)
            i+=1

        abs_hier_array = self.tree(hier_array)

    
        obj_list = []       # empty list for 3do objects



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

            for node in abs_hier_array:
                if int(node[3]) != midx:
                    pass
                else:
                    mesh_name = node[17]
                    x = float(node[8])* self.scale
                    y = float(node[9])* self.scale
                    z = float(node[10]) * self.scale
                    pitch = float(node[11])
                    yaw = float(node[12])
                    roll = float(node[13])
                    pivot_x = float(node[14]) * self.scale
                    pivot_y = float(node[15]) * self.scale
                    pivot_z = float(node[16]) * self.scale
            

            # read in vertices ###############################################

            vert_array = []  # 2D array with vertices x, y, z


            i=0
            while i < int(vertex_count):
                vert_line=""
                
                if self.motsflag:
                    vert_line=re.split("\s+", lines[i+vc_pos+1])
                    del vert_line[0]
                    del vert_line[3]
                    del vert_line[3]

                else:
                    vert_line=re.split("\s+", lines[i+vc_pos+2])
                    del vert_line[0]
                    del vert_line[0]
                    del vert_line[3]
                    del vert_line[3]

                vert_line[0]=float(vert_line[0]) * self.scale
                vert_line[1]=float(vert_line[1]) * self.scale
                vert_line[2]=float(vert_line[2]) * self.scale
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
                if self.motsflag:
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

                if self.motsflag:
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
            me = bpy.data.meshes.new(mesh_name+'Mesh')
            ob = bpy.data.objects.new(mesh_name, me)
            ob.show_name = False

            obj_list.append(ob)

            # add vertex color layer
            vcol = me.vertex_colors.new(name='Intensities')

            # Add materials to meshes
            for material in matList:
                try:
                    ob.data.materials.append(bpy.data.materials[material.lower()])
                except:
                    pass

            # offset has to be applied to root object
            ob.location = (x + self.xOffs, y + self.yOffs, z + self.zOffs)


            # ob.rotation_euler.rotate_axis("Z", radians(yaw + self.yawOffs))              # Correct order of local rotation axes (yaw, pitch, roll)
            # ob.rotation_euler.rotate_axis("X", radians(pitch + self.pitchOffs))
            # ob.rotation_euler.rotate_axis("Y", radians(roll + self.rollOffs))

            
            # Link object to scene
            scene = bpy.context.scene
            scene.collection.objects.link(ob)
            me.from_pydata(vert_array, [], surf_array)


            # add uv map
            me.uv_layers.new(name="UVMap")
            uvMap = me.uv_layers["UVMap"]


            # TODO Test, if texture exists!!!
            # assign every needed material to faces
            for isrf, surface in enumerate(surf_array):
                polygon = me.polygons[isrf]
                polygon.material_index = surf_material[isrf]
                currenttexture = matList[surf_material[isrf]].lower()
                try:
                    textureSize = bpy.data.images[currenttexture].size
                except:
                    textureSize = (64,64)
                # add uv data
                for jsrf, loop in enumerate(uv_indices[isrf]):
                    u = float(uvArray[uv_indices[isrf][jsrf]][0])
                    v = float(uvArray[uv_indices[isrf][jsrf]][1])
                    uvMap.data[polygon.loop_indices[jsrf]].uv = (u / textureSize[0], v /-textureSize[1])


            # Update mesh with new data
            me.update()

            midx+=1


        # add $$$dummy objects to object array
        # _________________________________________________________________________________________

        dummy_index = 0
        
        mesh_numbers = []

        for mesh in hier_array:
            mesh_no = int(mesh[3])
            if mesh_no != -1:
                mesh_numbers.append(mesh_no)
            else:
                pass

        sorting_list = []
        for i, obj in enumerate(obj_list):
            sorting_list.append(i)

        sorting_list.sort(key=dict(zip(sorting_list, mesh_numbers)).get)
        obj_list.sort(key=dict(zip(obj_list, sorting_list)).get)


        for i, mesh in enumerate(hier_array):
            mesh_name = mesh[-1].lower()
            if mesh_name == "$$$dummy":
                dummy_index += 1
                empty = bpy.data.objects.new( "empty", None )
                bpy.context.scene.collection.objects.link(empty)
                empty.empty_display_size = 1
                empty.empty_display_type = 'PLAIN_AXES'
                empty.location = (float(mesh[8]) + self.xOffs, float(mesh[9]) + self.yOffs, float(mesh[10]) + self.zOffs)
                obj_list.insert(i, empty)
            else:
                pass


        bpy.context.view_layer.update()                     # update all object matrices

        for i, mesh in enumerate(hier_array):
            parent_index = int(mesh[4])
            if parent_index != -1:
                child = obj_list[i]
                matrixcopy = child.matrix_world.copy()
                parent = obj_list[int(parent_index)]
                child.parent = parent
                child.matrix_world = matrixcopy
                
                #                  (yaw(z) pitch(x) roll(y))
                child.rotation_euler.rotate_axis("Z", radians(float(mesh[12])))
                child.rotation_euler.rotate_axis("X", radians(float(mesh[11])))
                child.rotation_euler.rotate_axis("Y", radians(float(mesh[13])))
                # print(child)
            else:
                pass        

        obj_list[0].rotation_euler.rotate_axis("Z", radians(self.yawOffs))              # Correct order of local rotation axes (yaw, pitch, roll)
        obj_list[0].rotation_euler.rotate_axis("X", radians(self.pitchOffs))
        obj_list[0].rotation_euler.rotate_axis("Y", radians(self.rollOffs))             

        return obj_list[0]
        

    def copy_Thing(self, obj):
        '''takes Thing mesh, returns copied Thing'''

        def copy_recursive(ob, par):
            ob_copy = ob.copy()
            ob_copy.parent = par
            ob_copy.matrix_parent_inverse = ob.matrix_parent_inverse.copy()
            bpy.context.scene.collection.objects.link(ob_copy)
            for child in ob.children:
                copy_recursive(child, ob_copy)

        obj_copy = bpy.data.objects.new(obj.name, obj.data)
        bpy.context.scene.collection.objects.link(obj_copy)
        for child in obj.children:
            copy_recursive(child, obj_copy)

        obj_copy.location = (self.xOffs, self.yOffs, self.zOffs)
        obj_copy.rotation_euler.rotate_axis("Z", radians(self.yawOffs))              # Correct order of local rotation axes (yaw, pitch, roll)
        obj_copy.rotation_euler.rotate_axis("X", radians(self.pitchOffs))
        obj_copy.rotation_euler.rotate_axis("Y", radians(self.rollOffs))
        return obj_copy

    def __str__(self):
        return self.name

