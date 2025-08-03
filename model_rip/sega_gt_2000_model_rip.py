import array
import io
import typing
import mathutils
import struct

import bmesh
import bpy


# Ninja Chunk Format
# IF file has "NJCM"(Ninja Chank Model Tree) Magic I'll not write this code.

# Chunk Tiny (0x08 - 0x09)
class Tiny:
    fmt = '<4B'
    def __init__(self):
        self.flip_u = False
        self.flip_v = False
        self.clamp_u = False
        self.clamp_v = False
        self.mipmap_adjust = 0x00
        self.filter_mode = 0x00
        self.super_sample = 0x00
        self.TexId = 0x00

    def unpack(self, file: typing.IO) -> None:
        bytes = file.read(struct.calcsize(self.fmt))
        buff = struct.unpack_from(self.fmt, bytes, 0)
        # TDOO Store


# Material (0x10 - 0x1F)
class Material:
    def __init__(self):
        self.chunck_flags = 0x00
        self.chunk_head = 0x00
        self.size = 0x00

    fmt = '<1B'
    def unpack(self, file: typing.IO) -> bool:
        bytes = file.read(struct.calcsize(self.fmt))
        buff = struct.unpack_from(self.fmt, bytes, 0)
        # TDOO Store
        skip = 0x00
        if ((buff[0]&0xF) == 1):
            skip = 7
        elif ((buff[0]&0xF) == 3):
            skip = 11
        elif ((buff[0]&0xF) == 7):
            skip = 15
        else:
            return True
        file.seek(skip, io.SEEK_CUR)
        return False


class VertexElement:
    formats = [ # optimize for SH4
            '<4f',     #00: x,y,z,1.0F, ...              correct?
            '<8f',     #01: x,y,z,1.0F,nx,ny,nz,0.0F,... correct?

            '<3f',     #02: x,y,z, ...
            '<3f1I',   #03: x,y,z,D8888,...
            '<3f1I',   #04: x,y,z,UserFlags32, ...
            '<3f1I',   #05: x,y,z,NinjaFlags32,...
            '<3f2H',   #06: x,y,z,D565|S565,...
            '<3f2H',   #07: x,y,z,D4444|S565,...
            '<3f2H',   #08: x,y,z,D16|S16,...
            # float vertex normal
            '<6f',     #09: x,y,z,nx,ny,nz, ...
            '<6f1I',   #10: x,y,z,nx,ny,nz,D8888,...
            '<6f1I',   #11: x,y,z,nx,ny,nz,UserFlags32,...
            '<6f1I',   #12: x,y,z,nx,ny,nz,NinjaFlags32,...
            '<6f2H',   #13: x,y,z,nx,ny,nz,D565|S565,...
            '<6f2H',   #14: x,y,z,nx,ny,nz,D4444|S565,...
            '<6f2H',   #15: x,y,z,nx,ny,nz,D16|S16,...
            # 32bits vertex normal  reserved(2)|x(10)|y(10)|z(10)
            '<3f1I',   #16: x,y,z,nxyz32, ...
            '<3f2I',   #17: x,y,z,nxyz32,D8888,...
            '<3f2I'    #18: x,y,z,nxyz32,UserFlags32,...
          ]
    
    def __init__(self):
        self.position = [0.0, 0.0, 0.0]
        self.normal = [0.0, 0.0, 0.0]
        self.user_flag = 0x00
        self.ninja_flag = 0x00
        self.diffuse_color = [0.0, 0.0, 0.0, 0.0]
        self.specular_color = [0.0, 0.0, 0.0, 0.0]

    def unpack(self, file: typing.IO, vtx_type: int) -> bool:
        #print('Vertex Type:{0:#0X} Vertex Adr: {1:#010X}'.format(vtx_type, file.tell()))
        if (vtx_type > 18):
            return True
        _fmt = self.formats[vtx_type]
        bytes = file.read(struct.calcsize(_fmt))
        buff = struct.unpack_from(_fmt, bytes, 0)
        self.position = [buff[0], buff[1], buff[2]]
        return False
        
