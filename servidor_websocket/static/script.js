// =================== VARIABLES GLOBALES ===================
let selectedClientId = null;
let selectedClientName = null;
let selectedGroupName = null;
let frasesLocal = [];
let usuarioActual = null;

// Siempre borra la sesión visual al recargar la página
window.addEventListener("load", () => {
  sessionStorage.clear();
});

// =================== AL CARGAR LA PÁGINA ===================
window.addEventListener("DOMContentLoaded", () => {
  console.log("✅ Página cargada");

  // 🔐 Validar sesión con el servidor (Línea ~10: Se mantiene sin prefijo)
  fetch("/usuario_actual")
    .then(res => res.json())
    .then(data => {
      if (!data.usuario) {
        console.log("⛔ No hay sesión activa.");
        sessionStorage.clear();
        bloquearInterfaz(); // Solo bloquea la interfaz, NO redirige si ya estás en "/"
        return;
      }

      sessionStorage.setItem("usuario", data.usuario);
      usuarioActual = data.usuario;
      console.log("✅ Sesión confirmada como:", data.usuario);


      // 🔓 Si hay sesión, desbloquear interfaz y cargar datos
      document.getElementById("userDisplay").textContent = `👤 ${usuarioActual}`;
      document.getElementById("loginBtn").style.display = "none";
      document.getElementById("logoutBtn").style.display = "inline-block";
      desbloquearInterfaz();
      loadClients();
      loadGroups();
      loadFrasesFromServer();
    });


  // 🔧 Mostrar solo el tab de clientes (vacío al inicio)
  document.querySelectorAll(".tab-content").forEach(t => t.style.display = "none");
  document.getElementById("clientesTab").style.display = "block";
  document.querySelectorAll(".tab-button").forEach(btn => btn.classList.remove("active"));
  document.querySelector(".tab-button").classList.add("active");

  // 🔒 Ocultar la interfaz completa
  bloquearInterfaz();

  // 🟡 Asegurar botón login funcione siempre
  document.getElementById("loginBtn").addEventListener("click", () => {
    console.log("👆 Botón login pulsado, abriendo modal");
    openModal("loginModal");

    // 🔁 Asegurar visual correcto al abrir login
    document.querySelectorAll(".tab-content").forEach(t => t.style.display = "none");
    document.getElementById("clientesTab").style.display = "block";
    document.querySelectorAll(".tab-button").forEach(btn => btn.classList.remove("active"));
    document.querySelector(".tab-button").classList.add("active");
  });

  // ✅ Permitir iniciar sesión con Enter
  document.getElementById("loginModal").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      login(); // Ejecutar la función login()
    }
  });

  // ✅ Botón logout funcional siempre
  document.getElementById("logoutBtn").onclick = () => {
    console.log("🔓 Logout pulsado");
    logout();
  };

  // 🧹 Ocultar modal por defecto
  setTimeout(() => {
    document.getElementById("loginModal").style.display = "none";
    console.log("🧹 Modal de login forzado a cerrar tras carga");
  }, 100);

  // 🌐 Socket.IO (aunque no haya sesión aún)
  const socket = io("https://172.17.204.80:5000", { transports: ["websocket"] });
  socket.on("actualizar_clientes", () => {
    if (usuarioActual) loadClients();
  });

// 🎩 Simular carga falsa con un delay entre 200ms y 2000ms
const delay = Math.floor(Math.random() * 1800) + 200;  // entre 200ms y 2000ms

setTimeout(() => {
  document.getElementById("loader").style.display = "none";
  document.getElementById("contenido").style.display = "block";
}, delay);


});

// =================== LOGIN ===================
function logout() {
  console.log("🔓 Cerrando sesión...");
  sessionStorage.removeItem("usuario");
  // Línea ~40: Se corrige de "/logout" a "/api/logout"
  fetch("/api/logout", { method: "POST" }).then(() => {
    location.reload();
  });
}

function bloquearInterfaz() {
  document.getElementById("clientesTab").style.display = "none";
  document.getElementById("gruposTab").style.display = "none";
  document.getElementById("globalMessageSection").style.display = "none";
  document.body.classList.add("body-bloqueado");  // 👈 Añadimos clase para bloquear scroll
}

function desbloquearInterfaz() {
  document.getElementById("clientesTab").style.display = "block";
  document.getElementById("gruposTab").style.display = "none"; // ❗ Aseguramos que empiece oculto
  document.getElementById("globalMessageSection").style.display = "block";
  document.body.classList.remove("body-bloqueado"); // 👈 Permitimos scroll cuando hay sesión
}

// =================== TABS ===================
function openTab(tabId, btn) {
  document.querySelectorAll(".tab-content").forEach(t => t.style.display = "none");
  document.querySelectorAll(".tab-button").forEach(b => b.classList.remove("active"));
  document.getElementById(tabId).style.display = "block";
  btn.classList.add("active");
}

