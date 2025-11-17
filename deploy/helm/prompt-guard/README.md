# Prompt Guard Helm Chart

Enterprise-grade PII anonymization for LLM/SLM applications - Kubernetes deployment via Helm.

## TL;DR

```bash
helm repo add prompt-guard https://nik-kale.github.io/llm-slm-prompt-guard
helm install my-prompt-guard prompt-guard/prompt-guard
```

## Introduction

This chart bootstraps a [Prompt Guard](https://github.com/nik-kale/llm-slm-prompt-guard) deployment on a [Kubernetes](https://kubernetes.io) cluster using the [Helm](https://helm.sh) package manager.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.8.0+
- PV provisioner support in the underlying infrastructure (for Redis and PostgreSQL persistence)

## Installing the Chart

To install the chart with the release name `my-prompt-guard`:

```bash
helm install my-prompt-guard prompt-guard/prompt-guard
```

The command deploys Prompt Guard on the Kubernetes cluster with default configuration. The [Parameters](#parameters) section lists the parameters that can be configured during installation.

## Uninstalling the Chart

To uninstall/delete the `my-prompt-guard` deployment:

```bash
helm delete my-prompt-guard
```

## Parameters

### Global Parameters

| Name                      | Description                                     | Value |
| ------------------------- | ----------------------------------------------- | ----- |
| `global.imageRegistry`    | Global Docker image registry                     | `""`  |
| `global.imagePullSecrets` | Global Docker registry secret names as an array | `[]`  |

### Proxy Parameters

| Name                                 | Description                                        | Value                              |
| ------------------------------------ | -------------------------------------------------- | ---------------------------------- |
| `proxy.enabled`                      | Enable proxy deployment                             | `true`                             |
| `proxy.replicaCount`                 | Number of proxy replicas                            | `3`                                |
| `proxy.image.repository`             | Proxy image repository                              | `ghcr.io/nik-kale/llm-slm-prompt-guard/proxy` |
| `proxy.image.tag`                    | Proxy image tag (default: chart appVersion)         | `""`                               |
| `proxy.image.pullPolicy`             | Proxy image pull policy                             | `IfNotPresent`                     |
| `proxy.service.type`                 | Proxy service type                                  | `ClusterIP`                        |
| `proxy.service.port`                 | Proxy service HTTP port                             | `8000`                             |
| `proxy.ingress.enabled`              | Enable ingress controller resource                  | `true`                             |
| `proxy.ingress.className`            | Ingress class name                                  | `nginx`                            |
| `proxy.resources.limits.cpu`         | CPU limit                                           | `1000m`                            |
| `proxy.resources.limits.memory`      | Memory limit                                        | `2Gi`                              |
| `proxy.resources.requests.cpu`       | CPU request                                         | `250m`                             |
| `proxy.resources.requests.memory`    | Memory request                                      | `512Mi`                            |
| `proxy.autoscaling.enabled`          | Enable autoscaling                                  | `true`                             |
| `proxy.autoscaling.minReplicas`      | Minimum number of replicas                          | `3`                                |
| `proxy.autoscaling.maxReplicas`      | Maximum number of replicas                          | `10`                               |
| `proxy.autoscaling.targetCPUUtilizationPercentage` | Target CPU utilization          | `70`                               |

### Redis Parameters

| Name                                 | Description                                        | Value                              |
| ------------------------------------ | -------------------------------------------------- | ---------------------------------- |
| `redis.enabled`                      | Enable Redis                                        | `true`                             |
| `redis.architecture`                 | Redis architecture (`standalone` or `replication`)  | `standalone`                       |
| `redis.auth.enabled`                 | Enable Redis authentication                         | `false`                            |
| `redis.master.persistence.enabled`   | Enable Redis persistence                            | `true`                             |
| `redis.master.persistence.size`      | Redis persistent volume size                        | `8Gi`                              |

### PostgreSQL Parameters

| Name                                 | Description                                        | Value                              |
| ------------------------------------ | -------------------------------------------------- | ---------------------------------- |
| `postgresql.enabled`                 | Enable PostgreSQL                                   | `true`                             |
| `postgresql.auth.username`           | PostgreSQL username                                 | `prompt_guard`                     |
| `postgresql.auth.database`           | PostgreSQL database                                 | `prompt_guard`                     |
| `postgresql.primary.persistence.enabled` | Enable PostgreSQL persistence                   | `true`                             |
| `postgresql.primary.persistence.size`    | PostgreSQL persistent volume size               | `20Gi`                             |

Specify each parameter using the `--set key=value[,key=value]` argument to `helm install`. For example:

```bash
helm install my-prompt-guard \
  --set proxy.replicaCount=5 \
  --set proxy.autoscaling.maxReplicas=15 \
  prompt-guard/prompt-guard
```

Alternatively, a YAML file that specifies the values for the parameters can be provided while installing the chart. For example:

```bash
helm install my-prompt-guard -f values.yaml prompt-guard/prompt-guard
```

## Configuration Examples

### Production Deployment

```yaml
# production-values.yaml
proxy:
  replicaCount: 5
  resources:
    limits:
      cpu: 2000m
      memory: 4Gi
    requests:
      cpu: 500m
      memory: 1Gi
  autoscaling:
    minReplicas: 5
    maxReplicas: 20
    targetCPUUtilizationPercentage: 60

redis:
  master:
    resources:
      limits:
        memory: 2Gi
      requests:
        cpu: 200m
        memory: 512Mi
    persistence:
      size: 20Gi

postgresql:
  primary:
    resources:
      limits:
        memory: 4Gi
      requests:
        cpu: 500m
        memory: 1Gi
    persistence:
      size: 50Gi
```

```bash
helm install my-prompt-guard -f production-values.yaml prompt-guard/prompt-guard
```

### Development Deployment

```yaml
# dev-values.yaml
proxy:
  replicaCount: 1
  autoscaling:
    enabled: false
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 100m
      memory: 128Mi

redis:
  master:
    persistence:
      enabled: false

postgresql:
  primary:
    persistence:
      enabled: false
```

```bash
helm install my-prompt-guard -f dev-values.yaml prompt-guard/prompt-guard
```

### Custom Ingress

```yaml
# custom-ingress-values.yaml
proxy:
  ingress:
    enabled: true
    className: nginx
    annotations:
      cert-manager.io/cluster-issuer: letsencrypt-prod
      nginx.ingress.kubernetes.io/ssl-redirect: "true"
      nginx.ingress.kubernetes.io/rate-limit: "100"
    hosts:
      - host: prompt-guard.mycompany.com
        paths:
          - path: /
            pathType: Prefix
    tls:
      - secretName: prompt-guard-tls
        hosts:
          - prompt-guard.mycompany.com
```

## Upgrading

### To 1.1.0

This is a new chart version with no breaking changes from previous versions.

## Persistence

The chart mounts persistent volumes for both Redis and PostgreSQL. The volumes are created using dynamic volume provisioning.

### Existing PersistentVolumeClaims

1. Create the PersistentVolume
2. Create the PersistentVolumeClaim
3. Install the chart

```bash
helm install my-prompt-guard \
  --set redis.master.persistence.existingClaim=my-redis-pvc \
  --set postgresql.primary.persistence.existingClaim=my-postgres-pvc \
  prompt-guard/prompt-guard
```

## Troubleshooting

### Pods not starting

Check pod status:
```bash
kubectl get pods -l app.kubernetes.io/name=prompt-guard
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Redis connection issues

Check Redis status:
```bash
kubectl get pods -l app.kubernetes.io/name=redis
kubectl logs <redis-pod-name>
```

### PostgreSQL connection issues

Check PostgreSQL status:
```bash
kubectl get pods -l app.kubernetes.io/name=postgresql
kubectl logs <postgresql-pod-name>
```

### Ingress not working

Check ingress status:
```bash
kubectl get ingress
kubectl describe ingress <ingress-name>
```

## License

MIT License - see LICENSE for details.

## Support

- GitHub Issues: https://github.com/nik-kale/llm-slm-prompt-guard/issues
- Documentation: https://docs.prompt-guard.com
