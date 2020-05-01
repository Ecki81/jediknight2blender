### Addon for blender 2.8

## Import Jedi Knight: Dark Forces 2 level files (.jkl) into blender 2.8

This script needs the original JK:DF2 or MotS container files (_.gob/.goo_)
to be unpacked into the same file structure as found in the container files themselves.
You need to use a container file manager like CONMAN.exe to unpack the .gob files inside the
games folder _'Episode'_ and _'Resource'_
For example, if the file JK1.GOB is inside the folder _'Episode'_, create a folder named
_'JK1'_ inside _'Episode'_. Create a _'jkl'_ folder inside _'JK1'_ and unpack all files from _'jkl'_
inside _JK1.GOB_ into that.
Do the same with all the files in _Resource/Res2.gob_.


Install downloaded/cloned and zipped repo files as an addon to blender:
Open Blender -> Edit -> Preferences -> Add-ons -> Install and select the zip


To open a Jedi Knight: Dark Forces 2 level file, go to -> File -> Import -> JK/MotS level
Depending on your hardware, it may take the script a while to import files larger than 1MB.

## Tasks

- [x] read in jkl
- [x] read in 3do
- [x] read in basic mat
- [x] place 3do in levels
- [x] texturing levels
- [x] texturing 3do
- [x] resolve 3do hierarchy and parenting
- [ ] parse GOB/GOO
 


_Sorry about the messy code, this is my first real programming project and still wip_ :P