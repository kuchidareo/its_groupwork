import os
import sys
if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
import traci
import gzip
from sumolib import checkBinary
import xml.etree.ElementTree as ET


sumoBinary = checkBinary("sumo")
# sumoBinary = checkBinary('sumo-gui') # to watch the simulation on sumo-gui
sumoCmd = [sumoBinary, "-c", "osm.sumocfg", "--no-warnings"]

CHARGING_STATUS_ID = 32
NUM_LIMIT_CHARGING_STATION = 2

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

    charging_stations = {}
    for charging_station in root.iter('chargingStation'):
        station_id = charging_station.get('id')
        station_lane = charging_station.get('lane') # 29394205#0_0"
        station_edge = station_lane.split("_")[0] # 29394205#0"
        charging_stations[station_id] = {"lane": station_lane, "edge": station_edge, "num_waiting": 0}

    return charging_stations

def find_nearest_empty_charging_station(ev_id, charging_stations):
    vehicle_edge_id = traci.vehicle.getRoadID(ev_id)
    min_distance = float("inf")
    nearest_station_flag = False

    for station_id in charging_stations.keys():
        station = charging_stations[station_id]
        if station["num_waiting"] > NUM_LIMIT_CHARGING_STATION:
            continue
    
        station_edge_id = station["edge"]
        distance = traci.simulation.findRoute(vehicle_edge_id, station_edge_id).length

        if distance < min_distance:
            min_distance = distance
            nearest_station_id = station_id
            nearest_station_edge_id = station_edge_id
            nearest_station_flag = True

    if nearest_station_flag:
        dest_station_id = nearest_station_id
        dest_station_edge_id = nearest_station_edge_id
    else:
        most_empty_station_id, _ = sorted(charging_stations.items(), key=lambda x: x[1]['num_waiting'])[0]
        most_empty_station_edge_id = charging_stations[most_empty_station_id]["edge"]
        dest_station_id = most_empty_station_id
        dest_station_edge_id = most_empty_station_edge_id

    return dest_station_id, dest_station_edge_id


charging_vehicles = {}

EV_trip_xml = "car.ev.trips.xml"
charging_station_xml_gz = "charging.stations.xml.gz"

soulEV65_ids = getIds_EV(EV_trip_xml)
charging_stations = get_chargingstations(charging_station_xml_gz)
charging_duration = 132

simulation_step = 1000 # the last car departs at step 3500.

waiting_queues = {}
ev_charging_station = {}

traci.start(sumoCmd)

step = 0
while step < simulation_step:
    if step % 100 == 0:
        print(f"STEP: {step} /{simulation_step}")
    traci.simulationStep()
    running_vehicles = traci.vehicle.getIDList()
    for key in waiting_queues.keys(): 
        queue = waiting_queues[key]
        for (item, idx) in zip(queue, range(len(queue))):
                if(idx == 0 or idx == 1):
                    queue[idx].charging_step_counter = queue[idx].charging_step_counter + 1
                else:
                    queue[idx].waiting_step_counter = queue[idx].waiting_step_counter + 1
    for ev_id in soulEV65_ids:
        if ev_id not in running_vehicles:
            continue
        elif ev_id in charging_vehicles.keys():
            # print(traci.vehicle.getStops(ev_id), ev_id)
            # status_id = traci.vehicle.getStops(ev_id)[0].stopFlags
                # remove queue item if it reached 138 steps for charging 
            if(ev_id in ev_charging_station.keys()):
                queue = waiting_queues[ev_charging_station[ev_id]]
                if len(queue) > 0 and queue[0].charging_step_counter == 138:
                    v = queue.pop(0)
                    ev_charging_station.pop(ev_id)
                    print('charging_station: ', v.charging_station_id, 'popped', v.id, 'waited: ', v.waiting_step_counter, 'charge_time: ', v.charging_step_counter, len(queue))

                if len(queue) > 1 and queue[1].charging_step_counter == 138:
                    v = queue.pop(1)
                    ev_charging_station.pop(ev_id)
                    print('charging_station: ', v.charging_station_id, 'popped', v.id, 'waited: ', v.waiting_step_counter, 'charge_time: ', v.charging_step_counter, len(queue))

            # if(len(queue) > 1 and queue[0].charging_step_counter == 138):
            #     queue.pop(0) 
            # if(len(queue) > 1 and queue[1].charging_step_counter == 138):
            #     queue.pop(1) 
            continue
        else:
            try:
                battery_remain = float(traci.vehicle.getParameter(ev_id, "device.battery.actualBatteryCapacity"))
                battery_capacity = float(traci.vehicle.getParameter(ev_id, "device.battery.maximumBatteryCapacity"))
                if battery_remain < battery_capacity / 10:
                    # TODO: Add charging stations
                    # TODO: Fix the error that there is no route to the station.
                    # TODO: Set the natual parameters of charging stations.
                    dest_station_id, dest_station_edge_id = find_nearest_empty_charging_station(ev_id, charging_stations)
                    # print(f"vehicle:{ev_id} is going to charging station:{nearest_station_id}")
                    traci.vehicle.changeTarget(ev_id, dest_station_edge_id)
                    traci.vehicle.setChargingStationStop(ev_id, dest_station_id, duration=charging_duration)
                    charging_vehicles[ev_id] = {"charging_station_id": dest_station_id}

                    if(dest_station_id not in waiting_queues.keys()):
                        waiting_queues[dest_station_id] = [] #initializing queue for the charging station

                    waiting_queues[dest_station_id].append(waiting_queue_item(dest_station_id, ev_id, 0, 0))
                    ev_charging_station[ev_id] = dest_station_id
                    # print(step)
                    # print(charging_stations)
                    charging_stations[dest_station_id]["num_waiting"] += 1
                    # traci.vehicle.setParameter(ev_id, "device.battery.actualBatteryCapacity", str(battery_capacity))
        
            except traci.exceptions.TraCIException as e: # Not Found the ev in the simulation map
                continue
    step += 1

traci.close()