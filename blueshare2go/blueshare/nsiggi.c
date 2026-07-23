#include <stdio.h>
#include <stdlib.h>
#include <sys/random.h>
#include <math.h>
#include <string.h>

// θ state as 2-bit entropy register
typedef enum {
    STATE_NO = 0b00,      // 0
    STATE_YES = 0b01,     // 1
    STATE_MAYBE = 0b10,   // θ (entropy residue)
    STATE_EPSILON = 0b11  // Channel clear
} trinary_state_t;

typedef struct {
    trinary_state_t state;
    double entropy;  // Measured entropy for this symbol
} nsigii_symbol_t;

typedef struct {
    nsigii_symbol_t *symbols;
    size_t length;
    double *entropy_bits;  // Per-symbol entropy measurements
} nsigii_message_t;

// Measure REAL entropy from OS, not pseudorandom
double measure_channel_entropy(size_t num_samples) {
    unsigned char buffer[64];
    double entropy = 0.0;
    
    // Use getrandom() for cryptographic entropy
    if (getrandom(buffer, sizeof(buffer), 0) != sizeof(buffer)) {
        perror("getrandom");
        return -1.0;
    }
    
    // Calculate Shannon entropy of the noise floor
    int freq[256] = {0};
    for (int i = 0; i < 64; i++) {
        freq[buffer[i]]++;
    }
    
    for (int i = 0; i < 256; i++) {
        if (freq[i] > 0) {
            double p = (double)freq[i] / 64.0;
            entropy -= p * log2(p);
        }
    }
    
    return entropy;
}

// Create sparse matrix encoding with θ preservation
void encode_sparse(nsigii_message_t *msg) {
    msg->entropy_bits = malloc(msg->length * sizeof(double));
    
    for (size_t i = 0; i < msg->length; i++) {
        if (msg->symbols[i].state == STATE_MAYBE) {
            // θ gets its own entropy measurement
            msg->entropy_bits[i] = measure_channel_entropy(64);
            msg->symbols[i].entropy = msg->entropy_bits[i];
            // Sparse pattern for θ: [1,0,1,0]
            printf("θ[%zu] entropy: %.4f bits\n", i, msg->entropy_bits[i]);
        } else if (msg->symbols[i].state == STATE_YES) {
            msg->entropy_bits[i] = 0.0;
            // YES pattern: [1,1,0,0]
        } else {  // STATE_NO
            msg->entropy_bits[i] = 0.0;
            // NO pattern: [0,0,1,1]
        }
    }
}

// Calculate work = F × d × cos(θ)
double calculate_work(nsigii_message_t *msg, double force, double distance) {
    double base_work = force * distance * cos(30.0 * M_PI / 180.0); // cos(30°) = 0.866
    
    // Add entropy cost for MAYBE states
    double entropy_cost = 0.0;
    for (size_t i = 0; i < msg->length; i++) {
        entropy_cost += msg->entropy_bits[i] * 0.1;  // Scale factor
    }
    
    return base_work + entropy_cost;
}

// Apply isomorphic transformation (YES↔NO, MAYBE preserved)
void apply_isomorphism(nsigii_message_t *src, nsigii_message_t *dst) {
    dst->length = src->length;
    dst->symbols = malloc(dst->length * sizeof(nsigii_symbol_t));
    dst->entropy_bits = malloc(dst->length * sizeof(double));
    
    for (size_t i = 0; i < src->length; i++) {
        switch (src->symbols[i].state) {
            case STATE_YES:
                dst->symbols[i].state = STATE_NO;
                break;
            case STATE_NO:
                dst->symbols[i].state = STATE_YES;
                break;
            case STATE_MAYBE:
                dst->symbols[i].state = STATE_MAYBE;  // Sacred
                break;
            default:
                dst->symbols[i].state = STATE_EPSILON;
        }
        dst->symbols[i].entropy = src->symbols[i].entropy;
        dst->entropy_bits[i] = src->entropy_bits[i];
    }
}

// XOR verification: sent ⊕ echoed → ε or θ
int verify_echo(nsigii_message_t *sent, nsigii_message_t *echoed) {
    if (sent->length != echoed->length) return 0;
    
    for (size_t i = 0; i < sent->length; i++) {
        trinary_state_t s = sent->symbols[i].state;
        trinary_state_t e = echoed->symbols[i].state;
        
        // XOR logic for trinary states
        if (s == STATE_MAYBE && e == STATE_MAYBE) {
            // θ ⊕ θ = 0 (verified as MAYBE)
            continue;
        } else if ((s == STATE_YES && e == STATE_NO) || 
                   (s == STATE_NO && e == STATE_YES)) {
            // Conjugate pair verified
            continue;
        } else {
            return 0;  // Invalid state
        }
    }
    
    return 1;
}

int main() {
    // Create message: YES, MAYBE, NO, MAYBE
    nsigii_symbol_t symbols[] = {
        {STATE_YES, 0.0},
        {STATE_MAYBE, 0.0},
        {STATE_NO, 0.0},
        {STATE_MAYBE, 0.0}
    };
    
    nsigii_message_t message = {
        .symbols = symbols,
        .length = 4,
        .entropy_bits = NULL
    };
    
    printf("=== NSIGII C Implementation ===\n");
    
    // Encode and measure entropy
    encode_sparse(&message);
    
    // Calculate work
    double work = calculate_work(&message, 1.25, 15.0);
    printf("Work Required: %.4f Joules\n", work);
    
    // Apply isomorphism
    nsigii_message_t echo;
    apply_isomorphism(&message, &echo);
    
    printf("Echo verified: %s\n", verify_echo(&message, &echo) ? "✓ VERIFIED" : "✗ FAILED");
    
    // Clean up
    free(message.entropy_bits);
    free(echo.symbols);
    free(echo.entropy_bits);
    
    return 0;
}
