# PCDdebugger


For PCD(SAAS):

# OpenStack Resource Debug Collector

This is a Python-based CLI tool to collect detailed information about OpenStack resources such as VMs, networks, volumes, stacks, users, and system health. It is useful for debugging infrastructure issues by fetching metadata from OpenStack services and organizing them into a structured folder.

---

## ✅ Features

- Collects VM (Nova) details, ports, migrations, and events
- Fetches attached volumes and associated images/flavors
- Retrieves security groups and rules (both VM-linked and global)
- Extracts stack and stack resource details (Heat)
- Collects user and role assignment information (Keystone)
- Performs health checks on compute, network, volume, and resource provider services
- Saves everything in a timestamped output directory

---

## 📦 Dependencies

Ensure the following are installed and configured:
- Python 3.x
- OpenStack CLI (`openstack`)
- Authentication sourced via `adminrc` or similar file

---

## 🚀 Usage

```bash
python3 openstack_debug.py [OPTIONS]
