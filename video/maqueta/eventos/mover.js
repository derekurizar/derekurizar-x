// Evento «mover» (ficha: mover.json): el actor va a un lugar en `dur` segundos. Lo resuelve scripts/maqueta_tipos/actor.py
// en las claves del actor (su trayectoria ya lo trae); aquí no dibuja.
(function (MAQ) {
  MAQ.EVENTOS.mover = { orden: 22, aplicar() {} };
})(window.MAQ = window.MAQ || { PIEZAS: {}, EVENTOS: {}, OBJETOS: {}, MUNDOS: {} });
