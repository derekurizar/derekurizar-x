// Evento «acelerar» (ficha: acelerar.json): un tramo frenado se suelta (o todo el flujo cambia de velocidad) en `dur`
// segundos. Como «frenar», lo resuelve scripts/maqueta_tipos/flujo.py en la trayectoria de cada vehículo; aquí no dibuja.
(function (MAQ) {
  MAQ.EVENTOS.acelerar = { orden: 22, aplicar() {} };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
