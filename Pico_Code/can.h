#ifndef CAN_H
#define CAN_H

#include "pico/stdlib.h"

#define CAN_TX_PIN 10
#define CAN_RX_PIN 11
#define CAN_ID 0x150

void can_init(void);
bool can_send_float(uint32_t id, float value);

#endif
