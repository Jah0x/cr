# Kubernetes manifests

В этой директории хранится базовый манифест мигратора.

## Миграции

1. Проверьте образ в `k8s/migrator-job.yaml` (`ghcr.io/<org-or-user>/crm-migrator:latest`).
2. Убедитесь, что существуют `Secret` и `ConfigMap`:
   - `crm-backend-secret`
   - `crm-backend-config`
3. Запустите job:

```bash
kubectl apply -f k8s/migrator-job.yaml
```

4. Посмотрите логи:

```bash
kubectl logs job/crm-migrator
```
