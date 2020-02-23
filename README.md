# jediknight2blender
Addon for blender 2.8

Import Jedi Knight: Dark Forces 2 level files (.jkl) into blender 2.8

This script needs the original JK:DF2 or MotS container files (.gob/.goo)
to be unpacked into the same file structure as found in the container files themselves.
You need to use a container file manager like CONMAN.exe to unpack the .gob files inside the
games folder 'Episode' and 'Resource'
For example, if the file JK1.GOB is inside the folder 'Episode', create a folder named
'JK1' inside 'Episode'. Create a 'jkl' folder inside 'JK1' and unpack all files from 'jkl'
inside JK1.GOB into that.
Do the same with all the files in Resource/Res2.gob.


Install downloaded/cloned and zipped repo files as an addon to blender:
Open Blender -> Edit -> Preferences -> Add-ons -> Install and select the zip


To open a Jedi Knight: Dark Forces 2 level file, go to -> File -> Import -> JK/MotS level
Depending on your hardware, it may take the script a while to import files over 1MB
