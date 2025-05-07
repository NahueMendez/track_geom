#ifndef GPS_H
#define GPS_H

#include "stm32f1xx_hal.h"
#include "NMEA.h"

// Prototipos
void GPS_Read(UART_HandleTypeDef *huart, char *buffer, size_t bufferSize, GGASTRUCT *gga);

#endif // GPS_H
