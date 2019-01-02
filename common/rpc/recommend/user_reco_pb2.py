# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: user_reco.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='user_reco.proto',
  package='',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n\x0fuser_reco.proto\"T\n\x04User\x12\x0f\n\x07user_id\x18\x01 \x01(\t\x12\x12\n\nchannel_id\x18\x02 \x01(\x05\x12\x13\n\x0b\x61rticle_num\x18\x03 \x01(\x05\x12\x12\n\ntime_stamp\x18\x04 \x01(\x05\"2\n\x07\x41rticle\x12\x12\n\narticle_id\x18\x01 \x01(\x05\x12\x13\n\x0b\x61rticle_num\x18\x02 \x01(\x05\"E\n\x06param2\x12\r\n\x05\x63lick\x18\x01 \x01(\t\x12\x0f\n\x07\x63ollect\x18\x02 \x01(\t\x12\r\n\x05share\x18\x03 \x01(\t\x12\x0c\n\x04read\x18\x04 \x01(\t\"5\n\x06param1\x12\x12\n\narticle_id\x18\x01 \x01(\x05\x12\x17\n\x06params\x18\x02 \x01(\x0b\x32\x07.param2\"J\n\x05Track\x12\x10\n\x08\x65xposure\x18\x01 \x01(\t\x12\x1b\n\nrecommends\x18\x02 \x03(\x0b\x32\x07.param1\x12\x12\n\ntime_stamp\x18\x03 \x01(\x05\"\x1d\n\x07Similar\x12\x12\n\narticle_id\x18\x01 \x03(\x05\x32]\n\rUserRecommend\x12!\n\x0euser_recommend\x12\x05.User\x1a\x06.Track\"\x00\x12)\n\x11\x61rticle_recommend\x12\x08.Article\x1a\x08.Similar\"\x00\x62\x06proto3')
)




_USER = _descriptor.Descriptor(
  name='User',
  full_name='User',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='user_id', full_name='User.user_id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='channel_id', full_name='User.channel_id', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='article_num', full_name='User.article_num', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='time_stamp', full_name='User.time_stamp', index=3,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=19,
  serialized_end=103,
)


_ARTICLE = _descriptor.Descriptor(
  name='Article',
  full_name='Article',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='article_id', full_name='Article.article_id', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='article_num', full_name='Article.article_num', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=105,
  serialized_end=155,
)


_PARAM2 = _descriptor.Descriptor(
  name='param2',
  full_name='param2',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='click', full_name='param2.click', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='collect', full_name='param2.collect', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='share', full_name='param2.share', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='read', full_name='param2.read', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=157,
  serialized_end=226,
)


_PARAM1 = _descriptor.Descriptor(
  name='param1',
  full_name='param1',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='article_id', full_name='param1.article_id', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='params', full_name='param1.params', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=228,
  serialized_end=281,
)


_TRACK = _descriptor.Descriptor(
  name='Track',
  full_name='Track',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='exposure', full_name='Track.exposure', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='recommends', full_name='Track.recommends', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='time_stamp', full_name='Track.time_stamp', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=283,
  serialized_end=357,
)


_SIMILAR = _descriptor.Descriptor(
  name='Similar',
  full_name='Similar',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='article_id', full_name='Similar.article_id', index=0,
      number=1, type=5, cpp_type=1, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=359,
  serialized_end=388,
)

_PARAM1.fields_by_name['params'].message_type = _PARAM2
_TRACK.fields_by_name['recommends'].message_type = _PARAM1
DESCRIPTOR.message_types_by_name['User'] = _USER
DESCRIPTOR.message_types_by_name['Article'] = _ARTICLE
DESCRIPTOR.message_types_by_name['param2'] = _PARAM2
DESCRIPTOR.message_types_by_name['param1'] = _PARAM1
DESCRIPTOR.message_types_by_name['Track'] = _TRACK
DESCRIPTOR.message_types_by_name['Similar'] = _SIMILAR
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

User = _reflection.GeneratedProtocolMessageType('User', (_message.Message,), dict(
  DESCRIPTOR = _USER,
  __module__ = 'user_reco_pb2'
  # @@protoc_insertion_point(class_scope:User)
  ))
_sym_db.RegisterMessage(User)

Article = _reflection.GeneratedProtocolMessageType('Article', (_message.Message,), dict(
  DESCRIPTOR = _ARTICLE,
  __module__ = 'user_reco_pb2'
  # @@protoc_insertion_point(class_scope:Article)
  ))
_sym_db.RegisterMessage(Article)

param2 = _reflection.GeneratedProtocolMessageType('param2', (_message.Message,), dict(
  DESCRIPTOR = _PARAM2,
  __module__ = 'user_reco_pb2'
  # @@protoc_insertion_point(class_scope:param2)
  ))
_sym_db.RegisterMessage(param2)

param1 = _reflection.GeneratedProtocolMessageType('param1', (_message.Message,), dict(
  DESCRIPTOR = _PARAM1,
  __module__ = 'user_reco_pb2'
  # @@protoc_insertion_point(class_scope:param1)
  ))
_sym_db.RegisterMessage(param1)

Track = _reflection.GeneratedProtocolMessageType('Track', (_message.Message,), dict(
  DESCRIPTOR = _TRACK,
  __module__ = 'user_reco_pb2'
  # @@protoc_insertion_point(class_scope:Track)
  ))
_sym_db.RegisterMessage(Track)

Similar = _reflection.GeneratedProtocolMessageType('Similar', (_message.Message,), dict(
  DESCRIPTOR = _SIMILAR,
  __module__ = 'user_reco_pb2'
  # @@protoc_insertion_point(class_scope:Similar)
  ))
_sym_db.RegisterMessage(Similar)



_USERRECOMMEND = _descriptor.ServiceDescriptor(
  name='UserRecommend',
  full_name='UserRecommend',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  serialized_start=390,
  serialized_end=483,
  methods=[
  _descriptor.MethodDescriptor(
    name='user_recommend',
    full_name='UserRecommend.user_recommend',
    index=0,
    containing_service=None,
    input_type=_USER,
    output_type=_TRACK,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='article_recommend',
    full_name='UserRecommend.article_recommend',
    index=1,
    containing_service=None,
    input_type=_ARTICLE,
    output_type=_SIMILAR,
    serialized_options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_USERRECOMMEND)

DESCRIPTOR.services_by_name['UserRecommend'] = _USERRECOMMEND

# @@protoc_insertion_point(module_scope)
