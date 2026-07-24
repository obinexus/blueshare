#ifndef BLUESHARE_CORE_H
#define BLUESHARE_CORE_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

// Configuration constants
#define MAX_NETWORKS 10
#define MAX_DEVICES 50
#define MAX_TRANSACTIONS 1000
#define BLUESHARE_SERVICE_UUID "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"

// Error codes
#define BLUESHARE_SUCCESS 0
#define BLUESHARE_ERROR_DEVICE_NOT_FOUND -1
#define BLUESHARE_ERROR_NO_SLOTS -2
#define BLUESHARE_ERROR_PRIVACY_PROOF_FAILED -3
#define BLUESHARE_ERROR_INVOICE_CREATION_FAILED -4

// Device role enumeration
typedef enum {
    ROLE_UNASSIGNED,
    ROLE_PRIMARY_HOST,
    ROLE_SECONDARY_HOST,
    ROLE_CLIENT,
    ROLE_BRIDGE
} blueshare_device_role_t;

// Network topology types
typedef enum {
    TOPOLOGY_STAR,
    TOPOLOGY_BUS,
    TOPOLOGY_MESH,
    TOPOLOGY_HYBRID
} network_topology_t;

// Core data structures
typedef struct {
    uint8_t device_id[6];
    blueshare_device_role_t role;
    uint32_t available_bandwidth_kbps;
    uint32_t cost_per_mb_microsat;
    bool payment_authorized;
    uint32_t session_timeout_ms;
} blueshare_device_t;

typedef struct {
    uint8_t network_id[16];
    uint8_t host_devices[10][6];
    uint8_t client_devices[50][6];
    uint8_t topology_type;
    uint32_t session_start_time;
    uint32_t total_bandwidth_kbps;
} blueshare_network_t;

typedef struct {
    uint8_t device_mac[6];
    uint64_t bytes_uploaded;
    uint64_t bytes_downloaded;
    uint32_t session_duration_ms;
    uint32_t average_bandwidth_kbps;
    uint32_t peak_bandwidth_kbps;
    uint8_t qos_priority;
} usage_statistics_t;

typedef struct {
    uint8_t payer_device_mac[6];
    uint8_t payee_device_mac[6];
    uint64_t data_transferred_bytes;
    uint32_t cost_microsat;
    uint32_t timestamp;
    uint8_t transaction_hash[32];
} payment_transaction_t;

// Core API functions
int blueshare_initialize(void);
int blueshare_create_network(blueshare_network_t* network, uint8_t topology_type);
int blueshare_join_network(const uint8_t* network_id, blueshare_device_role_t requested_role);
int blueshare_leave_network(const uint8_t* network_id);
int blueshare_monitor_device_usage(const uint8_t* device_mac, usage_statistics_t* stats);
int blueshare_process_payment(payment_transaction_t* transaction);
int blueshare_handle_topology_failure(blueshare_network_t* network);

#endif // BLUESHARE_CORE_H
