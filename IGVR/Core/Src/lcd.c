/*
 * lcd.c
 *
 *  Created on: 10/06/2018
 *      Author: Olivier Van den Eede
 *      ver tutorial (http://micropeta.com/video59) video: https://www.youtube.com/watch?v=9F2gTb3n_p0
 */

#include "lcd.h"
const uint8_t ROW_16[] = {0x00, 0x40, 0x10, 0x50};
const uint8_t ROW_20[] = {0x00, 0x40, 0x14, 0x54};
/************************************** Static declarations **************************************/

//static void lcd_write_data(Lcd_HandleTypeDef * lcd, uint8_t data);
static void lcd_write_command(Lcd_HandleTypeDef * lcd, uint8_t command);
static void lcd_write(Lcd_HandleTypeDef * lcd, uint8_t data, uint8_t len);


/************************************** Function definitions **************************************/

/**
 * Create new Lcd_HandleTypeDef and initialize the Lcd
 */
Lcd_HandleTypeDef Lcd_create(
		Lcd_PortType port[], Lcd_PinType pin[],
		Lcd_PortType rs_port, Lcd_PinType rs_pin,
		Lcd_PortType en_port, Lcd_PinType en_pin, Lcd_ModeTypeDef mode)
{
	Lcd_HandleTypeDef lcd;

	lcd.mode = mode;

	lcd.en_pin = en_pin;
	lcd.en_port = en_port;

	lcd.rs_pin = rs_pin;
	lcd.rs_port = rs_port;

	lcd.data_pin = pin;
	lcd.data_port = port;

	Lcd_init(&lcd);

	return lcd;
}

/**
 * Initialize 16x2-lcd without cursor
 */
void Lcd_init(Lcd_HandleTypeDef * lcd)
{
	if(lcd->mode == LCD_4_BIT_MODE)
	{
			lcd_write_command(lcd, 0x33);
			lcd_write_command(lcd, 0x32);
			lcd_write_command(lcd, FUNCTION_SET | OPT_N);				// 4-bit mode
	}
	else
		lcd_write_command(lcd, FUNCTION_SET | OPT_DL | OPT_N);


	lcd_write_command(lcd, CLEAR_DISPLAY);						// Clear screen
	lcd_write_command(lcd, DISPLAY_ON_OFF_CONTROL | OPT_D);		// Lcd-on, cursor-off, no-blink
	lcd_write_command(lcd, ENTRY_MODE_SET | OPT_INC);			// Increment cursor
}

/**
 * Write a number on the current position
 */
void Lcd_int(Lcd_HandleTypeDef * lcd, int number)
{
	char buffer[11];
	sprintf(buffer, "%d", number);
	Lcd_string(lcd, buffer);
}

void Lcd_int_hex(Lcd_HandleTypeDef * lcd, int number)
{
	char buffer[11];
	sprintf(buffer, "%X", number);
	Lcd_string(lcd, buffer);
}


/**
 * Write a number on the current position
 */
void Lcd_float(Lcd_HandleTypeDef * lcd, float number)
{
	char buffer[11];
	sprintf(buffer, "%f", number);

	Lcd_string(lcd, buffer);
}

/*
 * Write a number on the current position
 */
void Lcd_float_lim(Lcd_HandleTypeDef * lcd, float number, uint8_t decimal)
{
	int intPart = (int) number;
	Lcd_int(lcd, intPart);
	Lcd_string(lcd, ".");
	number = number - (float)intPart;
	number = number * pow(10,decimal);
	Lcd_int(lcd, (int)number);
}

/**
 * Write a string on the current position
 */
void Lcd_string(Lcd_HandleTypeDef * lcd, char * string)
{
	for(uint8_t i = 0; i < strlen(string); i++)
	{
		lcd_write_data(lcd, string[i]);
	}
}

/**
 * Set the cursor position
 */
void Lcd_cursor(Lcd_HandleTypeDef * lcd, uint8_t row, uint8_t col)
{
	#ifdef LCD20xN
	lcd_write_command(lcd, SET_DDRAM_ADDR + ROW_20[row] + col);
	#endif

	#ifdef LCD16xN
	lcd_write_command(lcd, SET_DDRAM_ADDR + ROW_16[row] + col);
	#endif
}

