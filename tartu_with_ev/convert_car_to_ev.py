import xml.etree.ElementTree as ET
import random

tree = ET.parse("osm.passenger.trips.xml")
root = tree.getroot()

soulEV65 = "soulEV65"

trip_elements = root.findall('.//trip')
random.shuffle(trip_elements)

ev_share = 0.5
num_ev = int(len(trip_elements) * ev_share)
for i in range(num_ev):
    trip_elements[i].set('type', soulEV65)


tree.write('car.ev.trips.xml')
