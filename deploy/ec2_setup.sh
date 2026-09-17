#!/usr/bin/env bash
# ==============================================================================
# Script de Despliegue Automatizado en AWS EC2 (Ubuntu 22.04 / 24.04 LTS o Amazon Linux 2023)
# Batería de Riesgo Psicosocial (MinProtección / Javeriana)
# ==============================================================================

set -e

echo "=== [1/6] Actualizando sistema operativo y herramientas básicas ==="
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
fi

if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    sudo apt-get update -y
    sudo apt-get install -y ca-certificates curl gnupg lsb-release htop zip unzip git nginx
elif [ "$OS" = "amzn" ] || [ "$OS" = "centos" ] || [ "$OS" = "rhel" ]; then
    sudo dnf update -y
    sudo dnf install -y curl htop zip unzip git nginx
fi

echo "=== [2/6] Configurando archivo Swap de 4GB para proteger contra picos de RAM ==="
if [ ! -f /swapfile ]; then
    echo "Creando swapfile..."
    sudo fallocate -l 4G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=4096
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "Swap de 4GB activado exitosamente."
fi

echo "=== [3/6] Instalando Docker Engine y Docker Compose ==="
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    sudo systemctl enable --now docker
    rm get-docker.sh
    echo "Docker instalado correctamente."
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

echo "=== [4/6] Configurando Nginx Reverse Proxy para Server-Sent Events (SSE) ==="
sudo mkdir -p /etc/nginx/conf.d
if [ -f "deploy/nginx.conf" ]; then
    sudo cp deploy/nginx.conf /etc/nginx/conf.d/bateria.conf
    # Desactivar configuración por defecto si existe
    if [ -f /etc/nginx/sites-enabled/default ]; then
        sudo rm -f /etc/nginx/sites-enabled/default
    fi
    sudo systemctl restart nginx || sudo service nginx restart
fi

echo "=== [5/6] Creando directorios persistentes de almacenamiento ==="
mkdir -p data/uploads out/casos out/crops out/batches
chmod -R 777 data out

echo "=== [6/6] Compilando e iniciando contenedor Docker ==="
docker compose down || true
docker compose build
docker compose up -d

echo ""
echo "=========================================================================="
echo " ¡DESPLIEGUE COMPLETADO EXITOSAMENTE! "
echo " Estado del contenedor:"
docker ps
echo ""
echo " Visite: http://<IP_PUBLICA_EC2>"
echo " Verifique salud en: http://<IP_PUBLICA_EC2>/health"
echo " Inspeccione logs con: docker compose logs -f"
echo "=========================================================================="
