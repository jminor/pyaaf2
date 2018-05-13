from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )

from aaf2 import cfb, mobid

from uuid import UUID
from io import BytesIO
from struct import unpack
import pprint

from aaf2.utils import (
    read_u8,
    read_u16le,
    read_u32le,
    decode_utf16le,
    mangle_name
    )

MetaDictionary = UUID("0d010101-0225-0000-060e-2b3402060101")

CLASSDEFINITIONS_PID = 0x0003
TYPEDEFINITIONS_PID  = 0x0004

IDENTIFICATION_PID  = 0x0005
DESCRIPTION_PID     = 0x0007
NAME_PID            = 0x0006

TypeDefInt          = UUID("0d010101-0204-0000-060e-2b3402060101")
TypeDefInt_IsSigned = 0x0010
TypeDefInt_Size     = 0x000F

TypeDefStrongRef                = UUID("0d010101-0205-0000-060e-2b3402060101")
TypeDefStrongRef_ReferencedType = 0x0011

TypeDefWeakRef                = UUID("0d010101-0206-0000-060e-2b3402060101")
TypeDefWeakRef_ReferencedType = 0x0012
TypeDefWeakRef_TargetSet      = 0x0013

TypeDefEnum               = UUID("0d010101-0207-0000-060e-2b3402060101")
TypeDefEnum_ElementType   = 0x0014
TypeDefEnum_ElementValues = 0x0016
TypeDefEnum_ElementNames  = 0x0015

TypeDefFixedArray               = UUID("0d010101-0208-0000-060e-2b3402060101")
TypeDefFixedArray_ElementCount  = 0x0018
TypeDefFixedArray_ElementType   = 0x0017

TypeDefVariableArray             = UUID("0d010101-0209-0000-060e-2b3402060101")
TypeDefVariableArray_ElementType = 0x0019

TypeDefSet             = UUID("0d010101-020a-0000-060e-2b3402060101")
TypeDefSet_ElementType = 0x001A

TypeDefString             = UUID("0d010101-020b-0000-060e-2b3402060101")
TypeDefString_ElementType = 0x001B

TypeDefStream             = UUID("0d010101-020c-0000-060e-2b3402060101")

TypeDefRecord             = UUID("0d010101-020d-0000-060e-2b3402060101")
TypeDefRecord_MemberNames = 0x001D
TypeDefRecord_MemberTypes = 0x001C

TypeDefRename             = UUID("0d010101-020e-0000-060e-2b3402060101")
TypeDefRename_RenamedType = 0x001E

TypeDefExtendibleEnum               = UUID("0d010101-0220-0000-060e-2b3402060101")
TypeDefExtendibleEnum_ElementValues = 0x0020
TypeDefExtendibleEnum_ElementNames  = 0x001F

TypeDefIndirect                 = UUID("0d010101-0221-0000-060e-2b3402060101")
TypeDefOpaque                   = UUID("0d010101-0222-0000-060e-2b3402060101")
TypeDefCharacter                = UUID("0d010101-0223-0000-060e-2b3402060101")


ClassDef                           = UUID("0d010101-0201-0000-060e-2b3402060101")
ClassDef_ParentClass               = 0x0008
ClassDef_Properties                = 0x0009
ClassDef_IsConcrete                = 0x000A

PropertyDef                        = UUID("0d010101-0202-0000-060e-2b3402060101")
PropertyDef_Type                   = 0x000B
PropertyDef_IsOptional             = 0x000C
PropertyDef_LocalIdentification    = 0x000D
PropertyDef_IsUniqueIdentifier     = 0x000E

typedef_cats= ("ints", "enums", "records", "fixed_arrays", "var_arrays",
               "renames", "strings", "streams", "opaques", "extenums",
               "chars", "indirects", "sets", "strongrefs", "weakrefs")

def read_properties(entry):
    stream = entry.get('properties')
    if stream is None:
        raise Exception("can not find properties")

    s = stream.open()
    # read the whole stream
    f = BytesIO(s.read())

    byte_order = read_u8(f)
    if byte_order != 0x4c:
        raise NotImplementedError("be byteorder")
    version = read_u8(f)
    entry_count = read_u16le(f)

    props = []
    for i in range(entry_count):
        pid = read_u16le(f)
        format = read_u16le(f)
        byte_size = read_u16le(f)

        props.append([pid, format, byte_size])

    property_entries = {}
    for pid, format, byte_size in props:
        data = f.read(byte_size)
        property_entries[pid] = data

    return property_entries

