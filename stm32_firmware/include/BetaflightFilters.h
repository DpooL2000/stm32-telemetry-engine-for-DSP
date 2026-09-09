#pragma once
#include <Arduino.h>

class DynamicNotchFilter {
  private:
    float b0, b1, b2, a1, a2;
    float x1, x2, y1, y2; 
    float sampleRate, q;
  public:
    DynamicNotchFilter(float sampleRateHz = 1000.0f, float qFactor = 2.5f);
    void updateCenterFrequency(float centerFreqHz);
    void updateQ(float newQ);
    float apply(float input);
};

class PT1Filter {
  private:
    float state, alpha;
  public:
    PT1Filter();
    void updateCutoff(float cutoffHz, float dt_seconds);
    float apply(float input);
};

class PT2Filter {
  private:
    PT1Filter pt1_a, pt1_b;
  public:
    void updateCutoff(float cutoffHz, float dt_seconds);
    float apply(float input);
};

class BiquadLPFilter {
  private:
    float b0, b1, b2, a1, a2;
    float x1, x2, y1, y2, sampleRate;
  public:
    BiquadLPFilter(float sampleRateHz = 1000.0f);
    void updateCutoff(float cutoffHz);
    float apply(float input);
};
