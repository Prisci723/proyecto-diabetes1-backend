// URL del API Backend
const API_URL = 'http://localhost:8000';

// Estado de la aplicación
let alimentosSeleccionados = [];
let categoriaActual = null;

// Estado de la dieta seleccionada
let dietaSeleccionada = null;
let tiempoComidaSeleccionado = null;
let carbohidratosPermitidos = 0;
let caloriasDietaActual = null;

// Inicializar la aplicación
document.addEventListener('DOMContentLoaded', () => {
    cargarCategorias();
});

/**
 * Cargar todas las categorías desde el API
 */
async function cargarCategorias() {
    try {
        const response = await fetch(`${API_URL}/categorias`);
        const data = await response.json();
        
        mostrarCategorias(data.categorias);
    } catch (error) {
        console.error('Error al cargar categorías:', error);
        mostrarError('No se pudieron cargar las categorías. Verifica que el servidor esté corriendo.');
    }
}

/**
 * Mostrar categorías en la interfaz
 */
function mostrarCategorias(categorias) {
    const container = document.getElementById('categorias-container');
    container.innerHTML = '';
    
    categorias.forEach(categoria => {
        const card = document.createElement('div');
        card.className = 'categoria-card';
        card.onclick = () => seleccionarCategoria(categoria.id, categoria.nombre);
        
        card.innerHTML = `
            <h3>${categoria.nombre}</h3>
        `;
        
        container.appendChild(card);
    });
}

/**
 * Seleccionar una categoría y mostrar sus alimentos
 */
async function seleccionarCategoria(categoriaId, categoriaNombre) {
    // Validar que se haya seleccionado una dieta
    if (!dietaSeleccionada || !tiempoComidaSeleccionado) {
        alert('⚠️ Debes seleccionar una Dieta y un Tiempo de Comida primero.\n\nPor favor, haz clic en uno de los botones de dieta en el encabezado.');
        return;
    }
    
    categoriaActual = categoriaId;
    
    // Ocultar categorías y mostrar alimentos
    document.querySelector('.categorias-section').style.display = 'none';
    document.getElementById('alimentos-section').style.display = 'block';
    document.getElementById('categoria-titulo').textContent = categoriaNombre;
    
    // Cargar alimentos
    await cargarAlimentos(categoriaId);
}

/**
 * Cargar alimentos de una categoría específica
 */
async function cargarAlimentos(categoria) {
    const container = document.getElementById('alimentos-container');
    container.innerHTML = '<div class="loader">Cargando alimentos...</div>';
    
    try {
        const response = await fetch(`${API_URL}/alimentos/${categoria}`);
        const alimentos = await response.json();
        
        mostrarAlimentos(alimentos, categoria);
    } catch (error) {
        console.error('Error al cargar alimentos:', error);
        container.innerHTML = '<p class="texto-vacio">Error al cargar los alimentos</p>';
    }
}

/**
 * Mostrar lista de alimentos
 */
function mostrarAlimentos(alimentos, categoria) {
    const container = document.getElementById('alimentos-container');
    container.innerHTML = '';
    
    if (alimentos.length === 0) {
        container.innerHTML = '<p class="texto-vacio">No hay alimentos registrados en esta categoría</p>';
        return;
    }
    
    // Si es categoría de platos preparados, agrupar por plato_base
    if (categoria === 'platos_preparados') {
        mostrarPlatosPreparados(alimentos, categoria);
        return;
    }
    
    alimentos.forEach(alimento => {
        const item = document.createElement('div');
        item.className = 'alimento-item';
        
        // Verificar si el alimento ya está seleccionado
        const estaSeleccionado = alimentosSeleccionados.some(
            a => a.id_alimento === alimento.id && a.categoria === categoria
        );
        
        if (estaSeleccionado) {
            item.classList.add('seleccionado');
        }
        
        item.innerHTML = `
            <input 
                type="checkbox" 
                class="alimento-checkbox" 
                id="alimento-${alimento.id}"
                ${estaSeleccionado ? 'checked' : ''}
                onchange="toggleAlimento('${categoria}', ${alimento.id}, '${alimento.alimento}', ${alimento.hidratos_carbono || 0})"
            >
            <div class="alimento-info">
                <div class="alimento-nombre">${alimento.alimento}</div>
                <div class="alimento-detalles">
                    <span class="alimento-detalle-item">📏 ${alimento.cantidad_sugerida || '-'} ${alimento.unidad || ''}</span>
                    <span class="alimento-detalle-item">⚡ ${alimento.energia_kcal || '-'} kcal</span>
                    <span class="alimento-detalle-item">🥩 ${alimento.proteina || '-'}g proteína</span>
                </div>
            </div>
            <div class="carbohidratos-badge">
                ${alimento.hidratos_carbono || 0}g CHO
            </div>
        `;
        
        container.appendChild(item);
    });
}

