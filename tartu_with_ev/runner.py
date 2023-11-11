import os
import sys
if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
import traci

from sumolib import checkBinary  # noqa
import xml.etree.ElementTree as ET

sumoBinary = checkBinary("sumo")
# sumoBinary = checkBinary('sumo-gui') # to watch the simulation on sumo-gui
sumoCmd = [sumoBinary, "-c", "osm.sumocfg", "--no-warnings"]

def getIds_EV():
    # Parse the XML file
    tree = ET.parse('car.ev.trips.xml')
    root = tree.getroot()
    # Find elements with 'type' attribute equal to 'soulEV65'
    soulEV65_ids = [elem.get('id') for elem in root.findall(".//trip[@type='soulEV65']")]
    return soulEV65_ids

traci.start(sumoCmd)
soulEV65_ids = getIds_EV()

simulation_step = 4000 # the last car departs at step 3500.
step = 0
while step < simulation_step:
    if step % 100 == 0:
        print(f"STEP: {step} /{simulation_step}")
    traci.simulationStep()
    running_vehicles = traci.vehicle.getIDList()
    for ev_id in soulEV65_ids:
        if ev_id not in running_vehicles:
            continue

        try:
            battery_remain = float(traci.vehicle.getParameter(ev_id, "device.battery.actualBatteryCapacity"))
            battery_capacity = float(traci.vehicle.getParameter(ev_id, "device.battery.maximumBatteryCapacity"))
            if battery_remain < battery_capacity / 10:
                # TODO: Find the nearest charging station and go
                # TODO: Add charging stations
                # TODO: Set the natual parameters of charging stations.
                delta_charging_station_id = "cS_2to19_0a"
                delta_charging_station_edge_id = "29394205#0"
                charging_duration = 100
                traci.vehicle.changeTarget(ev_id, delta_charging_station_edge_id)
                traci.vehicle.setChargingStationStop(ev_id, delta_charging_station_id, duration=charging_duration)
                # traci.vehicle.setParameter(ev_id, "device.battery.actualBatteryCapacity", str(battery_capacity))
                # print(f"vehicle:{ev_id} is going to charging station:{delta_charging_station_id}")
        except traci.exceptions.TraCIException as e: # Not Found the ev in the simulation map
            continue
    step += 1

traci.close()