# Chunk Vertex
class Vertex:
    fmt = '<2B3H'
    def __init__(self):
        self.head_bits = 0x00 # NF NinjaFlags32 only
        self.chunk_head = 0x00
        self.size = 0x00 # needs "(this_value - 1) * 4" to byte size
        self.user_offset = 0x00
        self.elements = []

    def unpack(self, file: typing.IO) -> bool:
        bytes = file.read(struct.calcsize(self.fmt))
        buff = struct.unpack_from(self.fmt, bytes, 0)
        self.chunk_head = buff[0]
        #self.head_bits = buff[1] #?
        self.size = buff[2]
        self.user_offset = buff[3]
        end_adr = file.tell() + (self.size-1) * 4
        vtx_type = buff[0]-0x20
        count_vertex = buff[4]
        #print('value: "count_vertex" {0:#X}'.format(count_vertex))
        #print('value: "end_adr" {0:#X}'.format(end_adr))
        for i in range(count_vertex):
            if (file.tell() > end_adr):
                return True
            vtx = VertexElement()
            result = vtx.unpack(file, vtx_type)
            if result:
                return True
            self.elements.append(vtx)
        if( file.tell() < end_adr):
            return True
        return False
        

# Chunk Volume (0x38 - 0x3A)
class Volume:
    fmt = '<3H'
    def __init__(self):
        self.chunck_flags = 0x00
        self.chunk_head = 0x00
        self.size = 0x00
        self.user_offset = 0x00
        self.count_polygon = 0x00
        self.count_strip = 0x00
    
    def unpack(self, file: typing.IO):
        bytes = file.read(struct.calcsize(self.fmt))
        buff = struct.unpack_from(self.fmt, bytes, 0)
        # TDOO Store
        skip = (buff[1]-1)*2
        file.seek(skip, io.SEEK_CUR)
        return False


# Elment of "Chunk Strip"
class StripElemnt:
    def __init__(self):
        self.idx = 0x00
        self.uv = [0.0, 0.0]
        self.normal = [0.0, 0.0, 0.0]
        self.user_flag = 0x00

# Chunk Strip (0x40 - 0x4B)
class Strip:
    fmt = '<2B2H'

    def __init__(self):
        self.chunk_flags = 0x00
        self.chunk_head = 0x00
        self.size = 0x00
        self.user_offset = 0x00
        self.count_strip = 0x00 # nbStrip
        self.elments = []

    def unpack(self, file: typing.IO) -> None:
        bytes = file.read(struct.calcsize(self.fmt))
        buff = struct.unpack_from(self.fmt, bytes, 0)
        self.size = buff[2]
        self.user_offset = ((buff[3] & 0xC0) >> 14)
        self.count_strip = buff[3] & 0x3F
        end_adr = file.tell() + (self.size-1) * 4


        # TDOO: Store
        # TODO: unapck strip elemnts
        size = self.size
        #self.size = size
        skip = (size-1) * 2
        file.seek(skip, io.SEEK_CUR)


class Mesh:
    def __init__(self):
        self.tinys = []
        self.materials = []
        self.vertexs = []
        self.volumes = []
        self.strips = []

    # Chunk Head ... means "Sort of Commands".
    def detect_head(self, file: typing.IO) -> int:
        bytes = file.read(struct.calcsize('B'))
        buff = struct.unpack_from('B', bytes, 0)
        file.seek(-1, io.SEEK_CUR) # Go Back Head Parse
        return buff[0]

    def unpack(self, file: typing.IO, max_chunk_count: int) -> bool:
        i = 0
        while(True):
            if (i > max_chunk_count):
                # Force Terminate parsing
                print('Unpack is force terminated. Max:{0}'.format(max_chunk_count))
                return True
            chunk_head = self.detect_head(file)
            #print('Chunk Head: {0:#010X} Chunk Adr: {1:#010X}'.format(chunk_head, file.tell()))
            if ((chunk_head&0xFF) == 0xFF):
                # End of Chunk (means parsing is correct)
                file.seek(4, io.SEEK_CUR)
                return False
            elif ( (chunk_head >= 0x8) and (chunk_head <= 0x9) ):
                # Tiny
                tiny = Tiny()
                tiny.unpack(file)
                self.tinys.append(tiny)
            elif ( (chunk_head >= 0x10) and (chunk_head <= 0x1F) ):
                # Material
                material = Material()
                material.unpack(file)
                self.materials.append(material)
            elif ( (chunk_head >= 0x20) and (chunk_head <= 0x32) ):
                # Vertex
                vertex = Vertex()
                result = vertex.unpack(file)
                if result:
                    return True
                self.vertexs.append(vertex)
            elif ( (chunk_head >= 0x38) and (chunk_head <= 0x3A) ):
                # Volume
                volume = Volume()
                volume.unpack(file)
                self.volumes.append(volume)
            elif ( (chunk_head >= 0x40) and (chunk_head <= 0x4B) ):
                # Strip
                strip = Strip()
                strip.unpack(file)
                self.strips.append(strip)
            else:
                print('Detect Unknown Chunk Head')
                print('--- Chunk Head: {0:#010X} Chunk Adr: {1:#010X} ---'.format(file.tell(), chunk_head))
                return True
            i = i + 1


