![jkl2blender title image](/jkl2blender_titleImage.png)
### Addon for blender 2.8

## Import Jedi Knight: Dark Forces 2 level files (.jkl) into blender 2.8 (WIP)

This script needs the original JK:DF2 or MotS container files (_.gob/.goo_)
for the materials and 3do objects.
The jkl files for the maps need to be unpacked into the Jedi Knight or MotS game directory, depending
on which game they are based on.
I used the container manager program [CONMAN.exe](http://www.jkhub.net/library/index.php?title=Tools:Container_Manager_%28ConMan%29_v0.91z) for that.


Install downloaded/cloned and zipped repo files as an addon to blender:
Open Blender -> Edit -> Preferences -> Add-ons -> Install and select the zip


To open a Jedi Knight: Dark Forces 2 level file (.jkl), go to -> File -> Import -> JK/MotS level
Depending on your hardware, it may take the script a while to import files larger than 1MB.

## Tasks

- [x] read in jkl
- [x] read in 3do
- [x] read in basic mat
- [x] place 3do in levels
- [x] texturing levels
- [x] texturing 3do
- [x] resolve 3do hierarchy and parenting
- [x] parse GOB/GOO
- [ ] jkl browser UI for packed (GOB) files
- [ ] vertex lighting
- [ ] faster loading

_Sorry about the messy code, this is my first real programming project and still wip.
Also, i have not yet tested it on any fan made jkls, but so far, it works on all original DF:JK 2
and MotS single and multiplayer level maps_
