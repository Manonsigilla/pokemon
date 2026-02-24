"""Script temporaire pour analyser les objets du TMX."""
import xml.etree.ElementTree as ET

tree = ET.parse("assets/maps/route01.tmx")
root = tree.getroot()

for g in root.findall(".//objectgroup"):
    print(f"GROUP: {g.get('name')}")
    for o in g.findall("object"):
        cls = o.get("class", o.get("type", ""))
        x = float(o.get("x", 0))
        y = float(o.get("y", 0))
        print(f"  name={o.get('name')}, class={cls}, x={x:.0f}, y={y:.0f}")
