import traci

sumoBinary = "/opt/homebrew/bin/sumo-gui"
sumoCmd = [sumoBinary, "-c", "helloWorld.sumocfg"]

traci.start(sumoCmd)
step = 0
while step < 1000:
    traci.simulationStep()
    if traci.inductionloop.getLastStepVehicleNumber("0") > 0:
        traci.trafficlight.setRedYellowGreenState("0", "GrGr")
    step += 1

traci.close(False)
