#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "Pico_Code.h"
#include "can.h"

#define MAX_CURRENT 600
#define MIN_CURRENT 10
#define NUM_SAMPLES_FORCE_AVG 500

#define WALL_FORCE 100000

// /// Force Filtering
// #define a 0.2

// /// PD Control
// #define Kp 0.03
// #define Kd -0.01


int main()
{
    stdio_init_all();
    i2c_init_all();
    can_init();
    int force_avg = hx711_init();
    
    printf("AVERAGE FORCE: %d\n", force_avg);

    int force_filtered = 0;

    int prev_err = 0;
    float error;
    float d_error;
    float desired_current;

    float a = 0.2;
    float Kp = 0.02;
    float Kd = -0.01;

    int desired_force = 0;

    while (true) {
        float angles = encoder_read();
        int forces = hx711_read();
        int forces_2 = forces - force_avg;
        force_filtered = a*force_filtered + (1-a)*forces_2; 

        if ((angles <= 5) && (angles >= 1)) 
        {
            desired_force = (WALL_FORCE/20) * angles;
            Kp = 0.5; 
            Kd = 0.1;
        }
        else if(angles < 100)
        {
            desired_force = WALL_FORCE;
            Kp = 0.5; 
            Kd = 0.1;
        }
        else
        {
            desired_force = 0;
            Kp = 0.02;
            Kd = -0.01;
        }

        // PD control
        error = desired_force - force_filtered;
        d_error = error - prev_err;
        desired_current = Kp*error + Kd*d_error;

        // Clamping the output value
        if (desired_current > MAX_CURRENT){ desired_current = MAX_CURRENT;}
        else if (desired_current < -MAX_CURRENT){desired_current = -MAX_CURRENT;}
        if (desired_current < MIN_CURRENT && desired_current > -MIN_CURRENT){ desired_current = 0;}

        // CAN CODE
        bool acked = can_send_float(CAN_ID, desired_current);
        printf("%.2f %d\n", angles, force_filtered); 
        prev_err = error;

        sleep_ms(10);
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

int hx711_init(){
    // Not too sure why there's a pull up for PIN_DOUT (does it stay pulled up)

    gpio_init(PIN_DOUT);
    gpio_set_dir(PIN_DOUT, GPIO_IN);
    gpio_pull_up(PIN_DOUT);

    gpio_init(PIN_SCK);
    gpio_set_dir(PIN_SCK, GPIO_OUT);
    gpio_put(PIN_SCK, 0);

    int force_avg = 0;

    for(int i = 0; i < NUM_SAMPLES_FORCE_AVG; i++){
        int val = hx711_read();
        force_avg += val;
    }

    force_avg = force_avg / NUM_SAMPLES_FORCE_AVG;
    
    return force_avg;
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
