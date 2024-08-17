FROM enclaveid/data-pipeline-vllm:master

# Update and install system dependencies
RUN apt-get update && apt-get install -y \
  git \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get update \
  && apt-get install -y nodejs \
  && npm install -g npm@latest \
  && rm -rf /var/lib/apt/lists/*

# Verify Node.js and npm installation
RUN node --version && npm --version

# Install Python packages
RUN pip install --no-cache-dir \
  azure-storage-blob \
  dtale \
  jupyterlab \
  ipykernel \
  jupyter-dash \
  jupyterlab-git \
  jupyterlab-lsp \
  python-lsp-server[all] \
  nbgitpuller \
  ipywidgets \
  jupyter-resource-usage \
  jupyterlab_code_formatter \
  black \
  isort \
  jupyterlab-nvdashboard

# Build JupyterLab
RUN jupyter lab build

# Set up Jupyter configuration
RUN mkdir -p /root/.jupyter && \
  echo "c.ServerApp.ip = '0.0.0.0'" >> /root/.jupyter/jupyter_server_config.py && \
  echo "c.ServerApp.open_browser = False" >> /root/.jupyter/jupyter_server_config.py && \
  echo "c.ServerApp.allow_root = True" >> /root/.jupyter/jupyter_server_config.py

# Expose JupyterLab port
EXPOSE 8888

# Set working directory
WORKDIR /workspace

# Start JupyterLab
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
