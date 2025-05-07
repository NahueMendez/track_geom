#include "sensors.h"
#include "math.h"

static ADC_HandleTypeDef *adcHandle;

void Sensors_Init(ADC_HandleTypeDef *hadc) {
    adcHandle = hadc;
    HAL_ADCEx_Calibration_Start(adcHandle); // Calibrar ADC
}

void Sensors_Read(float *trocha, float *peralte) {
	// Inicia la conversión en modo escaneado
	    HAL_ADC_Start(adcHandle);

	    // Espera a que termine la conversión del primer canal
	    HAL_ADC_PollForConversion(adcHandle, HAL_MAX_DELAY);
	    uint32_t adcValue1 = HAL_ADC_GetValue(adcHandle);  // Canal 1 (trocha)

	    // Espera a que termine la conversión del segundo canal
	    HAL_ADC_PollForConversion(adcHandle, HAL_MAX_DELAY);
	    uint32_t adcValue2 = HAL_ADC_GetValue(adcHandle);  // Canal 2 (peralte)

	    // Detiene el ADC si no se usa modo continuo
	    HAL_ADC_Stop(adcHandle);

	    // Ajustes lineales basados en la calibración
	    *trocha = 920.0f+(adcValue1 * 0.02479f + 0.10319f);       // Ajuste para trocha LVIT + offset trocha metrica
	    *trocha= floorf(*trocha * 10.0)/10.0;
	     float angle = adcValue2* 0.00705 - 14.502353; // Ajuste para peralte x-axis
	     angle = floorf(angle * 100.0f) / 100.0f;
	     *peralte =  3.14159f*angle/180.0f * (*trocha+70.0f) +30.0f;   //Trigonometria aproximada (1% error FSO) + carril UIC54

}
