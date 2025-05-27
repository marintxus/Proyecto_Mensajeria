// 🔒 Protección para evitar acceso indebido
fetch("/usuario_actual")
  .then(res => res.json())
  .then(data => {
    if (data.usuario !== "admin") {
      fetch("/logout", { method: "POST" }).then(() => {
        sessionStorage.removeItem("usuario");
        window.location.href = "/";
      });
    }
  });

document.getElementById("crearUsuarioForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const usuario = document.getElementById("nuevoUsuario").value.trim().toLowerCase();
  const clave1 = document.getElementById("nuevaClave1").value;
  const clave2 = document.getElementById("nuevaClave2").value;
  const mensajeDiv = document.getElementById("crearUsuarioMensaje");
  mensajeDiv.textContent = "";

  if (clave1 !== clave2) {
    mensajeDiv.textContent = "❌ Las contraseñas no coinciden.";
    mensajeDiv.className = "text-danger";
    return;
  }

  const res = await fetch("/admin/crear_usuario", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ usuario, contrasena1: clave1, contrasena2: clave2 })
  });

  const data = await res.json();
  if (data.status === "ok") {
    mensajeDiv.textContent = "✅ Usuario creado correctamente.";
    mensajeDiv.className = "text-success";
    document.getElementById("crearUsuarioForm").reset();
    cargarLogs();
  } else {
    mensajeDiv.textContent = "❌ " + (data.message || "Error al crear usuario.");
    mensajeDiv.className = "text-danger";
  }
});

let ultimaLineaLeida = null;
let segundosRestantes = 300;

