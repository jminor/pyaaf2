from __future__ import (
    unicode_literals,
    absolute_import,
    print_function,
    division,
    )
import traceback

from . import core
from . mobid import MobID
from uuid import UUID
from .utils import register_class

@register_class
class EssenceData(core.AAFObject):
    class_id = UUID("0d010101-0101-2300-060e-2b3402060101")

    @property
    def unique_key(self):
        return self.id

    @property
    def id(self):
        return self['MobID'].value

    @id.setter
    def id(self, value):
        self['MobID'].value = value

    def open(self, mode='r'):
        return self['Data'].open(mode)

@register_class
class EssenceDescriptor(core.AAFObject):
    class_id = UUID("0d010101-0101-2400-060e-2b3402060101")

    @property
    def locator(self):
        return self['Locator'].value

@register_class
class FileDescriptor(EssenceDescriptor):
    class_id = UUID("0d010101-0101-2500-060e-2b3402060101")

    @property
    def length(self):
        return self['Length'].value
    @length.setter
    def length(self, value):
        self['Length'].value = value

@register_class
class DigitalImageDescriptor(FileDescriptor):
    class_id = UUID("0d010101-0101-2700-060e-2b3402060101")

@register_class
class CDCIDescriptor(DigitalImageDescriptor):
    class_id = UUID("0d010101-0101-2800-060e-2b3402060101")

@register_class
class RGBADescriptor(DigitalImageDescriptor):
    class_id = UUID("0d010101-0101-2900-060e-2b3402060101")

    @property
    def pixel_layout(self):
        return self['PixelLayout'].value

@register_class
class TapeDescriptor(EssenceDescriptor):
    class_id = UUID("0d010101-0101-2e00-060e-2b3402060101")

@register_class
class SoundDescriptor(FileDescriptor):
    class_id = UUID("0d010101-0101-4200-060e-2b3402060101")

@register_class
class DataEssenceDescriptor(FileDescriptor):
    class_id = UUID("0d010101-0101-4300-060e-2b3402060101")

@register_class
class MultipleDescriptor(FileDescriptor):
    class_id = UUID("0d010101-0101-4400-060e-2b3402060101")

@register_class
class PCMDescriptor(SoundDescriptor):
    class_id = UUID("0d010101-0101-4800-060e-2b3402060101")

@register_class
class PhysicalDescriptor(EssenceDescriptor):
    class_id = UUID("0d010101-0101-4900-060e-2b3402060101")

@register_class
class ImportDescriptor(PhysicalDescriptor):
    class_id = UUID("0d010101-0101-4a00-060e-2b3402060101")
