import re
import bpy
import pathlib
from os.path import basename, dirname
from .import_3do import Thing
from .import_mat import Mat
from .import_gob import Gob
from . import jk_parse


class Level:

    def __init__(self, path, importThings, importMats, importIntensities, importEmission, importAlpha, scale, select_shader, import_sector_info, source):
        '''initialize jkl with diverse import flags'''
        self.lines = None
        self.importThings = importThings
        self.importMats = importMats
        self.importIntensities = importIntensities
        self.importEmission = importEmission
        self.importAlpha = importAlpha
        self.scale = scale * 10.0                        # blender units factor
        self.select_shader = select_shader
        self.import_sector_info = import_sector_info
        self.path = path
        self.name = ""
        self.source = source


    def open_jkl(self, jkl_file):
        f = open(jkl_file, 'r')
        self.lines=f.readlines()  # store the entire file in a variable
        f.close()


    def open_from_gob(self, ungobed_file):
        ungobed_string = ungobed_file.decode("ISO-8859-1")
        self.lines = re.split('\n', ungobed_string)
        del ungobed_string


    def import_Level(self):
        '''reads jkl, constructs 3d level mesh, fills with 3do objects and applies materials'''

        lines = self.lines

        levelpath = re.split("\\\\", self.path)
        name = levelpath[-1].replace(".jkl", "")

        path = pathlib.Path(self.path)
        gob_path = pathlib.Path('')

        this_addon = basename(dirname(__file__))
        prefs = bpy.context.preferences.addons[this_addon].preferences
        prefs_dir_jkdf = pathlib.Path(prefs.jkdf_path).parts[-1]
        prefs_dir_mots = pathlib.Path(prefs.jkdf_path).parts[-1]

        # check if gob is in one of the following parent directories
        # to determine the base game

        parent = 0
        jk_paths = [
            "Star Wars Jedi Knight - Dark Forces 2",                # GOG Dir
            "Star Wars Jedi Knight",                                # steam Dir
            prefs_dir_jkdf                                          # custom Dir in Prefs
            ]
        mots_paths = [
            "Star Wars Jedi Knight - Mysteries of the Sith",        # GOG Dir
            "Jedi Knight Mysteries of the Sith",                    # steam Dir
            prefs_dir_mots                                          # custom Dir in Prefs
            ]

        motsflag = False
        for folder in path.parts[::-1]:
            if folder in jk_paths:
                gob_path = path.parents[parent-1].joinpath('Resource')
                motsflag = False
                break
            elif folder in mots_paths:
                gob_path = path.parents[parent-1].joinpath('Resource')
                motsflag = True
                break
            else:
                # if base game not found take manual override parameter
                if self.source == "DFJK":
                    gob_path = pathlib.Path(prefs.jkdf_path).joinpath('Resource')
                    motsflag = False
                elif self.source == "MOTS":
                    gob_path = pathlib.Path(prefs.mots_path).joinpath('Resource')
                    motsflag = True
            parent += 1

        # # variable_section = [line position, variable count]

        materials_section = [0, 0]
        colormaps_section = [0, 0]
        vertices_section = [0, 0]
        uvs_section = [0, 0]
        adjoins_section = [0, 0]
        surfaces_section = [0, 0]
        sectors_section = [0, 0]
        models_section = [0, 0]
        templates_section = [0, 0]
        things_section = [0, 0]

        for pos, line in enumerate(lines):
            match_materials_section = jk_parse.WORLD_MATERIALS_RE.search(line)
            match_colormaps_section = jk_parse.WORLD_COLORMAPS_RE.search(line)
            match_vertices_section = jk_parse.WORLD_VERTICES_RE.search(line)
            match_uvs_section = jk_parse.WORLD_UVS_RE.search(line)
            match_adjoins_section = jk_parse.WORLD_ADJOINS_RE.search(line)
            match_surfaces_section = jk_parse.WORLD_SURFACES_RE.search(line)
            match_sectors_section = jk_parse.WORLD_SECTORS_RE.search(line)
            match_models_section = jk_parse.WORLD_MODELS_RE.search(line)
            match_templates_section = jk_parse.WORLD_TEMPLATES_RE.search(line)
            match_things_section = jk_parse.WORLD_THINGS_RE.search(line)
            if match_materials_section:
                materials_section = [pos+1 , int(match_materials_section.group(1))]
            elif match_colormaps_section:
                colormaps_section = [pos+1 , int(match_colormaps_section.group(1))]
            elif match_vertices_section:
                vertices_section = [pos+1 , int(match_vertices_section.group(1))]
            elif match_uvs_section:
                uvs_section = [pos+1 , int(match_uvs_section.group(1))]
            elif match_adjoins_section:
                adjoins_section = [pos+1 , int(match_adjoins_section.group(1))]
            elif match_surfaces_section:
                surfaces_section = [pos+1 , int(match_surfaces_section.group(1))]
            elif match_sectors_section:
                sectors_section = [pos+1 , int(match_sectors_section.group(1))]
            elif match_models_section:
                models_section = [pos+1 , int(match_models_section.group(1))]
            elif match_templates_section:
                templates_section = [pos+1 , int(match_templates_section.group(1))]
            elif match_things_section:
                things_section = [pos+1 , int(match_things_section.group(1))]
                break


        # read in vertices ###############################################

        vert_array = []  # 2D array with vertices x, y, z

        i=0
        while i < vertices_section[1]:
            i+=1
            vert_line=re.split("\s+", lines[i + vertices_section[0]], 4)
            del vert_line[0]
            del vert_line[3]
            vert_line[0]=float(vert_line[0]) * self.scale
            vert_line[1]=float(vert_line[1]) * self.scale
            vert_line[2]=float(vert_line[2]) * self.scale
            vert_array.append(vert_line)

        # read in uvs #####################################################

        uv_array = []
        i=0
        while i < uvs_section[1]:
            i += 1
            uv_line = re.split("\s+", lines[i + uvs_section[0]])
            del uv_line[0]
            del uv_line[-1]
            uv_line[0] = float(uv_line[0])
            uv_line[1] = float(uv_line[1])
            uv_array.append(uv_line)


        # read in sectors #################################################

        sector_pos = []
        sectors_pos_array = []
        # [[NUM, STARTPOS, ENDPOS], [NUM, STARTPOS, ENDPOS]...]

        i = 0
        while i < sectors_section[1]:
            sector_line_count = 0
            sectors_dict = {}
            for line in lines[sectors_section[0]:models_section[0]]:
                match_sector = jk_parse.SECTOR_RE.search(line)
                match_ambient = jk_parse.SECTOR_AMBIENT_RE.search(line)
                match_extra = jk_parse.SECTOR_EXTRA_RE.search(line)
                match_tint = jk_parse.SECTOR_TINT_RE.search(line)
                match_boundbox = jk_parse.SECTOR_BOUNDBOX_RE.search(line)
                match_center = jk_parse.SECTOR_CENTER_RE.search(line)
                match_radius = jk_parse.SECTOR_RADIUS_RE.search(line)
                match_surfaces = jk_parse.SECTOR_SURFACES_RE.search(line)
                sector_line_count += 1

                if match_sector:
                    sectors_dict = {'sector':int(match_sector.group(1))}
                    sectors_dict['start'] = sectors_section[0] + sector_line_count

                elif match_ambient:
                    sectors_dict['ambient'] = float(match_ambient.group(1))

                elif match_extra:
                    sectors_dict['extra'] = float(match_extra.group(1))

                elif match_tint:
                    sectors_dict['tint'] = [float(match_tint.group(1)), float(match_tint.group(2)), float(match_tint.group(3))]

                elif match_boundbox:
                    sectors_dict['boundbox'] = [float(match_boundbox.group(1)), float(match_boundbox.group(2)), float(match_boundbox.group(3)), float(match_boundbox.group(4)), float(match_boundbox.group(5)), float(match_boundbox.group(6))]

                elif match_center:
                    sectors_dict['center'] = [float(match_center.group(1)), float(match_center.group(2)), float(match_center.group(3))]

                elif match_radius:
                    sectors_dict['radius'] = [float(match_radius.group(1))]

                elif match_surfaces:
                    sectors_dict['end'] = sectors_section[0] + sector_line_count
                    sectors_dict['surfaces'] = int(match_surfaces.group(1)) + int(match_surfaces.group(2)) -1 # last surface in this sector

                    i += 1
                # if sectors_dict:
                    sectors_pos_array.append(sectors_dict)
            del sectors_dict

        def get_surface_index(surf):
            return surf.get('surfaces')

        sectors_pos_array.sort(key=get_surface_index)


        # read in surfaces ################################################

        surf_list = []                                      # world VERTICES
        surf_vertices = []

        surf_intensities = []
        surf_intensities_list = []

        uv_indices = []
        uv_index_list = []
        material_indices = []

        alpha_mats_ids = []
        alpha_mats = {}

        sector_extralight = 0.0
        sector_ambient = 0.0
        sector_tint = [0.0, 0.0, 0.0]

        current_sector = 0


        if self.import_sector_info:
            # create sector property objects
            sector_collection = bpy.data.collections.new('Sectors')
            sector_num_coll = bpy.data.collections.new('Index')
            sector_radius_coll = bpy.data.collections.new('Radius')
            sector_bbox_coll = bpy.data.collections.new('Boundbox')
            bpy.context.scene.collection.children.link(sector_collection)
            sector_collection.children.link(sector_num_coll)
            sector_collection.children.link(sector_radius_coll)
            sector_collection.children.link(sector_bbox_coll)
            for prop in sectors_pos_array:
                # boundboxes
                (x1, y1, z1, x2, y2, z2) = prop['boundbox']
                (x1, y1, z1, x2, y2, z2) = (x1*self.scale, y1*self.scale, z1*self.scale, x2*self.scale, y2*self.scale, z2*self.scale)
                bb_verts = ((x1, y1, z1), (x1, y2, z1), (x1, y2, z2), (x1, y1, z2), (x2, y1, z1), (x2, y2, z1), (x2, y2, z2), (x2, y1, z2))
                bb_faces = ((0, 1, 2, 3), (1, 5, 6, 2), (5, 4, 7, 6), (4, 0, 3, 7), (3, 2, 6, 7), (0, 4, 5, 1))
                boundbox_empty = bpy.data.meshes.new('boundbox_'+str(prop['sector'])+'Mesh')
                bbox_ob = bpy.data.objects.new('boundbox_'+str(prop['sector']), boundbox_empty)
                bbox_ob.display_type = 'WIRE'
                boundbox_empty.from_pydata(bb_verts, [], bb_faces)
                boundbox_empty.update()
                # sectors
                sector_empty = bpy.data.objects.new("sector_" + str(prop['sector']), None)
                sector_radius = bpy.data.objects.new("radius_" + str(prop['sector']), None)
                sector_radius.empty_display_type = 'SPHERE'
                sector_radius.empty_display_size = prop['radius'][0]*self.scale
                bpy.data.collections['Index'].objects.link(sector_empty)
                bpy.data.collections['Radius'].objects.link(sector_radius)
                bpy.data.collections['Boundbox'].objects.link(bbox_ob)
                sector_x, sector_y, sector_z = prop['center'][0]*self.scale, prop['center'][1]*self.scale, prop['center'][2]*self.scale
                sector_empty.location = sector_x, sector_y, sector_z
                sector_radius.location = sector_x, sector_y, sector_z
                sector_empty.show_name = True


        i=0
        while i < surfaces_section[1]:
            surfLine=re.split("\s+", lines[i + surfaces_section[0] + 1],)
            matId = int(surfLine[1])
            surfflag = int(surfLine[2], base=16)
            faceflag = int(surfLine[3], base=16)
            geomode = int(surfLine[4])                        # 0 = don't draw, 4 = textured (else)
            light = int(surfLine[5])
            tex = int(surfLine[6])
            adjoin = int(surfLine[7])
            extralight = float(surfLine[8])
            nvert=int(surfLine[9])                          # count of vertexes needed for surfaces (nverts)

            # if adjoin + material, then probably transparent!

            material_indices.append(matId)

            if adjoin > -1 and matId > -1:
                alpha_mats_ids.append(matId)
                alpha_mats_ids = sorted(set(alpha_mats_ids))

            j = 0

            while j < nvert:
                v_index  = re.split(",",surfLine[j+10])
                surf_vertices.append(int(v_index[0]))
                uv_index_list.append(int(v_index[1]))
                j+=1
            surf_list.append(surf_vertices)
            uv_indices.append(uv_index_list)


            # get sector light intensities per surface from sector list
            if i >= sectors_pos_array[current_sector]['surfaces']:
                sector_extralight = sectors_pos_array[current_sector]['extra']
                sector_ambient = sectors_pos_array[current_sector]['ambient']
                sector_tint = sectors_pos_array[current_sector]['tint']
                current_sector += 1


            j = 0
            if motsflag:                   #  color light intensities in Mots (intensity, r, g, b)
                while j < nvert*4:
                    surf_intensities.append(float(surfLine[10+nvert+j]) + extralight + sector_extralight)
                    j+=1
            else:
                while j < nvert:
                    intensity = float(surfLine[10+nvert+j])
                    r = intensity + extralight + sector_extralight # * sector_tint[0]
                    g = intensity + extralight + sector_extralight # * sector_tint[1]
                    b = intensity + extralight + sector_extralight # * sector_tint[2]
                    surf_intensities.append((r, g, b))
                    j+=1
            surf_intensities_list.append(surf_intensities)


            surf_vertices = []
            uv_index_list = []
            surf_intensities = []
            i+=1


        # read in materials ################################################
        # TODO find better ways to terminate at end of material list

        mat_line = ""
        mat_list = []
        mat_tiling_list = []
        for i in range(1, 1000): # only allows for 1000 mat files
            mat_line = lines[i + materials_section[0] + (1 if not motsflag else 0)]
            if re.match(r'(#|//).*', mat_line) or len(mat_line) < 3:
                # skip comment lines and empty lines
                continue
            mat_line = re.split("\s+", mat_line)
            mat_list.append(mat_line[1].lower())
            if mat_line[0] != "end":
                mat_tiling_tuple = (float(mat_line[2]), float(mat_line[3]))
                mat_tiling_list.append(mat_tiling_tuple)
            else:
                break
            if mat_line[0] == "end":
                break


        # get a material name list, for object application

        mat_name_list = []                                  # every material in jkl w/o file extension *.mat
        for material in mat_list:
            material_name = material.replace(".mat", "")
            mat_name_list.append(material_name)

        level_materials = []                                # list for select level geo material names
        material_list = sorted(set(material_indices))       # level mat indices, removed duplicates and sorted in ascending order
        for position in material_list:
            level_materials.append(mat_name_list[int(position)])
        for position in alpha_mats_ids:
            alpha_mats[mat_name_list[int(position)]] = "alpha"

        # print(alpha_mats)


        # create portal material ################################################

        def placeholder_mat(placeholder_name, color):
            mat = bpy.data.materials.new(placeholder_name)
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes["Principled BSDF"]
            mat.node_tree.nodes.remove(bsdf)
            output = mat.node_tree.nodes["Material Output"]
            transpNode = mat.node_tree.nodes.new('ShaderNodeBsdfTransparent')
            transpNode.location = -400,250
            mat.node_tree.links.new(output.inputs['Surface'], transpNode.outputs['BSDF'])
            mat.blend_method = 'CLIP'

        placeholder_mat('__portal', None)      # transparent bsdf

        # load GOB, if neccessary ###############################################

        if self.importMats or self.importThings:
            if motsflag:
                try:
                    gob = Gob(gob_path.joinpath("JKMRES.GOO"))
                    print("assigning JKMRES.GOO")
                except FileNotFoundError:
                    bpy.ops.report.exception(report_message="JKMRES.GOO")
                    self.importMats = False
                    self.importThings = False
            else:
                try:
                    gob = Gob(gob_path.joinpath("Res2.gob"))
                    print("assigning Res2.gob")
                except FileNotFoundError:
                    bpy.ops.report.exception(report_message="Res2.gob")
                    self.importMats = False
                    self.importThings = False


        # call material loading class ###########################################


        # select_shader
        surfflag = None


        if self.importMats:
            cmp_file = re.split("\s+", lines[colormaps_section[0]],)[1]
            colormap = gob.ungob(cmp_file.lower())
            print("colormap:", cmp_file.lower())
            for material in mat_list:
                material_loaded = material in bpy.data.materials
                if material in alpha_mats and self.importAlpha:
                    alpha = True
                    print(material, "has alpha channel")
                else:
                    alpha = False
                if material_loaded:
                    print(material, "already loaded")
                else:
                    try:
                        mat = Mat(gob.ungob(material), colormap, alpha, material, self.select_shader, self.importEmission, faceflag)
                        mat.import_Mat()
                    except:
                        placeholder_mat(material, (1.0,0.0,1.0,1))
                        print("couldn't import " + material + ". created placeholder mat")


        else:
            print("skipped material import")


        # test material append from other blend file ##########################

        # material_path = os.path.dirname(__file__) + "/materials/materials.blend\\Materials\\"
        # material_name = "jkl_sky"
        # bpy.ops.wm.append(filename=material_name, directory=material_path)



        # read in things option       #########################################

        if self.importThings:

            # read in templates ################################################
            #   TODO: MotS re                                                  #
            #   x, y, z, pitch, yaw and roll can also be single digits (0)     #
            #   instead of a number noted as float (0.0000000)

            #                          num   template  name      x              y             z             pitch         yaw           roll         sector            thingflag
            things_list = []
            thingsEx = re.compile("(\d+)\:\s(\S+)\s+(\S+)\s+(-?\d*\.?\d*)\s+(-?\d*\.?\d*)\s+(-?\d*\.?\d*)\s+(-?\d*\.?\d*)\s+(-?\d*\.?\d*)\s+(-?\d*\.?\d*)\s+(\d+)")
            for line in lines[things_section[0]+1:things_section[0]+things_section[1]+3]:
                match = thingsEx.search(line)
                if match:
                    thingtransforms = []
                    num = match.group(1)
                    template =  match.group(2)
                    tempName = match.group(3)
                    templateEx = re.compile("^" + tempName + "\s+\w+\s+.*?model3d=(\S+\.3do).*$")     ####   ^.*\b(one|two|three)\b.*$
                    for line in lines[templates_section[0]+1:templates_section[0]+templates_section[1]+3]:                                            ####
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
                    things_list.append(thingtransforms)
                    del thingtransforms

            copy_flag = True

            things_names = {}
            for mesh in things_list:
                mesh_name = mesh[0].replace(".3do", "")
                try:
                    ungobed_file = gob.ungob(mesh[0])
                    if copy_flag:
                        thing = Thing(ungobed_file, float(mesh[1]),float(mesh[2]),float(mesh[3]), float(mesh[4]), float(mesh[5]), float(mesh[6]), self.scale, mesh_name, motsflag, False)
                        if mesh[0] in things_names:
                            obj_copy = thing.copy_Thing(things_names[mesh[0]])
                        else:
                            obj = thing.import_Thing()
                            things_names[mesh[0]] = obj # fill dictionary with object file names and blender objects
                    else:
                        thing = Thing(ungobed_file, float(mesh[1]),float(mesh[2]),float(mesh[3]), float(mesh[4]), float(mesh[5]), float(mesh[6]), self.scale, mesh_name, motsflag, False)
                        thing.import_Thing()
                except:
                    pass

        else:
            print("thing parser skipped")




        # create the mesh ##################################################

        def create_Level(verts, faces):
            # Create mesh and object
            me = bpy.data.meshes.new(name+'Mesh')
            ob = bpy.data.objects.new(name, me)
            ob.show_name = True

            # Add materials to meshes
            for material in level_materials:
                try:
                    mat = bpy.data.materials[material]
                    ob.data.materials.append(mat)
                except:
                    print("couldn't append " + material + " to mesh")

            ob.data.materials.append(bpy.data.materials['__portal'])            # portal material at [-1] in material_index

            # Link object to scene
            scene = bpy.context.scene
            scene.collection.objects.link(ob)
            me.from_pydata(verts, [], faces)
            # me.validate()         # should be validated, currently UV index out of range error

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
                    u = float(uv_array[uv_indices[isrf][jsrf]][0])/texture_size[0]
                    v = float(uv_array[uv_indices[isrf][jsrf]][1])/-texture_size[1]
                    x_tile = tiling[0]                                                  # what's that for? multiplication for size? addition for translation?
                    y_tile = tiling[1]
                    uvMap.data[polygon.loop_indices[jsrf]].uv = (u, v)

                    if self.importIntensities:
                        color=()
                        if motsflag:
                            r = surf_intensities_list[isrf][jsrf*4+1]
                            g = surf_intensities_list[isrf][jsrf*4+2]
                            b = surf_intensities_list[isrf][jsrf*4+3]
                            color = (r, g, b, 1.0)
                        else:
                            surf_light = surf_intensities_list[isrf][jsrf]
                            r = surf_light[0]
                            g = surf_light[1]
                            b = surf_light[2]
                            color = (r, g, b, 1.0)
                        vcol.data[polygon.loop_indices[jsrf]].color = color


            #  #Delete Adjoin surfaces
            # if self.importMats:
            #     for port_surface in surf_list:
            #         print(port_surface)
            #     pass


            # Update mesh with new data
            me.update()

        ######################################################################

        create_Level(vert_array, surf_list)

        return {'FINISHED'}
