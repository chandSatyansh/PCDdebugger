#!/usr/bin/env python3

import argparse
import subprocess
import os
import json
from datetime import datetime, timezone
import re

DEFAULT_OUTPUT_DIR = f"openstack-debug-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
OUTPUT_DIR = DEFAULT_OUTPUT_DIR

def run_cmd(cmd):
    print(f"[RUNNING] {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {' '.join(cmd)}\n{e.stderr.strip()}")
        return f"ERROR: {e.stderr.strip()}"

def save_text(text, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)

def extract_id(raw):
    if isinstance(raw, dict):
        return raw.get("id")
    elif isinstance(raw, str):
        match = re.search(r"\(([a-f0-9\-]{36})\)", raw)
        return match.group(1) if match else raw.strip()
    return None

def check_openstack_auth():
    print("[INFO] Checking OpenStack authentication...")
    result = run_cmd(["openstack", "token", "issue"])
    if "ERROR" in result or "Missing" in result:
        print("[ERROR] OpenStack CLI is not authenticated. Please source your adminrc.")
        exit(1)
    print("[OK] OpenStack authentication validated.")

def collect_nova_info(vm_id):
    os.makedirs(f"{OUTPUT_DIR}/nova", exist_ok=True)

    show_raw = run_cmd(["openstack", "server", "show", vm_id, "-f", "json"])
    save_text(show_raw, f"{OUTPUT_DIR}/nova/server_show.json")

    try:
        vm_data = json.loads(show_raw)
    except json.JSONDecodeError:
        print(f"[ERROR] Failed to decode JSON from server show.")
        vm_data = {}

    events = run_cmd(["openstack", "server", "event", "list", vm_id])
    save_text(events, f"{OUTPUT_DIR}/nova/server_events.txt")

    migrations = run_cmd(["openstack", "server", "migration", "list", "--server", vm_id])
    save_text(migrations, f"{OUTPUT_DIR}/nova/migrations.txt")

    return vm_data

def collect_ports_for_vm(vm_id):
    os.makedirs(f"{OUTPUT_DIR}/neutron", exist_ok=True)
    ports_raw = run_cmd(["openstack", "port", "list", "--device-id", vm_id, "-f", "json"])
    save_text(ports_raw, f"{OUTPUT_DIR}/neutron/vm_ports.json")

    try:
        ports = json.loads(ports_raw)
        for port in ports:
            port_id = port.get("ID")
            if port_id:
                detail = run_cmd(["openstack", "port", "show", port_id])
                save_text(detail, f"{OUTPUT_DIR}/neutron/port_{port_id}.txt")

            network_id = port.get("Network ID")
            if network_id:
                net_detail = run_cmd(["openstack", "network", "show", network_id])
                save_text(net_detail, f"{OUTPUT_DIR}/neutron/network_{network_id}.txt")
    except Exception as e:
        print(f"[WARN] Port/Network parsing failed: {e}")

def collect_security_groups_for_vm(vm_id):
    os.makedirs(f"{OUTPUT_DIR}/neutron", exist_ok=True)
    try:
        ports = json.loads(run_cmd(["openstack", "port", "list", "--device-id", vm_id, "-f", "json"]))
        sg_ids = set()
        for port in ports:
            sgs = port.get("Security Group") or port.get("Security Groups")
            if isinstance(sgs, list):
                sg_ids.update(sgs)
            elif isinstance(sgs, str) and sgs.startswith("["):
                sg_ids.update(json.loads(sgs))

        for sg_id in sg_ids:
            sg_detail = run_cmd(["openstack", "security", "group", "show", sg_id])
            sg_rules = run_cmd(["openstack", "security", "group", "rule", "list", sg_id])
            save_text(sg_detail, f"{OUTPUT_DIR}/neutron/security_group_{sg_id}.txt")
            save_text(sg_rules, f"{OUTPUT_DIR}/neutron/security_group_{sg_id}_rules.txt")
    except Exception as e:
        print(f"[WARN] Security group collection failed: {e}")

def collect_security_groups():
    os.makedirs(f"{OUTPUT_DIR}/neutron", exist_ok=True)
    try:
        sg_list = json.loads(run_cmd(["openstack", "security", "group", "list", "-f", "json"]))
        for sg in sg_list:
            sg_id = sg.get("ID")
            if sg_id:
                sg_detail = run_cmd(["openstack", "security", "group", "show", sg_id])
                sg_rules = run_cmd(["openstack", "security", "group", "rule", "list", sg_id])
                save_text(sg_detail, f"{OUTPUT_DIR}/neutron/security_group_{sg_id}.txt")
                save_text(sg_rules, f"{OUTPUT_DIR}/neutron/security_group_{sg_id}_rules.txt")
    except Exception as e:
        print(f"[WARN] Failed to collect all security groups: {e}")

def collect_volumes_for_vm(vm_id):
    os.makedirs(f"{OUTPUT_DIR}/cinder", exist_ok=True)
    try:
        server = json.loads(run_cmd(["openstack", "server", "show", vm_id, "-f", "json"]))
        attached_vols = server.get("os-extended-volumes:volumes_attached", [])
        if not attached_vols:
            print(f"[INFO] No volumes attached to VM {vm_id}")
            return
        for vol in attached_vols:
            vol_id = vol.get("id")
            if vol_id:
                vol_show = run_cmd(["openstack", "volume", "show", vol_id])
                save_text(vol_show, f"{OUTPUT_DIR}/cinder/volume_{vol_id}.txt")
    except Exception as e:
        print(f"[WARN] Failed to collect volumes for VM: {e}")

