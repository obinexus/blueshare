import secrets
import time
import math
from enum import Enum

class State(Enum):
    YES = 1
    NO = 0
    MAYBE = -1

class NSIGIIMessage:
    def __init__(self, data: list[State]):
        self.data = data
        self.entropy_bits = []  # Measured entropy for each state
    
    def measure_channel_entropy(self) -> float:
        """Measure real entropy from system noise sources"""
        # Use secrets for true entropy, not random
        noise_samples = [secrets.randbits(8) for _ in range(len(self.data))]
        
        # Calculate Shannon entropy of the noise floor
        entropy = 0.0
        for sample in noise_samples:
            p = sample / 255.0
            if p > 0:
                entropy -= p * math.log2(p)
        
        return entropy  # Returns bits of entropy per symbol
    
    def encode_sparse(self):
        """Create sparse matrix with θ states preserved"""
        # For MAYBE states, we embed measured entropy
        matrix = []
        for i, state in enumerate(self.data):
            if state == State.MAYBE:
                # θ gets its own entropy vector
                theta_entropy = self.measure_channel_entropy()
                matrix.append([1, 0, 1, 0])  # θ pattern [1,0,1,0]
                self.entropy_bits.append(theta_entropy)
            elif state == State.YES:
                matrix.append([1, 1, 0, 0])  # YES pattern
                self.entropy_bits.append(0.0)
            else:  # NO
                matrix.append([0, 0, 1, 1])  # NO pattern
                self.entropy_bits.append(0.0)
        return matrix

class NSIGIIEchoServer:
    def __init__(self):
        self.force_newtons = 1.25  # From your physics model
        self.distance_meters = 15.0
        self.theta_angle = math.radians(30)  # cos(θ) = 0.866
        
    def calculate_work(self, message: NSIGIIMessage) -> float:
        """Calculate work = F × d × cos(θ)"""
        # Add entropy cost for MAYBE states
        base_work = self.force_newtons * self.distance_meters * math.cos(self.theta_angle)
        entropy_cost = sum(message.entropy_bits) * 0.1  # Scale factor
        return base_work + entropy_cost
    
    def apply_isomorphism(self, message: NSIGIIMessage):
        """Create conjugate pair: YES↔NO, MAYBE preserved"""
        transformed = []
        for state in message.data:
            if state == State.YES:
                transformed.append(State.NO)
            elif state == State.NO:
                transformed.append(State.YES)
            else:  # MAYBE is sacred
                transformed.append(State.MAYBE)
        return NSIGIIMessage(transformed)
    
    def verify_echo(self, sent: NSIGIIMessage, echoed: NSIGIIMessage) -> bool:
        """Verify via XOR: sent ⊕ echoed → ε or θ"""
        if len(sent.data) != len(echoed.data):
            return False
        
        for s, e in zip(sent.data, echoed.data):
            # XOR operation for trinary states
            if s == State.MAYBE and e == State.MAYBE:
                # θ ⊕ θ = 0 (verified as MAYBE)
                continue
            elif (s == State.YES and e == State.NO) or \
                 (s == State.NO and e == State.YES):
                # Conjugate pair verified
                continue
            else:
                # Invalid state transition
                return False
        
        # Check work calculation matches
        sent_work = self.calculate_work(sent)
        echoed_work = self.calculate_work(echoed)
        
        # Work difference must be within θ tolerance
        work_delta = abs(sent_work - echoed_work)
        return work_delta < 0.5  # 0.5 Joule tolerance

# Demo: "I Built a Consensus Protocol That Never Ghosts You"
if __name__ == "__main__":
    # Create message with MAYBE states
    message = NSIGIIMessage([
        State.YES, State.MAYBE, State.NO, State.MAYBE
    ])
    
    server = NSIGIIEchoServer()
    
    print("=== NSIGII Echo Verification ===")
    print(f"Original: {[s.name for s in message.data]}")
    
    # Measure entropy (this is the θ measurement)
    entropy = message.measure_channel_entropy()
    print(f"Channel Entropy: {entropy:.4f} bits/symbol")
    
    # Calculate work required
    work = server.calculate_work(message)
    print(f"Work Required: {work:.4f} Joules")
    
    # Apply isomorphism (what server echoes back)
    echo = server.apply_isomorphism(message)
    print(f"Echoed: {[s.name for s in echo.data]}")
    
    # Verify
    is_verified = server.verify_echo(message, echo)
    print(f"Verification: {'✓ VERIFIED' if is_verified else '✗ FAILED'}")
    
    # Simulate bit rate bounds
    bitrate = len(message.data) / (work / 10)  # Simplified
    print(f"Effective Bit Rate: {bitrate:.2f} messages/Joule")
