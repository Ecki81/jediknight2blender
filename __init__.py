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

import bpy
import bmesh
import mathutils
from decimal import Decimal
from collections import defaultdict
from pathlib import Path
from os.path import basename, dirname
from .import_jkl import Level
from .import_3do import Thing
from .import_mat import Mat
from .import_gob import Gob
from .import_bm import Bm
from .import_sft import Sft
from .import_cmp import Cmp
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty
from bpy.props import FloatProperty, CollectionProperty
from bpy.types import PropertyGroup, UIList, Operator, AddonPreferences


bl_info = {
    "name": "jediknight2blender",
    "author": "Ecki Seidel",
    "description": "Load GOB/GOO archives from Jedi Knight: "
    "Dark Forces II / Mysteries of the Sith (.gob/.goo)",
    "blender": (2, 81, 0),
    "version": (0, 9, 1),
    "location": "File > Import > JK/MotS Archive (.gob/.goo)",
    "wiki_url":
    "https://github.com/Ecki81/jediknight2blender/blob/master/README.md",
    "warning": "Work in progress",
    "category": "Import-Export"
}


# version steps:__________________________state__________________
# read in jkl                             DONE
# read in 3do                             DONE
# read in mat                             DONE
#                                         TODO: transp, emission)
# place 3do in levels                     DONE
# texturing levels                        DONE (not sure about tiling)
# texturing things                        DONE
# resolve 3do hierarchy and parenting     DONE
# parse GOB/GOO                           DONE
# read in template structure              TODO
# separate into sectors                   TODO


class JKLAddon_Prefs(AddonPreferences):
    bl_idname = basename(dirname(__file__))

    jkdf_path: StringProperty(
        name="DF:JK Resource dir",
        subtype='DIR_PATH',
        default=""
    )

    mots_path: StringProperty(
        name="MotS Resource dir",
        subtype='DIR_PATH',
        default=""
    )

    temp_folder: StringProperty(
        name="Temporary image folder",
        description="Temporary folder for texture files. Neccessary, if "
        "textures need to be packed in an fbx",
        subtype='DIR_PATH',
        default=""
    )

    def draw(self, context):
        layout = self.layout
        layout.label(
            text="Please locate the \"Resource\" directories"
            " for DF:JK and / or MotS"
            )
        layout.prop(self, "jkdf_path")
        layout.prop(self, "mots_path")
        layout.label(
            text="Select a temporary image folder for textures. You "
            "may need one, if you want to export an fbx with packed textures."
            )
        layout.prop(self, "temp_folder")


class ImportGOBfile(Operator):
    """Load an archive file from Star Wars Jedi Knight / MotS (.gob)"""
    bl_idname = "import_scene.gob_data"
    bl_label = "Import GOB"

    filter_glob: StringProperty(
        default="*.gob;*.goo",
        options={'HIDDEN'},
        maxlen=255
        )
    filepath: StringProperty(name="", subtype="FILE_PATH", options={'HIDDEN'})

    def invoke(self, context, event):
        wm = context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        bpy.ops.popup.gob_browser('INVOKE_DEFAULT', filepath=self.filepath)
        return {'FINISHED'}


class File_Item(PropertyGroup):
    '''Repesents the file items in GOB file'''

    name: StringProperty()

    size: FloatProperty(default=0.0)


class Dir_Item(PropertyGroup):
    '''Repesents the file items in GOB file'''

    name: StringProperty()

    indent: IntProperty()

    file_collection: CollectionProperty(
        name="File Collection",
        type=File_Item
    )