// ... resto del script sigue igual ...

function mostrarMensaje(titulo, mensaje) {
  document.getElementById("mensajeModalTitulo").textContent = titulo;
  document.getElementById("mensajeModalTexto").textContent = mensaje;
  openModal("mensajeModal");
}

// CLIENTES
function loadClients() {
  fetch("/api/estado_clientes")
    .then(res => res.json())
    .then(data => renderClients(data.conectados, data.desconectados))
    .catch(err => console.error("❌ Error al cargar clientes:", err));
}


function renderClients(conectados, desconectados) {
  const conectadosList = document.getElementById("conectadosList");
  const desconectadosList = document.getElementById("desconectadosList");
  conectadosList.innerHTML = "";
  desconectadosList.innerHTML = "";

  conectados.forEach(cliente => {
    const li = document.createElement("li");
    li.classList.add("connected");
    li.innerHTML = `<span class="status-indicator online"></span> ${cliente.nombre} (Últ. Conex: ${cliente.ultima_conexion || "-"})`;
    li.addEventListener("click", () => openMensajeClienteModal(cliente.id, cliente.nombre));
    conectadosList.appendChild(li);
  });

  desconectados.forEach(cliente => {
    const li = document.createElement("li");
    li.classList.add("disconnected");
    li.innerHTML = `<span class="status-indicator offline"></span> ${cliente.nombre} (Últ. Conex: ${cliente.ultima_conexion || "-"})`;
    li.addEventListener("click", () => openEliminarClienteModal(cliente.id, cliente.nombre));
    desconectadosList.appendChild(li);
  });
}

// MENSAJE GLOBAL
function sendGlobalMessage() {
  const mensaje = document.getElementById("mensajeGlobalTextarea").value.trim();
  if (!mensaje) return;

  // Línea ~70: Se corrige de "/enviar_mensaje" a "/api/enviar_mensaje"
  fetch("/api/enviar_mensaje", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mensaje, destino: "GLOBAL" })
  }).then(() => {
    console.log("📣 Mensaje global enviado");
    document.getElementById("mensajeGlobalTextarea").value = "";
  });
}

function applyPredefinedPhrase() {
  const select = document.getElementById("frasesPredefinidas");
  const textarea = document.getElementById("mensajeGlobalTextarea");
  if (select.value) textarea.value = select.value;
}

// FRASES
function loadFrasesFromServer() {
  // Línea ~90: Se corrige de "/frases" a "/api/frases"
  fetch("/api/frases")
    .then(res => res.json())
    .then(data => {
      frasesLocal = data;
      renderFrasesEnSelect();
    });
}

function saveFrasesToServer() {
  // Línea ~100: Se corrige de "/frases" a "/api/frases"
  fetch("/api/frases", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ frases: frasesLocal })
  });
}

function renderFrasesEnSelect() {
  const select = document.getElementById("frasesPredefinidas");
  select.innerHTML = `<option value="">Frase predefinida (opcional)</option>`;
  frasesLocal.forEach(frase => {
    const opt = document.createElement("option");
    opt.value = frase;
    opt.textContent = frase;
    select.appendChild(opt);
  });
}

function openManagePhrasesModal() {
  renderFrasesEnSelect();
  const container = document.getElementById("phrasesListContainer");
  container.innerHTML = "";

  frasesLocal.forEach(phrase => {
    const div = document.createElement("div");
    div.className = "phrase-item";
    div.textContent = phrase;

    const btnDel = document.createElement("button");
    btnDel.className = "btn btn-danger btn-sm";
    btnDel.textContent = "Borrar";
    btnDel.onclick = () => removePhrase(phrase);
    div.appendChild(btnDel);

    container.appendChild(div);
  });

  openModal("managePhrasesModal");
}

function addPhrase() {
  const input = document.getElementById("newPhraseInput");
  const phrase = input.value.trim();
  if (!phrase) return;

  // 🔍 Verificamos si ya existe (ignorando mayúsculas)
  const existe = frasesLocal.some(f => f.trim().toLowerCase() === phrase.toLowerCase());
  if (existe) {
    mostrarMensaje("Frase duplicada", "Ya existe una frase similar.");
    return;
  }

  frasesLocal.push(phrase);
  saveFrasesToServer();
  input.value = "";
  openManagePhrasesModal();
}

function removePhrase(phrase) {
  const index = frasesLocal.indexOf(phrase);
  if (index >= 0) {
    frasesLocal.splice(index, 1);
    saveFrasesToServer();
    openManagePhrasesModal();
  }
}

