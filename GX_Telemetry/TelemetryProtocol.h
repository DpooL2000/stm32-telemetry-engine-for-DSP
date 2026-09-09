#pragma once
#include <stdint.h>

// --- 44-BYTE TELEMETRY STRUCT ---
struct TelemetryData {
  uint32_t sync = 0xDDBBCCAA;
  uint32_t loop_cycles;
  float    gyro_x;
  float    gyro_y;
  float    gyro_z;
  float    accel_x;
  float    accel_y;
  float    accel_z;
  float    angle_roll;
  float    angle_pitch;
  float    angle_yaw;
} __attribute__((packed));