class GOB_UL_List(UIList):
    '''List type for GOB file display'''

    def draw_item(self, context, layout, data, item, icon,
                  active_data, active_property, index):
        ext = item.name.split(".")[-1]
        size = item.size

        if ext == "3do":
            custom_icon = 'MATCUBE'
            filetype = "3D Object"
        elif ext == "key":
            custom_icon = 'ANIM'
            filetype = "Animation"
        elif ext == "mat":
            custom_icon = 'TEXTURE'
            filetype = "Texture"
        elif ext == "jkl":
            custom_icon = 'SCENE_DATA'
            filetype = "Level"
        elif ext == "bm":
            custom_icon = 'IMAGE_RGB'
            filetype = "Bitmap"
        elif ext == "sft":
            custom_icon = 'FILE_FONT'
            filetype = "Font"
        elif ext == "cog":
            custom_icon = 'SETTINGS'
            filetype = "Cog Script"
        elif ext == "cmp":
            custom_icon = 'COLOR'
            filetype = "Color Map"
        elif ext == "par":
            custom_icon = 'POINTCLOUD_DATA'
            filetype = "Particle Cloud"
        elif ext == "pup":
            custom_icon = 'POSE_HLT'
            filetype = "Puppet File"
        elif ext == "snd":
            custom_icon = 'SPEAKER'
            filetype = "Sound Info"
        elif ext == "spr":
            custom_icon = 'SEQ_PREVIEW'
            filetype = "Sprite Info"
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
            row_1.label(text=item.name, icon=custom_icon)
            if item.size < 1000:
                row_2.label(text=format(item.size, ".1f") + " KiB")
            else:
                row_2.label(text=format(item.size/1024, ".1f") + " MiB")
            row_2.label(text=filetype)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon=custom_icon)

    def invoke(self, context, event):
        pass


class GOB_UL_Dir_List(UIList):
    '''List type for GOB directory display'''

    def draw_item(self, context, layout, data, item, icon,
                  active_data, active_property, index):

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item.indent > 0:
                split = layout.split(factor=0.05*item.indent)
                split_indent = split.row()
                split_dir = split.row()
                split_dir.label(text=item.name, icon="FILE_FOLDER")
            else:
                layout.label(text=item.name, icon="FILE_FOLDER")
        elif self.layout_type in {'GRID'}:
            layout.label(text="", icon="FILE_FOLDER")


gob = None


