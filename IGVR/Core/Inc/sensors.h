#ifndef SENSORS_H
#define SENSORS_H

#include "stm32f1xx_hal.h"

// Prototipos
void Sensors_Init(ADC_HandleTypeDef *hadc);
void Sensors_Read(float *trocha, float *peralte);

#endif // SENSORS_H
