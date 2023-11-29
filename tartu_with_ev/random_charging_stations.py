import xml.etree.ElementTree as ET
import gzip
import random

with gzip.open('charging.stations.xml.gz', 'rt') as xml:
        tree = ET.parse(xml)
#tree = ET.parse("")

root = tree.getroot()

soulEV65 = "soulEV65"

trip_elements = root.findall('.//trip')
random.shuffle(trip_elements)

ev_share = 0.15
num_charging_stations = 15 #int(len(trip_elements) * ev_share)
for i in range(num_charging_stations):
    # get random location.
    # add charging station.
    param_element = ET.Element('param', {'key': 'actualBatteryCapacity', 'value': str(battery)})
    trip_elements[i].append(param_element)

with gzip.open('charging.stations.xml.gz', 'w') as xml:
    tree.write(xml)