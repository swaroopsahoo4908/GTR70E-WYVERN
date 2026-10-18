#pragma once
struct TwoWire { void beginTransmission(uint8_t){} uint8_t endTransmission(bool=true){return 1;} size_t write(uint8_t){return 1;}
  size_t write(const uint8_t*, size_t n){return n;} uint8_t requestFrom(uint8_t, uint8_t){return 0;} int available(){return 0;} int read(){return 0;}
  void setSDA(int){} void setSCL(int){} void begin(){} void setClock(uint32_t){} };
static TwoWire Wire, Wire1;
