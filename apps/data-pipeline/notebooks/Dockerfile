FROM enclaveid/data-pipeline-vllm:master

# Install curl
RUN apt-get update && apt-get install -y curl

# Install Node.js 20.x
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
  && apt-get install -y nodejs \
  && npm install -g npm@latest

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

# Install JupyterLab extensions
RUN jupyter labextension install \
  @jupyter-widgets/jupyterlab-manager \
  @jupyterlab/git \
  @krassowski/jupyterlab-lsp \
  @jupyterlab/debugger \
  @jupyterlab/google-drive \
  @jupyterlab/toc \
  jupyterlab-plotly \
  @jupyterlab/dataregistry-extension \
  jupyterlab-nvdashboard

# Enable JupyterLab extensions
RUN jupyter serverproxy enable --sys-prefix && \
  jupyter labextension enable @jupyterlab/git && \
  jupyter labextension enable @krassowski/jupyterlab-lsp && \
  jupyter labextension enable @jupyterlab/debugger

# Set up Jupyter configuration
RUN mkdir -p /root/.jupyter && \
  echo "c.NotebookApp.ip = '0.0.0.0'" >> /root/.jupyter/jupyter_notebook_config.py && \
  echo "c.NotebookApp.open_browser = False" >> /root/.jupyter/jupyter_notebook_config.py && \
  echo "c.NotebookApp.allow_root = True" >> /root/.jupyter/jupyter_notebook_config.py

# Expose JupyterLab port
EXPOSE 8888

# Set working directory
WORKDIR /workspace

# Start JupyterLab
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
