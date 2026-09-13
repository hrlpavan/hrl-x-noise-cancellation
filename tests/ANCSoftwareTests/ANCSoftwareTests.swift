//
//  ANCSoftwareTests.swift
//  ANCSoftwareTests
//
//  Pure Swift Assert-Based Validation Suite.
//

import Foundation
import ANCSoftware

print("Running ANCSoftware Swift Test Suite...")

// 1. Wave Inversion Test
let noise: [Float] = [0.1, 0.5, 0.8, -0.4, -0.9, 0.0]
let anti = AcousticPhysics.invertPhase(noise)
assert(noise.count == anti.count, "Count mismatch")
for i in 0..<noise.count {
    assert(abs(anti[i] - (-noise[i])) < 1e-5, "180 degree inversion failed")
}
print("[✓] testAcousticWaveInversion passed")

// 2. Destructive Interference Test
let sampleCount = 4800
let noiseSin: [Float] = (0..<sampleCount).map { i in sin(Float(i) * 2.0 * .pi * 120.0 / 48000.0) }
let antiSin = AcousticPhysics.invertPhase(noiseSin)
let annihilated = AcousticPhysics.superimpose(noise: noiseSin, antiNoise: antiSin)
let attenuation = AcousticPhysics.attenuationDB(input: noiseSin, output: annihilated)
assert(attenuation < -80.0, "Superposition attenuation must be deep")
print("[✓] testDestructiveInterference passed (\(attenuation) dB)")

// 3. boAt Rockerz 411 Profile Test
assert(BoAtRockerz411Profile.micToSpeakerDistanceMM == 45.0, "boAt 411 distance mismatch")
assert(abs(BoAtRockerz411Profile.acousticDelayMicroseconds - 131.195) < 0.1, "Delay calculation mismatch")
assert(BoAtRockerz411Profile.expectedAttenuationDB(forFrequency: 120.0) <= -40.0, "boAt 411 fan attenuation mismatch")
print("[✓] testBoAtRockerz411Profile passed")

// 4. Silicon Cycle Budget Test
let silicon = H1SiliconCore()
assert(silicon.executionTimeMicroseconds < H1SiliconCore.cycleBudgetMicroseconds, "Silicon budget exceeded")
print("[✓] testSiliconCycleBudget passed (\(silicon.executionTimeMicroseconds) μs < \(H1SiliconCore.cycleBudgetMicroseconds) μs)")

// 5. Full Pipeline Engine Test
let engine = ANCEngine()
let (residual, antiOut) = engine.processBuffer(noiseBuffer: noiseSin)
assert(residual.count == noiseSin.count, "Residual count mismatch")
assert(antiOut.count == noiseSin.count, "Anti-noise count mismatch")
assert(engine.latestAttenuationDB < -10.0, "Pipeline attenuation failed")
print("[✓] testFullEnginePipeline passed")

print("====================================================================")
print("ALL 5 SWIFT VALIDATION SUITES PASSED SUCCESSFULLY!")
print("====================================================================")