/**
 * Clear the screen
 */
void Lcd_clear(Lcd_HandleTypeDef * lcd) {
	lcd_write_command(lcd, CLEAR_DISPLAY);
}

void Lcd_define_char(Lcd_HandleTypeDef * lcd, uint8_t code, uint8_t bitmap[]){
	lcd_write_command(lcd, SETCGRAM_ADDR + (code << 3));
	for(uint8_t i=0;i<8;++i){
		lcd_write_data(lcd, bitmap[i]);
	}

}


/************************************** Static function definition **************************************/

/**
 * Write a byte to the command register
 */
void lcd_write_command(Lcd_HandleTypeDef * lcd, uint8_t command)
{
	HAL_GPIO_WritePin(lcd->rs_port, lcd->rs_pin, LCD_COMMAND_REG);		// Write to command register

	if(lcd->mode == LCD_4_BIT_MODE)
	{
		lcd_write(lcd, (command >> 4), LCD_NIB);
		lcd_write(lcd, command & 0x0F, LCD_NIB);
	}
	else
	{
		lcd_write(lcd, command, LCD_BYTE);
	}

}

/**
 * Write a byte to the data register
 */
void lcd_write_data(Lcd_HandleTypeDef * lcd, uint8_t data)
{
	HAL_GPIO_WritePin(lcd->rs_port, lcd->rs_pin, LCD_DATA_REG);			// Write to data register

	if(lcd->mode == LCD_4_BIT_MODE)
	{
		lcd_write(lcd, data >> 4, LCD_NIB);
		lcd_write(lcd, data & 0x0F, LCD_NIB);
	}
	else
	{
		lcd_write(lcd, data, LCD_BYTE);
	}

}

/**
 * Set len bits on the bus and toggle the enable line
 */
void lcd_write(Lcd_HandleTypeDef * lcd, uint8_t data, uint8_t len)
{
	for(uint8_t i = 0; i < len; i++)
	{
		HAL_GPIO_WritePin(lcd->data_port[i], lcd->data_pin[i], (data >> i) & 0x01);
	}

	HAL_GPIO_WritePin(lcd->en_port, lcd->en_pin, 1);
	DELAY(1);
	HAL_GPIO_WritePin(lcd->en_port, lcd->en_pin, 0); 		// Data receive on falling edge
}


//Nuevas cosas
#include <stdio.h>
#include <string.h>
#include "lcd.h"
#include "sdcard.h"  // Incluir para obtener el estado de la SD

void Lcd_show_info(Lcd_HandleTypeDef* lcd, char* gpsBuffer, int trocha, float peralte) {
    char gps_text[10];
    char sd_text[10];
    char trocha_text[12];
    char peralte_text[12];

    // Verifica si el GPS tiene datos válidos
    if (strstr(gpsBuffer, "No fix") != NULL || strstr(gpsBuffer, "No data") != NULL) {
        snprintf(gps_text, sizeof(gps_text), "GPS:NO");
    } else {
        snprintf(gps_text, sizeof(gps_text), "GPS:OK");
    }

    // Obtener estado de la SD desde la función SD_Status()
    if (SD_Status()) {
        snprintf(sd_text, sizeof(sd_text), "SD:OK");
    } else {
        snprintf(sd_text, sizeof(sd_text), "SD:NO");
    }

    // Formatear los valores de trocha y peralte como enteros
    snprintf(trocha_text, sizeof(trocha_text), "t:%d mm", trocha);
    snprintf(peralte_text, sizeof(peralte_text), "p:%.1f mm", peralte);

    // Escribir en el LCD
    Lcd_clear(lcd);
    Lcd_cursor(lcd, 0, 10);
    Lcd_string(lcd, gps_text);
    Lcd_cursor(lcd, 1, 11);
    Lcd_string(lcd, sd_text);
    Lcd_cursor(lcd, 0, 0);
    Lcd_string(lcd, trocha_text);
    Lcd_cursor(lcd, 1, 0);
    Lcd_string(lcd, peralte_text);
}
