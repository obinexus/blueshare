#ifndef PLATFORM_INTERFACE_H
#define PLATFORM_INTERFACE_H

#include "../core/blueshare_core.h"

// Platform-specific function prototypes
int platform_init_bluetooth(void);
int platform_enable_hotspot(const char* ssid, const char* password);
int platform_get_device_usage(const uint8_t* device_mac, usage_statistics_t* stats);
int platform_route_traffic(const uint8_t* client_mac, const void* data, size_t data_len);
int platform_cleanup(void);

// Bluetooth operations
int platform_bluetooth_scan(blueshare_device_t* devices, size_t max_devices);
int platform_bluetooth_pair(const uint8_t* target_mac, const char* passkey);
int platform_bluetooth_advertise(const char* device_name, uint32_t available_bandwidth);

// Network operations
int platform_create_access_point(const char* ssid, const char* password);
int platform_get_connected_clients(uint8_t clients[][6], size_t max_clients);
int platform_set_bandwidth_limit(const uint8_t* client_mac, uint32_t limit_kbps);

#endif // PLATFORM_INTERFACE_H
