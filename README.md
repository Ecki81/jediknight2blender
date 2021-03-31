![jkl2blender title image](/jkl2blender_titleImage.png)
### Add-on for blender 2.8x

## Import Jedi Knight: Dark Forces 2 assets into blender 2.8x (WIP)

With this add-on you can open the JK:DF2 or MotS container archives (_.gob/.goo_)
and import a variety of assets into blender.


Install downloaded/cloned and zipped repo files as an addon to blender:
Open Blender -> Edit -> Preferences -> Add-ons -> Install and select the zip


To open a JK:DF2 gob file (.gob), go to -> File -> Import -> JK/MotS Archive.
Depending on your hardware, it may take the script a while to import files larger than 1MB.


You also need to specify the original game "Resource" directories in the add-on Preferences.
![jkl2blender preferences](/jkl2blender_preferences.png)


## Tasks

- [x] read in jkl
- [x] read in 3do
- [x] read in basic mat
- [x] place 3do in levels
- [x] texturing levels
- [x] texturing 3do
- [x] resolve 3do hierarchy and parenting
- [x] parse GOB/GOO
- [x] jkl browser UI for packed (GOB) files
- [ ] vertex lighting
- [ ] faster loading

_Sorry about the messy code, this is my first real programming project and still wip.
Also, i have not yet tested it on any fan made jkls, but so far, it works on all original DF:JK 2
and MotS single and multiplayer level maps_
