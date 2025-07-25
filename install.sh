#!/bin/bash
{

echo -e "\033[97;44;1m                               \033[m"
echo -e "\033[97;44;1m       42basepairs Setup       \033[m"
echo -e "\033[97;44;1m                               \033[m"
echo


# ------------------------------------------------------------------------------
# Initialize
# ------------------------------------------------------------------------------

# Make sure we have the environment variables we need for the setup
if [[ -z "$LICENSE_KEY" ]] || [[ -z "$DOMAIN_AUTH" ]] || [[ -z "$DOMAIN_42BASEPAIRS" ]] || [[ -z "$IP_ADDRESS" ]] || [[ -z "$SITE_ADMIN_EMAIL" ]]; then
    echo "Error: missing environment variables"
    echo "Make sure you ran this setup script from Cloud Shell."
    echo "Please refer to the documentation on https://42basepairs.com/docs/self-hosting for details."
    exit
fi
echo "Found environment variables ✅"


# ------------------------------------------------------------------------------
# Validate license key
# ------------------------------------------------------------------------------

isValid=$(curl --silent -H "x-omgenomics-license-key: $LICENSE_KEY" "https://license.omgenomics.com/api/v1/42basepairs/status" | grep '"success":true')
if [[ "$isValid" == "" ]]; then
    echo "ERROR: Invalid license key."
    exit
else
    echo "Valid license ✅"
fi


# ------------------------------------------------------------------------------
# Set up a folder for logs
# ------------------------------------------------------------------------------

DIR_LOGS=/42basepairs-setup
sudo mkdir -p $DIR_LOGS
sudo chmod -R 777 $DIR_LOGS


# ------------------------------------------------------------------------------
# Install general dependencies
# ------------------------------------------------------------------------------

EXISTING_UNZIP=$(sudo unzip -v 2>&1)
if [[ "$EXISTING_UNZIP" == "sudo: unzip: command not found" ]]; then
    echo "Installing general dependencies (ETA 30s)..."
    {
        sudo apt-get install -y unzip postgresql-client make
    } > $DIR_LOGS/00-dependencies.log 2>&1
fi


# ------------------------------------------------------------------------------
# Install Docker
# Source: https://docs.docker.com/engine/install/debian/#install-using-the-repository
# ------------------------------------------------------------------------------

EXISTING_DOCKER=$(sudo docker --version 2>&1)
if [[ "$EXISTING_DOCKER" != "sudo: docker: command not found" ]]; then
    echo "Docker already installed: ${EXISTING_DOCKER} ✅"
else
    echo "Installing Docker (ETA 30s)..."
    {
        # Add Docker's official GPG key:
        sudo apt-get update
        sudo apt-get install -y ca-certificates curl
        sudo install -m 0755 -d /etc/apt/keyrings
        sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
        sudo chmod a+r /etc/apt/keyrings/docker.asc

        # Add the repository to Apt sources:
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
        $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update

        # Install Docker
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    } > $DIR_LOGS/10-docker.log 2>&1
fi

# ------------------------------------------------------------------------------
# Install Supabase
# ------------------------------------------------------------------------------

EXISTING_SUPABASE=$(sudo supabase --version 2>&1)
if [[ "$EXISTING_SUPABASE" != "sudo: supabase: command not found" ]]; then
    echo "Supabase already installed: ${EXISTING_SUPABASE} ✅"
else
    echo "Installing Supabase, a tool used to manage the 42basepairs database..."
    {
        SUPABASE_VERSION=1.155.2
        curl -LO https://github.com/supabase/cli/releases/download/v${SUPABASE_VERSION}/supabase_${SUPABASE_VERSION}_linux_amd64.deb
        sudo dpkg -i supabase_${SUPABASE_VERSION}_linux_amd64.deb
        rm supabase_${SUPABASE_VERSION}_linux_amd64.deb
    } > $DIR_LOGS/20-supabase.log 2>&1
fi

# ------------------------------------------------------------------------------
# Install Node.js: https://nodejs.org/en/download/package-manager
# ------------------------------------------------------------------------------

EXISTING_NODE=$(sudo node --version 2>&1)
if [[ "$EXISTING_NODE" != "sudo: node: command not found" ]]; then
    echo "Node already installed: ${EXISTING_NODE} ✅"
    echo "NPM already installed: $(npm --version) ✅"
else
    echo "Installing Node.js, the back-end that runs the 42basepairs app..."
    {
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
        source $HOME/.nvm/nvm.sh
        nvm install 20

        # Allow using node from root user (need root to use port 80; https://stackoverflow.com/a/40078875)
        sudo ln -sf "$NVM_DIR/versions/node/$(nvm version)/bin/node" "/usr/local/bin/node"
        sudo ln -sf "$NVM_DIR/versions/node/$(nvm version)/bin/npm" "/usr/local/bin/npm"
        sudo ln -sf "$NVM_DIR/versions/node/$(nvm version)/bin/npx" "/usr/local/bin/npx"
    } > $DIR_LOGS/30-node.log 2>&1
fi


# ------------------------------------------------------------------------------
# Install NGINX
# ------------------------------------------------------------------------------

EXISTING_NGINX=$(sudo nginx -version 2>&1)
if [[ "$EXISTING_NGINX" != "sudo: nginx: command not found" ]]; then
    echo "NGINX already installed: ${EXISTING_NGINX} ✅"
else
    echo "Installing NGINX, the web server (ETA 60s)..."
    {
        sudo apt install -y nginx snapd
        # Install snap so we can install certbot (SSL certificate management)
        sudo snap install core
        sudo snap install --classic certbot
        sudo ln -s /snap/bin/certbot /usr/bin/certbot
    } > $DIR_LOGS/40-nginx.log 2>&1

    echo "Configuring routes for NGINX server..."
    {
        # Don't serve pages from /var/www/html
        sudo sed -i 's|^[[:space:]]*root /var/www/html;|# root /var/www/html;|g' /etc/nginx/sites-enabled/default
        # Proxy / to the web server at port 3000
        # Notes:
        # 1. Increase proxy buffer sizes, otherwise get error about "upstream sent too big header while reading response header from upstream" (https://www.cyberciti.biz/faq/nginx-upstream-sent-too-big-header-while-reading-response-header-from-upstream/)
        # 2. Set proxy_pass to 127.0.0.1 intead of localhost to avoid error "Connection refused while connecting to upstream" (https://serverfault.com/a/529403)
        sudo sed -i 's|^[[:space:]]*try_files $uri $uri/ =404;|  proxy_busy_buffers_size   512k;  \n  proxy_buffers   4 512k;  \n  proxy_buffer_size   256k;  \n  proxy_set_header Host $host;  \n  proxy_set_header X-Real-IP $remote_addr;  \n  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;  \n  proxy_set_header X-Forwarded-Proto $scheme;  \n  proxy_pass http://127.0.0.1:3000;|g' /etc/nginx/sites-enabled/default
        # Proxy Supabase requests to the right port
        if [[ "$(grep 'rest' /etc/nginx/sites-enabled/default)" == "" ]]; then
            sudo sed -i 's|^[[:space:]]*location / {|location /rest/ {  \n  proxy_busy_buffers_size   512k;  \n  proxy_buffers   4 512k;  \n  proxy_buffer_size   256k;  \n  proxy_set_header Host $host;  \n  proxy_set_header X-Real-IP $remote_addr;  \n  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;  \n  proxy_set_header X-Forwarded-Proto $scheme;  \n  proxy_pass http://127.0.0.1:54321; \n  } \n location / { |g' /etc/nginx/sites-enabled/default
        fi
    } > $DIR_LOGS/60-nginx-routes.log 2>&1
fi


# ------------------------------------------------------------------------------
# Install 42basepairs
# ------------------------------------------------------------------------------

if [[ -d "/42basepairs" ]]; then
    version=$(cat /42basepairs/version)
    echo "Existing 42basepairs installation detected at /42basepairs: $version ✅"
fi

# Download latest release
if [[ ! -d "/42basepairs" ]]; then
    echo -n "Downloading latest 42basepairs release... "

    # Download latest code
    curl --silent -H "x-omgenomics-license-key: $LICENSE_KEY" -o release.zip "https://license.omgenomics.com/api/v1/42basepairs/releases/latest/download"
    if [[ "$(wc -c < release.zip)" -lt 1000 ]]; then
        echo "Could not download latest release."
        exit
    fi
    sudo unzip -qq release.zip -d /42basepairs && rm release.zip

    cat /42basepairs/version

    # Set up 42basepairs crons (NOTE: can't have dots in crontab file names)
    sudo cp /42basepairs/on-prem/42basepairs.crontab /etc/cron.d/crond-42basepairs
    # Set up 42basepairs web server service
    sudo cp /42basepairs/on-prem/42basepairs.service /etc/systemd/system/
fi

# Initialize Supabase installation if needed
if [[ ! -d "$HOME/supabase" ]]; then
    echo "Initializing Supabase environment..."
    echo "nn" | sudo supabase init > $DIR_LOGS/70-supabase-init.log 2>&1
fi


# ------------------------------------------------------------------------------
# Set up env variables
# ------------------------------------------------------------------------------

cd /42basepairs

if [[ -f /42basepairs/.env ]]; then
    echo "42basepairs environment variables detected at /42basepairs/.env ✅"
else
    # Generate 42basepairs keys
    BASEPAIRS_ENCRYPT_KEY="$(uuidgen)"
    BASEPAIRS_CRONS_KEY="$(uuidgen)"
    SETUP_TOKEN="$(uuidgen)"
    SUPABASE_AUTH_JWT_SECRET="$(uuidgen)-$(uuidgen)"
    AUTH_SECRET="$(openssl rand -base64 33)"  # for auth.js

    # Infer Supabase env vars
    echo "Downloading Supabase container images (ETA 3 mins)..."
    {
        sudo SECRET=$SUPABASE_AUTH_JWT_SECRET bash -c 'echo -e "SUPABASE_AUTH_JWT_SECRET=${SECRET}" > /42basepairs/.env'
        sudo supabase stop --no-backup
        sudo supabase start
        SUPABASE_KEY_ADMIN=$(sudo supabase status 2>/dev/null | grep "service_role key" | awk '{ print $NF }')
        sudo supabase stop
        sudo rm /42basepairs/.env
    } > $DIR_LOGS/80-supabase-tokens.log 2>&1

    cat > ~/.env.tmp << EOF
# ------------------------------------------------------------------------------
# 42basepairs environment variables
# DO NOT EDIT
# ------------------------------------------------------------------------------

PUBLIC_IS_ON_PREM="true"
PUBLIC_ENVIRONMENT="prd"

# 42basepairs config
LICENSE_KEY="$LICENSE_KEY"
SETUP_TOKEN="$SETUP_TOKEN"
PUBLIC_LOGIN_EMAIL_DOMAIN="$DOMAIN_AUTH"
# UUID used to encrypt bucket tokens in the DB. If changed, tokens stored in the DB need to be re-encrypted with the new key.
BASEPAIRS_ENCRYPT_KEY="$BASEPAIRS_ENCRYPT_KEY"
# UUID used to authorize calls to /api/v1/crons from a cron job system
BASEPAIRS_CRONS_KEY="$BASEPAIRS_CRONS_KEY"

# Supabase configs (despite its name, the JWT_SECRET is not only used for auth)
SUPABASE_KEY_ADMIN="$SUPABASE_KEY_ADMIN"
SUPABASE_AUTH_JWT_SECRET="$SUPABASE_AUTH_JWT_SECRET"
PUBLIC_SUPABASE_URL="http://127.0.0.1:54321"

# Auth.js credentials (OAuth creds will be fetched from the DB at app initialization time)
AUTH_SECRET="$AUTH_SECRET"

# 42basepairs setup information
SETUP_IP_ADDRESS="$IP_ADDRESS"
DOMAIN_42BASEPAIRS="$DOMAIN_42BASEPAIRS"
SITE_ADMIN_EMAIL="$SITE_ADMIN_EMAIL"
EOF

    sudo mv ~/.env.tmp /42basepairs/.env

    # Link .env file in app folder (Node.js adapter seems to need it there)
    sudo ln -sf /42basepairs/.env /42basepairs/app/.env
fi

# ------------------------------------------------------------------------------
# Launch 42basepairs
# ------------------------------------------------------------------------------

echo
echo -e "\033[97;44;1m                               \033[m"
echo -e "\033[97;44;1m     Launching 42basepairs     \033[m"
echo -e "\033[97;44;1m                               \033[m"
echo

echo "Launching Supabase containers (ETA 30s)..."
sudo supabase stop > $DIR_LOGS/90-supabase-restart.log 2>&1
sudo supabase start >> $DIR_LOGS/90-supabase-restart.log 2>&1

# Build app
cd /42basepairs/app
echo "Installing 42basepairs JavaScript dependencies (ETA 30s)..."
sudo npm install > $DIR_LOGS/100-npm-install.log 2>&1

# Restart servers to get new nginx configuration
echo "Launching 42basepairs..."
sudo systemctl restart 42basepairs
sudo systemctl enable 42basepairs

sudo systemctl restart nginx

echo
echo "42basepairs has been successfully installed!"
echo "To finish the setup, go to:"
echo "   http://${IP_ADDRESS}/admin/setup/${SETUP_TOKEN}"
echo
}
