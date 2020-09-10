from struct import *

class Gob:
    '''extract single files from GOB/GOO container file''',
    
    def __init__(self, gob_file):
        '''
        Initialize GOB / GOO container file
        '''
        f=open(gob_file,'rb') # open file for reading
        self.data = f.read()
        f.close()
        self.toc = {}
        self.jkls = []
        
    def get_toc(self):
        '''returns dict. key = filename, value = tuple(file offset from gob start, file length)'''
        first_size_offset, first_offset, file_count, offset, length = unpack('LLLLL', self.data[4:24])

        i = 0
        toc = {}
        while i < file_count:
            byte_offset = 24+i*136
            file_name = unpack('<128s', self.data[byte_offset:byte_offset+128])
            file_offset, length = unpack('LL', self.data[byte_offset-8:byte_offset])
            file_name = file_name[0].decode('ascii').split('\x00',1)[0] # bin to text, removed \x00
            file_name_clean = file_name.split('\\', 2)[-1]
            toc[file_name_clean] = (file_offset, length)
            i += 1
        
        self.toc = toc


    def ungob(self, file):
        '''takes string of file in GOB/GOO ("00tabl.3do"), returns extracted file'''
        # print("ungob() took \"", file, "\" string")
        self.get_toc()
        file_offset, length = self.toc[file]
        file_ungob = self.data[file_offset:file_offset+length]

        # print("returned file" , str(type(file_ungob)))

        return file_ungob

    def get_jkls(self):
        '''returns a list of jkl files names'''
        self.get_toc()
        for file in self.toc:
            print(file.keys())

        return jkl_list


# gob = Gob("D:/GalaxyClient/Games/Star Wars Jedi Knight - Dark Forces 2/Resource/Res2.gob")
# gob.ungob("yundead.3do")