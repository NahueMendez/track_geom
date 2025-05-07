#include "sdcard.h"
FATFS fs;
static int sd = 0; // 0 = NO, 1 = OK

void SD_Write(FIL *fil, const char *data) {
    if (f_mount(&fs, "", 0) == FR_OK) {
        if (f_open(fil, "track.txt", FA_OPEN_ALWAYS | FA_WRITE | FA_READ) == FR_OK) {
            f_lseek(fil, fil->fsize);
            f_puts(data, fil);
            f_sync(fil);
            f_close(fil);
            sd=1;
            HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_14);
        }
    }
    else{sd=0;}
}

int SD_Status(void) {
    return sd;
}
