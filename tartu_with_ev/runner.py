import os
import sys
if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
import traci
import gzip
import math
from sumolib import checkBinary
import xml.etree.ElementTree as ET

class waiting_queue_item:
    def __init__(self, charging_station_id, id, waiting_step_counter, charging_step_counter):
        self.charging_station_id = charging_station_id
        self.id = id
        self.waiting_step_counter = waiting_step_counter
        self.charging_step_counter = charging_step_counter



def getIds_EV(xml):
    tree = ET.parse(xml)
    root = tree.getroot()
    # Find elements with 'type' attribute equal to 'soulEV65'
    soulEV65_ids = [elem.get('id') for elem in root.findall(".//trip[@type='soulEV65']")]
    return soulEV65_ids

def get_chargingstations(xml_gz):
    with gzip.open(xml_gz, 'rt') as xml:
        tree = ET.parse(xml)
    root = tree.getroot()

    charging_stations = []
    for charging_station in root.iter('chargingStation'):
        station_id = charging_station.get('id')
        station_lane = charging_station.get('lane') # 29394205#0_0"
        station_edge = station_lane.split("_")[0] # 29394205#0"
        charging_stations.append({"id": station_id, "lane": station_lane, "edge": station_edge})

    return charging_stations

def find_nearest_charging_station(ev_id, charging_stations):
    vehicle_edge_id = traci.vehicle.getRoadID(ev_id)
    min_distance = float("inf")
    for station in charging_stations:
        station_id = station["id"]
        station_edge_id = station["edge"]
        distance = traci.simulation.findRoute(vehicle_edge_id, station_edge_id).length

        if distance < min_distance:
            min_distance = distance
            nearest_station_id = station_id
            nearest_station_edge_id = station_edge_id

    return nearest_station_id, nearest_station_edge_id


sumoBinary = checkBinary("sumo")
# sumoBinary = checkBinary('sumo-gui') # to watch the simulation on sumo-gui
sumoCmd = [sumoBinary, "-c", "osm.sumocfg", "--no-warnings"]

EV_trip_xml = "car.ev.trips.xml"
charging_station_xml_gz = "charging.stations.xml.gz"

soulEV65_ids = getIds_EV(EV_trip_xml)
charging_stations = get_chargingstations(charging_station_xml_gz)
charging_duration = 100

simulation_step = 4000 # the last car departs at step 3500.

traci.start(sumoCmd)

waiting_queues = {}
ev_station = {}
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
            
            if(ev_id in ev_station.keys()):
                queue = waiting_queues[ev_station[ev_id]]
                if(queue[0].charging_step_counter == 138):
                    queue.pop(0) 
                if(len(queue) > 1 and queue[1].charging_step_counter == 138):
                    queue.pop(1) 

                for (item, idx) in zip(queue, range(len(queue))):
                    if(idx == 0 or idx == 1):
                        queue[idx].charging_step_counter = queue[idx].charging_step_counter + 1
                    else:
                        queue[idx].waiting_step_counter = queue[idx].waiting_step_counter + 1

            if battery_remain < battery_capacity / 10:
                # TODO: Add charging stations
                # TODO: Fix the error that there is no route to the station.
                # TODO: Set the natual parameters of charging stations.
                nearest_station_id, nearest_station_edge_id = find_nearest_charging_station(ev_id, charging_stations)
                # print(f"vehicle:{ev_id} is going to charging station:{nearest_station_id}")
                if(nearest_station_id not in waiting_queues.keys()):
                    waiting_queues[nearest_station_id] = [] #initializing queue for the charging station

                waiting_queues[nearest_station_id].append(waiting_queue_item(nearest_station_id, ev_id, 0, 0))
                ev_station[ev_id] = nearest_station_id
                traci.vehicle.changeTarget(ev_id, nearest_station_edge_id)
                traci.vehicle.setChargingStationStop(ev_id, nearest_station_id, duration=charging_duration)
                # traci.vehicle.setParameter(ev_id, "device.battery.actualBatteryCapacity", str(battery_capacity))
       
        except traci.exceptions.TraCIException as e: # Not Found the ev in the simulation map
            continue
    step += 1

traci.close()
