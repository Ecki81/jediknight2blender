import re

# jkl world regular expressions

WORLD_MATERIALS_RE = re.compile(r"World materials\s(\d+)")
WORLD_COLORMAPS_RE = re.compile(r"World Colormaps\s(\d+)")
WORLD_VERTICES_RE = re.compile(r"World vertices\s(\d+)")
WORLD_UVS_RE = re.compile(r"World texture vertices\s(\d+)")
WORLD_ADJOINS_RE = re.compile(r"World adjoins\s(\d+)")
WORLD_SURFACES_RE = re.compile(r"World surfaces\s(\d+)")
WORLD_SECTORS_RE = re.compile(r"World sectors\s(\d+)")
WORLD_MODELS_RE = re.compile(r"World models\s(\d+)")
WORLD_TEMPLATES_RE = re.compile(r"World templates\s(\d+)")
WORLD_THINGS_RE = re.compile(r"World things\s(\d+)")

# jkl sectors regular expressions

SECTOR_RE = re.compile(r"SECTOR\s(\d+)")
SECTOR_AMBIENT_RE = re.compile(r"AMBIENT LIGHT\s(-?\d*\.?\d*)")
SECTOR_EXTRA_RE = re.compile(r"EXTRA LIGHT\s(-?\d*\.?\d*)")
SECTOR_TINT_RE = re.compile(r"TINT\s(-?\d*\.?\d*)\s(-?\d*\.?\d*)\s(-?\d*\.?\d*)")
SECTOR_BOUNDBOX_RE = re.compile(r"BOUNDBOX\s(-?\d*\.?\d*)\s(-?\d*\.?\d*)\s(-?\d*\.?\d*)\s(-?\d*\.?\d*)\s(-?\d*\.?\d*)\s(-?\d*\.?\d*)")
SECTOR_CENTER_RE = re.compile(r"CENTER\s(-?\d*\.?\d*)\s(-?\d*\.?\d*)\s(-?\d*\.?\d*)")
SECTOR_RADIUS_RE = re.compile(r"RADIUS\s(-?\d*\.?\d*)")
SECTOR_SURFACES_RE = re.compile(r"SURFACES\s(\d+)\s(\d+)")

# 3do regular expressions

OBJ_MATERIALS_RE = re.compile(r"^MATERIALS\s(\d+)")
OBJ_VERTICES_RE = re.compile(r"^VERTICES\s(\d+)")
OBJ_UVS_RE = re.compile(r"^TEXTURE VERTICES\s(\d+)")
OBJ_FACES_RE = re.compile(r"^FACES\s(\d+)")
OBJ_MESHES_RE = re.compile(r"^MESHES\s(\d+)")
OBJ_MESH_RE = re.compile(r"^MESH\s(\d+)")
OBJ_HIERARCHY_RE = re.compile(r"^HIERARCHY NODES\s(\d+)")