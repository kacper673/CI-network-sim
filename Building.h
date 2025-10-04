#ifndef BUILDING_H
#define BUILDING_H
#include <iostream>

class Building {
public:
    std::string id;
    int status; //0-offline 1-online 2 - UPS 
    std::string demand;
    std::string supply;
   

    Building(std::string id_, int status_, std::string demand_, std::string supply_) : id(id_), status(status_), demand(demand_), supply(supply_) {}

};

class WaterWorks : Building {
public:
    double pump_capacity = 0.0;       // wydajnosc pompy [m3h]
    double flow_rate = 0.0;           // aktualny przep³yw [m3h]
    double storage_capacity = 0.0;     // pojemnoœæ zbiornika [m3]
    double pressure = 0.0;            // aktualne ciœnienie [bar]
    double min_pressure = 1.5;        // minimalne ciœnienie operacyjne [bar]
    double power_demand = 0.0;         // zapotrzebowanie na pr¹d [MW]

    WaterWorks(double pump_capacity_, double flow_rate_, double storage_capacity_, double pressure_, double min_pressure_, double power_demand_, std::string id_, int status_, std::string demand_, std::string supply_) :
    Building(id_, status_, demand_, supply_),
    pump_capacity(pump_capacity_),
    flow_rate(flow_rate_),
    storage_capacity(storage_capacity_),
    pressure(pressure_),
    min_pressure(min_pressure_),
    power_demand(power_demand_)
    {}

    void recive() {

    }
};

#endif