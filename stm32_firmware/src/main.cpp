#include <Arduino.h>
#include <Wire.h>
#include <Servo.h>

// Modules
#include "TelemetryProtocol.h"
#include "CORDIC_Trig.h"
#include "BetaflightFilters.h"

const float GYRO_SCALE_F = 0.015267175f; 
const float ACCEL_SCALE_F = 0.000061035f; // 1.0 / 16384.0 for +/- 2g

// Using PB7 & PB6 to avoid the PB8/BOOT0 DFU Trap
#define MPU_SDA_PIN PB7
#define MPU_SCL_PIN PB6
#define ESC_PWM_PIN PB14

Servo esc;
TelemetryData t_data;

DynamicNotchFilter dNotch[3];
PT1Filter          lp1_pt1[3], lp2_pt1[3];
PT2Filter          lp1_pt2[3], lp2_pt2[3];
BiquadLPFilter     lp1_bq[3],  lp2_bq[3];

// --- GUI Configuration States ---
int lp1_en = 1, lp1_type = 0; float lp1_cut = 125.0f;
int lp2_en = 1, lp2_type = 0; float lp2_cut = 250.0f;
int notch_en = 1;             float notch_q = 2.50f;
int currentThrottle = 1000;
int trigger_calibration = 0;

unsigned long loopTimer = 0;
String serialBuffer = "";

// --- ATTITUDE VARIABLES ---
float abs_roll = 0.0f, abs_pitch = 0.0f, abs_yaw = 0.0f;
float gyro_bias[3] = {0, 0, 0};
float resting_roll_offset = 0.0f;
float resting_pitch_offset = 0.0f;

int parsePayload(String payload, float* values, int maxValues) {
    int count = 0, startIndex = 0, commaIndex = payload.indexOf(',');
    while (commaIndex != -1 && count < maxValues) {
        values[count++] = payload.substring(startIndex, commaIndex).toFloat();
        startIndex = commaIndex + 1; commaIndex = payload.indexOf(',', startIndex);
    }
    if (startIndex < payload.length() && count < maxValues) {
        values[count++] = payload.substring(startIndex).toFloat();
    }
    return count;
}

void calibrate_IMU() {
    esc.writeMicroseconds(1000); // Stop motor for safety
    float sum_gx = 0, sum_gy = 0, sum_gz = 0;
    float sum_roll = 0, sum_pitch = 0;
    
    for (int i = 0; i < 1000; i++) {
        Wire.beginTransmission(0x68);
        Wire.write(0x3B);
        Wire.endTransmission(false);
        Wire.requestFrom(0x68, 14);

        int16_t ax = (Wire.read() << 8) | Wire.read();
        int16_t ay = (Wire.read() << 8) | Wire.read();
        int16_t az = (Wire.read() << 8) | Wire.read();
        Wire.read(); Wire.read(); // Temp
        int16_t gx = (Wire.read() << 8) | Wire.read();
        int16_t gy = (Wire.read() << 8) | Wire.read();
        int16_t gz = (Wire.read() << 8) | Wire.read();

        sum_gx += (float)gx * GYRO_SCALE_F;
        sum_gy += (float)gy * GYRO_SCALE_F;
        sum_gz += (float)gz * GYRO_SCALE_F;

        float accelX = (float)ax * ACCEL_SCALE_F;
        float accelY = (float)ay * ACCEL_SCALE_F;
        float accelZ = (float)az * ACCEL_SCALE_F;
        
        sum_roll += atan2f(accelY, accelZ) * 180.0f / PI;
        sum_pitch += atan2f(-accelX, sqrtf(accelY*accelY + accelZ*accelZ)) * 180.0f / PI;
        delay(2); // Wait for next reading
    }

    gyro_bias[0] = sum_gx / 1000.0f;
    gyro_bias[1] = sum_gy / 1000.0f;
    gyro_bias[2] = sum_gz / 1000.0f;
    
    resting_roll_offset = sum_roll / 1000.0f;
    resting_pitch_offset = sum_pitch / 1000.0f;

    abs_roll = resting_roll_offset;
    abs_pitch = resting_pitch_offset;
    abs_yaw = 0.0f;
}

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(1); 
  
  CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
  DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
  RCC->AHB1ENR |= RCC_AHB1ENR_CORDICEN;
  CORDIC->CSR = (6 << CORDIC_CSR_PRECISION_Pos) | CORDIC_CSR_NRES; 
  
  esc.attach(ESC_PWM_PIN, 1000, 2000); 
  esc.writeMicroseconds(1000); 
  delay(3000); 

  Wire.setSDA(MPU_SDA_PIN); Wire.setSCL(MPU_SCL_PIN);
  Wire.begin(); Wire.setClock(400000); 

  Wire.beginTransmission(0x68); Wire.write(0x6B); Wire.write(0x00); Wire.endTransmission();
  Wire.beginTransmission(0x68); Wire.write(0x1B); Wire.write(0x08); Wire.endTransmission();
  Wire.beginTransmission(0x68); Wire.write(0x1A); Wire.write(0x03); Wire.endTransmission();

  calibrate_IMU(); // Calibrate at boot
  loopTimer = micros();
}