/**
 * Mostrar platos preparados con imágenes agrupados
 */
function mostrarPlatosPreparados(alimentos, categoria) {
    const container = document.getElementById('alimentos-container');
    container.innerHTML = '';
    
    // Agrupar por plato_base
    const platosAgrupados = {};
    alimentos.forEach(alimento => {
        const platoBase = alimento.plato_base || alimento.alimento;
        if (!platosAgrupados[platoBase]) {
            platosAgrupados[platoBase] = {
                imagen: alimento.imagen,
                porciones: []
            };
        }
        platosAgrupados[platoBase].porciones.push(alimento);
    });
    
    // Mostrar cada grupo de platos
    Object.keys(platosAgrupados).forEach(platoBase => {
        const grupo = platosAgrupados[platoBase];
        
        const grupoDiv = document.createElement('div');
        grupoDiv.className = 'plato-grupo';
        
        let porcionesHTML = '';
        grupo.porciones.forEach(alimento => {
            const estaSeleccionado = alimentosSeleccionados.some(
                a => a.id_alimento === alimento.id && a.categoria === categoria
            );
            
            porcionesHTML += `
                <div class="porcion-item ${estaSeleccionado ? 'seleccionado' : ''}">
                    <input 
                        type="checkbox" 
                        class="alimento-checkbox" 
                        id="alimento-${alimento.id}"
                        ${estaSeleccionado ? 'checked' : ''}
                        onchange="toggleAlimento('${categoria}', ${alimento.id}, '${alimento.alimento}', ${alimento.hidratos_carbono || 0})"
                    >
                    <div class="porcion-info">
                        <div class="porcion-nombre">${alimento.alimento}</div>
                        <div class="porcion-detalles">
                            <span>⚡ ${alimento.energia_kcal || '-'} kcal</span>
                            <span>🥩 ${alimento.proteina || '-'}g proteína</span>
                        </div>
                    </div>
                    <div class="carbohidratos-badge-small">
                        ${alimento.hidratos_carbono || 0}g CHO
                    </div>
                </div>
            `;
        });
        
        grupoDiv.innerHTML = `
            <div class="plato-imagen-container">
                <img src="images/${grupo.imagen}" alt="${platoBase}" class="plato-imagen" onerror="this.src='images/placeholder.jpg'">
                <h3 class="plato-nombre">${platoBase}</h3>
            </div>
            <div class="porciones-lista">
                ${porcionesHTML}
            </div>
        `;
        
        container.appendChild(grupoDiv);
    });
}

/**
 * Toggle selección de alimento (agregar o quitar)
 */
function toggleAlimento(categoria, id, nombre, carbohidratos) {
    const index = alimentosSeleccionados.findIndex(
        a => a.id_alimento === id && a.categoria === categoria
    );
    
    if (index > -1) {
        // Quitar alimento
        alimentosSeleccionados.splice(index, 1);
    } else {
        // Agregar alimento
        alimentosSeleccionados.push({
            categoria: categoria,
            id_alimento: id,
            nombre_alimento: nombre,
            hidratos_carbono: carbohidratos
        });
    }
    
    actualizarResumen();
}

/**
 * Actualizar el resumen de carbohidratos
 */