// MENSAJES PRIVADOS
function openMensajeClienteModal(id, nombre) {
  selectedClientId = id;
  selectedClientName = nombre;
  document.getElementById("clienteObjetivo").textContent = nombre;
  document.getElementById("mensajeClienteTextarea").value = "";
  openModal("mensajeClienteModal");
}

function sendPrivateMessage() {
  const mensaje = document.getElementById("mensajeClienteTextarea").value.trim();
  if (!mensaje) return;

  // Línea ~130: Se corrige de "/enviar_mensaje" a "/api/enviar_mensaje"
  fetch("/api/enviar_mensaje", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mensaje, destino: selectedClientId })
  }).then(() => {
    closeModal("mensajeClienteModal");
  });
}

function openEliminarClienteModal(id, nombre) {
  selectedClientId = id;
  selectedClientName = nombre;
  document.getElementById("mensajeEliminarCliente").textContent = `¿Eliminar al cliente "${nombre}"?`;
  openModal("eliminarClienteModal");
}

function deleteCliente() {
  // Línea ~140: Se corrige de "/eliminar_cliente" a "/api/eliminar_cliente"
  fetch("/api/eliminar_cliente", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: selectedClientId })
  }).then(() => {
    closeModal("eliminarClienteModal");
    loadClients();
  });
}

// GRUPOS
function loadGroups() {
  // Línea ~150: Se corrige de "/grupos" a "/api/grupos"
  fetch("/api/grupos")
    .then(res => res.json())
    .then(renderGroups);
}

function renderGroups(grupos) {
  const container = document.getElementById("gruposContainer");
  container.innerHTML = "";

  grupos.forEach(grupo => {
    const div = document.createElement("div");
    const nombre = document.createElement("strong");
    nombre.textContent = grupo.nombre;

    const btnMsg = crearBoton("Mensaje", "btn btn-primary", () => openMensajeGrupoModal(grupo.nombre));
    const btnEdit = crearBoton("Editar", "btn btn-primary", () => openEditarGrupoModal(grupo.nombre, grupo.miembros));
    const btnDel = crearBoton("Eliminar", "btn btn-danger", () => openEliminarGrupoModal(grupo.nombre));
    const btnInfo = crearBoton("Info", "btn", () => openInfoGrupoModal(grupo.nombre));

    div.append(nombre, btnMsg, btnEdit, btnDel, btnInfo);
    container.appendChild(div);
  });
}

function crearBoton(texto, clases, onClick) {
  const btn = document.createElement("button");
  btn.textContent = texto;
  btn.className = clases;
  btn.onclick = onClick;
  return btn;
}

function openCrearGrupoModal() {
  document.getElementById("nuevoGrupoNombre").value = "";
  document.getElementById("nuevoGrupoMiembros").value = "";
  openModal("crearGrupoModal");
}

function createGroup() {
  const nombre = document.getElementById("nuevoGrupoNombre").value.trim();
  const miembros = document.getElementById("nuevoGrupoMiembros").value.split(",").map(m => m.trim()).filter(Boolean);
  if (!nombre) return;

  // Línea ~170: Se corrige de "/crear_grupo" a "/api/crear_grupo"
  fetch("/api/crear_grupo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nombre, miembros })
  }).then(() => {
    closeModal("crearGrupoModal");
    loadGroups();
  });
}

function openMensajeGrupoModal(nombreGrupo) {
  selectedGroupName = nombreGrupo;
  document.getElementById("grupoObjetivo").textContent = nombreGrupo;
  document.getElementById("mensajeGrupoTextarea").value = "";
  openModal("mensajeGrupoModal");
}

function sendGroupMessage() {
  const mensaje = document.getElementById("mensajeGrupoTextarea").value.trim();
  if (!mensaje) return;

  // Línea ~180: Se corrige de "/enviar_grupo" a "/api/enviar_grupo"
  fetch("/api/enviar_grupo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ grupo: selectedGroupName, mensaje })
  }).then(() => {
    closeModal("mensajeGrupoModal");
  });
}

function openEditarGrupoModal(nombre, miembros) {
  selectedGroupName = nombre;
  document.getElementById("editarGrupoNombreActual").textContent = nombre;
  document.getElementById("editarGrupoNuevoNombre").value = nombre;
  document.getElementById("editarGrupoMiembros").value = miembros.join(", ");
  openModal("editarGrupoModal");
}

function editGroup() {
  const nuevoNombre = document.getElementById("editarGrupoNuevoNombre").value.trim();
  const miembros = document.getElementById("editarGrupoMiembros").value.split(",").map(m => m.trim()).filter(Boolean);
  if (!nuevoNombre) return;

  // Línea ~190: Se corrige de "/editar_grupo" a "/api/editar_grupo"
  fetch("/api/editar_grupo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nombre_actual: selectedGroupName, nuevo_nombre: nuevoNombre, miembros })
  }).then(() => {
    closeModal("editarGrupoModal");
    loadGroups();
  });
}