class POPUP_OT_gob_browser(Operator):
    '''Display popup window for list of files in GOB/GOO archive'''
    bl_idname = "popup.gob_browser"
    bl_label = "GOB Archive"
    bl_options = {'INTERNAL'}

    filepath: StringProperty()
    dir_entries: CollectionProperty(type=Dir_Item)
    list_index: IntProperty(default=0)
    dir_index: IntProperty(default=0)

    import_things: BoolProperty(
        name="3do meshes",
        description="Level things (.3do) are imported and placed, "
        "if found in .gob",
        default=True,
    )

    import_mats: BoolProperty(
        name="Materials",
        description="Level and thing meshes are textured with materials,"
        " if found in .gob",
        default=True,
    )

    import_intensities: BoolProperty(
        name="Vertex Lighting",
        description="Import jkl light intensities as vertex color."
        " Vertex colors are added to material via multiplier node",
        default=True,
    )

    import_emission: BoolProperty(
        name="Emissive Textures",
        description="Import jkl light levels as emission.",
        default=False,
    )

    import_alpha: BoolProperty(
        name="Transparency",
        description="Alpha from 1st transparency table in .cmp file",
        default=True,
    )

    import_scale: FloatProperty(
        name="Scale",
        description="Default jk scale is 0.1 blender units; "
        "scale \"1.00\" multiplies jk with 10",
        default=1.0,
        min=0.0001,
    )

    select_shader: EnumProperty(
        name="Shader",
        description="Lighting & material options",
        items=(
            (
                'BSDF',
                "BSDF material",
                "BSDF materials with transparency and emission map"),
            (
                'VERT',
                "Vertex lighting",
                '''Sith engine light intensities in vertex color channel,
                multiplied with textures in shader'''),
            (
                'SOLID',
                "Solid colors",
                '''Solid geometry from Sith engine advanced
                display settings with light intensities'''),
        ),
        default='VERT',
    )

    import_sector_info: BoolProperty(
        name="Sectors info",
        description="Display empties w/ sector properties"
        " in separate Collection",
        default=False,
    )

    in_text_editor: BoolProperty(
        name="load into Text Editor",
        description="Raw text gets loaded into blender's Text Editor, "
        "if possible",
        default=False
    )

    manual_source_override: BoolProperty(
        name="Manual Source Game Override",
        description="If source game cannot be identified, select source game manually",
        default=False
    )

    source_mots: EnumProperty(
        name="Source game",
        description="Needs to be selected for 3DO assets",
        items=(
            ("DFJK", "DF:JK 3DO", ""),
            ("MOTS", "MotS 3DO", "")
        ),
        default="DFJK"
    )

    is_mots: EnumProperty(
        name="Source game",
        description="Needs to be selected for 3DO assets",
        items=(
            ("DFJK", "DF:JK 3DO", ""),
            ("MOTS", "MotS 3DO", "")
        ),
        default="DFJK"
    )

    palette_file: StringProperty(
        name="CMP Override",
        description="Type in desired palette file (\"01narsh.cmp\")",
        default="01narsh.cmp"
    )

    def invoke(self, context, event):
        global gob
        gob = Gob(self.filepath)

        # The following feels a bit awkward.
        # Put all files from thegob into defaultdict,
        # then into collection property.
        # Check, if there is a more direct way.

        FILE_MARKER = '<files>'

        def attach(branch, trunk):
            '''
            Insert a branch of directories on its trunk.
            '''
            parts = branch.split('/', 1)
            if len(parts) == 1:  # branch is a file
                trunk[FILE_MARKER].append(parts[0])
            else:
                node, others = parts
                if node not in trunk:
                    trunk[node] = defaultdict(dict, ((FILE_MARKER, []),))
                attach(others, trunk[node])

        dir_entry = self.dir_entries.add()
        dir_entry.name = Path(self.filepath).parts[-1]
        dir_entry.indent = 0

        def prettify(d, indent=1):
            '''
            Print the file tree structure with proper indentation.
            '''
            for key, value in d.items():
                if key != FILE_MARKER:                              # dir
                    # print('  ' * indent + str(key))
                    dir_entry = self.dir_entries.add()
                    dir_entry.name = str(key)
                    dir_entry.indent = indent
                    if isinstance(value, dict):
                        prettify(value, indent+1)
                    else:
                        # print('  ' * (indent+1) + str(value))
                        pass
                else:
                    if value:                                       # file
                        # print('  ' * indent + str(value))
                        for file_item in value:
                            actual_file = self.dir_entries[-1].file_collection.add()
                            actual_file.name = file_item.split(",")[0]
                            file_size = file_item.split(",")[2]
                            actual_file.size = float(file_size)/1024

        main_dict = defaultdict(dict, ((FILE_MARKER, []),))
        for item in gob.get_gobed_paths().items():
            item_windows_path = item[0].replace('\\', '/')
            item_size = str(item[1][0]) + "," + str(item[1][1])
            combined_item = item_windows_path + "," + item_size
            attach(combined_item, main_dict)

        prettify(main_dict)

        # with "OK" button for now
        return context.window_manager.invoke_props_dialog(self, width=800)

    def draw(self, context):

        layout = self.layout

        layout.label(text=self.filepath, icon="OUTLINER")

        split_files = layout.split(factor=0.25)

        split_files.row().template_list(
            listtype_name="GOB_UL_Dir_List",
            list_id="The_Dir_List",
            dataptr=self,
            propname="dir_entries",
            active_dataptr=self,
            active_propname="dir_index",
            rows=25
            )

        active_directory = self.dir_entries[self.dir_index]

        split_files.row().template_list(
            listtype_name="GOB_UL_List",
            list_id="The_List",
            dataptr=active_directory,
            propname="file_collection",
            active_dataptr=self,
            active_propname="list_index",
            rows=25
            )

        layout.label(text="Import Preferences")

        split = layout.split()

        col_jkl = split.column()
        col_thing = split.column()
        col_bitmaps = split.column()

        col_jkl.label(text="Level (.jkl)", icon="SCENE_DATA")
        col_thing.label(text="Things (.3do)", icon="MATCUBE")
        col_bitmaps.label(text="Bitmaps (.mat/.bm/.sft)", icon="TEXTURE")

        box_jkl = col_jkl.box().column()
        box_thing = col_thing.box().column()
        box_bitmaps = col_bitmaps.box().column()

        box_jkl.prop(self, "import_things")
        box_jkl.prop(self, "import_mats")
        box_jkl.prop(self, "import_intensities")
        box_jkl.prop(self, "import_sector_info")
        box_jkl.prop(self, "import_scale")
        box_jkl.prop(self, "manual_source_override")
        if self.manual_source_override:
            box_jkl.prop(self, "source_mots")

        box_thing.prop(self, property="is_mots")

        box_bitmaps.prop(self, "import_alpha")
        box_bitmaps.prop(self, "import_emission")
        box_bitmaps.prop(self, "select_shader")
        box_bitmaps.prop(self, "palette_file", text="CMP")

        layout.prop(self, "in_text_editor")

    def execute(self, context):
        global gob

        prefs = bpy.context.preferences.addons[__name__].preferences

        jkdf_res = prefs.jkdf_path + "\Res2.gob"
        mots_res = prefs.mots_path + "\JKMRES.GOO"

        restwo_file = Path(jkdf_res)
        if restwo_file.is_file():
            print("Res2.gob FOUND!")
        else:
            print("Res2.gob NOT FOUND!")

        jkmres_file = Path(mots_res)
        if jkmres_file.is_file():
            print("JKMRES.GOO FOUND!")
        else:
            print("JKMRES.GOO NOT FOUND!")

        filename = self.dir_entries[self.dir_index].file_collection[self.list_index].name
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

            # replace break characters, otherwise
            # line feed & carriage return bytes
            # are interpreted as a 16bit wide box character
            decoded_text = ungobed_file.decode("iso-8859-1").splitlines()
            text.write('\n'.join(decoded_text))
            text.cursor_set(0)

        if ext == "jkl":
            level = Level(
                self.filepath + "\\" + filename,
                self.import_things,
                self.import_mats,
                self.import_intensities,
                self.import_emission,
                self.import_alpha,
                self.import_scale,
                self.select_shader,
                self.import_sector_info,
                self.source_mots
                )
            level.open_from_gob(ungobed_file)
            level.import_Level()
            self.report({'INFO'}, "Level \"" + filename[:-4] + "\" imported")

        elif ext == "3do":
            thing = Thing(
                ungobed_file,   # binary file buffer
                0.0,            # x
                0.0,            # y
                0.0,            # z
                0.0,            # pitch
                0.0,            # yaw
                0.0,            # roll
                10.0,           # scale
                filename,
                motsflag,
                True            # import textures
                )
            thing.import_Thing()
            self.report({'INFO'}, "Object \"" + filename[:-4] + "\" imported")

        elif ext == "mat":
            mat = Mat(
                ungobed_file,
                ungobed_palette,
                self.import_alpha,
                filename,
                self.select_shader,
                self.import_emission,
                None                # flag ?
                )
            mat.import_Mat()
            self.report(
                {'INFO'},
                "Material \"" + filename[:-4] + "\" imported"
                )

        elif ext == "bm":
            res_gob = Gob(jkdf_res)
            ungobed_ui_palette = res_gob.ungob("uicolormap.cmp")
            bm = Bm(ungobed_file, filename, ungobed_ui_palette)
            bm.import_Bm()

        elif ext == "sft":
            res_gob = Gob(jkdf_res)
            ungobed_ui_palette = res_gob.ungob("uicolormap.cmp")
            sft = Sft(ungobed_file, filename, ungobed_ui_palette)
            sft.import_Sft()

        elif ext == "cmp":
            colormap = Cmp(ungobed_file, filename)
            colormap.import_Cmp()

        elif ext == "wav":
            self.report({'WARNING'}, ext.upper() + "s: not yet implemented")

        else:
            self.report({'WARNING'}, ext.upper() + "s: only text supported")

        return {'FINISHED'}


def import_gob_button(self, context):
    self.layout.operator(
        ImportGOBfile.bl_idname,
        text="JK/MotS Archive (.gob/.goo)"
        )


def register():

    bpy.utils.register_class(JKLAddon_Prefs)
    bpy.utils.register_class(ImportGOBfile)
    bpy.utils.register_class(File_Item)
    bpy.utils.register_class(Dir_Item)
    bpy.utils.register_class(POPUP_OT_gob_browser)
    bpy.utils.register_class(GOB_UL_List)
    bpy.utils.register_class(GOB_UL_Dir_List)
    bpy.types.TOPBAR_MT_file_import.append(import_gob_button)


def unregister():

    bpy.utils.unregister_class(JKLAddon_Prefs)
    bpy.utils.unregister_class(ImportGOBfile)
    bpy.utils.unregister_class(File_Item)
    bpy.utils.unregister_class(Dir_Item)
    bpy.utils.unregister_class(POPUP_OT_gob_browser)
    bpy.utils.unregister_class(GOB_UL_List)
    bpy.utils.unregister_class(GOB_UL_Dir_List)
    bpy.types.TOPBAR_MT_file_import.remove(import_gob_button)


if __name__ == '__main__':
    register()
