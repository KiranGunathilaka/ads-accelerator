import numpy as np
import scipy.io.wavfile as wav
import time
import os

class RealTimeCenteredNLMS:
    def __init__(self, L, mu=0.01):
        """
        Centered NLMS filter for real-time block processing.
        L: Filter length
        mu: Step size
        """
        self.L = L
        self.mu = mu
        self.w = np.zeros(L)
        self.center_tap = L // 2
        
        # History buffers for block processing
        self.x_history = np.zeros(L)
        self.d_history = np.zeros(self.center_tap)

    def process_block(self, x_block, d_block):
        B = len(x_block)
        
        # Concatenate history with the new block
        x_full = np.concatenate((self.x_history, x_block))
        d_full = np.concatenate((self.d_history, d_block))
        
        # The delayed reference signal for this block
        d_delayed = d_full[:B]
        
        # --- True Block LMS Update ---
        # --- True Block LMS Update (Vectorized / SIMD style) ---
        # Instead of looping over each row, we construct a BxL matrix 'X'
        # and compute the error and gradient for the entire block all at once!
        
        # 1. Build the BxL input matrix (each row is a sliding window)
        X = np.array([x_full[i + self.L : i : -1] for i in range(B)])
        
        # 2. Filter phase for the entire block (Matrix-Vector multiplication)
        y = np.dot(X, self.w)
        
        # 3. Error calculation for the entire block (Vector subtraction)
        e = d_delayed - y
        
        # 4. Accumulate gradient for the entire block (Matrix-Vector multiplication)
        gradient = np.dot(X.T, e)
        
        
        # Update weights ONCE per block
        # (You may need to divide mu by B to keep stability comparable to sample-by-sample)
        self.w = self.w + (self.mu / B) * gradient

        # ---------------------------------------------------------
        # NOTE: If you wanted Sample-by-Sample LMS *inside* a block,
        # you would update self.w inside the loop like this instead:
        # self.w = self.w + self.mu * e * x_vec 
        # ---------------------------------------------------------

        # Update histories for the next block
        self.x_history = x_full[-self.L:]
        self.d_history = d_full[-self.center_tap:]
        
        # Estimate delay relative to center_tap
        # Negative delay implies x arrives before d
        estimated_delay = self.center_tap - np.argmax(np.abs(self.w)) 
        return estimated_delay


def generate_moving_source_signals(audio_file):
    import sys
    script_dir = os.path.dirname(os.path.abspath(__file__))
    audio_path = os.path.join(script_dir, audio_file)
    
    print(f"Attempting to load source audio: {audio_path}")
    
    if os.path.exists(audio_path):
        fs, source_audio = wav.read(audio_path)
        print("Audio file loaded successfully.")
    else:
        print(f"No audio file found at {audio_path}. Exiting.")
        sys.exit(1)
        
    # Convert to mono if stereo
    if len(source_audio.shape) > 1:
        source_audio = source_audio[:, 0]
        
    # Normalize to [-1.0, 1.0]
    source_audio = source_audio.astype(np.float32) / np.iinfo(np.int16).max
    
    # 2. Define 3D Coordinates (in meters) - standard tetrahedral
    mic_positions = np.array([
        [0.0, 0.0, 0.0],          # Mic 1 (Reference)
        [0.1, 0.0, 0.0],          # Mic 2
        [0.05, 0.0866, 0.0],      # Mic 3
        [0.05, 0.0289, 0.0816]    # Mic 4
    ])
    
    SPEED_OF_SOUND = 343.0
    N = len(source_audio)
    t = np.arange(N) / fs
    
    # Define circular trajectory for the source
    # Radius = 2.0m, Height z = 0.5m, completing 1 full circle over the audio duration
    R = 2.0
    omega = 2 * np.pi / (N / fs) 
    
    x_s = R * np.cos(omega * t)
    y_s = R * np.sin(omega * t)
    z_s = np.full(N, 0.5)
    
    source_pos = np.stack((x_s, y_s, z_s), axis=-1)
    
    print("Simulating moving source (this might take a moment)...")
    mic_signals = np.zeros((4, N), dtype=np.float32)
    true_delays = np.zeros((4, N), dtype=np.float32)
    
    # Linear interpolation for fractional delay to prevent clicks
    for i, mic_pos in enumerate(mic_positions):
        dist = np.linalg.norm(source_pos - mic_pos, axis=-1)
        delay_samples = (dist / SPEED_OF_SOUND) * fs
        true_delays[i, :] = delay_samples
        
        # Compute source indices mapped to current time
        src_indices = np.arange(N) - delay_samples
        
        # Valid indices within the array bounds
        valid_mask = (src_indices >= 0) & (src_indices < N - 1)
        
        # Interpolation
        idx_floor = np.floor(src_indices[valid_mask]).astype(int)
        frac = src_indices[valid_mask] - idx_floor
        
        mic_signals[i, valid_mask] = (1 - frac) * source_audio[idx_floor] + frac * source_audio[idx_floor + 1]
        
    return fs, mic_signals, true_delays