void loop() {
  // 1. SERIAL COMMAND PARSER
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      float vals[12] = {0};
      if (parsePayload(serialBuffer, vals, 12) == 12) {
        lp1_en = (int)vals[0]; lp1_cut = vals[1]; lp1_type = (int)vals[2];
        lp2_en = (int)vals[3]; lp2_cut = vals[4]; lp2_type = (int)vals[5];
        notch_en = (int)vals[6]; notch_q = vals[7] / 100.0f;
        
        float notch_min = vals[8];
        float notch_max = vals[9];
        
        currentThrottle = (int)vals[10];
        trigger_calibration = (int)vals[11];

        if (trigger_calibration) { calibrate_IMU(); }

        if (currentThrottle >= 1000 && currentThrottle <= 2000) {
          esc.writeMicroseconds(currentThrottle);
          
          float throttlePct = (currentThrottle - 1000.0f) / 1000.0f;
          float dynFreq = notch_min + (throttlePct * (notch_max - notch_min));
           
          for(int i=0; i<3; i++) {
            dNotch[i].updateCenterFrequency(dynFreq);
            dNotch[i].updateQ(notch_q);
          }
        }
        for(int i=0; i<3; i++) {
          lp1_pt1[i].updateCutoff(lp1_cut, 0.001f);
          lp1_pt2[i].updateCutoff(lp1_cut, 0.001f);
          lp1_bq[i].updateCutoff(lp1_cut);
          
          lp2_pt1[i].updateCutoff(lp2_cut, 0.001f);
          lp2_pt2[i].updateCutoff(lp2_cut, 0.001f);
          lp2_bq[i].updateCutoff(lp2_cut);
        }
      }
      serialBuffer = "";
    } else {
      serialBuffer += c;
    }
  }

  // 2. 1kHz CONTROL LOOP
  if (micros() - loopTimer >= 1000) { 
    uint32_t startCycle = DWT->CYCCNT;
    loopTimer = micros();

    Wire.beginTransmission(0x68);
    Wire.write(0x3B); 
    Wire.endTransmission(false);
    Wire.requestFrom(0x68, 14);

    int16_t rawAx = (Wire.read() << 8) | Wire.read();
    int16_t rawAy = (Wire.read() << 8) | Wire.read();
    int16_t rawAz = (Wire.read() << 8) | Wire.read();
    Wire.read(); Wire.read();
    int16_t rawGx = (Wire.read() << 8) | Wire.read();
    int16_t rawGy = (Wire.read() << 8) | Wire.read();
    int16_t rawGz = (Wire.read() << 8) | Wire.read();

    float accelX = (float)rawAx * ACCEL_SCALE_F;
    float accelY = (float)rawAy * ACCEL_SCALE_F;
    float accelZ = (float)rawAz * ACCEL_SCALE_F;

    float rawGyro[3];
    rawGyro[0] = ((float)rawGx * GYRO_SCALE_F) - gyro_bias[0];
    rawGyro[1] = ((float)rawGy * GYRO_SCALE_F) - gyro_bias[1];
    rawGyro[2] = ((float)rawGz * GYRO_SCALE_F) - gyro_bias[2];

    float filteredGyro[3];
    for (int i = 0; i < 3; i++) {
      float sig = rawGyro[i];
      if (notch_en) sig = dNotch[i].apply(sig);
      if (lp1_en) {
        if (lp1_type == 0) sig = lp1_pt1[i].apply(sig);
        else if (lp1_type == 1) sig = lp1_pt2[i].apply(sig);
        else if (lp1_type == 2) sig = lp1_bq[i].apply(sig);
      }
      if (lp2_en) {
        if (lp2_type == 0) sig = lp2_pt1[i].apply(sig);
        else if (lp2_type == 1) sig = lp2_pt2[i].apply(sig);
        else if (lp2_type == 2) sig = lp2_bq[i].apply(sig);
      }
      filteredGyro[i] = sig;
    }

    float dt = 0.001f;
    float accel_roll = atan2f(accelY, accelZ) * 180.0f / PI;
    float accel_pitch = atan2f(-accelX, sqrtf(accelY*accelY + accelZ*accelZ)) * 180.0f / PI;

    abs_roll  = 0.998f * (abs_roll + filteredGyro[0] * dt) + 0.002f * accel_roll;
    abs_pitch = 0.998f * (abs_pitch + filteredGyro[1] * dt) + 0.002f * accel_pitch;
    abs_yaw  += filteredGyro[2] * dt; 

    uint32_t endCycle = DWT->CYCCNT;

    t_data.loop_cycles = endCycle - startCycle;
    t_data.gyro_x = filteredGyro[0];
    t_data.gyro_y = filteredGyro[1];
    t_data.gyro_z = filteredGyro[2];
    t_data.accel_x = accelX;
    t_data.accel_y = accelY;
    t_data.accel_z = accelZ;
    t_data.angle_roll  = abs_roll - resting_roll_offset; 
    t_data.angle_pitch = abs_pitch - resting_pitch_offset; 
    t_data.angle_yaw   = abs_yaw; 
    
    Serial.write((uint8_t*)&t_data, sizeof(TelemetryData));
  }
}
