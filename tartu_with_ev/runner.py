import os
import sys
if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
import traci
import traci.constants as tc

from sumolib import checkBinary  # noqa
import xml.etree.ElementTree as ET
sumoBinary = checkBinary('sumo')
sumoCmd = [sumoBinary, "-c", "osm.sumocfg"]

def getIds_EV():
    # Parse the XML file
    tree = ET.parse('car.ev.trips.xml')
    root = tree.getroot()
    # Find elements with 'type' attribute equal to 'soulEV65'
    soulEV65_ids = [elem.get('id') for elem in root.findall(".//trip[@type='soulEV65']")]
    return soulEV65_ids


traci.start(sumoCmd)
soulEV65_ids = getIds_EV()

step = 0
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    try:
        if (step > 5):
            #print(float(traci.vehicle.getParameter("2", "device.battery.totalEnergyConsumed")))
            #print(float(traci.vehicle.getParameter("2", "device.battery.energyConsumed")))
            print(float(traci.vehicle.getParameter("2", "device.battery.actualBatteryCapacity")))
    except:
        break
    step += 1

traci.close()