def decode_weakref(data):
    f = BytesIO(data)
    weakref_index = read_u16le(f)
    key_pid = read_u16le(f)
    key_size = read_u8(f)
    assert key_size in (16, 32)
    if key_size == 16:
        ref = UUID(bytes_le=f.read(key_size))
    else:
        ref = key = MobID(bytes_le=f.read(key_size))
    return ref

def decode_auid_array(data):
    f = BytesIO(data)
    result = []

    while True:
        d = f.read(16)
        if not d:
            break

        if len(d) == 16:
            result.append(UUID(bytes_le=d))
        else:
            raise Exception("auid length wrong: %d" % len(d))

    return result

def decode_utf16_array(data):
    start = 0
    data = bytearray(data)
    result = []
    for i in range(0, len(data), 2):
        if data[i] == 0x00 and data[i+1] == 0x00:
            result.append(data[start:i].decode("utf-16le"))
            start = i+2
    return result

def read_set_index(entry):

    s = entry.open('r')
    # read the whole of the index
    f = BytesIO(s.read())

    count = read_u32le(f)
    next_free_key = read_u32le(f)
    last_free_key = read_u32le(f)
    key_pid = read_u16le(f)
    key_size = read_u8(f)
    assert key_size in (16, 32)

    references = []

    for i in range(count):
        local_key = read_u32le(f)
        ref_count = read_u32le(f)

        # not sure if ref count is actually used
        # doesn't apear to be
        assert ref_count == 1

        if key_size == 16:
            key = UUID(bytes_le=f.read(key_size))
        else:
            key = mobid.MobID(bytes_le=f.read(key_size))
        references.append((key, local_key))
        # references[key] = local_key

    return references

def read_weakref_array_index(entry):
    s = entry.open('r')
    # read the whole index
    f = BytesIO(s.read())

    count = read_u32le(f)
    weakref_index = read_u16le(f)
    key_pid = read_u16le(f)
    key_size = read_u8(f)
    assert key_size in (16, 32)
    references = []
    for i in range(count):
        if key_size == 16:
            key = UUID(bytes_le=f.read(key_size))
        else:
            key = key = MobID(bytes_le=f.read(key_size))
        references.append(key)
    return references

def read_typedef(entry, types):
    p  = read_properties(entry)
    name = decode_utf16le(p[NAME_PID])
    identification = UUID(bytes_le=p[IDENTIFICATION_PID])

    # description = decode_utf16le(p[DESCRIPTION_PID])
    # print(name, description)

    data = [identification]

    if entry.class_id == TypeDefInt:
        size = read_u8(BytesIO(p[TypeDefInt_Size]))
        signed = p[TypeDefInt_IsSigned] == b"\x01"
        data.extend([size, signed])
        types['ints'][name] = data

    elif entry.class_id == TypeDefStrongRef:
        ref_type = decode_weakref(p[TypeDefStrongRef_ReferencedType])
        data.extend([ref_type])
        types['strongrefs'][name] = data

    elif entry.class_id == TypeDefWeakRef:
        ref_type = decode_weakref(p[TypeDefWeakRef_ReferencedType])
        target_set = decode_auid_array(p[TypeDefWeakRef_TargetSet])
        data.extend([ref_type, target_set])
        types['weakrefs'][name] = data

    elif entry.class_id  == TypeDefEnum:
        type = decode_weakref(p[TypeDefEnum_ElementType])
        names = decode_utf16_array(p[TypeDefEnum_ElementNames])

        # aafInt64Array
        values = p[TypeDefEnum_ElementValues]
        size = 8
        elements = len(values)//size
        values = unpack('<%dq'% elements, values)

        data.extend([type, dict(zip(values, names))])
        types['enums'][name] = data

    elif entry.class_id == TypeDefFixedArray:
        # aafUInt32
        elements = read_u32le(BytesIO(p[TypeDefFixedArray_ElementCount]))
        type = decode_weakref(p[TypeDefFixedArray_ElementType])
        data.extend([type, elements])
        types['fixed_arrays'][name] = data

    elif entry.class_id == TypeDefVariableArray:
        type = decode_weakref(p[TypeDefVariableArray_ElementType])
        data.extend([type])
        types['var_arrays'][name] = data

    elif entry.class_id == TypeDefSet:
        type = decode_weakref(p[TypeDefSet_ElementType])
        data.extend([type])
        types['sets'][name] = data

    elif entry.class_id == TypeDefString:
        type = decode_weakref(p[TypeDefString_ElementType])
        data.extend([type])
        types['strings'][name] = data

    elif entry.class_id == TypeDefStream:
        types['streams'][name] = data

    elif entry.class_id == TypeDefRecord:
        member_names = decode_utf16_array(p[TypeDefRecord_MemberNames])
        member_index_name = decode_utf16le(p[TypeDefRecord_MemberTypes])
        member_types = read_weakref_array_index(entry.get(member_index_name + " index"))
        data.append(list(zip(member_names, member_types)))
        types['records'][name] = data

    elif entry.class_id == TypeDefRename:
        type = decode_weakref(p[TypeDefRename_RenamedType])
        data.extend([type])
        types['renames'][name] = data

    elif entry.class_id == TypeDefExtendibleEnum:
        element_values = decode_auid_array(p[TypeDefExtendibleEnum_ElementValues])
        element_names = decode_utf16_array(p[TypeDefExtendibleEnum_ElementNames])
        data.extend([dict(zip(element_values, element_names))])
        types['extenums'][name] = data

    elif entry.class_id == TypeDefIndirect:
        types['indirects'][name] = data
    elif entry.class_id == TypeDefOpaque:
        types['opaques'][name] = data
    elif entry.class_id == TypeDefCharacter:
        types['chars'][name] = data
    else:
        raise Exception()

