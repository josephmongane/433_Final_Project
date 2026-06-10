#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "Pico_Code.h"
#include "can.h"

int main()
{
    stdio_init_all();
    i2c_init_all();
    can_init();
    hx711_init();

    sleep_ms(1000);
    int force_avg = 0;
    for(int i = 0; i < 500; i++){
        int val = hx711_read();
        force_avg += val;
    }
    force_avg = force_avg / 500;
    printf("AVERAGE FORCE: %d\n", force_avg);
    int force_filtered = 0;
    float a = 0.2;
    float b = 1 - a;

    

    while (true) {

        // CAN CODE
        float desired_current = 100.0;
        bool acked = can_send_float(CAN_ID, desired_current);


        // TESTING CODE
 
        float angles = encoder_read();
        int forces = hx711_read() - force_avg; 
        force_filtered = a*force_filtered + b*forces;

        //printf("%.2f %d %d\n", angles, forces, force_filtered); 

        sleep_ms(100);
    }
}


///
/// HELPER FUNCTIONS
///


void i2c_init_all(){
    // I2C Initialisation. Using it at 400Khz.
    i2c_init(I2C_PORT, 400*1000);
    
    gpio_set_function(I2C_SDA, GPIO_FUNC_I2C);
    gpio_set_function(I2C_SCL, GPIO_FUNC_I2C);
    gpio_pull_up(I2C_SDA);
    gpio_pull_up(I2C_SCL);
}

float encoder_read(){
    uint8_t reg = REG_ANGLE_H;
    uint8_t buf[2];
    uint16_t val = 0;
    
    i2c_write_blocking(i2c0, ENCODER_ADDR, &reg, 1, true);
    i2c_read_blocking(i2c0, ENCODER_ADDR, buf, 2, false);

    val = ((uint16_t)(buf[0] & 0x0F) << 8) | buf[1];
    float angle_deg = (val / 4096.0f) * 360.0f;

    return angle_deg;
}

void hx711_init(){
    // Not too sure why there's a pull up for PIN_DOUT (does it stay pulled up)

    gpio_init(PIN_DOUT);
    gpio_set_dir(PIN_DOUT, GPIO_IN);
    gpio_pull_up(PIN_DOUT);

    gpio_init(PIN_SCK);
    gpio_set_dir(PIN_SCK, GPIO_OUT);
    gpio_put(PIN_SCK, 0);
}

int hx711_read(){

    uint64_t clock_time_us = 10;
    unsigned int data;

    while(gpio_get(PIN_DOUT)){
        tight_loop_contents();
    }

    unsigned int raw = 0;
    for (int i = 0; i < 24; i++){
        gpio_put(PIN_SCK, 1);
        sleep_us(clock_time_us);

        if (gpio_get(PIN_DOUT)){
            data = 1;
        }
        else{
            data = 0;
        }

        raw = (raw << 1) | data;

        gpio_put(PIN_SCK, 0);
        sleep_us(clock_time_us);
    }

    // set gain for next piece of data
    gpio_put(PIN_SCK, 1);
    sleep_us(clock_time_us);
    gpio_put(PIN_SCK, 0);
    sleep_us(clock_time_us);

    if (raw & 0x800000){
        raw = raw | 0xFF000000;
    }

    return (int)raw;
}
