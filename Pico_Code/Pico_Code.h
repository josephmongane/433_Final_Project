#ifndef PICO_CODE_H
#define PICO_CODE_H


// ENCODER
#define I2C_PORT i2c0
#define I2C_SDA 8
#define I2C_SCL 9

#define ENCODER_ADDR  0x36
#define REG_ANGLE_H  0x0E

void i2c_init_all();
float encoder_read();
 

// Force Sensor
#define PIN_DOUT 4
#define PIN_SCK 5

void hx711_init();
int hx711_read();

#endif 