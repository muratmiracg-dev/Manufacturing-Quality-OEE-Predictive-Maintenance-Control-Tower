# Kubernetes reference deployment

The manifests deploy the recommendation-only API with two replicas, a
read-only root filesystem, non-root identity, dropped capabilities, probes,
resource bounds, HPA, PDB and default-deny-style network policy.

Before use:

1. publish an immutable image and replace the example image tag;
2. supply secrets through an external secrets manager;
3. adapt ingress/egress selectors to the cluster;
4. sign and verify the image;
5. validate the model and operational thresholds for the target facility.

