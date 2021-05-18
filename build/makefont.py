import os
import pathlib
import json
import time

from svgpathtools import parse_path
from io import StringIO
import xml.etree.cElementTree as ET

definition = json.loads(open('build/RebbleIcons.json').read())

existing_files = []
last_id = 0xe800
addon = ''
json_addon = "\n    \"{glyph_id}\": {{ \"src\": \"{glyph_name}\", \"width\": 1000 }},"
dart = ''
dart_addon = "\n  static const IconData {glyph_name} = IconData({glyph_id}, fontFamily: _kFontFam, fontPackage: _kFontPkg);"

for k,v in definition['glyphs'].items():
  existing_files.append(v['src'])
  last_id = hex(int(k, 16))
  dart += dart_addon.format(glyph_id = k, glyph_name = v['src'][0:-4])

if not os.path.isdir("exported/"):
  os.mkdir("exported/")

for sizedir in [f for f in os.listdir() if f.endswith('px')]:
  for filename in [f for f in os.listdir(sizedir) if f.endswith('.svg')]:
    current_file = os.path.join(sizedir, filename)
    size = int(sizedir[0:-2])
    name = filename[0:-4].lower().replace(' ', '_')
    if size != 25:
      name += str(size)
    export_file = os.path.join("exported", name + ".svg")
    export_file_background = os.path.join("exported", name + "_background.svg")
    cmd = "inkscape --batch-process --verb=\"EditSelectAll;StrokeToPath;SelectionUnGroup;SelectionUnGroup;SelectionUnGroup;SelectionUnGroup;EditSelectNext;EditSelectSameFillColor;SelectionUnion;EditSelectNext;EditSelectSameFillColor;SelectionUnion;\" -o {export_file} \"{import_file}\""
    os.system(cmd.format(export_file = export_file, import_file = current_file))

    ET.register_namespace("", "http://www.w3.org/2000/svg")

    xml = open(export_file)
    it = ET.iterparse(StringIO(xml.read()))
    for _, el in it:
      _, _, el.tag = el.tag.rpartition('}')
    root = it.root

    allpaths = ''
    for elem in root.findall('.//path'):
        allpaths += elem.attrib.get('d')
    
    path = parse_path(allpaths)
    bbox = path.bbox()

    scale = 1000 / size
    original_width = (bbox[1] - bbox[0])
    width = original_width * scale
    original_height = (bbox[3] - bbox[2])
    height = original_height * scale
    offset_x = ((width - original_width) / 2) + (bbox[0] * (scale - 1))
    offset_y = ((height - original_height) / 2) + (bbox[2] * (scale - 1))
    cmd = "inkscape --actions=\"select-all;transform-scale:{scale};transform-translate:{translate_x},{translate_y}\" -o {export_file} {export_file}"
    scale = (width - original_width)
    if ((height - original_height) > scale):
      scale = (height - original_height) # Yeah, I don't understand why inkscape does it like that either
    os.system(cmd.format(scale = scale, translate_x = offset_x, translate_y = offset_y, export_file = export_file, import_file = current_file))

    xml = open(export_file)
    it = ET.iterparse(StringIO(xml.read()))
    for _, el in it:
      _, _, el.tag = el.tag.rpartition('}')
    root = it.root
    
    stroke = ''
    fill = ''
    for elem in root.findall('.//path'):
      if 'fill:#000000' in elem.attrib.get('style'):
        stroke += elem.attrib.get('d')
      if 'fill:#ffffff' in elem.attrib.get('style'):
        fill += elem.attrib.get('d')

    svg = ET.Element('svg')
    svg.set('viewBox', '0 0 1000 1000')
    svg.set('width', '1000')
    svg.set('height', '1000')
    child = ET.SubElement(svg, 'path')

    if stroke:
      child.set('d', stroke)
      f = open(export_file, 'w')
      f.write(ET.tostring(svg).decode('utf-8'))
      f.close()
      if not name + ".svg" in existing_files:
        last_id += 1
        addon += json_addon.format(glyph_id = hex(last_id), glyph_name = name + ".svg")

    if fill:
      svg.remove(child)
      child = ET.SubElement(svg, 'path')
      child.set('d', fill)
      f = open(export_file_background, 'w')
      f.write(ET.tostring(svg).decode('utf-8'))
      f.close()
      if not name + "_background.svg" in existing_files:
        last_id += 1
        addon += json_addon.format(glyph_id = hex(last_id), glyph_name = name + "_background.svg")


if addon:
  print("Add the following lines to RebbleIcons.json to have the glyphs appear in the font")
  print("(Don't forget about the comma on the current last line!)")
  print(addon[0:-1])
else:
  f = open('rebble_icons.dart', 'w')
  f.write(open('build/rebble_icons.template').read().replace('%REPLACE%', dart))
  f.close()
  os.system("build/svgs2ttf build/RebbleIcons.json")
