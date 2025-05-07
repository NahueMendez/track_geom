#include "gps.h"
#include <string.h>
#include <stdio.h>

// Función para convertir latitud o longitud a grados decimales
static float convertToDecimal(float raw, char direction) {
      float decimal = raw;

      // Aplicar el signo dependiendo de la dirección
      if (direction == 'S' || direction == 'W') {
          decimal = -decimal;
                }
      return decimal;
}

void GPS_Read(UART_HandleTypeDef *huart, char *buffer, size_t bufferSize, GGASTRUCT *gga) {
    // Recibir datos con timeout (1 segundo)
    HAL_StatusTypeDef status = HAL_UART_Receive(huart, (uint8_t *)buffer, bufferSize, 280);

    // Verificar si hubo un error o timeout en la recepción
    if (status != HAL_OK) {
        snprintf(buffer, bufferSize, "No data,No data,0.0,00:00:00\n");
        return;  // Salir de la función si hubo un error o timeout
    }

    char *token = strtok(buffer, "$");  // Divide las sentencias NMEA
    char ggaMessage[100] = "";  // Almacena la última sentencia GPGGA válida encontrada
    char rmcMessage[100] = ""; // Almacena la última sentencia GPRMC válida encontrada

    while (token != NULL) {
        if (strncmp(token, "GPGGA", 5) == 0) {  // Si encontramos GPGGA
            snprintf(ggaMessage, sizeof(ggaMessage), "$%s", token);  // Guardamos la sentencia
        }
        else if (strncmp(token, "GPRMC", 5) == 0) {  // Si encontramos GPRMC
            snprintf(rmcMessage, sizeof(rmcMessage), "$%s", token);  // Guardamos la sentencia
        }
        token = strtok(NULL, "$");  // Pasamos al siguiente mensaje
    }

    // Variables para los nuevos datos
        float speed = 0.0f;       // Velocidad en nudos
        char time[10] = "00:00:00"; // Hora en formato HH:MM:SS

        // Procesar RMC para obtener velocidad
        RMCSTRUCT rmc;
        if (rmcMessage[0] != '\0') {
            if (decodeRMC(rmcMessage, &rmc) == 0 && rmc.isValid) {
                speed = rmc.speed;
            }
        }

    // Si se encontró un mensaje GPGGA válido
    if (ggaMessage[0] != '\0') {
        if (decodeGGA(ggaMessage, gga) == 0 && gga->isfixValid) {
            float latitude = convertToDecimal(gga->lcation.latitude, gga->lcation.NS); //Offset para corregir
            float longitude = convertToDecimal(gga->lcation.longitude, gga->lcation.EW); //Offset para corregir

            snprintf(buffer, bufferSize, "%.6f,%.6f,%.1f,%02d:%02d:%02d\n", latitude-0.2513991, longitude-0.1518045,speed, gga->tim.hour, gga->tim.min, gga->tim.sec);
            HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_15);
        } else {
            snprintf(buffer, bufferSize, "No fix,No fix,0.0,00:00:00\n");
        }
    } else {
        snprintf(buffer, bufferSize, "No data,No data,0.0,00:00:00\n");
    }
}





