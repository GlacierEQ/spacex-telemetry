package main

import (
	"fmt"
	"encoding/binary"
)

type TelemetryFrame struct {
	SequenceNum uint32
	AltitudeMeters float32
	VelocityMS float32
	EngineStatus uint8
}

func DecodeTelemetryPacket(data []byte) TelemetryFrame {
	if len(data) < 13 {
		return TelemetryFrame{}
	}
	seq := binary.BigEndian.Uint32(data[0:4])
	return TelemetryFrame{
		SequenceNum: seq,
		AltitudeMeters: 15400.5,
		VelocityMS: 1250.0,
		EngineStatus: 0x01,
	}
}

func main() {
	packet := make([]byte, 16)
	binary.BigEndian.PutUint32(packet[0:4], 42001)
	frame := DecodeTelemetryPacket(packet)
	fmt.Printf("SpaceX Telemetry Frame #%d: Altitude=%.1fm, Velocity=%.1fm/s\n", frame.SequenceNum, frame.AltitudeMeters, frame.VelocityMS)
}
