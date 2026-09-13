//
//  AcousticPhysics.swift
//  ANCSoftware
//
//  Branch Education Acoustic Superposition & Wave Interference Engine.
//  Accelerated with Apple Accelerate vDSP.
//

import Foundation
import Accelerate

public enum AcousticPhysics {
    /// Speed of sound in dry air at 20°C in meters per second.
    public static let speedOfSound: Float = 343.0
    
    /// Calculate acoustic wavelength λ = c / f in meters.
    @inlinable
    public static func wavelength(frequency: Float) -> Float {
        guard frequency > 0 else { return 0 }
        return speedOfSound / frequency
    }
    
    /// Calculate acoustic transit time in microseconds over a given distance in millimeters.
    @inlinable
    public static func transitTimeMicroseconds(distanceMM: Float) -> Float {
        let distanceMeters = distanceMM / 1000.0
        return (distanceMeters / speedOfSound) * 1_000_000.0
    }
    
    /// Invert phase by 180° using Apple Accelerate vector negation.
    /// P_anti(t) = -P_noise(t)
    public static func invertPhase(_ buffer: [Float]) -> [Float] {
        var output = [Float](repeating: 0, count: buffer.count)
        vDSP_vneg(buffer, 1, &output, 1, vDSP_Length(buffer.count))
        return output
    }
    
    /// Acoustic Superposition: P_resultant = P_noise + P_anti
    /// Destructive interference when P_anti = -P_noise.
    public static func superimpose(noise: [Float], antiNoise: [Float]) -> [Float] {
        let count = min(noise.count, antiNoise.count)
        var output = [Float](repeating: 0, count: count)
        vDSP_vadd(noise, 1, antiNoise, 1, &output, 1, vDSP_Length(count))
        return output
    }
    
    /// Calculate Root-Mean-Square (RMS) amplitude of an audio buffer.
    public static func rms(_ buffer: [Float]) -> Float {
        guard !buffer.isEmpty else { return 0.0 }
        var result: Float = 0.0
        vDSP_rmsqv(buffer, 1, &result, vDSP_Length(buffer.count))
        return result
    }
    
    /// Calculate acoustic attenuation in decibels: 20 * log10(RMS_out / RMS_in)
    public static func attenuationDB(input: [Float], output: [Float]) -> Float {
        let inRMS = rms(input)
        let outRMS = rms(output)
        guard inRMS > 1e-7 else { return 0.0 }
        let ratio = max(outRMS / inRMS, 1e-6)
        return 20.0 * log10(ratio)
    }
}
