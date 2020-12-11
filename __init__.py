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
    "name" : "jediknight2blender",
    "author" : "Ecki Seidel",
    "description" : "Load level files from Jedi Knight: Dark Forces II / Mysteries of the Sith (.jkl)",
    "blender" : (2, 81, 0),
    "version" : (0, 8, 0),
    "location" : "File > Import > JK/MotS Level (.jkl)",
    "wiki_url" : "https://github.com/Ecki81/jediknight2blender/blob/master/README.md",
    "warning" : "",
    "category" : "Import-Export"
}


# version steps:__________________________state__________________
# read in jkl                             DONE
# read in 3do                             DONE
# read in mat                             DONE
#                                         TODO: transp, anim)
# place 3do in levels                     DONE
# texturing levels                        DONE (not sure about tiling / tile factor)
# texturing things                        DONE
# resolve 3do hierarchy and parenting     DONE
# parse GOB/GOO                           DONE
# read in template structure              TODO
# separate into sectors                   TODO
# 

import bpy, bmesh, mathutils
from .import_jkl import Level
from .import_3do import Thing
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty, CollectionProperty
from bpy.types import PropertyGroup, UIList, Operator, AddonPreferences


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
        name="3do meshes",
        description="Level things (.3do) are imported and placed, if found in .gob",
        default=True,
    )

    import_mats: BoolProperty(
        name="Materials",
        description="Level and thing meshes are textured with materials, if found in .gob",
        default=True,
    )

    import_intensities: BoolProperty(
        name="Vertex Lighting",
        description="Imports jkl light intensities as vertex color information. Vertex colors are added to material via multiplier node",
        default=True,
    )

    import_alpha: BoolProperty(
        name="Transparency",
        description="Alpha from 1st transparency table in .cmp file",
        default=True,
    )

    import_scale: FloatProperty(
        name="Scale",
        description="Default jk scale is 0.1 blender units; scale \"1.00\" multiplies jk with 10",
        default=1.0,
        min=0.0001,
    )

    select_shader: EnumProperty(
        name="Shaders",
        description="Lighting & material options",
        items=(
            ('BSDF', "BSDF material", "BSDF materials with transparency and emission map"),
            ('VERT', "Vertex lighting", "Sith engine light intensities in vertex color channel, multiplied with textures in shader"),
        ),
        default='VERT',
    )

    import_sector_info: BoolProperty(
        name="Sector information (Collection: Sectors)",
        description="Display empties w/ sector properties in separate collection",
        default=False,
    )

    def draw_import_config(self, context):
        layout = self.layout
        box = layout.box()

        box.label(text = "JKL Import Options", icon='IMPORT')
        box.prop(self, "import_things")
        box.prop(self, "import_scale")
        box.prop(self, "import_mats")
        transp_row = box.row()
        light_row = box.row()
        sector_row = box.row()
        if self.import_mats:
            transp_row.enabled = True
            light_row.enabled = True
        else:
            transp_row.enabled = False
            light_row.enabled = False
        transp_row.prop(self, "import_alpha")
        light_row.prop(self, "select_shader")
        sector_row.prop(self, "import_sector_info")


        

    def draw(self, context):
        self.draw_import_config(context)

    def execute(self, context):
        level = Level(self.filepath, self.import_things, self.import_mats, self.import_intensities, self.import_alpha, self.import_scale, self.select_shader, self.import_sector_info)
        return level.import_Level()



# class JK2B_PT_Panel(bpy.types.Panel):
#     """Creates a Panel in the Object properties window"""
#     bl_label = "Jedi Knight to Blender"
#     bl_idname = "JK2B_PT_Panel"
#     bl_space_type = 'VIEW_3D'
#     bl_region_type = 'UI'
#     bl_category = 'Jedi Knight'

#     def draw(self, context):
#         layout = self.layout
#         layout.label(text="GOB file", icon="FILE_ARCHIVE")


#         layout.operator("jk.show_gob")

# class JK2B_OT_Show_Gob(Operator):
#     bl_label = "GOB file"
#     bl_idname = "jk2b.show_gob"

# class Gob_File_Item(PropertyGroup):

#     file_name: StringProperty(
#         name="file_name",
#         description="Name of packed file"
#     )

#     file_extension: StringProperty(
#         name="extension",
#         description="Type of packed file"
#     )

def import_jkl_button(self, context):
    self.layout.operator(ImportJKLfile.bl_idname, text="JK/MotS Level (.jkl)")

def register():
    bpy.utils.register_class(ImportJKLfile)
    # bpy.utils.register_class(JK2B_PT_Panel)
    # bpy.utils.register_class(JK2B_OT_Show_Gob)
    bpy.types.TOPBAR_MT_file_import.append(import_jkl_button)

def unregister():
    bpy.utils.unregister_class(ImportJKLfile)
    # bpy.utils.unregister_class(JK2B_PT_Panel)
    # bpy.utils.unregister_class(JK2B_OT_Show_Gob)
    bpy.types.TOPBAR_MT_file_import.remove(import_jkl_button)

if __name__ == '__main__':
    register()