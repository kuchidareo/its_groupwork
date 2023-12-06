import os
import sys
import csv
if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
import traci
import gzip
from sumolib import checkBinary
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

sumoBinary = checkBinary("sumo")
# sumoBinary = checkBinary('sumo-gui') # to watch the simulation on sumo-gui
sumoCmd = [sumoBinary, "-c", "osm.sumocfg", "--no-warnings"]

CHARGING_STATUS_ID = 32
NUM_LIMIT_CHARGING_STATION = 2
MAXIMUM_BATTERY_CAPACITY = 64000

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
        charging_stations[station_id] = {"lane": station_lane, "edge": station_edge, "num_going": 0}

    return charging_stations

def find_nearest_empty_charging_station(ev_id, charging_stations):
    vehicle_edge_id = traci.vehicle.getRoadID(ev_id)
    min_distance = float("inf")
    nearest_station_flag = False

    for station_id in charging_stations.keys():
        station = charging_stations[station_id]
        if station["num_going"] >= NUM_LIMIT_CHARGING_STATION:
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
        most_empty_station_id, _ = sorted(charging_stations.items(), key=lambda x: x[1]['num_going'])[0]
        most_empty_station_edge_id = charging_stations[most_empty_station_id]["edge"]
        dest_station_id = most_empty_station_id
        dest_station_edge_id = most_empty_station_edge_id

    return dest_station_id, dest_station_edge_id



EV_trip_xml = "car.ev.trips.xml"
charging_station_xml_gz = "charging.stations.xml.gz"

soulEV65_ids = getIds_EV(EV_trip_xml)
charging_stations = get_chargingstations(charging_station_xml_gz)
CHARGING_DURATION_STEPS = 330

simulation_step = 3000 # the last car departs at step 3500.

waiting_queues = {}
ev_charging_station = {}

LOGGING = {}
log_steps = []
log_average_waiting_time = []

traci.start(sumoCmd)

step = 0
# while step < simulation_step:
while step < simulation_step:
    if step % 100 == 0:
        print("-----------")
        print(f"STEP: {step}")
        # for station_id in charging_stations.keys():
        #     station = charging_stations[station_id]
        #     print(station_id, station["num_going"])
        for key in waiting_queues.keys(): 
            # if key == "enefit_volt_78141":
            queue = waiting_queues[key]
            print(f"station: {key}")
            sum_waiting_step = 0
            for item in queue:
                sum_waiting_step += item.waiting_step_counter
                print(item.id, item.waiting_step_counter, item.charging_step_counter)
            log_steps.append(step)
            log_average_waiting_time.append(sum_waiting_step/len(charging_stations))
        
           
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
        
        elif (ev_id in ev_charging_station.keys()): # Going to the charging station. -> [Going]
            charging_station_id = ev_charging_station[ev_id]["charging_station_id"]

            vehicle_edge_id = traci.vehicle.getRoadID(ev_id)
            station_edge_id = charging_stations[charging_station_id]["edge"]
            distance = traci.simulation.findRoute(vehicle_edge_id, station_edge_id).length

            if distance < 100: # Getting to the charging station. -> [Waiting]
                if charging_station_id not in waiting_queues.keys():
                    waiting_queues[charging_station_id] = [] #initializing queue for the charging station

                if ev_charging_station[ev_id]["state"] == "Going":
                    waiting_queues[charging_station_id].append(waiting_queue_item(charging_station_id, ev_id, 0, 0))
                    ev_charging_station[ev_id]["state"] = "Waiting"

                queue = waiting_queues[charging_station_id]
                if len(queue) > 0 and queue[0].charging_step_counter >= CHARGING_DURATION_STEPS:
                    LOGGING["vehicle_id"] = ev_id
                    LOGGING[ev_id] = queue[0].waiting_step_counter
                    charging_stations[charging_station_id]["num_going"] -= 1
                    v = queue.pop(0)
                    ev_charging_station[ev_id]["state"] = "Charged"
                    # ev_charging_station.pop(ev_id)
                    print('charging_station: ', v.charging_station_id, 'popped', v.id, 'waited: ', v.waiting_step_counter, 'charge_time: ', v.charging_step_counter, len(queue))

                if len(queue) > 1 and queue[1].charging_step_counter >= CHARGING_DURATION_STEPS:
                    LOGGING["vehicle_id"] = ev_id
                    LOGGING[ev_id] = queue[1].waiting_step_counter
                    charging_stations[charging_station_id]["num_going"] -= 1
                    v = queue.pop(1)
                    ev_charging_station[ev_id]["state"] = "Charged"
                    # ev_charging_station.pop(ev_id)
                    print('charging_station: ', v.charging_station_id, 'popped', v.id, 'waited: ', v.waiting_step_counter, 'charge_time: ', v.charging_step_counter, len(queue))
        else:
            try:
                battery_remain = float(traci.vehicle.getParameter(ev_id, "device.battery.actualBatteryCapacity"))
                if battery_remain < MAXIMUM_BATTERY_CAPACITY / 10:
                    dest_station_id, dest_station_edge_id = find_nearest_empty_charging_station(ev_id, charging_stations)

                    traci.vehicle.changeTarget(ev_id, dest_station_edge_id)
                    traci.vehicle.setChargingStationStop(ev_id, dest_station_id, duration=CHARGING_DURATION_STEPS)

                    charging_stations[dest_station_id]["num_going"] += 1
                    if ev_id not in ev_charging_station:
                        ev_charging_station[ev_id] = {"charging_station_id": dest_station_id, "state": "Going"}
        
            except traci.exceptions.TraCIException as e: # Not Found the ev in the simulation map
                continue
    step += 1

traci.close()

plt.plot(log_steps, log_average_waiting_time, "--o")
plt.show()

csv_file_path = 'waiting_time_summary.csv'

# Writing the dictionary to a CSV file
with open(csv_file_path, 'w', newline='') as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=LOGGING.keys())
    
    # Write the header
    writer.writeheader()
    
    # Write the data
    for i in range(len(LOGGING['vehicle_id'])):
        row_data = {key: LOGGING[key] for key in LOGGING.keys()}
        writer.writerow(row_data)

print(f"CSV file written to {csv_file_path}")