class Polygon:
    fmtHead = 'B'
    def __init__(self):
        self.meshs = []
        self.vertex = Mesh() 
   
    def unpack(self, file: typing.IO, max_chunk_count: int) -> bool:
        #print('--- Mesh Adr: {0:#X} ---'.format(file.tell()))
        mesh = Mesh()
        result = mesh.unpack(file, max_chunk_count)
        if result:
            print('Chunk Unpack Faild!!! File Position: {0:#X}'.format(file.tell()))
            return True
        self.meshs.append(mesh)
        
        #print('--- Vertex Adr: {0:#X} ---'.format(file.tell()))
        #vtx = Mesh()
        result = self.vertex.unpack(file, max_chunk_count)
        if result:
            print('Vertex Chunk Unpack Faild!!! File Position: {0:#X}'.format(file.tell()))
            return True
        return False


class Model:
    def __init__(self):
        self.polygons = []
    
    def unpack(self, file: typing.IO, skip: int, max_polygon_count: int, max_chunk_count) -> None:
        # Go to EOF
        file.seek(0x0, io.SEEK_END)
        file_max = file.tell()
        # Go to 1st Polygon
        file.seek(skip, io.SEEK_SET)
        
        #while (True):
        for i in range(max_polygon_count):
            if ( file.tell() >= file_max ):
                print('Parsing Ninja Chunks Done!')
                break
            #print('-- Polygon Adr: {0:#X} --'.format(file.tell()))
            polygon = Polygon()
            result = polygon.unpack(file, max_chunk_count)
            if result:
                break
            self.polygons.append(polygon)
        


# FACE(Parsing Strip) DEVLOP
offset = 0x6530
#for safe
max_polygon_count = 1
max_chunk_count = 1000
filename = r"format\carmodel\00000000_toppo_bj\00000000_toppo_bj.bin"


# CAR
#offset = 0x134
#for safe
#max_polygon_count = 60
#max_chunk_count = 1000
#filename = r"format\carmodel\00000000_toppo_bj\00000000_toppo_bj.bin"
#filename = r"format\carmodel\00000456_ralliart_gto\00000456_ralliart_gto.bin"

# COURSE
#offset = 0x1C20
##for safe
#max_polygon_count = 2000
#max_chunk_count = 1000
#filename = r"format\track\night_section_a_001\00000000\00000000.bin" # Night Section A
##filename = r"format\track\SonyGT2\00000152\00000000.bin" # SonyGT2
##filename = r"extract_empire\STR1\00000156\00000000.bin"

# Path
path = "D:\Hack\SEGA\segaGT\\" + filename

# open files
file = open(path, 'rb')

model = Model()
model.unpack(file, offset, max_polygon_count, max_chunk_count)

for i, polygon in enumerate(model.polygons):
    #break
    mesh_name = 'polygon_{0:04}'.format(i)
    #print("---- Generate {0} ---".format(mesh_name))
    bl_mesh = bpy.data.meshes.new(mesh_name)
    bl_obj = bpy.data.objects.new(mesh_name, bl_mesh)
    
    scene = bpy.context.scene
    bpy.context.collection.objects.link(bl_obj)
    bpy.context.view_layer.objects.active = bl_obj
    bl_obj.select_set(True)
    bl_mesh = bpy.context.object.data
    bm = bmesh.new()
    
    normals = []
    uvs = []
    #vertex
    vtxs = []
    #print('vertex count:{0}'.format(len(polygon.vertex.vertexs[0].elements)))
    for vtx in polygon.vertex.vertexs[0].elements:
        v = bm.verts.new(vtx.position)
        #vtxs.append(v)
        #normals.append(vtx.normal)
        #uvs.append(vtx.uv)

    bm.to_mesh(bl_mesh)
    bm.free()
    
    #break   
    continue
    
    # apply normal
    #clnors = array.array('f', [0.0] * (len(bl_mesh.loops) * 3))
    #bl_mesh.loops.foreach_get("normal", clnors)
    #bl_mesh.polygons.foreach_set("use_smooth", [True] * len(bl_mesh.polygons))
    
    #bl_mesh.use_auto_smooth = True
    #bl_mesh.normals_split_custom_set_from_vertices(normals)

    #uv
    channel_name = 'uv0'
    bl_mesh.uv_textures.new(channel_name) # 2.7
    for i, loop in enumerate(bl_mesh.loops):
        bl_mesh.uv_layers[channel_name].data[i].uv = uvs[loop.vertex_index]