def read_propertdef(entry):
    p  = read_properties(entry)
    name = decode_utf16le(p[NAME_PID])
    identification = UUID(bytes_le=p[IDENTIFICATION_PID])

    typedef =  UUID(bytes_le=p[PropertyDef_Type])
    is_optional = p[PropertyDef_IsOptional] == b"\x01"
    local_id = read_u16le(BytesIO(p[PropertyDef_LocalIdentification]))

    data = [identification, local_id, typedef, is_optional]

    if PropertyDef_IsUniqueIdentifier in p:
        is_unique = p[PropertyDef_IsUniqueIdentifier]  == b"\x01"
        data.append(is_unique)

    return name, data

def read_classdef(entry):
    p  = read_properties(entry)
    name = decode_utf16le(p[NAME_PID])
    identification = UUID(bytes_le=p[IDENTIFICATION_PID])
    parent_class = decode_weakref(p[ClassDef_ParentClass])
    is_concrete = p[ClassDef_IsConcrete] == b"\x01"
    data = [identification, parent_class, is_concrete]
    properties = {}
    if ClassDef_Properties in p:
        index_name = decode_utf16le(p[ClassDef_Properties])
        property_reference_keys = read_set_index(entry.get(index_name + " index"))
        # print(entry.listdir())
        for key, local_key in property_reference_keys:
            dirname = "%s{%x}" % (index_name, local_key)
            p_name, p_data = read_propertdef(entry.get(dirname))
            properties[p_name] = p_data

    data.append(properties)

    return name, data


def dump_model(path):

    with open(path, 'rb') as f:
        c = cfb.CompoundFileBinary(f, 'rb')
        metadict = None
        for item in c.listdir("/"):
            if item.class_id == MetaDictionary:
                metadict = item
                break
        if not metadict:
            raise Exception("can not find metadict")

        properties = read_properties(metadict)

        index_name = decode_utf16le(properties[CLASSDEFINITIONS_PID])
        class_reference_keys = read_set_index(metadict.get(index_name + " index"))

        index_name = decode_utf16le(properties[TYPEDEFINITIONS_PID])
        type_reference_keys = read_set_index(metadict.get(index_name + " index"))


        #TypeDefinitions
        index_name = mangle_name("TypeDefinitions", TYPEDEFINITIONS_PID, 32-10)

        typedefs = {}
        for key in typedef_cats:
            typedefs[key] = {}

        for key, local_key in class_reference_keys:
            dirname = "%s{%x}" % (index_name, local_key)
            read_typedef(metadict.get(dirname), typedefs)

        # for cat in typedef_cats:
        #     print(cat, "= ")
        #     pprint.pprint(typedefs[cat])
        #
        #ClassDefinitions
        index_name = mangle_name("ClassDefinitions", CLASSDEFINITIONS_PID, 32-10)

        classdefs = {}
        for key, local_key in class_reference_keys:
            dirname = "%s{%x}" % (index_name, local_key)
            class_name, class_data = read_classdef(metadict.get(dirname))
            classdefs[class_name] = class_data

        pprint.pprint(classdefs)






if __name__ == "__main__":
    import sys
    dump_model(sys.argv[1])
