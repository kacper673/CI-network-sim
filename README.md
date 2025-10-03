# CI-network-sim
Simulator of critical infrastructure network failures, attacks and resilience 
Simulations shows the dependencies in every day infrostructre

idea is to have mulitple graph layers connected, each graph representing one filed of infrostructer eg. power, water, telecom

each layer consists of following:

 - node (objects in infrostucture eg. powerstation, telecom tower, hospital etc.)
    each node has:
     - state (online, offline, emergency power supply)
     - attributes (eg. power, water preassure, priority)
   
 - path (connection of objects in each layer, weight symbolizes either length of a pipe, distance of towers, etc.)

 - KPI (effectivnnes/healt factor, eg. % of electricty supply in simulation, % of water supply, avg. water preassure etc., in genereal metrics used to evaluate how helathy the layer is)
   - KPI is calculated after dt

 - Cross Layer Dependencies (eg. power_station_1 is offline -> water_pump_2 is on emergency power -> emergency power supply runs out ->  KPI drops down)


   all graphs combined should look like something like this this:

   <img width="500" height="550" alt="pobrane" src="https://github.com/user-attachments/assets/d4be3bc2-14eb-4f82-8d48-fe3a9abe58df" />


   minimal UI (SFML?, OpenGUI?), json config files - different scenarios (cyber attack, physical damege etc.)
   
