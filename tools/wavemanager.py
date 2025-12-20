import struct
import numpy as np
import math
import os
# from misc.logger import Log

class WaveManager:
    def __init__(self, table_size=2048, sample_rate=44100):
        self.table_size = table_size
        self.sample_rate = sample_rate
        # Standard amount of MIP-levels (octaves) to cover all freqs up to Neuquists
        self.num_mips = 12 

    def _generate_additive(self, harmonics_weights):
        """
        Generates a set of tables (MIP-chain) with additive synthesis, naturalizing by applying sigma-approximation
        harmonics_weights: A function that takes a harmonic number (k) and returns the amplitude
        """
        mips_data = []
        base_freq = self.sample_rate / self.table_size
        nyquist = self.sample_rate / 2.0

        for mip_level in range(self.num_mips):
            pitch_shift = 2 ** mip_level
            effective_freq = base_freq * pitch_shift
            
            max_harmonic = int(math.floor(nyquist / effective_freq))
            
            table = np.zeros(self.table_size, dtype=np.float32)
            t = np.linspace(0, 1, self.table_size, endpoint=False)

            for k in range(1, max_harmonic + 1):
                amp = harmonics_weights(k)
                
                # SIGMA APPROXIMATION (Lanczos factor)
                # To get rid of Gibbs effect (ringing) on the edges of wave
                sigma = 1.0
                if k > 1:
                    x = np.pi * k / (max_harmonic + 1)
                    sigma = np.sin(x) / x

                if amp != 0:
                    table += (amp * sigma) * np.sin(2 * np.pi * k * t)

            peak = np.max(np.abs(table))
            if peak > 1e-9:
                table /= peak
            
            mips_data.append(table)
            print(f"  [MIP {mip_level}] Shift: {pitch_shift}x, MaxHarm: {max_harmonic} (Sigma Applied)")

        return mips_data

    def generate_saw(self):
        print(f"Generating Saw (Size: {self.table_size})...")
        # Saw: Amp = 1/k
        return self._generate_additive(lambda k: 1.0 / k)

    def generate_square(self):
        print(f"Generating Square (Size: {self.table_size})...")
        # Square: Amp = 1/k for odd, 0 for even
        return self._generate_additive(lambda k: (1.0 / k) if k % 2 != 0 else 0.0)

    def generate_triangle(self):
        print(f"Generating Triangle (Size: {self.table_size})...")
        # Triangle: Amp = 1/k^2 for odd, alternating sign
        def tri_amp(k):
            if k % 2 == 0: return 0.0
            amp = 1.0 / (k * k)

            if ((k - 1) // 2) % 2 != 0:
                amp = -amp
            return amp
        return self._generate_additive(tri_amp)

    def generate_sine(self):
        print(f"Generating Sine (Size: {self.table_size})...")

        mips_data = []
        t = np.linspace(0, 1, self.table_size, endpoint=False)
        table = np.sin(2 * np.pi * t).astype(np.float32)
        
        for _ in range(self.num_mips):
            mips_data.append(table)
        return mips_data

    def save_wvt(self, filename, mips_data):
        """
        Saves as binary to .wvt
        Header: Magic(4b), NumMips(4b), TableSize(4b)
        Body: Float32 array
        """
        with open(filename, 'wb') as f:
            # 1. Header
            f.write(b'WVT1') # Magic
            f.write(struct.pack('<i', len(mips_data))) # Num Mips (int32 little endian)
            f.write(struct.pack('<i', self.table_size)) # Table Size (int32)
            
            # 2. Data
            # Glue all the tables to single array
            flat_data = np.concatenate(mips_data).astype(np.float32)
            f.write(flat_data.tobytes())
            
        print(f"Saved {filename}: {len(mips_data)} tables of size {self.table_size}")

    def load_wvt(self, filename):
        """
        Read .wvt file (for debbuging in the common case)
        """
        if not os.path.exists(filename):
            print(f"Error: {filename} not found.")
            return None

        with open(filename, 'rb') as f:
            magic = f.read(4)
            if magic != b'WVT1':
                print("Error: Invalid file format")
                return None
            
            num_mips = struct.unpack('<i', f.read(4))[0]
            table_size = struct.unpack('<i', f.read(4))[0]
            
            print(f"Loading {filename} | Mips: {num_mips} | Size: {table_size}")
            
            total_samples = num_mips * table_size
            raw_bytes = f.read(total_samples * 4) 
            data = np.frombuffer(raw_bytes, dtype=np.float32)
            
            mips_restored = np.split(data, num_mips)
            return mips_restored

if __name__ == "__main__":
    manager = WaveManager(table_size=2048, sample_rate=44100)
    
    saw_data = manager.generate_saw()
    square_data = manager.generate_square()
    tri_data = manager.generate_triangle()
    sine_data = manager.generate_sine()

    manager.save_wvt("saw.wvt", saw_data)
    manager.save_wvt("square.wvt", square_data)
    manager.save_wvt("triangle.wvt", tri_data)
    manager.save_wvt("sine.wvt", sine_data)

    loaded = manager.load_wvt("saw.wvt")
    if loaded is not None:
        print(f"Debug: First sample of loaded saw: {loaded[0][0]}")