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
            '<3f4B',   #03: x,y,z,D8888,...
            '<3f1I',   #04: x,y,z,UserFlags32, ...
            '<3f1I',   #05: x,y,z,NinjaFlags32,...
            '<3f2H',   #06: x,y,z,D565|S565,...
            '<3f2H',   #07: x,y,z,D4444|S565,...
            '<3f2H',   #08: x,y,z,D16|S16,...
            # float vertex normal
            '<6f',     #09: x,y,z,nx,ny,nz, ...
            '<6f4B',   #10: x,y,z,nx,ny,nz,D8888,...
            '<6f1I',   #11: x,y,z,nx,ny,nz,UserFlags32,...
            '<6f1I',   #12: x,y,z,nx,ny,nz,NinjaFlags32,...
            '<6f2H',   #13: x,y,z,nx,ny,nz,D565|S565,...
            '<6f2H',   #14: x,y,z,nx,ny,nz,D4444|S565,...
            '<6f2H',   #15: x,y,z,nx,ny,nz,D16|S16,...
            # 32bits vertex normal  reserved(2)|x(10)|y(10)|z(10)
            '<3f1I',   #16: x,y,z,nxyz32, ...
            '<3f4B',   #17: x,y,z,nxyz32,D8888,...
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
        #print('Vertex Type:{0:#04X} Vertex Adr: {1:#010X}'.format(vtx_type, file.tell()))
        if (vtx_type > 18):
            return True
        fmt = self.formats[vtx_type]
        bytes = file.read(struct.calcsize(fmt))
        buff = struct.unpack_from(fmt, bytes, 0)
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
        self.length = 0x00 # nbIndices
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
        self.length = buff[4]
        #print('value: "count_vertex" {0:#X}'.format(count_vertex))
        #print('value: "end_adr" {0:#X}'.format(end_adr))
        for i in range(self.length):
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
class StripElement:
    fmt1 = '<1H'
    fmt2 = '<3H'
    fmt3 = '<1H3h'
    fmt4 = '<3H3h'
    fmt5 = '<1H4B'
    fmt6 = '<3H4B'
    fmt7 = '<5H'
    fx_UV = 0xFF
    fx_UVH = 0x40
    fx_VN = 0x8000
    fx_D8 = 0xFF
    
    formats = [
                fmt1, fmt2, fmt2, #0-2
                fmt3, fmt4, fmt4, #3-5
                fmt5, fmt6, fmt6, #6-8
                fmt1, fmt7, fmt7  #9-11
              ]
    
    def __init__(self):
        self.idx = 0x00
        self.uv = [0.0, 0.0]
        self.uv2 = [0.0, 0.0]
        self.normal = [0.0, 0.0, 0.0]
        self.color = [0.0, 0.0, 0.0, 0.0]
        self.user_flag2 = 0x00
        
    def unpack(self, file: typing.IO, strip_type: int, n: int) -> bool:
        if (strip_type > 12 or strip_type > 1):
            print('Detect Unallowing Strip Type: {0}'.format(strip_type))
            return True
        fmt = self.formats[strip_type]
        bytes = file.read(struct.calcsize(fmt))
        buff = struct.unpack_from(fmt, bytes, 0)
        
        if (strip_type == 0):
            self.idx = buff[0]
        elif (strip_type == 1):
            self.idx = buff[0]
            self.uv = [buff[1]/self.fx_UV, buff[2]/self.fx_UV]
        elif (strip_type == 2):
            self.idx = buff[0]
            self.uv = [buff[1]/self.fx_UVH, buff[2]/self.fx_UVH]
        elif (strip_type == 3):
            self.idx = buff[0]
            self.normal = [buff[1]/self.fx_VN, buff[2]/self.fx_VN, buff[3]/self.fx_VN]
        elif (strip_type == 4):
            self.idx = buff[0]
            self.uv = [buff[1]/self.fx_UV, buff[2]/self.fx_UV]            
            self.normal = [buff[3]/self.fx_VN, buff[4]/self.fx_VN, buff[5]/self.fx_VN]
        elif (strip_type == 5):
            self.idx = buff[0]
            self.uv = [buff[1]/self.fx_UVH, buff[2]/self.fx_UVH]            
            self.normal = [buff[3]/self.fx_VN, buff[4]/self.fx_VN, buff[5]/self.fx_VN]
        elif (strip_type == 6):
            self.idx = buff[0]
            slef.color = [buff[1]/self.fx_D8, buff[2]/self.fx_D8, buff[3]/self.fx_D8, buff[4]/self.fx_D8]
        elif (strip_type == 7):
            self.idx = buff[0]
            self.uv = [buff[1]/self.fx_UV, buff[2]/self.fx_UV]
            slef.color = [buff[3]/self.fx_D8, buff[4]/self.fx_D8, buff[5]/self.fx_D8, buff[6]/self.fx_D8]
        elif (strip_type == 8):
            self.idx = buff[0]
            self.uv = [buff[1]/self.fx_UV, buff[2]/self.fx_UV]
            slef.color = [buff[3]/self.fx_D8, buff[4]/self.fx_D8, buff[5]/self.fx_D8, buff[6]/self.fx_D8]
        elif (strip_type == 9):
            self.idx = buff[0]
        elif (strip_type == 10):
            self.idx = buff[0]
            self.uv = [buff[1]/self.fx_UV, buff[2]/self.fx_UV]
            self.uv2 = [buff[3]/self.fx_UV, buff[4]/self.fx_UV]
        elif (strip_type == 11):
            self.idx = buff[0]
            self.uv = [buff[1]/self.fx_UVH, buff[2]/self.fx_UVH]
            self.uv2 = [buff[3]/self.fx_UVH, buff[4]/self.fx_UVH]
        return False