function openEliminarGrupoModal(nombre) {
  selectedGroupName = nombre;
  document.getElementById("mensajeEliminarGrupo").textContent = `¿Eliminar el grupo "${nombre}"?`;
  openModal("eliminarGrupoModal");
}

function deleteGroup() {
  // Línea ~200: Se corrige de "/eliminar_grupo" a "/api/eliminar_grupo"
  fetch("/api/eliminar_grupo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nombre: selectedGroupName })
  }).then(() => {
    closeModal("eliminarGrupoModal");
    loadGroups();
  });
}

function openInfoGrupoModal(nombreGrupo) {
  fetch(`/api/info_grupo?nombre=${encodeURIComponent(nombreGrupo)}`)
    .then(res => res.json())
    .then(data => {
      const div = document.getElementById("infoGrupoContenido");
      div.innerHTML = `<h3>Grupo: ${data.nombre}</h3><ul style="list-style:none; padding:0;">`;

      data.miembros.forEach(m => {
        let estado = "";
        let icono = "";
        if (m.estado === "conectado") {
          estado = "🟢 Conectado";
          icono = "✅";
        } else if (m.estado === "desconectado") {
          estado = "🔴 Desconectado";
          icono = "❌";
        } else {
          estado = "❓ No existe";
          icono = "⚠️";
        }

        div.innerHTML += `<li style="margin:5px 0;"><strong>${icono} ${m.nombre}</strong> — ${estado}` +
          (m.ultima_conexion ? ` (Últ. conexión: ${m.ultima_conexion})` : "") +
          `</li>`;
      });

      div.innerHTML += `</ul>`;
      openModal("infoGrupoModal");
    })
    .catch(err => {
      console.error("❌ Error al cargar info del grupo:", err);
      mostrarMensaje("Error", "No se pudo cargar la información del grupo.");
    });
}

// MODALES
function openModal(id) {
  console.log("🪟 Abriendo modal:", id);
  const modal = document.getElementById(id);
  modal.classList.remove("oculto");         // ✅ Le quitamos la clase
  modal.style.removeProperty("display");    // ✅ Eliminamos cualquier display="none"
}

function closeModal(id) {
  const modal = document.getElementById(id);
  modal.classList.add("oculto");            // ✅ Lo ocultamos con la clase
}
// =================== FUNCIÓN LOGIN ===================
function login() {
  const user = document.getElementById("usuario").value.trim();
  const pass = document.getElementById("contrasena").value.trim();

  if (!user || !pass) {
    return mostrarMensaje("Error", "Por favor, completa ambos campos.");
  }

  fetch("/api/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ usuario: user, contrasena: pass }),
  })
  .then(res => res.json())
  .then(data => {
    console.log("🧾 Respuesta del login:", data);
  
    if (data.status === "ok") {
      console.log("✅ Login correcto como:", user);
      sessionStorage.setItem("usuario", user);
      usuarioActual = user;
  
      const userLower = user.trim().toLowerCase();
      if (userLower === "admin") {
        window.location.href = "/admin";
      } else {
        document.getElementById("userDisplay").textContent = `👤 ${user}`;
        document.getElementById("loginBtn").style.display = "none";
        document.getElementById("logoutBtn").style.display = "inline-block";
        desbloquearInterfaz();
        loadClients();
        loadGroups();
        loadFrasesFromServer();
  
        mostrarMensaje("Sesión iniciada", `Bienvenido, ${user}`);
        closeModal("loginModal");
      }
    } else {
      mostrarMensaje("Error", "❌ Usuario o contraseña incorrectos");
    }
  })
  .catch(err => {
    console.error("❌ Error inesperado tras login:", err);
    if (!usuarioActual) mostrarMensaje("Error", "❌ Error inesperado al iniciar sesión.");
  });
}  
// =================== ENTER y ESCAPE EN MODALES ===================
document.addEventListener("keydown", function (e) {
  const modalVisible = document.querySelector(".modal:not(.oculto)");
  if (!modalVisible) return;

  if (e.key === "Enter") {
    const btnOk = modalVisible.querySelector(".btn-primary, .btn-success");
    if (btnOk) btnOk.click();
  }

  if (e.key === "Escape") {
    const btnClose = modalVisible.querySelector(".btn-close, .close");
    if (btnClose) btnClose.click();
    else closeModal(modalVisible.id); // Fallback si no hay botón
  }
});

// 🔁 Refrescar automáticamente la lista de clientes cada 20 segundos
setInterval(() => {
  if (usuarioActual) {
    loadClients();
  }
}, 15000);  // Puedes ajustar a 10000 para cada 10s si quieres más rapidez
