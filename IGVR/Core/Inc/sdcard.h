#ifndef SDCARD_H
#define SDCARD_H

#include "fatfs.h"
extern FATFS fs;

// Escritura
void SD_Write(FIL *fil, const char *data);
int SD_Status(void);

#endif // SDCARD_H
