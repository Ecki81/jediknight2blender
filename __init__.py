# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "Import JK/MotS Levels",
    "author" : "Eckhard Seidel",
    "description" : "Load level files from Star Wars Jedi Knight / Mysteries of the Sith (.jkl)",
    "blender" : (2, 81, 0),
    "version" : (0, 4, 0),
    "location" : "File > Import > JK/MotS Level (.jkl)",
    "warning" : "",
    "category" : "Import-Export"
}


# version steps:__________________________state__________________
# read in jkl                             DONE
# read in 3do                             basic
# read in mat                             works most of the time (pixel matrix sometimes shifted,
#                                         TODO: transp, anim, save to resource folder for quick loading)
# place 3do in levels                     DONE (TODO: implement some caching technique to speed up loading)
# texturing levels                        DONE (not sure about tiling / tile factor)
# texturing things                        DONE
# resolve 3do hierarchy and parenting     TODO
# parse GOB/GOO                           TODO
# better programming                      TODO, obviously! (better OOP structure ;) )


import re
import bpy, bmesh, mathutils
import sys
from struct import *
from .import_3do import Thing
from .import_mat import Mat
import pathlib

# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


def read_jkl_data(context, filename, importThings, importMats, importIntensities):
    print("reading jkl data file...")
    f = open(filename, 'r')
    lines=f.readlines()  # store the entire file in a variable 
    f.close()
    
    levelpath = re.split("\\\\", filename)
    name = levelpath[-1].replace(".jkl", "")

    path = pathlib.Path(filename)

    meshpath = pathlib.Path('')
    matpath = pathlib.Path('')
    thingmatpath = pathlib.Path('')
    cmppath = pathlib.Path('')

    parent = 0

    motsflag = True
    for folder in path.parts[::-1]:
 
        if folder == "Star Wars Jedi Knight - Dark Forces 2":
            meshpath = path.parents[parent-1].joinpath('Resource', 'Res2', '3do')
            matpath = path.parents[parent-1].joinpath('Resource', 'Res2', 'mat')
            thingmatpath = path.parents[parent-1].joinpath('Resource', 'Res2', '3do', 'mat')
            cmppath = path.parents[parent-1].joinpath('Resource', 'Res2', 'misc', 'cmp')
            motsflag = False
            break
        if folder == "Star Wars Jedi Knight - Mysteries of the Sith":
            meshpath = path.parents[parent-1].joinpath('Resource', 'JKMRES', '3do')
            matpath = path.parents[parent-1].joinpath('Resource', 'JKMRES', 'mat')
            thingmatpath = path.parents[parent-1].joinpath('Resource', 'JKMRES', '3do', 'mat')
            cmppath = path.parents[parent-1].joinpath('Resource', 'JKMRES', 'misc', 'cmp')
            motsflag = True
            break
        parent += 1


    # would normally load the data here
    # get the vertex count ##########################################

    vcPos = 0
    vertexCount = 0
    i=0
    while i < len(lines):
        i+=1
        if re.search("World vertices ",lines[i],re.I)!=None:
            vcString = re.split("\s", lines[i], 2)
            vertexCount = int(vcString[2])
            vcPos = i+1
            break


    # get the uv count ##############################################

    uv_pos = 0
    uvCount = 0
    for line_index, line in enumerate(lines):
        if re.search("World texture vertices ", line, re.I) != None:
            uvString = re.split("\s", line, 3)
            uvCount = int(uvString[-1])
            uv_pos = line_index+1
            break


    # get the surface count #########################################

    scPos = 0
    surfaceCount = 0
    i=0
    while i < len(lines):
        i+=1
        if re.search("World surfaces ",lines[i],re.I)!=None:
            scString = re.split("\s", lines[i], 2)
            surfaceCount = int(scString[2])
            scPos = i+1
            break
        
    # get the material count ##########################################

    mcPos = 0
    materialCount = 0
    i=0
    while i < len(lines):
        i+=1
        if re.search("World materials ",lines[i],re.I)!=None:
            mcString = re.split("\s", lines[i], 2)
            materialCount = int(mcString[2])
            mcPos = i+1
            break

    # get the colormaps ##############################################
 
    cmcPos = 0
    colormapCount = 0
    i=0
    while i <= len(lines):
        i+=1
        if re.search("World Colormaps",lines[i],re.I)!=None:
            cmcString = re.split("\s", lines[i], 2)
            colormapCount = int(cmcString[-1])
            cmcPos = i+1
            break
    colormap = re.split("\s+", lines[cmcPos],)
    colormap = colormap[1]

    # read in vertices ###############################################

    vertArray = []  # 2D array with vertices x, y, z


    i=0
    while i < int(vertexCount):
        i+=1
        vertLine=re.split("\s+", lines[i+vcPos], 4)
        del vertLine[0]
        del vertLine[3]
        vertLine[0]=float(vertLine[0])
        vertLine[1]=float(vertLine[1])
        vertLine[2]=float(vertLine[2])
        vertArray.append(vertLine)

    # read in uvs #####################################################

    uvArray = []
    i=0
    while i < int(uvCount):
        i += 1
        uv_line = re.split("\s+", lines[i+uv_pos])
        del uv_line[0]
        del uv_line[-1]
        uv_line[0] = float(uv_line[0])
        uv_line[1] = float(uv_line[1])
        uvArray.append(uv_line)


    # read in surfaces ################################################

    surf_list = []                                      # world VERTICES
    surf_vertices = []

    surf_intensities = []
    surf_intensities_list = []

    uv_indices = []
    uv_index_list = []
    material_indices = []

    i=0
    while i < int(surfaceCount):
        surfLine=re.split("\s+", lines[i+scPos+1],)
        matId = int(surfLine[1])
        surfflag = int(surfLine[2], base=16)
        faceflag = int(surfLine[3], base=16)
        geomode = int(surfLine[4])                        # 0 = don't draw, 4 = textured (else)
        light = int(surfLine[5])
        tex = int(surfLine[6])
        adjoin = int(surfLine[7])
        extralight = float(surfLine[8])
        nvert=int(surfLine[9])                          # count of vertexes needed for surfaces (nverts)
        sky = 0x200
        sky2 = 0x400
        skyflag=(surfflag & sky)
        sky2flag=(surfflag & sky2)
        #scrollflag=(surfflag & 0x800)
        # if adjoin + material, then probably transparent!

		
        j=0
        while j < nvert:
            v_index  = re.split(",",surfLine[j+10])
            surf_vertices.append(int(v_index[0]))                       
            uv_index_list.append(int(v_index[1]))
            surf_intensities.append(float(surfLine[10+nvert+j]))
            j+=1
        surf_list.append(surf_vertices)
        uv_indices.append(uv_index_list)
        surf_intensities_list.append(surf_intensities)
        material_indices.append(matId)
        surf_vertices = []
        uv_index_list = []
        surf_intensities = []
        i+=1

        # else:
        #     # material_indices.append(matId)            # material id for skipped faces (sky or portals). necessary?
        #     i+=1


    # read in materials ################################################
    # TODO find better ways to terminate at end of material list

    i=0
    matLine = ""
    mat_list = []
    mat_tiling_list = []
    while i < 1000:                                     # only allows for 1000 mat files
        i+=1
        if motsflag:
            matLine = re.split("\s+", lines[i+mcPos],)
        else:
            matLine = re.split("\s+", lines[i+mcPos+1],)
        mat_list.append(matLine[1])
        if matLine[0] != "end":
            mat_tiling_tuple = (float(matLine[2]), float(matLine[3]))
            mat_tiling_list.append(mat_tiling_tuple)
        else:
            break
        if matLine[0] == "end":
            break

    
    # get a material name list, for object appliance

    mat_name_list = []                                  # every material in jkl w/o file extension *.mat
    for material in mat_list:
        material_name = material.replace(".mat", "")
        mat_name_list.append(material_name)

    level_materials = []                                # list for select level geo material names
    material_list = sorted(set(material_indices))       # level mat indices, removed duplicates and sorted in ascending order
    for position in material_list:
        level_materials.append(mat_name_list[int(position)])


    # TODO: if material in material_list == -1, then material = __portal

    # read in sectors ##################################################
    
    # scPos = 0
    # surfaceCount = 0
    # i=0
    # while i < len(lines):
    #     i+=1
    #     if re.search("World surfaces ",lines[i],re.I)!=None:
    #         scString = re.split("\s", lines[i], 2)
    #         surfaceCount = int(scString[2])
    #         scPos = i+1
    #         break

    # sectorrg = re.compile(r"World sectors\s(\w+)")

    # for line in lines:
    #     m = sectorrg.search(line)
    #     if m:
    #         sectorCount = m.group(1)
    #         print("sector count: " + sectorCount)

    # read in array of sector centers

    # create portal material ################################################

    def placeholder_mat(placeholder_name):
        mat = bpy.data.materials.new(placeholder_name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        colorNode = mat.node_tree.nodes.new('ShaderNodeRGB')
        colorNode.outputs[0].default_value = (1.0,0.0,1.0,1)      # magenta
        colorNode.location = -400,250
        mat.node_tree.links.new(bsdf.inputs['Base Color'], colorNode.outputs['Color'])

    placeholder_mat('__portal')

    # call material loading class ###########################################
    
    if importMats:
        for material in mat_list:
            testmat = Mat(thingmatpath / material, cmppath / colormap)
            try:
                Mat.importMat(thingmatpath / material, cmppath / colormap)
            except:
                try:
                    Mat.importMat(matpath / material, cmppath / colormap)
                except:
                    print("couldn't import material " + material)
                    placeholder_mat(material)
                    print("placeholder material created")

    else:
        print("skipped material import")
        
    # read in things option       #########################################

    if importThings:
        templatesCount = re.compile(r"World templates\s(\d+)")
        thingsCount= re.compile(r"World things\s(\d+)")

        templatesline = 0
        for line in lines:
            templatesline += 1
            if templatesCount.search(line):
                print('templates starting at line ' + str(templatesline))      # line position to start parsing for things
        
        # read in templates ################################################
        #   TODO: MotS re                                                  #
        #   x, y, z, pitch, yaw and roll can also be single digits (0)     #
        #   instead of a number noted as float (0.0000000)
        
        #                          num   template  name      x              y             z             pitch         yaw           roll         sector            thingflag
        thingsList = []
        things_names = {}
        thingsEx = re.compile("(\d+)\:\s(\S+)\s+(\S+)\s+(-?\d*\.?\d*)\s+(-?\d*\.?\d*)\s+(-?\d*\.?\d*)\s+(-?\d*\.?\d*)\s+(-?\d*\.?\d*)\s+(-?\d*\.?\d*)\s+(\d+)")
        for line in lines:
            match = thingsEx.search(line)
            if match:
                thingtransforms = []
                num = match.group(1)
                template =  match.group(2)
                tempName = match.group(3)
                templateEx = re.compile("^" + tempName + "\s+\w+\s+.*?model3d=(\S+\.3do).*$")     ####   ^.*\b(one|two|three)\b.*$
                for line in lines:                                            ####
                    found = templateEx.search(line)                           ####    experimental
                    if found:                                                 ####
                        tempName = found.group(1)                             ####
                thingtransforms.append(tempName)
                thingX = match.group(4)
                thingtransforms.append(thingX)
                thingY = match.group(5)
                thingtransforms.append(thingY)
                thingZ = match.group(6)
                thingtransforms.append(thingZ)
                thingPitch = match.group(7)
                thingtransforms.append(thingPitch)
                thingYaw = match.group(8)
                thingtransforms.append(thingYaw)
                thingRoll = match.group(9)
                thingtransforms.append(thingRoll)
                Sector = match.group(10)
                thingsList.append(thingtransforms)
                del thingtransforms
        
        for mesh in thingsList:
            try:
                thing = Thing(meshpath.joinpath(mesh[0]), float(mesh[1]),float(mesh[2]),float(mesh[3]), float(mesh[4]), float(mesh[5]), float(mesh[6]))
                thing.import_Thing()
                things_names[mesh[0][:-4]] = thing.name # fill dictionary with object file names and its corresponding JK ingame names
            except:
                pass
                # print("couldn't import mesh " + mesh[0])
        
    else:
        print("thing parser skipped")

    


    # create the mesh ##################################################

    def create_Mesh (verts, edges):
        # Create mesh and object
        me = bpy.data.meshes.new(name+'Mesh')
        ob = bpy.data.objects.new(name, me)
        ob.show_name = True

        # Add materials to meshes
        for material in level_materials:
            try:
                ob.data.materials.append(bpy.data.materials[material])
            except:
                print("couldn't append " + material + " to mesh")
        
        ob.data.materials.append(bpy.data.materials['__portal'])            # portal material at [-1] in material_index

        # Link object to scene
        scene = bpy.context.scene
        scene.collection.objects.link(ob)
        me.from_pydata(verts, [], edges)
        
        # add uv map
        me.uv_layers.new(name='UVMap')
        uvMap = me.uv_layers['UVMap']

        # add vertex color layer
        vcol = me.vertex_colors.new(name='Intensities')

        # assign every needed material to faces
        for isrf, surface in enumerate(surf_list):
            polygon = me.polygons[isrf]                                     # assign face from 'world surfaces' list

            texture_size = (16, 16)
            tiling = (1.0, 1.0)

            if material_indices[isrf] != -1:                                # material numbers from world surfaces (188, 189, 190, -1)
                material_name = mat_name_list[(material_indices[isrf])]     # 189 -> '07fst1a' (specific material name)
                for index, material in enumerate(me.materials):             # 
                    if material_name in bpy.data.materials:                 # check if material exists
                        if material.name == material_name:
                            polygon.material_index = index
                    else:
                        polygon.material_index = len(me.materials) 

                if material_name in bpy.data.images:
                    if bpy.data.images[material_name].size[0] != 0:
                        texture_size = bpy.data.images[material_name].size
            
            else:
                polygon.material_index = len(me.materials)-1                           # apply last material in material_index (__portal) to portals
            
            tiling=mat_tiling_list[material_indices[isrf]]


            for jsrf, loop in enumerate(uv_indices[isrf]):
                u = float(uvArray[uv_indices[isrf][jsrf]][0])/texture_size[0]
                v = float(uvArray[uv_indices[isrf][jsrf]][1])/-texture_size[1]
                x_tile = tiling[0]                                                  # what's that for? multiplication for size? addition for translation?
                y_tile = tiling[1]
                uvMap.data[polygon.loop_indices[jsrf]].uv = (u, v)

                if importIntensities:
                    color=()
                    if motsflag:

                        r = surf_intensities_list[isrf][jsrf*4+1]

                        g = surf_intensities_list[isrf][jsrf*4+2]

                        b = surf_intensities_list[isrf][jsrf*4+3]

                        color = (r, g, b, 1.0)
                    else:
                        surf_light = surf_intensities_list[isrf][jsrf]
                        r = surf_light
                        g = surf_light
                        b = surf_light
                        color = (r, g, b, 1.0)
                    vcol.data[polygon.loop_indices[jsrf]].color = color

        # add uv data
        

        # Update mesh with new data
        me.update()

    ######################################################################

    create_Mesh(vertArray, surf_list)
    print("created level " + name)


        
    return {'FINISHED'}


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
# from bpy_extras.io_utils import ImportHelper
# from bpy.props import StringProperty, BoolProperty, EnumProperty
# from bpy.types import Operator


class ImportJKLfile(Operator, ImportHelper):
    """Load a level file from Star Wars Jedi Knight / Mysteries of the Sith (.jkl)"""
    bl_idname = "import_scene.jkl_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import JKL"

    # ImportHelper mixin class uses this
    filename_ext = ".jkl"

    filter_glob: StringProperty(
        default="*.jkl",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    import_things: BoolProperty(
        name="Import Things",
        description="Level things (.3do files) are additionally imported and placed, if found",
        default=True,
    )

    import_mats: BoolProperty(
        name="Import Materials",
        description="Level geometry and things are textured with Materials (.mat), if found",
        default=True,
    )

    import_intensities: BoolProperty(
        name="Import Light Intensities",
        description="Imports jkl light intensities as vertex color information. Is then multiplied to texture node",
        default=False,
    )
#
#   type: EnumProperty(
#        name="Example Enum",
#        description="Choose between two items",
#        items=(
#            ('OPT_A', "First Option", "Description one"),
#            ('OPT_B', "Second Option", "Description two"),
#        ),
#        default='OPT_A',
#    )

    def execute(self, context):
        return read_jkl_data(context, self.filepath, self.import_things, self.import_mats, self.import_intensities)


# Only needed if you want to add into a dynamic menu
#def menu_func_import(self, context):
#    self.layout.operator(ImportSomeData.bl_idname, text="Text Import Operator")


def import_jkl_button(self, context):
    self.layout.operator(ImportJKLfile.bl_idname, text="JK/MotS Level (.jkl)")


def register():
    bpy.utils.register_class(ImportJKLfile)
    #bpy.utils.register_class(Thing)
    #bpy.types.VIEW3D_MT_image_add.append(import_jkl_button)
    bpy.types.TOPBAR_MT_file_import.append(import_jkl_button)


def unregister():
    bpy.utils.unregister_class(ImportJKLfile)
    #bpy.utils.unregister_class(Thing)
    #bpy.types.VIEW3D_MT_image_add.remove(import_jkl_button)
    bpy.types.TOPBAR_MT_file_import.remove(import_jkl_button)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_scene.jkl_data('INVOKE_DEFAULT')
