# Teragon POI Parser, v2
#
# Python script for scraping POI xml and generating the input for Teragon's "Read POI Property List" command.
# Requires Python3
#
# It will ask for a directory, and it crawl all subdirectories.
# Check the console for any issues - bad prefab tags will be reported there.
#
# - grumpybeard, January 2023

# CONFIGURATION

# Output file name.  The script will place this in the same directory in which it is run.
output_file = "teragon poi list.txt"

# Any files to explore.  Uses regex matching for flexibility. 
# .xml suffix is assumed and can be left off.
# Examples:
# "deco_.*" will skip any file that starts with deco_
# "DFalls_DemonPortal" will *only* skip a file named exactly "DFalls_DemonPortal.xml"
skip_files = ["deco_.*", "DFalls_DemonPortal"]

# Any directories to ignore. Uses regex matching for flexibility.
skip_dirs = ["CustomWorldPOIs","WWM Vanilla POIs"]  # "WWM .* POIs" would also work for the latter example

###########################################################################################

import os
import re
import xml.etree.ElementTree as ET
from tkinter import filedialog as fd
from pathlib import Path

selfpath = Path(__file__).parent
rootpath = fd.askdirectory()
output = ""

rootdir,targetdir = os.path.split(os.path.normpath(rootpath))
print("Walking Directory: %s" % (targetdir))

#walk through the target directory
for root, dirs, files in os.walk(rootpath):
    path, current_directory = os.path.split(root)
    relpath = root.split(targetdir)

    # Compare with our list of patterns to skip.
    dir_match = [d for d in skip_dirs if re.search("^"+d+"$", current_directory) is not None]
    if dir_match != []:
        print("INF: Skipping directory:",targetdir+relpath[1])
    else:
        print("Entering directory:",targetdir+relpath[1])

        city_pois, wilderness_pois, rwg_tiles = [],[],[]

        for file in files:
            if file.endswith(".xml"):
                # Compare with our list of patterns to skip.
                file_match = [f for f in skip_files if re.search("^"+f+"\.xml$", file) is not None]
                if file_match != []:
                    print("INF: Skipping file:",file)

                else:
                    poi_name = file.split(".")[0]
                    poitree = ET.parse( root+'/'+file)
                    poiroot = poitree.getroot()

                    if poiroot.tag != 'prefab':
                        # Not a POI.  Skip it.
                        continue

                    yoffset, x, y, z, rot, biomes, tags = "","","","","","",""
                    for property in poiroot:
                        match property.get('name'):
                            case "RotationToFaceNorth":rot = property.get('value')
                            case "AllowedBiomes":biomes = property.get('value')
                            case "PrefabSize":
                                dims = property.get('value')
                                if len(dims.split(",")) == 3: 
                                    x = dims.split(",")[0].strip()
                                    y = dims.split(",")[1].strip()
                                    z = dims.split(",")[2].strip()
                            case "YOffset":yoffset = property.get('value')
                            case "Tags":tags = property.get('value')

                    if x=='' or y=='' or z=='':
                        # POI not sized correctly, skip it.
                        print("WRN: %s, %s has bad or no PrefabSize tag.  Skipping." % (poi_name, poiroot.tag))
                        continue
                    
                    if yoffset=='':
                        # POI missing YOffset, skip it.
                        print("WRN: %s, %s has bad or no YOffset tag.  Skipping." % (poi_name, poiroot.tag))
                        continue

                    # Adjust distance for large wilderness pois
                    # Default 4.  64 for pois > 120 blocks in either x or z
                    # These values are rather arbitary and probably need better definition.
                    dist = 4 if max(int(x),int(z)) < 120 else 64

                    # set default biomes if not tagged
                    if biomes == '':
                        biomes = 'burnt,desert,forest,snow,wasteland'

                    if tags.lower().find("wilderness") >= 0:
                        # This is a wilderness POI
                        # name;rotation;yoffset;xyz;distance;biome;region;road
                        road = 'gravel'
                        region = 'default'    
                        wilderness_pois.append("%s;%s;%s;%s;%s;%s;%d;biomes:%s;region:%s;road:%s" % (poi_name, rot, yoffset, x, y, z, dist, biomes, region, road))

                    elif tags.lower().find("streettile") >= 0:
                        # This is an RWG tile
                        # name;rotation;yoffset;xyz;alone
                        rwg_tiles.append("%s;%s;%s;%s;%s;%s;alone" % (poi_name, rot, yoffset, x, y, z))

                    else:
                        # This is a normal (city) POI:
                        # name;rotation;yoffset;xyz;alone
                        city_pois.append("%s;%s;%s;%s;%s;%s;alone" % (poi_name, rot, yoffset, x, y, z))

        # end of directory walk
        total_pois = len(city_pois) + len(wilderness_pois) + len(rwg_tiles)
        if total_pois > 0:
            print("%d POIs recorded." % (total_pois))
            output += "//\n// --------- \\"+ targetdir+relpath[1] +"\\ ---------\n"
            output += "// %d Total POIs\n" % (total_pois)
            if city_pois != []:
                output += "// %d City POIs\n" % (len(city_pois))
                output += '\n'.join(city_pois) + '\n'
            if wilderness_pois != []:
                output += "// %d Wilderness POIs\n" % (len(wilderness_pois))
                output += '\n'.join(wilderness_pois) + '\n'
            if rwg_tiles != []:
                output += "// %d RWG Tiles\n" % (len(rwg_tiles))
                output += '\n'.join(rwg_tiles) + '\n'

f = open(selfpath / output_file, "w")
f.write(output)
f.close()
print("Finished")