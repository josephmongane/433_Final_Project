#ifndef PICO_CODE_H
#define PICO_CODE_H

#define I2C_PORT i2c0
#define I2C_SDA 8
#define I2C_SCL 9

#define ENCODER_ADDR  0x36
#define REG_ANGLE_H  0x0E

void i2c_init_all();
float encoder_read();

#endif PICO_CODE_H