function actualizarResumen() {
    const container = document.getElementById('alimentos-seleccionados');
    const totalElement = document.getElementById('total-carbohidratos');
    const alertaElement = document.getElementById('alerta-carbohidratos');
    
    if (alimentosSeleccionados.length === 0) {
        container.innerHTML = '<p class="texto-vacio">No has seleccionado ningún alimento</p>';
        totalElement.textContent = '0.0';
        alertaElement.style.display = 'none';
        return;
    }
    
    // Mostrar alimentos seleccionados
    container.innerHTML = '';
    alimentosSeleccionados.forEach(alimento => {
        const item = document.createElement('div');
        item.className = 'alimento-seleccionado-item';
        item.innerHTML = `
            <span class="alimento-seleccionado-nombre">${alimento.nombre_alimento}</span>
            <span class="alimento-seleccionado-carbohidratos">${alimento.hidratos_carbono}g CHO</span>
        `;
        container.appendChild(item);
    });
    
    // Calcular y mostrar total
    const total = alimentosSeleccionados.reduce(
        (sum, alimento) => sum + alimento.hidratos_carbono, 
        0
    );
    totalElement.textContent = total.toFixed(1);
    
    // Mostrar alerta de comparación si hay dieta seleccionada
    if (dietaSeleccionada && carbohidratosPermitidos > 0) {
        alertaElement.style.display = 'block';
        
        const diferencia = total - carbohidratosPermitidos;
        const porcentaje = (total / carbohidratosPermitidos) * 100;
        
        if (total <= carbohidratosPermitidos) {
            // Dentro del límite
            alertaElement.className = 'alerta-carbohidratos alerta-ok';
            alertaElement.innerHTML = `
                ✅ <strong>Excelente!</strong> Estás dentro del límite permitido.<br>
                Has consumido ${total.toFixed(1)}g de ${carbohidratosPermitidos}g permitidos (${porcentaje.toFixed(1)}%)
            `;
        } else if (diferencia <= 5) {
            // Ligeramente sobre el límite
            alertaElement.className = 'alerta-carbohidratos alerta-warning';
            alertaElement.innerHTML = `
                ⚠️ <strong>Atención:</strong> Estás ligeramente sobre el límite.<br>
                Has consumido ${total.toFixed(1)}g de ${carbohidratosPermitidos}g permitidos (+${diferencia.toFixed(1)}g)
            `;
        } else {
            // Muy sobre el límite
            alertaElement.className = 'alerta-carbohidratos alerta-danger';
            alertaElement.innerHTML = `
                ❌ <strong>Cuidado:</strong> Has excedido el límite de carbohidratos.<br>
                Has consumido ${total.toFixed(1)}g de ${carbohidratosPermitidos}g permitidos (+${diferencia.toFixed(1)}g)
            `;
        }
        
        // Mostrar modal de alerta si se excede el límite
        if (total > carbohidratosPermitidos) {
            mostrarModalExceso(total, carbohidratosPermitidos, diferencia);
        }
    } else {
        alertaElement.style.display = 'none';
    }
}

/**
 * Volver a la vista de categorías
 */
function volverACategorias() {
    document.querySelector('.categorias-section').style.display = 'block';
    document.getElementById('alimentos-section').style.display = 'none';
    categoriaActual = null;
}

/**
 * Limpiar toda la selección
 */
function limpiarSeleccion() {
    if (alimentosSeleccionados.length === 0) {
        return;
    }
    
    if (confirm('¿Estás seguro de que deseas limpiar toda la selección?')) {
        alimentosSeleccionados = [];
        actualizarResumen();
        
        // Si estamos viendo alimentos, recargar la vista para desmarcar checkboxes
        if (categoriaActual) {
            cargarAlimentos(categoriaActual);
        }
    }
}

/**
 * Mostrar mensaje de error
 */
function mostrarError(mensaje) {
    const container = document.getElementById('categorias-container');
    container.innerHTML = `
        <div style="text-align: center; padding: 40px; color: #e74c3c;">
            <h3>⚠️ Error</h3>
            <p>${mensaje}</p>
        </div>
    `;
}

/**
 * Datos de las dietas
 */
