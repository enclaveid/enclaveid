# nvembed-ray-serve

Ray Serve Application for embedding generation.

## Deployment

Create cluster:

```bash
kubectl apply -f cluster/ray-cluster.yaml
```

Configure aks autoscaler:

```bash
kubectl apply -f cluster/aks-autoscaler.yaml
```

Add aks routing addon:

```bash
kubectl apply -f cluster/aks-routing-addon.yaml
```

Install helm charts:

```bash
helm install ray-serve helm/ray-serve
```

Deploy application:

```bash
kubectl apply -f cluster/ray-serve.yaml
```