class Strip:
    fmt = '<1h'
    
    def __init__(self):
        self.flag = 0x00
        self.length = 0x00
        self.elements = []
    
    def unpack(self, file: typing.IO, strip_type: int) -> bool:
        #print('Strip Type:{0:#04X} Strip Adr: {1:#010X}'.format(strip_type, file.tell()))
        bytes = file.read(struct.calcsize(self.fmt))
        buff = struct.unpack_from(self.fmt, bytes, 0)
        self.flag = (buff[0]&0xC000)>>14
        self.length = abs(buff[0])
        #print('Strip Element Length:{0:#010X} Strip Adr: {1:#010X}'.format(self.length, file.tell()))
        
        for i in range(self.length):
            element = StripElement()
            result = element.unpack(file, strip_type, 0) # How do I get "N" values?
            if result:
                return True
            self.elements.append(element)
        return False

# Chunk Strip (0x40 - 0x4B)
class ChunkStrip:
    fmt = '<2B2H'

    def __init__(self):
        self.chunk_flags = 0x00
        self.chunk_head = 0x00
        self.size = 0x00
        self.user_offset = 0x00
        self.length = 0x00 # nbStrip
        self.strips = []

    def unpack(self, file: typing.IO) -> None:
        bytes = file.read(struct.calcsize(self.fmt))
        buff = struct.unpack_from(self.fmt, bytes, 0)
        self.size = buff[2]
        self.user_offset = ((buff[3] & 0xC000) >> 14)
        self.length = buff[3] & 0x3FFF
        end_adr = file.tell() + (self.size-1) * 2
        #print('{0:#0X}'.format(end_adr))

        strip_type = buff[0]-0x40
        for i in range(self.length):
            if (file.tell() > end_adr):
                return True
            strip = Strip()
            result = strip.unpack(file, strip_type)
            if result:
                return True
            self.strips.append(strip)
        left_bytes = file.tell()%4
        if (left_bytes != 0):
            file.seek(left_bytes, io.SEEK_CUR)
        if( file.tell() < end_adr):
            return True
        return False


class Mesh:
    def __init__(self):
        self.chunk_tinys = []
        self.chunk_materials = []
        self.vertexs = []
        self.chunk_volumes = []
        self.chunk_strips = []

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
                self.chunk_tinys.append(tiny)
            elif ( (chunk_head >= 0x10) and (chunk_head <= 0x1F) ):
                # Material
                material = Material()
                material.unpack(file)
                self.chunk_materials.append(material)
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
                self.chunk_volumes.append(volume)
            elif ( (chunk_head >= 0x40) and (chunk_head <= 0x4B) ):
                # ChunkStrip
                strip = ChunkStrip()
                result = strip.unpack(file)
                if result:
                    return True
                self.chunk_strips.append(strip)
            else:
                print('Detect Unknown Chunk Head')
                print('--- Chunk Head: {0:#04X} Chunk Adr: {1:#010X} ---'.format(chunk_head, file.tell()))
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
            print('Unpack Chunk Faild!!! File Position: {0:#X}'.format(file.tell()))
            return True
        self.meshs.append(mesh)
        
        #print('--- Vertex Adr: {0:#X} ---'.format(file.tell()))
        #vtx = Mesh()
        result = self.vertex.unpack(file, max_chunk_count)
        if result:
            print('Unpack Vertex Unpack Faild!!! File Position: {0:#X}'.format(file.tell()))
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
#offset = 0x6530
#max_polygon_count = 16
offset = 0x134
max_polygon_count = 99
#offset = 0x39EC
#max_polygon_count = 1

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
    idxs = []
    vtxs = []
    #print('vertex count:{0}'.format(len(polygon.vertex.vertexs[0].elements)))
    for vtx in polygon.vertex.vertexs[0].elements:
        v = bm.verts.new(vtx.position)
        vtxs.append(v)

    if(len(polygon.meshs[0].chunk_strips) < 1):
        continue
    for i, strip in enumerate(polygon.meshs[0].chunk_strips[0].strips):
        is_cw = strip.flag > 1
        for vtx_cnt, element in enumerate(strip.elements):
            #Generate Face
            if vtx_cnt > 1:
                #print('is_cs: {0}'.format(is_cw))
                v2 = vtxs[element.idx]
                if is_cw == True:
                    face = bm.faces.new((v2, v1, v0))
                    is_cw = False
                else:
                    face = bm.faces.new((v0, v1, v2))
                    is_cw = True
                #face.material_index = idx
                #if vtx_cnt == 2:
                    ##compare blender face and rrv model normal
                    #_normals = mesh_data.normals[-3:]
                    #_face_normal = sum(_normals, mathutils.Vector()) / 3.0
                    #_bl_face_normal = mathutils.geometry.normal(v0.co, v1.co, v2.co)
                    #dot_res = _bl_face_normal.dot(_face_normal)
                    #if (dot_res < 0):
                    #    #flipping generated face
                    #    face.normal_flip()
                    #    #inversing next faces
                    #    is_cw = False if is_cw else True
                v0 = v1
                v1 = v2
            elif vtx_cnt == 1:
                v1 = vtxs[element.idx]
            elif vtx_cnt == 0:
                v0 = vtxs[element.idx]
            idxs.append(element.idx)




    #print(idxs)
    #for i in range(len(idxs)):
    #    if((i+3) > len(idxs)):
    #        break
    #    v0 = vtxs[idxs[i]]
    #    v1 = vtxs[idxs[i+1]]
    #    v2 = vtxs[idxs[i+2]]
    #    bm.faces.new((v0, v1, v2))

    
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