def realtime_localization_loop(fs, mic_signals, true_delays, B=2048, L=256, mu=0.05):
    """
    Simulates real-time processing of the microphone arrays with ping-pong buffering.
    B: Block size
    L: Filter length for the Centered NLMS
    """
    N = mic_signals.shape[1]
    
    # Instantiate 3 filters for Mics 2, 3, 4 relative to Mic 1 (d)
    lms_21 = RealTimeCenteredNLMS(L, mu)
    lms_31 = RealTimeCenteredNLMS(L, mu)
    lms_41 = RealTimeCenteredNLMS(L, mu)
    
    print(f"\nStarting Real-Time Ping-Pong Buffer Simulation...")
    print(f"Block Size (B) = {B}, Filter Length (L) = {L}")
    print("-" * 60)
    
    num_blocks = N // B
    
    for block_idx in range(num_blocks):
        start_idx = block_idx * B
        end_idx = start_idx + B
        
        # Read the new block (simulating DMA filling Buffer A)
        # while processing the previous block (Buffer B).
        d_block = mic_signals[0, start_idx:end_idx]
        x2_block = mic_signals[1, start_idx:end_idx]
        x3_block = mic_signals[2, start_idx:end_idx]
        x4_block = mic_signals[3, start_idx:end_idx]
        
        # Process block
        tau_21 = lms_21.process_block(x2_block, d_block)
        tau_31 = lms_31.process_block(x3_block, d_block)
        tau_41 = lms_41.process_block(x4_block, d_block)
        
        # Theoretical relative delays in samples at the center of the block
        mid_idx = start_idx + B // 2
        if mid_idx >= N:
            mid_idx = N - 1
            
        true_21 = true_delays[1, mid_idx] - true_delays[0, mid_idx]
        true_31 = true_delays[2, mid_idx] - true_delays[0, mid_idx]
        true_41 = true_delays[3, mid_idx] - true_delays[0, mid_idx]
        
        time_sec = end_idx / fs
        
        # Formatted string for neat continuous updates
        print(f"\r[Time: {time_sec:6.2f}s] "
              f"Est: Mic2={tau_21:3d} | Mic3={tau_31:3d} | Mic4={tau_41:3d}   "
              f"True: ({true_21:5.1f}, {true_31:5.1f}, {true_41:5.1f})", end="", flush=True)
        
        # Small sleep to simulate visual real-time terminal output 
        # (A 2048 block at 16kHz corresponds to 128ms)
        time.sleep(0.01)
        
    print()
    print("-" * 60)
    print("Real-time simulation finished.")

if __name__ == "__main__":
    audio_file = "source2.wav"
    
    # Generate the 4 microphone arrays
    fs, mic_signals, true_delays = generate_moving_source_signals(audio_file)
    
    # Configure Block Size and Filter Length
    B = 128
    L = 64
    
    # Run the real-time simulation
    realtime_localization_loop(fs, mic_signals, true_delays, B=B, L=L, mu=0.05)
