package main

import (
	"encoding/binary"
	"errors"
	"fmt"
	"math"
)

const telemetryPacketSize = 13

// TelemetryFrame is a small repository-local binary telemetry example.
// It is not a SpaceX, Falcon, Starship, CCSDS, or production wire contract.
type TelemetryFrame struct {
	SequenceNum    uint32
	AltitudeMeters float32
	VelocityMS     float32
	EngineStatus   uint8
}

// DecodeTelemetryPacketStrict decodes the repository's deterministic 13-byte
// demonstration format: sequence, altitude, velocity, and one status byte.
func DecodeTelemetryPacketStrict(data []byte) (TelemetryFrame, error) {
	if len(data) != telemetryPacketSize {
		return TelemetryFrame{}, fmt.Errorf("packet length: got %d want %d", len(data), telemetryPacketSize)
	}

	altitude := math.Float32frombits(binary.BigEndian.Uint32(data[4:8]))
	velocity := math.Float32frombits(binary.BigEndian.Uint32(data[8:12]))
	if math.IsNaN(float64(altitude)) || math.IsInf(float64(altitude), 0) {
		return TelemetryFrame{}, errors.New("altitude must be finite")
	}
	if math.IsNaN(float64(velocity)) || math.IsInf(float64(velocity), 0) {
		return TelemetryFrame{}, errors.New("velocity must be finite")
	}

	return TelemetryFrame{
		SequenceNum:    binary.BigEndian.Uint32(data[0:4]),
		AltitudeMeters: altitude,
		VelocityMS:     velocity,
		EngineStatus:   data[12],
	}, nil
}

// DecodeTelemetryPacket preserves the original zero-value-on-invalid API while
// delegating valid input to the strict decoder.
func DecodeTelemetryPacket(data []byte) TelemetryFrame {
	frame, err := DecodeTelemetryPacketStrict(data)
	if err != nil {
		return TelemetryFrame{}
	}
	return frame
}

// EncodeTelemetryPacket is the inverse demonstration encoder used by tests.
func EncodeTelemetryPacket(frame TelemetryFrame) ([]byte, error) {
	if math.IsNaN(float64(frame.AltitudeMeters)) || math.IsInf(float64(frame.AltitudeMeters), 0) {
		return nil, errors.New("altitude must be finite")
	}
	if math.IsNaN(float64(frame.VelocityMS)) || math.IsInf(float64(frame.VelocityMS), 0) {
		return nil, errors.New("velocity must be finite")
	}
	packet := make([]byte, telemetryPacketSize)
	binary.BigEndian.PutUint32(packet[0:4], frame.SequenceNum)
	binary.BigEndian.PutUint32(packet[4:8], math.Float32bits(frame.AltitudeMeters))
	binary.BigEndian.PutUint32(packet[8:12], math.Float32bits(frame.VelocityMS))
	packet[12] = frame.EngineStatus
	return packet, nil
}

func main() {
	packet, err := EncodeTelemetryPacket(TelemetryFrame{
		SequenceNum:    42001,
		AltitudeMeters: 15400.5,
		VelocityMS:     1250.0,
		EngineStatus:   0x01,
	})
	if err != nil {
		panic(err)
	}
	frame, err := DecodeTelemetryPacketStrict(packet)
	if err != nil {
		panic(err)
	}
	fmt.Printf("Telemetry Frame #%d: Altitude=%.1fm, Velocity=%.1fm/s\n", frame.SequenceNum, frame.AltitudeMeters, frame.VelocityMS)
}
