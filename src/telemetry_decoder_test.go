package main

import (
	"math"
	"testing"
)

func TestTelemetryPacketRoundTrip(t *testing.T) {
	want := TelemetryFrame{
		SequenceNum:    42,
		AltitudeMeters: 1234.5,
		VelocityMS:     -17.25,
		EngineStatus:   3,
	}
	packet, err := EncodeTelemetryPacket(want)
	if err != nil {
		t.Fatalf("encode: %v", err)
	}
	got, err := DecodeTelemetryPacketStrict(packet)
	if err != nil {
		t.Fatalf("decode: %v", err)
	}
	if got != want {
		t.Fatalf("round trip: got %+v want %+v", got, want)
	}
}

func TestTelemetryPacketRejectsInvalidLength(t *testing.T) {
	if _, err := DecodeTelemetryPacketStrict(make([]byte, telemetryPacketSize-1)); err == nil {
		t.Fatal("expected short packet rejection")
	}
	if got := DecodeTelemetryPacket(make([]byte, telemetryPacketSize-1)); got != (TelemetryFrame{}) {
		t.Fatalf("compat decoder should fail closed, got %+v", got)
	}
}

func TestTelemetryPacketRejectsNonFiniteValues(t *testing.T) {
	_, err := EncodeTelemetryPacket(TelemetryFrame{AltitudeMeters: float32(math.Inf(1))})
	if err == nil {
		t.Fatal("expected non-finite altitude rejection")
	}
}
