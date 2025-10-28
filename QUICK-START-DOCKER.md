# 🚀 Quick Start - Testing Local con Docker

## 📋 Pasos Rápidos

### **PASO 1: Instalar Docker** (5 minutos)

1. **Descargar**: https://www.docker.com/products/docker-desktop
2. **Instalar**: Arrastra Docker.app a Applications
3. **Abrir**: Docker Desktop desde Applications
4. **Esperar**: Hasta que veas la ballena en la barra superior y diga "Engine running"

### **PASO 2: Ejecutar Testing** (1 comando)

```bash
./test-docker-local.sh
```

¡Eso es todo! El script hará:
- ✅ Verificar que Docker esté corriendo
- ✅ Construir las imágenes Docker (5-10 min)
- ✅ Iniciar los 4 servicios
- ✅ Verificar que todo funcione

---

## 🎯 Resultado Esperado

Después de ejecutar el script verás:

```
✅ Docker está corriendo
✅ .env creado
✅ Modelo de Rasa encontrado
✅ Imágenes construidas
✅ Servicios iniciados

📊 Estado de los servicios:
NAME                 STATUS    PORTS
sctbnk-mariadb      running   0.0.0.0:3306->3306/tcp
sctbnk-rasa         running   0.0.0.0:5005->5005/tcp
sctbnk-actions      running   0.0.0.0:5055->5055/tcp
sctbnk-twilio       running   0.0.0.0:5000->5000/tcp

✅ MariaDB: localhost:3306
✅ Twilio Server: http://localhost:5000
✅ Rasa: http://localhost:5005
✅ Actions: http://localhost:5055/health
```

---

## 📱 Probar con Twilio

Una vez que todo esté corriendo:

### 1. Exponer con ngrok (en otra terminal)
```bash
ngrok http 5000
```

### 2. Copiar la URL
```
https://abc123.ngrok-free.app
```

### 3. Configurar en Twilio Console
- Ir a: https://console.twilio.com/
- Phone Numbers → Tu número
- Voice & Fax → Webhook:
  ```
  https://abc123.ngrok-free.app/webhook/twilio/voice
  ```
- Save

### 4. ¡Llamar y probar!

---

## 🛠️ Comandos Útiles

### Ver logs en tiempo real
```bash
docker-compose logs -f
```

### Ver logs de un servicio específico
```bash
docker-compose logs -f twilio
docker-compose logs -f rasa
docker-compose logs -f actions
```

### Reiniciar un servicio
```bash
docker-compose restart twilio
```

### Detener todo
```bash
docker-compose down
```

### Ver qué está corriendo
```bash
docker-compose ps
```

### Entrar a un contenedor (debug)
```bash
docker-compose exec twilio bash
docker-compose exec rasa bash
```

---

## 🐛 Problemas Comunes

### "Docker no está instalado"
- Abre Docker Desktop
- Espera a que diga "Engine running"
- Vuelve a intentar

### "Puerto ya en uso"
```bash
# Detener servicios locales que puedan estar usando los puertos
pkill -f "rasa"
pkill -f "twilio_voice_server"

# Luego vuelve a intentar
./test-docker-local.sh
```

### "Rasa no responde"
```bash
# Ver logs de Rasa
docker-compose logs -f rasa

# Si falta el modelo, entrenarlo:
rasa train
# Luego reiniciar:
docker-compose restart rasa
```

### "Freshdesk falla"
Es normal si no tienes credenciales de Freshdesk configuradas.
El bot seguirá funcionando, solo no creará tickets.

---

## ✅ Checklist

- [ ] Docker Desktop instalado y corriendo
- [ ] Script `test-docker-local.sh` ejecutado exitosamente
- [ ] 4 servicios corriendo (docker-compose ps)
- [ ] ngrok exponiendo puerto 5000
- [ ] Twilio webhook configurado
- [ ] Llamada de prueba exitosa

---

## 📚 Próximos Pasos

Una vez que el testing local funcione:

1. **Leer**: `CLOUD-STRATEGY.md` (para tu jefe)
2. **Seguir**: `DEPLOYMENT.md` (para deployment a la nube)
3. **Ejecutar**: `./deploy-k8s.sh` (cuando estés listo para producción)

---

## 🆘 Ayuda

Si algo no funciona:
1. Revisa los logs: `docker-compose logs -f`
2. Verifica Docker Desktop esté corriendo
3. Asegúrate de tener `.env` configurado
4. Consulta `DEPLOYMENT.md` para troubleshooting detallado

**¡Buena suerte! 🚀**

