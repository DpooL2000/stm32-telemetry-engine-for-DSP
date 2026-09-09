#pragma once
#include <Arduino.h>

inline void get_Fast_Sin_Cos(float angle_rad, float* out_sin, float* out_cos) {
  while(angle_rad > PI) angle_rad -= 2.0f * PI;
  while(angle_rad < -PI) angle_rad += 2.0f * PI;
  int32_t angle_q31 = (int32_t)((angle_rad / PI) * 2147483648.0f);
  CORDIC->WDATA = angle_q31;
  *out_cos = (float)CORDIC->RDATA / 2147483648.0f;
  *out_sin = (float)CORDIC->RDATA / 2147483648.0f;
}
