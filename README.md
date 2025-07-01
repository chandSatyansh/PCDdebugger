

---

### ✅ `README.md`

````markdown
# PCDdebugger

This repository contains two debug tools for Platform9-managed OpenStack environments:

1. **`pcddebugger.py`** – For **on-prem PCD** deployments. Meant to be run directly on the control plane node with access to Kubernetes and OpenStack CLIs.
2. **`saasdebugger.py`** – For **SaaS-hosted PCD** regions. Designed to collect OpenStack debug data without requiring Kubernetes access.

---

## 📁 Components

### 1. `pcddebugger.py`

A self-contained Python tool to collect detailed debug information about OpenStack VMs and their attached resources **alongside Kubernetes pod logs**.

---

### 🔧 Features

- Collects VM-related data:
  - Server details, events, and migrations
  - Attached volumes
  - Ports and networks
  - Security groups and rules
  - Image and flavor info
- Collects logs and descriptions for OpenStack pods (Nova, Glance, Keystone, Cinder, Neutron)
- Heat stack resources and metadata
- Keystone user info and roles
- OpenStack service health checks
- Option to archive output into a `.zip` file

---

### ✅ Requirements

- Python 3.6+
- `openstack` CLI installed and authenticated (`source admin.rc`)
- `kubectl` installed and configured (`~/.kube/config`)
- Access to relevant Kubernetes namespace

---

### 🚀 Usage

```bash
./pcddebugger.py --namespace <k8s-namespace> [OPTIONS]
````

#### Required:

* `--namespace`: Kubernetes namespace where OpenStack pods are deployed (e.g. `supportinternal-region-one`)

#### Optional Flags:

| Flag             | Description                               |
| ---------------- | ----------------------------------------- |
| `--vm <vm_id>`   | VM ID to collect details and associations |
| `--stack <id>`   | Heat stack ID                             |
| `--user <id>`    | Keystone user ID or name                  |
| `--volume <id>`  | Volume ID (for targeted volume logs)      |
| `--port <id>`    | Port ID (for targeted neutron logs)       |
| `--network <id>` | Network ID (for targeted neutron logs)    |
| `--output <dir>` | Custom output directory                   |
| `--zip`          | Zip the entire output folder              |

---

### 📂 Output Structure

```
debug-output-YYYYMMDD-HHMMSS/
├── nova/
├── cinder/
├── neutron/
├── heat/
├── keystone/
├── glance/
├── health/
├── logs/
├── describe/
├── events/
├── summary.txt
└── debug-output-*.zip   # If --zip used
```

---

### 🧪 Example

```bash
./pcddebugger.py \
  --namespace supportinternal-region-one \
  --vm 95c6cf8e-8b18-43cc-9c3e-87424139e611 \
  --stack my_stack_id \
  --user demo \
  --zip
```

---

### 🛠️ Notes

* Must be run from a control plane node or environment with `kubectl` and `openstack` CLI access.
* Pod logs are fetched for all relevant containers. `--previous` logs included if the pod has restarted.
* Make sure your `kubeconfig` and `admin.rc` are both correctly sourced.

---

---

### 2. `saasdebugger.py`

A lightweight OpenStack CLI tool for collecting debug info **without Kubernetes access** — useful for SaaS-based deployments.

---

### 🔍 Features

* Collects:

  * VM details, events, migrations
  * Attached volumes
  * Ports and networks
  * Security groups and rules
  * Image and flavor
* Optional:

  * Heat stack and resource details
  * Keystone user role mappings
* Health checks for:

  * Compute services
  * Network agents
  * Volume services
  * Resource providers
* Organizes all collected data in a timestamped output directory

---

### ✅ Requirements

* Python 3.x
* OpenStack CLI (`openstack`)
* Environment should be authenticated using `source admin.rc`

---

### 🚀 Usage

```bash
python3 saasdebugger.py --vm <vm_id> [OPTIONS]
```

#### Common Options

| Flag             | Description                          |
| ---------------- | ------------------------------------ |
| `--vm <vm_id>`   | VM ID to collect info for (Required) |
| `--stack <id>`   | Heat stack ID                        |
| `--user <id>`    | Keystone user ID or name             |
| `--output <dir>` | Custom output directory              |
| `--zip`          | Zip the output folder                |

---

### 🧪 Example

```bash
python3 saasdebugger.py \
  --vm 95c6cf8e-8b18-43cc-9c3e-87424139e611 \
  --zip
```

---

## 📄 License

This script is internal tooling for Platform9 troubleshooting. You may modify, fork, and adapt it for your custom workflows.

---


