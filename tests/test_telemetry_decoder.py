"""Test suite for SpaceX Telemetry Decoder."""
import unittest

class TelemetryDecoderSim:
    def decode_packet(self, seq: int) -> dict:
        return {"seq": seq, "altitude_m": 15400.5, "velocity_ms": 1250.0}

class TestTelemetryDecoder(unittest.TestCase):
    def test_decoder(self):
        dec = TelemetryDecoderSim()
        f = dec.decode_packet(42001)
        self.assertEqual(f["seq"], 42001)

if __name__ == "__main__":
    unittest.main()
