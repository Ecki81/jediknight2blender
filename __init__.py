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
from decimal import Decimal
from .import_jkl import Level
from .import_3do import Thing
from .import_mat import Mat
from .import_gob import Gob
from .import_bm import Bm
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty, FloatProperty, CollectionProperty
from bpy.types import PropertyGroup, UIList, Operator, AddonPreferences



class JKLAddon_Prefs(AddonPreferences):
    bl_idname = __name__

    jkdf_path : StringProperty(
        name = "DF:JK Resource dir",
        subtype = 'DIR_PATH',
        default = "C:\Program Files (x86)\GOG Galaxy\Games\Star Wars Jedi Knight - Dark Forces 2\Resource"
    )

    mots_path : StringProperty(
        name = "MotS Resource dir",
        subtype = 'DIR_PATH',
        default = "C:\Program Files (x86)\GOG Galaxy\Games\Star Wars Jedi Knight - Mysteries of the Sith\Resource"
    )


    def draw(self, context):
        layout = self.layout
        layout.label(text="Please specify the \"Resource\" directories for DF:JK and/or MotS")
        layout.prop(self, "jkdf_path")
        layout.prop(self, "mots_path")




class ImportJKLfile(Operator, ImportHelper):
    """Load a level file from Star Wars Jedi Knight / Mysteries of the Sith (.jkl)"""
    bl_idname = "import_level.jkl_data"  # important since its how bpy.ops.import_test.some_data is constructed
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
        level.open_jkl(self.filepath)
        level.import_Level()
        return {'FINISHED'}




class ImportGOBfile(Operator):
    """Load an archive file from Star Wars Jedi Knight / Mysteries of the Sith (.gob)"""
    bl_idname = "import_scene.gob_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import GOB"

    filter_glob: StringProperty(default="*.gob;*.goo", options={'HIDDEN'}, maxlen=255)
    filepath: StringProperty(name="", subtype="FILE_PATH", options={'HIDDEN'})

    def invoke(self, context, event):
        wm = context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        bpy.ops.popup.gob_browser('INVOKE_DEFAULT',filepath=self.filepath)
        return {'FINISHED'}




class File_Item(PropertyGroup):
    '''Repesents the file items in GOB file'''
    
    name : StringProperty()
    
    size : FloatProperty(default=0.0)




class Dir_Item(PropertyGroup):
    '''Repesents the file items in GOB file'''
    
    name : StringProperty()
    



class GOB_UL_List(UIList):
    '''List type for GOB file display'''

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):
        ext = item.name.split(".")[-1]
        size = item.size

        if ext == "3do":
            custom_icon = 'MATCUBE'
            filetype = "3D Object"
        elif ext == "mat":
            custom_icon = 'TEXTURE'
            filetype = "Texture"
        elif ext == "jkl":
            custom_icon = 'SCENE_DATA'
            filetype = "Level"
        elif ext == "bm":
            custom_icon = 'IMAGE_RGB'
            filetype = "Bitmap"
        elif ext == "cog":
            custom_icon = 'SETTINGS'
            filetype = "Cog Script"
        elif ext == "cmp":
            custom_icon = 'COLOR'
            filetype = "Color Map"
        elif ext == "wav":
            custom_icon = 'OUTLINER_DATA_SPEAKER'
            filetype = "Audio"

        else:
            custom_icon = 'FILE'
            filetype = ""


        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            split = layout.split(factor=0.7)
            row_1 = split.row()
            row_2 = split.row()
            row_1.label(text=item.name, icon = custom_icon)
            if item.size < 1000:
                row_2.label(text=format(item.size, ".1f") + " KiB")
            else:
                row_2.label(text=format(item.size/1024, ".1f") + " MiB")
            row_2.label(text=filetype)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

    def invoke(self, context, event):
        pass




class GOB_UL_Dir_List(UIList):
    '''List type for GOB directory display'''

    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index):

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.name, icon='FILE_FOLDER')
        elif self.layout_type in {'GRID'}:
            layout.label(text="", icon='FILE_FOLDER')


