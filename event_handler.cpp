#include "Building.h"
#include <vector>

void run(std::vector<Building> buildings) {
	for (auto& it : buildings) {
		it.recive(2);
		it.produce(2);
	}

}
int main() {

	PowerPlant p1;
	WaterWorks w1;



	return 0;
}