async function cargarLogs() {
  const usuario = document.getElementById("filtroUsuario").value.trim().toLowerCase();
  const fechaInput = document.getElementById("filtroFecha").value;
  const hoy = new Date().toISOString().slice(0, 10);

  if (fechaInput && fechaInput > hoy) {
    alert("⛔ No puedes seleccionar una fecha futura.");
    return;
  }

  const fechaParam = (fechaInput && fechaInput !== hoy) ? fechaInput : "";
  const res = await fetch(`/admin/logs?usuario=${usuario}&fecha=${fechaParam}`);
  const data = await res.json();

  const tbody = document.getElementById("logsBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  let lineaInsertada = false;

  data.forEach((linea) => {
    const partes = linea.split(" - ");
    if (partes.length >= 3) {
      const fecha = partes[0].split(",")[0];
      const usuario = partes[1];
      let mensaje = partes.slice(2).join(" - ");
      const row = document.createElement("tr");

      let clase = "log-info";
      if (mensaje.includes("iniciado sesión") || mensaje.includes("cerrado sesión")) clase = "log-warning";
      else if (mensaje.includes("envía mensaje") || mensaje.includes("envió mensaje")) clase = "log-success";
      else if (mensaje.includes("elimina cliente") || mensaje.includes("eliminó al usuario")) clase = "log-danger";
      else if (mensaje.includes("creó el usuario") || mensaje.includes("cambió la contraseña")) clase = "log-success";

      row.className = clase;
      row.innerHTML = `<td>${fecha}</td><td>${usuario}</td><td>${mensaje}</td>`;
      tbody.appendChild(row);  // ✅ solo una vez

      // 🔴 Insertar línea roja justo después del último mensaje leído
      if (!lineaInsertada && ultimaLineaLeida && linea === ultimaLineaLeida) {
        const lineaRoja = document.createElement("tr");
        lineaRoja.innerHTML = `
          <td colspan="3" style="border-top: 2px solid red; padding-top: 6px;">
            <span style="
              display: inline-block;
              margin-top: -6px;
              margin-bottom: 4px;
              background: #fff;
              padding: 0 6px;
              color: red;
              font-size: 0.75rem;
              font-weight: bold;
              border-radius: 4px;
            ">
              Último mensaje leído
            </span>
          </td>
        `;
        tbody.appendChild(lineaRoja);
        lineaInsertada = true;
      }
    }
  });

  // 🔴 Guardar nueva última línea leída
  if (data.length > 0) {
    ultimaLineaLeida = data[0];
  }
}

document.getElementById("actualizarLogsBtn").addEventListener("click", () => {
  cargarLogs();
  segundosRestantes = 300;
});

function actualizarCuentaAtras() {
  segundosRestantes--;
  if (segundosRestantes <= 0) {
    cargarLogs();
    segundosRestantes = 300;
  }
  const mins = Math.floor(segundosRestantes / 60);
  const secs = segundosRestantes % 60;
  document.getElementById("cuentaAtras").textContent =
    `Próxima actualización automática en: ${mins}:${secs.toString().padStart(2, '0')}`;
}

setInterval(actualizarCuentaAtras, 1000);

function descargarLog() {
  const fecha = document.getElementById("fechaLog").value.trim();
  if (!fecha) {
    alert("Introduce una fecha válida ('hoy' o YYYY-MM-DD)");
    return;
  }
  window.location.href = `/admin/descargar_log/${fecha}`;
}

async function cargarUsuarios() {
  const res = await fetch("/admin/usuarios");
  const data = await res.json();

  const tbody = document.getElementById("usuariosBody");
  tbody.innerHTML = "";

  data.forEach(usuario => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${usuario}</td>
      <td>
        <button class="btn btn-danger btn-sm" onclick="eliminarUsuario('${usuario}')">Eliminar</button>
        <button class="btn btn-primary btn-sm" onclick="cambiarContrasenaPrompt('${usuario}')">Cambiar Contraseña</button>
      </td>
    `;
    tbody.appendChild(row);
  });
// 👉 AÑADE ESTO DESPUÉS:
const select = document.getElementById("usuarioParaClave");
select.innerHTML = "";
data.forEach(usuario => {
  const option = document.createElement("option");
  option.value = usuario;
  option.textContent = usuario;
  select.appendChild(option);
});
}

async function eliminarUsuario(usuario) {
  if (usuario === "admin") {
    alert("❌ No puedes eliminar al usuario admin.");
    return;
  }

  const confirmacion = confirm(`¿Estás seguro de que deseas eliminar al usuario "${usuario}"?`);
  if (!confirmacion) return;

  const res = await fetch("/admin/eliminar_usuario", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ usuario })
  });

  const data = await res.json();
  if (data.status === "ok") {
    alert("✅ Usuario eliminado correctamente.");
    cargarUsuarios();
    cargarLogs();
  } else {
    alert("❌ Error al eliminar usuario: " + (data.message || "Desconocido"));
  }
}

document.getElementById("cambiarClaveForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const usuario = document.getElementById("usuarioParaClave").value;
  const clave1 = document.getElementById("nuevaClaveCambio1").value;
  const clave2 = document.getElementById("nuevaClaveCambio2").value;
  const msg = document.getElementById("mensajeCambioClave");

  msg.textContent = "";
  msg.className = "";

  if (!usuario || !clave1 || !clave2) {
    msg.textContent = "❌ Todos los campos son obligatorios.";
    msg.className = "text-danger";
    return;
  }

  if (clave1 !== clave2) {
    msg.textContent = "❌ Las contraseñas no coinciden.";
    msg.className = "text-danger";
    return;
  }

  const res = await fetch("/admin/cambiar_contrasena", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ usuario, nueva_clave: clave1 })
  });

  const data = await res.json();
  if (data.status === "ok") {
    msg.textContent = "✅ Contraseña cambiada correctamente.";
    msg.className = "text-success";
    document.getElementById("cambiarClaveForm").reset();
    cargarLogs();
  } else {
    msg.textContent = "❌ " + (data.message || "Error al cambiar contraseña.");
    msg.className = "text-danger";
  }
});

document.getElementById("logFilterForm").addEventListener("submit", (e) => {
  e.preventDefault();
  cargarLogs();
});

document.getElementById("filtroUsuario").addEventListener("input", cargarLogs);
document.getElementById("filtroFecha").addEventListener("input", cargarLogs);
document.getElementById("formImportarCSV").addEventListener("submit", function (e) {
  e.preventDefault();
  const formData = new FormData();
  const archivo = document.getElementById("archivoCSV").files[0];
  if (!archivo) return;

  // ✅ nombre del campo debe coincidir con backend: "archivo"
  formData.append("archivo", archivo);

  fetch("/admin/importar_csv", {
    method: "POST",
    body: formData
  })
    .then(async res => {
      const div = document.getElementById("csvResultado");
      let data = { message: "❌ Error desconocido." };

      try {
        data = await res.json();
      } catch (e) {
        console.warn("⚠️ La respuesta no fue un JSON válido.");
      }

      if (res.ok && data.status === "ok") {
        div.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
      } else {
        div.innerHTML = `<div class="alert alert-danger">${data.message || "❌ Archivo inválido."}</div>`;
      }
    })
    .catch((error) => {
      console.error("❌ Error al importar CSV:", error);
      document.getElementById("csvResultado").innerHTML =
        `<div class="alert alert-danger">❌ Error al importar CSV</div>`;
    });
});



cargarLogs();
cargarUsuarios();