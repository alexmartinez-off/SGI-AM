// Script extraído de informe_baja.html para inicializar el cálculo de valor residual

document.addEventListener('DOMContentLoaded', function() {
    const valorAdquisicion = window.valorAdquisicion || 0;
    const fechaAdquisicion = window.fechaAdquisicion || '2000-01-01';
    const vidaUtil = window.vidaUtil || 5;
    if (window.initValorResidual) {
        window.initValorResidual(valorAdquisicion, fechaAdquisicion, vidaUtil);
    }
});
