// Evento «frenar» (ficha: frenar.json): un tramo de un flujo baja a `vel_kmh` en `dur` segundos y la cola crece hacia
// atrás. El efecto NO se calcula aquí: scripts/maqueta_tipos/flujo.py lo mete en la trayectoria de cada vehículo (modelo de
// Newell, _movimiento.py), así la cámara que sigue y las anotaciones lo ven igual. Este módulo solo existe para que el motor
// conozca el tipo (aplicar no dibuja nada).
(function (MAQ) {
  MAQ.EVENTOS.frenar = { orden: 22, aplicar() {} };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
