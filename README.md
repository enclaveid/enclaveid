# EnclaveID

[Figma mocks](https://www.figma.com/design/sCKxY4WbgHs13Sd3sNp1GF?fuid=899291250420012310&prev-plan-id=899291252722142386&prev-plan-type=team&prev-selected-view=recentsAndSharing&prev-tab=recently-viewed) |
[Trello board](https://trello.com/b/jsbSDdMQ/enclaveid) | [Tinkerers Slides](https://docs.google.com/presentation/d/1zX_3J0rcH2t8o6apqhF56PW4a3ipjmwj9UgBtGPgWWc/edit#slide=id.g30acb7aad6b_0_3)

## Prototype demo
https://github.com/user-attachments/assets/e6b077cc-6617-4423-a652-dfb55b9abbe4

## Docs

- [Architecture](docs/architecture.md)
- [Deployment](docs/deployment.md)
- [Verification](docs/verification.md)

## Getting started

Docker and Node.js are required for local development. The monorepo is managed with `bun` and Nx; to install them and the project dependencies, run:

```bash
brew tap oven-sh/bun
brew install bun
bun add --global nx@latest
bun install
```

Additionally, you should install all the [recommended](.vscode/extensions.json) VSCode extensions. Most importantly, the [Nx Console](https://marketplace.visualstudio.com/items?itemName=nrwl.angular-console) extension.

## Development

We distinguish 3 different environments in the development cycle:

- **No cluster**: when developing features in isolation, for example when adding frontend components.
- **Microk8s cluster**: for development reliant on k8s features, such as chrome-controller.
- **AKS cluster**: for development reliant on locally unavailable hardware, such as GPU for the data pipeline and AMD SEV-SNP for confidentiality.

See the [deployment](docs/deployment.md) document for instructions on how to set up the clusters. Get in touch with the development team to get access to the AKS cluster credentials.

### Environment variables

The environment variables are managed with the `.env` file. The `.env.example` file contains all the required variables. Copy it to `.env` and fill in the values you need for the application you're developing.

These variables are also made available in the Microk8s cluster.

### Folder structure

- `apps/`: Nx managed applications
- `libs/`: Nx managed libraries
- `docs/`: Documentation
- `scripts/`: Scripts to manage the project
- `k8s/aux_containers/`: Auxiliary containers (initContainers, sidecars)
- `k8s/helm/`: Helm chart
- `k8s/renders/`: Helm chart renders
- `k8s/scripts/`: Scripts to post-process the renders

Refer to each application / library's README for more information on how to run them.
