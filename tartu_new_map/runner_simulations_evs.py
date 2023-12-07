import runner 
import csv
simulation_result_path = f'log_waiting_vs_cars_simulation.csv'
fields = ["SimulationId", "EVPercentage", "AvergaWaitime"]
rows = []

ev_percentages = ["05", "10", "15", "20", "25", "30", "35", "40", "45", "50"]

EV_trip_xml_list = [f"car.ev.trips.{i}.xml" for i in ev_percentages]
sumo_file_list = [f"osm.{i}.sumocfg" for i in ev_percentages]
for EV_trip_xml, sumo_file, simulation_id, ev_percentage in zip(EV_trip_xml_list, sumo_file_list, range(10), ev_percentages):
    waiting_queues = runner.run(EV_trip_xml, sumo_file)

    csv_file_path = f'log_{EV_trip_xml}.csv'

    # Writing the dictionary to a CSV file
    total_waiting_time = 0
    for key, value in waiting_queues.items():
        total_waiting_time += value['waiting_steps']

    avg_waiting_time = total_waiting_time / len(waiting_queues.keys())
    rows.append([simulation_id, ev_percentage, avg_waiting_time])

with open(simulation_result_path, 'w', newline='') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(fields)

    writer.writerow(rows)


print(f"CSV file written to {csv_file_path}")