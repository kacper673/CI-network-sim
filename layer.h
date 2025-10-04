#ifndef LAYER_H
#define LAYER_H
#include <iostream>
#include "edge.h"
#include "Building.h"
#include <vector>

class Layer {
public:
    std::string id;    ///energetyka, wodociagi,telocom itp

    struct graph {
        Builidng node;
    }


    void UPS(int t0, int dt);
};



#endif

