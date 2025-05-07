#ifndef ENCODER_H
#define ENCODER_H

#include "stm32f1xx_hal.h"

// Prototipos
void Encoder_Init(TIM_HandleTypeDef *htim);
int32_t Encoder_ReadDelta(void);
float Encoder_GetDistance(float wheelDiameter);

#endif // ENCODER_H
