import Foundation
import Vision
let url = URL(fileURLWithPath: CommandLine.arguments[1])
let request = VNDetectBarcodesRequest()
request.usesCPUOnly = true
do {
    try VNImageRequestHandler(url: url).perform([request])
    for result in request.results ?? [] { print(result.payloadStringValue ?? "UNREADABLE") }
} catch { print("QR decode unavailable: \(error.localizedDescription)"); exit(1) }
