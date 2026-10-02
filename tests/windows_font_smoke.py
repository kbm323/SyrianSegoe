"""Process-private Windows parser/glyph check; never registers system fonts.
Run with a locally built output directory, optionally a Variable face name.
"""
import ctypes,json,sys
from ctypes import wintypes as W
from pathlib import Path
from fontTools.ttLib import TTFont
G=ctypes.WinDLL('gdi32')
def signature(name,result,args):
 f=getattr(G,name);f.restype=result;f.argtypes=args;return f
add=signature('AddFontResourceExW',ctypes.c_int,[W.LPCWSTR,W.DWORD,ctypes.c_void_p])
remove=signature('RemoveFontResourceExW',W.BOOL,[W.LPCWSTR,W.DWORD,ctypes.c_void_p])
create_dc=signature('CreateCompatibleDC',W.HDC,[W.HDC])
create_font=signature('CreateFontW',W.HFONT,[ctypes.c_int]*5+[W.DWORD]*8+[W.LPCWSTR])
select=signature('SelectObject',W.HANDLE,[W.HDC,W.HANDLE])
delete=signature('DeleteObject',W.BOOL,[W.HANDLE])
delete_dc=signature('DeleteDC',W.BOOL,[W.HDC])
data=signature('GetFontData',W.DWORD,[W.HDC,W.DWORD,W.DWORD,ctypes.c_void_p,W.DWORD])
indices=signature('GetGlyphIndicesW',W.DWORD,[W.HDC,W.LPCWSTR,ctypes.c_int,ctypes.POINTER(W.WORD),W.DWORD])
chars=''.join(chr(cp) for cp in range(0xAC00,0xD7A4))+'한글 Windows 0123456789 ₩ → ㈜ ① 漢字'
results=[]
for path in sorted(Path(sys.argv[1]).glob('*.ttf')):
 with TTFont(path) as font:family=font['name'].getDebugName(1);weight=font['OS/2'].usWeightClass
 if len(sys.argv)>2 and path.name!='SegUIVar_system_mod.ttf':continue
 if path.name=='SegUIVar_system_mod.ttf':family=sys.argv[2] if len(sys.argv)>2 else 'Segoe UI Variable Text'
 full=str(path.resolve());count=add(full,0x10,None)
 if not count:raise RuntimeError('Windows rejected '+path.name)
 dc=None;handle=None;old=None
 try:
  dc=create_dc(None);handle=create_font(-20,0,0,0,weight,0,0,0,1,4,0,5,0,family)
  if not dc or not handle:raise RuntimeError('GDI creation failed')
  old=select(dc,handle)
  tag=int.from_bytes(b'name','little');length=data(dc,tag,0,None,0)
  if length==0xffffffff:raise RuntimeError('Name table unavailable')
  buffer=ctypes.create_string_buffer(length);data(dc,tag,0,buffer,length)
  if 'SyrianSegoe-Korean'.encode('utf-16-be') not in buffer.raw:
   raise RuntimeError('GDI selected the original instead of the private replacement: '+path.name+'; family '+family+'; private count '+str(count))
  glyphs=(W.WORD*len(chars))()
  if indices(dc,chars,len(chars),glyphs,1)==0xffffffff or any(g in (0,0xffff) for g in glyphs):
   raise RuntimeError('Windows glyph mapping failed: '+path.name)
  results.append({'file':path.name,'private_faces_loaded':count,'modern_hangul_gdi_mapped':11172,
                  'replacement_identity_confirmed':True,'selected_family':family})
 finally:
  if dc and old:select(dc,old)
  if handle:delete(handle)
  if dc:delete_dc(dc)
  if not remove(full,0x10,None):raise RuntimeError('Private cleanup failed')
print(json.dumps({'method':'Windows GDI FR_PRIVATE process-only; resources removed',
                  'global_registration_modified':False,'fonts':results},indent=2))
