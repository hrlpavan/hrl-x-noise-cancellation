//
//  AdaptiveFilter.swift
//  ANCSoftware
//
//  Normalized Least Mean Squares (NLMS) & Filtered-X LMS (FxLMS) Engine.
//

import Foundation
import Accelerate

public final class FxLMSFilter {
    public let filterLength: Int
    public var weights: [Float]
    @usableFromInline internal var buffer: [Float]
    public var stepSize: Float
    public var leakage: Float
    
    public init(filterLength: Int = 64, stepSize: Float = 0.015, leakage: Float = 0.9999) {
        self.filterLength = filterLength
        self.weights = [Float](repeating: 0.0, count: filterLength)
        self.buffer = [Float](repeating: 0.0, count: filterLength)
        self.stepSize = stepSize
        self.leakage = leakage
    }
    
    /// Process a single acoustic sample through the adaptive FIR filter.
    /// Returns: Anti-noise sample y[n] = Σ w[k] * x[n-k]
    @inlinable
    public func filter(sample: Float) -> Float {
        // Shift buffer
        for i in stride(from: filterLength - 1, to: 0, by: -1) {
            buffer[i] = buffer[i - 1]
        }
        buffer[0] = sample
        
        // Dot product: y = weights • buffer
        var y: Float = 0.0
        vDSP_dotpr(weights, 1, buffer, 1, &y, vDSP_Length(filterLength))
        return y
    }
    
    /// Adapt FIR weights using error feedback e[n]:
    /// w_{k+1} = (1 - λ) w_k + μ * e[n] * x[n-k] / (||x||^2 + ε)
    @inlinable
    public func adapt(error: Float) {
        var energy: Float = 0.0
        vDSP_svesq(buffer, 1, &energy, vDSP_Length(filterLength))
        let norm = stepSize / (energy + 1e-5)
        
        for i in 0..<filterLength {
            weights[i] = (weights[i] * leakage) + (norm * error * buffer[i])
        }
    }
    
    /// Reset filter state to zero.
    public func reset() {
        weights = [Float](repeating: 0.0, count: filterLength)
        buffer = [Float](repeating: 0.0, count: filterLength)
    }
}
