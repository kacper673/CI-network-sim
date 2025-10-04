class Building{
public:
    bool online;
    bool emergency;
    double time_left;
    double repair_time;
    bool road_req;
    double power_req;
    double water_req;

    Building(bool road_req, double power_req, double water_req, double repair_time){
        road_req = road_req;
        power_req = power_req;
        water_req = water_req;
        repair_time = repair_time;
        online = true;
        emergency = false;
        time_left = 0;
    };
};

class PowerPlant : Building{
};