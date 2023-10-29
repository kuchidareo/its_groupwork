import xml.etree.ElementTree as ET
import random

tree = ET.parse("osm.passenger.trips.xml")

root = tree.getroot()

soulEV65 = "soulEV65"

trip_elements = root.findall('.//trip')
random.shuffle(trip_elements)

ev_share = 0.15
num_ev = int(len(trip_elements) * ev_share)
for i in range(num_ev):
    trip_elements[i].set('type', soulEV65)

evConfig = '''<vType id="soulEV65" minGap="2.50" maxSpeed="29.06" color="white" accel="1.0" decel="1.0" sigma="0.0" emissionClass="Energy/unknown">
    <param key="has.battery.device" value="true"/>
    <param key="airDragCoefficient" value="0.35"/>       <!-- https://www.evspecifications.com/en/model/e94fa0 -->
    <param key="constantPowerIntake" value="100"/>       <!-- observed summer levels -->
    <param key="frontSurfaceArea" value="2.6"/>          <!-- computed (ht-clearance) * width -->
    <param key="internalMomentOfInertia" value="0.01"/>  <!-- guesstimate -->
    <param key="maximumBatteryCapacity" value="64000"/>
    <param key="maximumPower" value="150000"/>           <!-- website as above -->
    <param key="propulsionEfficiency" value=".98"/>      <!-- guesstimate value providing closest match to observed -->
    <param key="radialDragCoefficient" value="0.1"/>     <!-- as above -->
    <param key="recuperationEfficiency" value=".96"/>    <!-- as above -->
    <param key="rollDragCoefficient" value="0.01"/>      <!-- as above -->
    <param key="stoppingThreshold" value="0.1"/>         <!-- as above -->
    <param key="vehicleMass" value="1830"/>              <!-- 1682kg curb wt + average 2 passengers / bags -->
</vType>'''

evConfigXml = ET.fromstring(evConfig)

root.insert(0, evConfigXml)

tree.write('car.ev.trips.xml')