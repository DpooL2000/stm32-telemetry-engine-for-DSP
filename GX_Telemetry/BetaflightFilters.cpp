#include "BetaflightFilters.h"
#include "CORDIC_Trig.h"

// ==========================================
// Dynamic Notch Filter
// ==========================================
DynamicNotchFilter::DynamicNotchFilter(float sampleRateHz, float qFactor) {
    x1 = 0; x2 = 0; y1 = 0; y2 = 0;
    sampleRate = sampleRateHz; 
    q = qFactor; 
    updateCenterFrequency(sampleRate / 4.0); 
}

void DynamicNotchFilter::updateCenterFrequency(float centerFreqHz) {
    if (centerFreqHz <= 0.0f || centerFreqHz >= sampleRate / 2.0f) return;
    float omega = 2.0f * PI * centerFreqHz / sampleRate;
    float sn, cs; 
    get_Fast_Sin_Cos(omega, &sn, &cs);
    float alpha = sn / (2.0f * q);
    float a0_inv = 1.0f / (1.0f + alpha);
    
    b0 = 1.0f * a0_inv; 
    b1 = -2.0f * cs * a0_inv; 
    b2 = b0; 
    a1 = b1; 
    a2 = (1.0f - alpha) * a0_inv;
}

void DynamicNotchFilter::updateQ(float newQ) { 
    if (newQ > 0.1f) q = newQ; 
}

float DynamicNotchFilter::apply(float input) {
    float output = b0 * input + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2;
    x2 = x1; x1 = input; 
    y2 = y1; y1 = output; 
    return output;
}

// ==========================================
// PT1 Filter (First Order Lowpass)
// ==========================================
PT1Filter::PT1Filter() : state(0.0f), alpha(1.0f) {}

void PT1Filter::updateCutoff(float cutoffHz, float dt_seconds) {
    if (cutoffHz <= 0.0f) { alpha = 1.0f; return; }
    float rc = 1.0f / (2.0f * PI * cutoffHz);
    alpha = dt_seconds / (rc + dt_seconds);
}

float PT1Filter::apply(float input) { 
    state = state + alpha * (input - state); 
    return state; 
}

// ==========================================
// PT2 Filter (Cascaded First Order)
// ==========================================
void PT2Filter::updateCutoff(float cutoffHz, float dt_seconds) {
    float f_adj = cutoffHz * 1.55377397f; 
    pt1_a.updateCutoff(f_adj, dt_seconds); 
    pt1_b.updateCutoff(f_adj, dt_seconds);
}

float PT2Filter::apply(float input) { 
    return pt1_b.apply(pt1_a.apply(input)); 
}

// ==========================================
// Biquad Lowpass Filter (Butterworth)
// ==========================================
BiquadLPFilter::BiquadLPFilter(float sampleRateHz) { 
    x1 = 0; x2 = 0; y1 = 0; y2 = 0;
    sampleRate = sampleRateHz; 
}

void BiquadLPFilter::updateCutoff(float cutoffHz) {
    if (cutoffHz <= 0.0f || cutoffHz >= sampleRate / 2.0f) return;
    float omega = 2.0f * PI * cutoffHz / sampleRate;
    float sn, cs; 
    get_Fast_Sin_Cos(omega, &sn, &cs);
    float alpha = sn * 0.70710678f; 
    float a0_inv = 1.0f / (1.0f + alpha);
    
    b1 = (1.0f - cs) * a0_inv; 
    b0 = b1 * 0.5f; 
    b2 = b0; 
    a1 = -2.0f * cs * a0_inv; 
    a2 = (1.0f - alpha) * a0_inv;
}

float BiquadLPFilter::apply(float input) {
    float output = b0 * input + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2;
    x2 = x1; x1 = input; 
    y2 = y1; y1 = output; 
    return output;
}
