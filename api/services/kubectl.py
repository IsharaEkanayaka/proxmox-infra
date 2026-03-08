import logging
import paramiko

from .. import config
from ..database import get_db

logger = logging.getLogger(__name__)


def _get_control_plane_ip(cluster_id: str) -> str:
    """Get the first control plane IP for a cluster."""
    db = get_db()
    try:
        row = db.execute("SELECT ip_start FROM clusters WHERE id=?", (cluster_id,)).fetchone()
        if not row:
            raise RuntimeError(f"cluster {cluster_id} not found")
        return f"{config.VM_IP_PREFIX}{row['ip_start']}"
    finally:
        db.close()


def run_kubectl(cluster_id: str, args: list[str], timeout: int = 30) -> str:
    """Run a kubectl command on the cluster's control plane via SSH (paramiko)."""
    ip = _get_control_plane_ip(cluster_id)
    base = config.read_base_tfvars()
    user = base.get("ssh_user", "ubuntu")
    password = base.get("ssh_password", "ubuntu")

    cmd = "kubectl " + " ".join(args)
    logger.info("[%s] %s on %s", cluster_id, cmd, ip)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(ip, username=user, password=password, timeout=10, look_for_keys=False)
        _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        if exit_code != 0:
            raise RuntimeError(f"kubectl failed: {err}")
        return out
    finally:
        client.close()
