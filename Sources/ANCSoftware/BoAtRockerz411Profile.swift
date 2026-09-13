//
//  BoAtRockerz411Profile.swift
//  ANCSoftware
//
//  Hardware Calibration Profile for boAt Rockerz 411 ANC Headphones.
//

import Foundation

public struct BoAtRockerz411Profile {
    public static let modelName = "boAt Rockerz 411 ANC"
    public static let driverDiameterMM: Float = 40.0
    public static let driverImpedanceOhms: Float = 32.0
    
    /// Physical distance between feedforward reference mic and speaker diaphragm (45 mm).
    public static let micToSpeakerDistanceMM: Float = 45.0
    
    /// Acoustic transit delay across the 45 mm air gap:
    /// t = 0.045 m / 343 m/s = 131.2 microseconds.
    public static let acousticDelayMicroseconds: Float = 131.195
    
    /// Samples delay at 48,000 Hz sampling rate (131.2 μs * 48,000 Hz = 6.3 samples).
    public static let delaySamples48kHz: Float = 6.297
    
    /// Frequency attenuation capability profile:
    /// - 120 Hz Ceiling Fan Hum: -38 dB to -42 dB
    /// - 220 Hz Table Fan Motor: -34 dB
    /// - 65 Hz AC Compressor: -40 dB
    /// - 450 Hz PC Blower: -28 dB
    public static func expectedAttenuationDB(forFrequency frequency: Float) -> Float {
        switch frequency {
        case ..<80:
            return -40.0 // AC Hum
        case 80..<160:
            return -42.0 // Ceiling fan fundamental (120 Hz)
        case 160..<300:
            return -35.0 // Table fan (220 Hz)
        case 300..<600:
            return -28.0 // High-speed server/PC fan
        default:
            return -18.0 // High frequencies (passive isolation dominates)
        }
    }
}
