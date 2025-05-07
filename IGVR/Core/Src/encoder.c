#include "encoder.h"

// Variables estáticas para almacenar información del encoder
static TIM_HandleTypeDef *encoderTimer = NULL;
static int32_t lastCount = 0;
static int32_t totalPulses = 0;

// Inicializa el encoder
void Encoder_Init(TIM_HandleTypeDef *htim) {
    encoderTimer = htim;
    HAL_TIM_Encoder_Start(encoderTimer, TIM_CHANNEL_ALL);
    encoderTimer->Instance->CNT = 0;  // Reiniciar el contador
}

//Para debugging
int32_t Encoder_ReadRaw(void) {
    if (encoderTimer == NULL) return 0;
    return encoderTimer->Instance->CNT;
}

// Lee el delta de pulsos desde la última lectura
int32_t Encoder_ReadDelta(void) {
    if (encoderTimer == NULL) return 0;  // Verificar si está inicializado

    int32_t currentCount = encoderTimer->Instance->CNT;
    int32_t deltaCount = currentCount - lastCount;

    // Manejo de desbordamiento del contador
    if (deltaCount > 32767) {
        deltaCount -= 65536;
    } else if (deltaCount < -32768) {
        deltaCount += 65536;
    }

    lastCount = currentCount;  // Actualizar el último valor leído
    totalPulses += deltaCount; // Acumular los pulsos
    return deltaCount;
}

// Calcula la distancia recorrida en metros
float Encoder_GetDistance(float wheelDiameter) {
    // Asumimos 360 pulsos por revolución
    float pulsesPerRevolution = 600.0;
    return (3.14159 * wheelDiameter * totalPulses) / pulsesPerRevolution;
}
