#include <iostream>

class Building{
public:
    bool online;
    bool emergency;
    double time_left;
    double repair_time;
    bool road_req;
    double power_req;
    double water_req;

    Building(bool _road_req, double _power_req, double _water_req, double _repair_time){
        road_req = _road_req;
        power_req = _power_req;
        water_req = _water_req;
        repair_time = _repair_time;
        online = true;
        emergency = false;
        time_left = 0;
    };
};

class PowerPlant : public Building{
public:
    double power; // power in kWh
    double max_power;
    PowerPlant(double _power, double _max_power, bool _road_req, double _power_req, double _water_req, double _repair_time):
        Building(_road_req, _power_req, _water_req, _repair_time){
        power = _power;
        _max_power = max_power;
    };
};

class WaterPump : public Building{
public:
    
}

int main(void){
    PowerPlant pp1 = PowerPlant(20, 50, true, 10, 10, 20);
    std::cout << pp1.power;
    return 0;
}