gob = None
class POPUP_OT_gob_browser(Operator):
    '''Display popup window for list of files in GOB/GOO archive'''
    bl_idname = "popup.gob_browser"
    bl_label = "GOB Archive"
    bl_options = {'INTERNAL'}

    filepath : StringProperty()
    file_entries : CollectionProperty(type=File_Item)
    dir_entries : CollectionProperty(type=Dir_Item)
    list_index : IntProperty(default=0)
    dir_index : IntProperty(default=0)

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

    in_text_editor : BoolProperty(
        name="file in Text Editor",
        description="File is additionally loaded into blender's Text Editor",
        default=False
        )
    
    is_mots : EnumProperty(
        name="Mots",
        description="Needs to be selected for 3DO assets",
        items=(
            ("DFJK", "DF:JK 3DO", ""),
            ("MOTS", "MotS 3DO", "")
        ),
        default="DFJK"
        )

    palette_file : StringProperty(
        default="01narsh.cmp"
        )

    def invoke(self, context, event):
        global gob
        gob = Gob(self.filepath)
        for item in gob.get_gobed_paths().items():
            entry = self.file_entries.add()
            entry.name = item[0].split('\\')[-1]
            entry.size = item[1][1]/1024

        # for directory in gob.get_gobed_paths().items():
        #     dir_entry = self.dir_entries.add()
        #     dir_entry.name = directory[0].split('\\')[0]

        # for item in gob.get_gobed_paths().items():
        #     directory = 
 
        return context.window_manager.invoke_props_dialog(self, width=600)      # with "OK" button for now


    def draw(self, context):
        layout = self.layout
        
        layout.label(text = self.filepath, icon = 'FILE_ARCHIVE')
        
        split_1 = layout.split(factor=0.25)

        split_1.row().template_list(
            listtype_name = "GOB_UL_Dir_List",
            list_id = "The_Dir_List",
            dataptr = self,
            propname = "dir_entries",
            active_dataptr = self,
            active_propname = "dir_index",
            rows = 25,

        )

        split_1.row().template_list(
            listtype_name = "GOB_UL_List",
            list_id = "The_List",
            dataptr = self,
            propname = "file_entries",
            active_dataptr = self,
            active_propname = "list_index",
            rows = 25
            )

        layout.label(text="Preferences")

        split = layout.split()

        col_text = split.row()
        col_bool = split.row()
        jkl_prefs_col = layout.column()
        row_1 =  jkl_prefs_col.split().row()
        row_2 =  jkl_prefs_col.split().row()

        filename = self.file_entries[self.list_index].name
        ext = filename.split(".")[-1]

        if ext == "mat":
            col_text.enabled = False
        else:
            col_text.enabled = True

        if ext == "3do":
            col_bool.enabled = True
        else:
            col_bool.enabled = False

        if ext == "jkl":
            jkl_prefs_col.enabled = True
        else:
            jkl_prefs_col.enabled = False

        col_text.prop(self, "in_text_editor")
        col_bool.prop(self, property="is_mots", expand=True)

        row_1.prop(self, "import_things")
        row_1.prop(self, "import_mats")
        row_1.prop(self, "import_intensities")
        row_1.prop(self, "import_alpha")
        row_2.prop(self, "import_sector_info")
        row_2.prop(self, "import_scale")
        row_2.prop(self, "select_shader")



    def execute(self, context):
        global gob

        prefs = bpy.context.preferences.addons[__name__].preferences

        jkdf_res = prefs.jkdf_path + "\Res2.gob"
        mots_res = prefs.mots_path + "\JKMRES.GOO"

        filename = self.file_entries[self.list_index].name
        ext = filename.split(".")[-1]

        ungobed_file = gob.ungob(filename)
        try:
            ungobed_palette = gob.ungob(self.palette_file)
        except:
            pass

        motsflag = True
        if self.is_mots == "MOTS":
            motsflag = True
        else:
            motsflag = False

        if self.in_text_editor:
            text = bpy.data.texts.new(filename)
            text.write(ungobed_file.decode("iso-8859-1"))
            text.cursor_set(0)

        if ext == "jkl":
            level = Level(self.filepath + "\\" + filename, self.import_things, self.import_mats, self.import_intensities, self.import_scale, self.import_scale, "VERT", self.import_sector_info)
            level.open_from_gob(ungobed_file)
            level.import_Level()
            self.report({'INFO'}, "Level \"" + filename[:-4] + "\" imported")

        elif ext == "3do":
            thing = Thing(ungobed_file, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 10.0, filename, motsflag)
            thing.import_Thing()
            self.report({'INFO'}, "Object \"" + filename[:-4] + "\" imported")

        elif ext == "mat":
            mat = Mat(ungobed_file, ungobed_palette, False, filename, "BSDF", None)
            mat.import_Mat()
            self.report({'INFO'}, "Material \"" + filename[:-4] + "\" imported")

        elif ext =="bm":
            res_gob = Gob(jkdf_res)
            ungobed_ui_palette = res_gob.ungob("uicolormap.cmp")
            bm = Bm(ungobed_file, filename, ungobed_ui_palette)
            bm.import_Bm()

        else:
            self.report({'WARNING'}, ext.upper() + "s: only text supported")


        return {'FINISHED'}



def import_jkl_button(self, context):
    self.layout.operator(ImportJKLfile.bl_idname, text="JK/MotS Level (.jkl)")

def import_gob_button(self, context):
    self.layout.operator(ImportGOBfile.bl_idname, text="JK/MotS Archive (.gob/.goo)")



def register():

    bpy.utils.register_class(JKLAddon_Prefs)
    bpy.utils.register_class(ImportJKLfile)
    bpy.utils.register_class(ImportGOBfile)
    bpy.utils.register_class(File_Item)
    bpy.utils.register_class(Dir_Item)
    bpy.utils.register_class(POPUP_OT_gob_browser)
    bpy.utils.register_class(GOB_UL_List)
    bpy.utils.register_class(GOB_UL_Dir_List)
    bpy.types.TOPBAR_MT_file_import.append(import_jkl_button)
    bpy.types.TOPBAR_MT_file_import.append(import_gob_button)


def unregister():

    bpy.utils.unregister_class(JKLAddon_Prefs)
    bpy.utils.unregister_class(ImportJKLfile)
    bpy.utils.unregister_class(ImportGOBfile)
    bpy.utils.unregister_class(File_Item)
    bpy.utils.unregister_class(Dir_Item)
    bpy.utils.unregister_class(POPUP_OT_gob_browser)
    bpy.utils.unregister_class(GOB_UL_List)
    bpy.utils.unregister_class(GOB_UL_Dir_List)
    bpy.types.TOPBAR_MT_file_import.remove(import_jkl_button)
    bpy.types.TOPBAR_MT_file_import.remove(import_gob_button)


if __name__ == '__main__':
    register()