const dietasData = {
    1200: {
        titulo: "CUADRO DIETOSINTÉTICO - DIETA 1200 kcal/día",
        nombre: "1200 Kcal/día",
        nutrientes: [
            { nombre: "Hidratos de carbono", porcentaje: "60%", kcal: 720, gramos: 180 },
            { nombre: "Proteína", porcentaje: "15%", kcal: 180, gramos: 45 },
            { nombre: "Lípidos", porcentaje: "25%", kcal: 300, gramos: 33 }
        ],
        tiemposComida: {
            desayuno: { tiempo: "Desayuno", porcentaje: "30%", kcal: 216, carbohidratos: 54 },
            almuerzo: { tiempo: "Almuerzo", porcentaje: "40%", kcal: 288, carbohidratos: 72 },
            cena: { tiempo: "Cena", porcentaje: "30%", kcal: 216, carbohidratos: 54 }
        }
    },
    1400: {
        titulo: "CUADRO DIETOSINTÉTICO - DIETA 1400 kcal/día",
        nombre: "1400 Kcal/día",
        nutrientes: [
            { nombre: "Hidratos de carbono", porcentaje: "60%", kcal: 840, gramos: 210 },
            { nombre: "Proteína", porcentaje: "15%", kcal: 210, gramos: 52 },
            { nombre: "Lípidos", porcentaje: "25%", kcal: 350, gramos: 39 }
        ],
        tiemposComida: {
            desayuno: { tiempo: "Desayuno", porcentaje: "30%", kcal: 252, carbohidratos: 63 },
            almuerzo: { tiempo: "Almuerzo", porcentaje: "40%", kcal: 336, carbohidratos: 84 },
            cena: { tiempo: "Cena", porcentaje: "30%", kcal: 252, carbohidratos: 63 }
        }
    },
    1600: {
        titulo: "CUADRO DIETOSINTÉTICO - DIETA 1600 kcal/día",
        nombre: "1600 Kcal/día",
        nutrientes: [
            { nombre: "Hidratos de carbono", porcentaje: "60%", kcal: 986, gramos: 246 },
            { nombre: "Proteína", porcentaje: "15%", kcal: 247, gramos: 62 },
            { nombre: "Lípidos", porcentaje: "25%", kcal: 411, gramos: 46 }
        ],
        tiemposComida: {
            desayuno: { tiempo: "Desayuno", porcentaje: "30%", kcal: 296, carbohidratos: 74 },
            almuerzo: { tiempo: "Almuerzo", porcentaje: "40%", kcal: 394, carbohidratos: 98 },
            cena: { tiempo: "Cena", porcentaje: "30%", kcal: 296, carbohidratos: 74 }
        }
    },
    1800: {
        titulo: "CUADRO DIETOSINTÉTICO - DIETA 1800 kcal/día",
        nombre: "1800 Kcal/día",
        nutrientes: [
            { nombre: "Hidratos de carbono", porcentaje: "60%", kcal: 1080, gramos: 270 },
            { nombre: "Proteína", porcentaje: "15%", kcal: 270, gramos: 68 },
            { nombre: "Lípidos", porcentaje: "25%", kcal: 450, gramos: 50 }
        ],
        tiemposComida: {
            desayuno: { tiempo: "Desayuno", porcentaje: "30%", kcal: 324, carbohidratos: 81 },
            almuerzo: { tiempo: "Almuerzo", porcentaje: "40%", kcal: 432, carbohidratos: 108 },
            cena: { tiempo: "Cena", porcentaje: "30%", kcal: 324, carbohidratos: 81 }
        }
    }
};

/**
 * Abrir modal con información de la dieta
 */
