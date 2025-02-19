# EnclaveID

User understanding for the AI era

## Docs

- [Architecture](docs/architecture.md)
- [Verification](docs/verification.md)

## Getting started

Docker, Node.js, Python and Poetry are required for local development. The monorepo is managed with `bun` and Nx; to install them and the project dependencies, run:

```bash
brew tap oven-sh/bun
brew install bun poetry pyenv
pyenv install 3.12.7
bun add --global nx@latest
bun install
```

When prompted by VSCode, use Python version `3.12.7` to create the virtual environment.

Install all the [recommended](.vscode/extensions.json) VSCode extensions, most importantly the [Nx Console](https://marketplace.visualstudio.com/items?itemName=nrwl.angular-console) extension.

Refer to each application / library's README for more information on how to run them.
