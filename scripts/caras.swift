// caras.swift — detecta caras con Vision (macOS) para los focos de las fotos de /historia (historia.py focos).
// Uso (lo compila historia.py la primera vez en sesiones/_descargas/bin/caras): caras IMAGEN... → JSON
// {ruta: [{x, y, w, h, conf}]} con coordenadas 0–1 desde la esquina de arriba a la izquierda.
import Foundation
import Vision
import AppKit

var salida: [String: [[String: Double]]] = [:]
for ruta in CommandLine.arguments.dropFirst() {
    guard let img = NSImage(contentsOfFile: ruta),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { salida[ruta] = []; continue }
    let req = VNDetectFaceRectanglesRequest()
    try? VNImageRequestHandler(cgImage: cg, options: [:]).perform([req])
    salida[ruta] = (req.results ?? []).map { f in
        let b = f.boundingBox
        return ["x": Double(b.minX), "y": Double(1 - b.maxY), "w": Double(b.width), "h": Double(b.height),
                "conf": Double(f.confidence)]
    }
}
let d = try! JSONSerialization.data(withJSONObject: salida, options: [.sortedKeys])
print(String(data: d, encoding: .utf8)!)