function abrirModalDieta(calorias) {
    const modal = document.getElementById('modal-dieta');
    const contenido = document.getElementById('contenido-dieta');
    const dieta = dietasData[calorias];
    
    if (!dieta) {
        alert('Información de dieta no disponible');
        return;
    }
    
    caloriasDietaActual = calorias;
    
    // Crear array de tiempos de comida
    const tiemposArray = Object.values(dieta.tiemposComida);
    
    contenido.innerHTML = `
        <h2 class="dieta-titulo">${dieta.titulo}</h2>
        
        <div class="dieta-seccion">
            <table class="dieta-tabla">
                <thead>
                    <tr>
                        <th>NUTRIMENTO</th>
                        <th>PORCENTAJE</th>
                        <th>KCAL</th>
                        <th>GRAMOS</th>
                    </tr>
                </thead>
                <tbody>
                    ${dieta.nutrientes.map(n => `
                        <tr>
                            <td><strong>${n.nombre}</strong></td>
                            <td>${n.porcentaje}</td>
                            <td>${n.kcal}</td>
                            <td>${n.gramos}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
        
        <div class="dieta-seccion">
            <table class="dieta-tabla">
                <caption>PLAN DE ALIMENTACIÓN PARA CARBOHIDRATOS POR TIEMPOS DE COMIDA</caption>
                <thead>
                    <tr>
                        <th>TIEMPO DE COMIDA</th>
                        <th>PORCENTAJE</th>
                        <th>KCAL</th>
                        <th>GRAMOS DE CARBOHIDRATOS</th>
                    </tr>
                </thead>
                <tbody>
                    ${tiemposArray.map(t => `
                        <tr>
                            <td><strong>${t.tiempo}</strong></td>
                            <td>${t.porcentaje}</td>
                            <td>${t.kcal}</td>
                            <td>${t.carbohidratos}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    // Resetear selector
    document.getElementById('tiempo-comida').value = '';
    
    modal.style.display = 'block';
}

/**
 * Cerrar modal de dieta
 */
function cerrarModalDieta() {
    const modal = document.getElementById('modal-dieta');
    modal.style.display = 'none';
}

/**
 * Aceptar la dieta y tiempo de comida seleccionados
 */
function aceptarDieta() {
    const tiempoSelect = document.getElementById('tiempo-comida');
    const tiempoValor = tiempoSelect.value;
    
    if (!tiempoValor) {
        alert('⚠️ Por favor, selecciona un Tiempo de Comida');
        return;
    }
    
    if (!caloriasDietaActual) {
        alert('⚠️ Error: No se ha seleccionado una dieta');
        return;
    }
    
    const dieta = dietasData[caloriasDietaActual];
    const tiempoData = dieta.tiemposComida[tiempoValor];
    
    // Guardar selección
    dietaSeleccionada = caloriasDietaActual;
    tiempoComidaSeleccionado = tiempoValor;
    carbohidratosPermitidos = tiempoData.carbohidratos;
    
    // Actualizar información en el header
    document.getElementById('dieta-nombre').textContent = dieta.nombre;
    document.getElementById('tiempo-nombre').textContent = tiempoData.tiempo;
    document.getElementById('carbohidratos-permitidos').textContent = tiempoData.carbohidratos;
    document.getElementById('dieta-seleccionada-info').style.display = 'block';
    
    // Cerrar modal
    cerrarModalDieta();
    
    // Mostrar secciones de categorías
    document.querySelector('.categorias-section').style.display = 'block';
    
    // Limpiar selección anterior
    alimentosSeleccionados = [];
    actualizarResumen();
    
    alert(`✅ Dieta ${dieta.nombre} configurada
Tiempo de comida: ${tiempoData.tiempo}
Carbohidratos permitidos: ${tiempoData.carbohidratos}g`);
}

/**
 * Cancelar selección de dieta
 */
function cancelarDieta() {
    if (confirm('¿Estás seguro de cancelar? Deberás seleccionar una dieta para continuar.')) {
        cerrarModalDieta();
    }
}

// Cerrar modal al hacer clic fuera de él
window.onclick = function(event) {
    const modal = document.getElementById('modal-dieta');
    if (event.target === modal) {
        cerrarModalDieta();
    }
    
    const modalAlerta = document.getElementById('modal-alerta-exceso');
    if (event.target === modalAlerta) {
        cerrarModalAlerta();
    }
}

/**
 * Mostrar modal de alerta cuando se excede el límite de carbohidratos
 */
function mostrarModalExceso(totalActual, permitido, exceso) {
    const modal = document.getElementById('modal-alerta-exceso');
    
    // Actualizar valores en el modal
    document.getElementById('alerta-permitidos').textContent = permitido.toFixed(1);
    document.getElementById('alerta-actuales').textContent = totalActual.toFixed(1);
    document.getElementById('alerta-exceso').textContent = exceso.toFixed(1);
    
    // Mostrar modal
    modal.style.display = 'block';
}

/**
 * Cerrar modal de alerta de exceso
 */
function cerrarModalAlerta() {
    const modal = document.getElementById('modal-alerta-exceso');
    modal.style.display = 'none';
}