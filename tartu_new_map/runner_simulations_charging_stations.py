import runner 
import csv

# ev_percentages = ["05", "10", "15", "20", "25", "30", "35", "40", "45", "50"]
ev_percentages = ["25", "30", "35", "40", "45", "50"]
for ev_percentage in ev_percentages:
    simulation_result_path = f'per{ev_percentage}:log_waiting_vs_charging_station_simulation.csv'
    fields = ["SimulationId", "EVPercentage", "AvergaWaitime"]
    rows = []

    charging_station_counts = ["13", "15", "17", "19", "21", "23"]
    # charging_station_counts = ["13", "15"]

    charging_station_xml_list = [f"charging.stations.{i}.xml.gz" for i in charging_station_counts]
    #sumo_file_list = [f"osm.{i}.sumocfg" for i in charging_station_counts]
    for charging_station_file, simulation_id, charging_station_count in zip(charging_station_xml_list, range(len(charging_station_counts)), charging_station_counts):

        EV_trip_xml = f'car.ev.trips.{ev_percentage}.xml'
        waiting_queues = runner.run(EV_trip_xml, f'osm.{ev_percentage}.sumocfg', charging_station_file)
        # Writing the dictionary to a CSV file

        total_waiting_time = 0
        for key, value in waiting_queues.items():
            if(value['total_cars'] != 0):
                total_waiting_time += value['waiting_steps']/value['total_cars']

        avg_waiting_time = total_waiting_time / len(waiting_queues.keys())
        rows.append([simulation_id, charging_station_count, avg_waiting_time])

    with open(simulation_result_path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(fields)

        writer.writerow(rows)


    print(f"CSV file written to {simulation_result_path}")