def collect_image_and_flavor(vm_data):
    image_id = extract_id(vm_data.get("image"))
    flavor_id = extract_id(vm_data.get("flavor"))
    print(f"[DEBUG] image_id = {image_id}, flavor_id = {flavor_id}")

    if image_id:
        img = run_cmd(["openstack", "image", "show", image_id])
        save_text(img, f"{OUTPUT_DIR}/glance/image_show.txt")
    if flavor_id:
        flv = run_cmd(["openstack", "flavor", "show", flavor_id])
        save_text(flv, f"{OUTPUT_DIR}/nova/flavor_show.txt")

def collect_stack_info(stack_id):
    os.makedirs(f"{OUTPUT_DIR}/heat", exist_ok=True)
    show = run_cmd(["openstack", "stack", "show", stack_id])
    save_text(show, f"{OUTPUT_DIR}/heat/stack_show.txt")

    res_list = run_cmd(["openstack", "stack", "resource", "list", stack_id])
    save_text(res_list, f"{OUTPUT_DIR}/heat/stack_resources.txt")

    try:
        resources = json.loads(run_cmd(["openstack", "stack", "resource", "list", stack_id, "-f", "json"]))
        for res in resources:
            name = res.get("resource_name")
            if name:
                res_show = run_cmd(["openstack", "stack", "resource", "show", stack_id, name])
                save_text(res_show, f"{OUTPUT_DIR}/heat/resource_{name}.txt")
    except Exception as e:
        print(f"[WARN] Resource parsing failed: {e}")

def collect_neutron_info(network_id):
    net = run_cmd(["openstack", "network", "show", network_id])
    save_text(net, f"{OUTPUT_DIR}/neutron/network_show.txt")

def collect_port_info(port_id):
    port = run_cmd(["openstack", "port", "show", port_id])
    save_text(port, f"{OUTPUT_DIR}/neutron/port_show.txt")

def collect_cinder_info(volume_id):
    vol = run_cmd(["openstack", "volume", "show", volume_id])
    save_text(vol, f"{OUTPUT_DIR}/cinder/volume_show.txt")

def collect_keystone_user_info(user_id_or_name):
    os.makedirs(f"{OUTPUT_DIR}/keystone", exist_ok=True)
    usr = run_cmd(["openstack", "user", "show", user_id_or_name])
    save_text(usr, f"{OUTPUT_DIR}/keystone/user_show.txt")

    roles = run_cmd(["openstack", "role", "assignment", "list", "--user", user_id_or_name, "--names"])
    save_text(roles, f"{OUTPUT_DIR}/keystone/user_role_assignments.txt")

def collect_health_checks():
    os.makedirs(f"{OUTPUT_DIR}/healthchecks", exist_ok=True)
    commands = [
        (["openstack", "hypervisor", "list", "--long"], "hypervisors.txt"),
        (["openstack", "compute", "service", "list"], "compute_services.txt"),
        (["openstack", "resource", "provider", "list"], "resource_providers.txt"),
        (["openstack", "network", "agent", "list"], "network_agents.txt"),
        (["openstack", "volume", "service", "list"], "volume_services.txt"),
    ]
    for cmd, filename in commands:
        output = run_cmd(cmd)
        save_text(output, f"{OUTPUT_DIR}/healthchecks/{filename}")

def main():
    global OUTPUT_DIR
    parser = argparse.ArgumentParser(description="OpenStack-only Resource Collector")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_DIR, help="Output directory")
    parser.add_argument("--vm", help="VM ID")
    parser.add_argument("--network", help="Network ID")
    parser.add_argument("--port", help="Port ID")
    parser.add_argument("--volume", help="Volume ID")
    parser.add_argument("--stack", help="Heat Stack ID")
    parser.add_argument("--user", help="Keystone User ID or Name")

    args = parser.parse_args()
    OUTPUT_DIR = args.output
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    check_openstack_auth()

    vm_data = {}
    if args.vm:
        vm_data = collect_nova_info(args.vm)
        collect_ports_for_vm(args.vm)
        collect_volumes_for_vm(args.vm)
        collect_security_groups_for_vm(args.vm)
        collect_image_and_flavor(vm_data)

    if args.network:
        collect_neutron_info(args.network)
    if args.port:
        collect_port_info(args.port)
    if args.volume:
        collect_cinder_info(args.volume)
    if args.stack:
        collect_stack_info(args.stack)
    if args.user:
        collect_keystone_user_info(args.user)

    collect_security_groups()
    collect_health_checks()

    summary = f"""OpenStack Resource Summary - {datetime.now(timezone.utc).isoformat()} UTC
VM: {args.vm or 'N/A'}
Stack: {args.stack or 'N/A'}
User: {args.user or 'N/A'}
"""
    save_text(summary, f"{OUTPUT_DIR}/summary.txt")

if __name__ == "__main__":
    main()
