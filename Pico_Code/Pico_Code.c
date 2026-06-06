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

    const uint32_t PERIOD_US = 1000;  // 1000Hz
    uint32_t next_time = time_us_32();

    while (true) {
        // COPIED ENCODER CODE
        float angle = encoder_read();
        printf("%f\n", angle);

        // COPIED FORCE SENSOR CODE
        int num;
        scanf("%d",&num);

        int voltages[5000];
        uint64_t times[5000];
        
        for (int i = 0; i < num; i++){
            int val = hx711_read();

            voltages[i] = val;
            times[i] = to_ms_since_boot(get_absolute_time());
        }

        for (int i = 0; i < num; i++){
            printf("%d %llu %d\n", i, times[i], voltages[i]);
        }

        // COPIED CAN CODE
        bool acked = can_send_float(CAN_ID, desired_current);
 
        if (!acked) {
            printf("CAN no ACK\n");
        }
 
        next_time += PERIOD_US;
        uint32_t now = time_us_32();
        if ((int32_t)(next_time - now) > 0) {
            sleep_us(next_time - now);
        }
    }
}

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
