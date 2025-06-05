#!/usr/bin/env python3
"""
Cisco AUX Port Telnet Audit Script via Jump Host
Connects to jump host 172.16.39.128 and audits routers from CSV file
Compatible with Linux and Windows
"""

import csv
import json
import os
import sys
import getpass
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import re
from pathlib import Path

try:
    from netmiko import ConnectHandler
    import paramiko
except ImportError:
    print("Required packages not installed. Please run:")
    print("pip install netmiko paramiko")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('audit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class JumpHostAuditor:
    def __init__(self):
        self.jump_host = {
            "device_type": "linux",
            "host": "172.16.39.128",
            "username": "root",
            "password": None
        }
        self.routers = []
        self.results = []
        self.env_file = Path(".env")

    def load_environment(self):
        """Load or create .env file with jump host password"""
        jump_password = None

        if self.env_file.exists():
            try:
                with open(self.env_file, 'r') as f:
                    for line in f:
                        if line.startswith('JUMP_HOST_PASSWORD='):
                            jump_password = line.split('=', 1)[1].strip().strip('"\'')
                            break

                if jump_password:
                    use_saved = input(f"Use saved jump host password? (y/n): ").lower().strip()
                    if use_saved != 'y':
                        jump_password = None

            except Exception as e:
                logger.warning(f"Error reading .env file: {e}")

        if not jump_password:
            jump_password = getpass.getpass("Enter jump host (172.16.39.128) password: ")

            save_password = input("Save password to .env file? (y/n): ").lower().strip()
            if save_password == 'y':
                try:
                    with open(self.env_file, 'w') as f:
                        f.write(f'JUMP_HOST_PASSWORD="{jump_password}"\n')
                    logger.info("Password saved to .env file")
                except Exception as e:
                    logger.warning(f"Could not save password: {e}")

        self.jump_host["password"] = jump_password

    def load_routers_from_csv(self, csv_file="routers.csv"):
        """Load router configurations from CSV file"""
        if not Path(csv_file).exists():
            # Create sample CSV file
            sample_data = [
                ["hostname", "ip", "device_type", "username", "password", "secret", "ios_version", "notes"],
                ["R0", "172.16.39.100", "cisco_ios", "cisco", "cisco", "cisco", "15.1", "Default entry"],
                ["R1", "172.16.39.101", "cisco_ios", "cisco", "cisco", "cisco", "15.1", "Default entry"],
                ["R2", "172.16.39.102", "cisco_ios", "cisco", "cisco", "cisco", "15.1", "Default entry"],
                ["R3", "172.16.39.103", "cisco_ios", "cisco", "cisco", "cisco", "15.1", "Default entry"],
                ["R4", "172.16.39.104", "cisco_ios", "cisco", "cisco", "cisco", "15.1", "Default entry"],
                ["R5", "172.16.39.105", "cisco_ios", "cisco", "cisco", "cisco", "15.1", "Default entry"]
            ]

            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(sample_data)

            logger.info(f"Created sample {csv_file} file. Please update with your router details.")

        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Filter for routers R1-R5 (and R0 if needed)
                    if row['hostname'].upper() in ['R0', 'R1', 'R2', 'R3', 'R4', 'R5']:
                        router_config = {
                            "device_type": row['device_type'].strip(),
                            "host": row['ip'].strip(),
                            "username": row['username'].strip(),
                            "password": row['password'].strip(),
                            "secret": row['secret'].strip() if row['secret'].strip() else None,
                            "hostname": row['hostname'].strip()
                        }
                        self.routers.append(router_config)

            logger.info(f"Loaded {len(self.routers)} routers from {csv_file}")

        except FileNotFoundError:
            logger.error(f"CSV file {csv_file} not found")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            sys.exit(1)

    def test_jump_host_connection(self):
        """Test connection to jump host"""
        logger.info("Testing jump host connection...")
        try:
            with ConnectHandler(**self.jump_host, timeout=10) as conn:
                output = conn.send_command("hostname", delay_factor=1)
                logger.info(f"✓ Connected to jump host: {output.strip()}")
                return True
        except Exception as e:
            logger.error(f"✗ Jump host connection failed: {e}")
            return False

    def audit_router_via_jump(self, router_config):
        """Audit a single router via jump host"""
        router_name = router_config["hostname"]
        router_ip = router_config["host"]

        logger.info(f"Auditing {router_name} ({router_ip}) via jump host...")

        result = {
            "hostname": router_name,
            "ip_address": router_ip,
            "line": "connection_failed",
            "telnet_allowed": "UNKNOWN",
            "login_method": "UNKNOWN",
            "exec_timeout": "UNKNOWN",
            "risk_level": "UNKNOWN",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": None,
            "connection_method": "jump_host"
        }

        try:
            # Connect to jump host first
            with ConnectHandler(**self.jump_host, timeout=15) as jump_conn:
                # Method 1: Try using sshpass (Linux/Unix)
                ssh_command = f"sshpass -p '{router_config['password']}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 {router_config['username']}@{router_ip}"

                try:
                    # Send SSH command to connect to router
                    output = jump_conn.send_command_timing(ssh_command, delay_factor=2, max_loops=10)

                    # Check if we got a router prompt
                    if '>' not in output and '#' not in output:
                        # If sshpass failed, try expect-style login
                        raise Exception("sshpass method failed, trying manual SSH")

                except:
                    # Method 2: Manual SSH with expect-style interaction
                    logger.info(f"Trying manual SSH for {router_name}...")
                    ssh_command = f"ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 {router_config['username']}@{router_ip}"

                    # Send SSH command
                    jump_conn.write_channel(ssh_command + '\n')

                    # Wait for password prompt and send password
                    output = ""
                    for i in range(15):  # Wait up to 15 seconds
                        time.sleep(1)
                        new_output = jump_conn.read_channel()
                        output += new_output

                        if 'password:' in output.lower() or 'Password:' in output:
                            jump_conn.write_channel(router_config['password'] + '\n')
                            time.sleep(2)
                            output += jump_conn.read_channel()
                            break
                        elif '>' in output or '#' in output:
                            break
                        elif 'Connection refused' in output or 'No route to host' in output:
                            raise Exception(f"Cannot connect to {router_ip}")

                # At this point, we should be connected to the router
                # Check if we need to enter enable mode
                if '>' in output and '#' not in output:
                    jump_conn.write_channel('enable\n')
                    time.sleep(1)
                    enable_output = jump_conn.read_channel()

                    if 'Password:' in enable_output and router_config.get('secret'):
                        jump_conn.write_channel(router_config['secret'] + '\n')
                        time.sleep(1)
                        enable_output += jump_conn.read_channel()

                    output += enable_output

                # Send the audit command
                audit_cmd = "show run | include ^hostname|^line aux|^ transport input|^ login|^ exec-timeout"
                jump_conn.write_channel(audit_cmd + '\n')
                time.sleep(3)  # Give time for command to execute

                # Read the command output
                cmd_output = jump_conn.read_channel()

                # Clean up - exit from router
                jump_conn.write_channel('exit\n')
                time.sleep(1)

                # Parse the router output
                if cmd_output and len(cmd_output.strip()) > 10:  # Ensure we got substantial output
                    result.update(self.parse_router_output(cmd_output, router_name, router_ip))
                    logger.info(f"✓ {router_name} - Risk: {result['risk_level']}")
                else:
                    raise Exception("No meaningful output received from router")

        except Exception as e:
            error_msg = str(e)
            result["error"] = error_msg
            logger.error(f"✗ {router_name} - {error_msg}")

        return result

    def parse_router_output(self, output, fallback_hostname, router_ip):
        """Parse router output and assess security risk"""
        lines = output.strip().split('\n')

        # Clean up the output (remove command echo and prompts)
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Skip command echo, prompts, and empty lines
            if (line and
                    not line.startswith('show run') and
                    not line.endswith('#') and
                    not line.endswith('>') and
                    not 'show run | include' in line):
                cleaned_lines.append(line)

        # Initialize parsing results
        hostname = fallback_hostname
        aux_line = "line aux 0"  # default
        telnet_allowed = "NO"
        login_method = "unknown"
        exec_timeout = "default"

        # Parse each line
        for line in cleaned_lines:
            if line.startswith("hostname"):
                parts = line.split()
                if len(parts) >= 2:
                    hostname = parts[1]
            elif line.startswith("line aux"):
                aux_line = line
            elif "transport input" in line:
                if re.search(r"transport input.*(all|telnet)", line, re.IGNORECASE):
                    telnet_allowed = "YES"
                elif re.search(r"transport input.*(ssh|none)", line, re.IGNORECASE):
                    telnet_allowed = "NO"
            elif line.strip() == "login":
                login_method = "line_password"
            elif "login local" in line:
                login_method = "local"
            elif "login authentication" in line:
                login_method = "aaa"
            elif "exec-timeout" in line:
                timeout_match = re.search(r"exec-timeout (\d+) (\d+)", line)
                if timeout_match:
                    min_val, sec_val = timeout_match.groups()
                    if min_val == "0" and sec_val == "0":
                        exec_timeout = "never"
                    else:
                        exec_timeout = f"{min_val}m{sec_val}s"

        # If no login method found but telnet is enabled, it might be no authentication
        if login_method == "unknown" and telnet_allowed == "YES":
            login_method = "none"

        # Risk assessment logic
        risk_level = self.assess_risk(telnet_allowed, login_method, exec_timeout)

        return {
            "hostname": hostname,
            "ip_address": router_ip,
            "line": aux_line,
            "telnet_allowed": telnet_allowed,
            "login_method": login_method,
            "exec_timeout": exec_timeout,
            "risk_level": risk_level,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": None,
            "connection_method": "jump_host"
        }

    def assess_risk(self, telnet_allowed, login_method, exec_timeout):
        """Assess security risk based on configuration"""
        if telnet_allowed != "YES":
            return "LOW"

        # Telnet is enabled, assess based on other factors
        if login_method in ["unknown", "none"]:
            return "CRITICAL"
        elif login_method == "line_password":
            return "HIGH"
        elif login_method in ["local", "aaa"]:
            if exec_timeout == "never":
                return "MEDIUM"
            else:
                return "MEDIUM"

        return "MEDIUM"

    def run_audit(self, max_workers=3):
        """Run audit across all routers via jump host"""
        logger.info(f"Starting audit of {len(self.routers)} routers via jump host...")

        # Test jump host connection first
        if not self.test_jump_host_connection():
            logger.error("Cannot connect to jump host. Exiting.")
            return False

        # Sequential processing (safer for jump host)
        for router in self.routers:
            result = self.audit_router_via_jump(router)
            self.results.append(result)

        return True

    def generate_reports(self):
        """Generate CSV report and summary"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"aux_telnet_audit_{timestamp}.csv"

        # CSV Report
        fieldnames = ["hostname", "ip_address", "line", "telnet_allowed", "login_method",
                      "exec_timeout", "risk_level", "connection_method", "timestamp", "error"]

        with open(csv_filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)

        # Console Summary
        self.print_summary()

        logger.info(f"Detailed report saved to: {csv_filename}")
        return csv_filename

    def print_summary(self):
        """Print audit summary to console"""
        total = len(self.results)
        successful = len([r for r in self.results if r["error"] is None])
        telnet_enabled = len([r for r in self.results if r["telnet_allowed"] == "YES"])

        risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
        for result in self.results:
            risk_level = result["risk_level"]
            if risk_level in risk_counts:
                risk_counts[risk_level] += 1

        print("\n" + "=" * 60)
        print("CISCO AUX PORT TELNET AUDIT SUMMARY (via Jump Host)")
        print("=" * 60)
        print(f"Jump Host: {self.jump_host['host']}")
        print(f"Total routers: {total}")
        print(f"Successfully audited: {successful}")
        print(f"Connection failures: {total - successful}")
        print(f"AUX telnet enabled: {telnet_enabled}")
        print("\nRisk Distribution:")
        for risk, count in risk_counts.items():
            if count > 0:
                print(f"  {risk}: {count}")

        # High-risk devices
        high_risk = [r for r in self.results if r["risk_level"] in ["CRITICAL", "HIGH"]]
        if high_risk:
            print(f"\n⚠️  HIGH-RISK DEVICES ({len(high_risk)}):")
            for device in high_risk:
                error_info = f" - ERROR: {device['error']}" if device['error'] else ""
                print(f"  • {device['hostname']} ({device['ip_address']}) - {device['risk_level']} "
                      f"(login: {device['login_method']}){error_info}")

        # Connection failures
        failed = [r for r in self.results if r["error"] is not None]
        if failed:
            print(f"\n❌ CONNECTION FAILURES ({len(failed)}):")
            for device in failed:
                print(f"  • {device['hostname']} ({device['ip_address']}) - {device['error']}")


def main():
    """Main execution function"""
    print("=" * 60)
    print("Cisco AUX Port Telnet Audit Script")
    print("Connects via Jump Host: 172.16.39.128")
    print("=" * 60)

    # Check for required tools
    if os.name == 'nt':  # Windows
        sshpass_check = os.system("where sshpass >nul 2>&1")
        if sshpass_check != 0:
            print("Warning: sshpass not found. You may need to install it or use alternative authentication.")
    else:  # Linux/Unix
        sshpass_check = os.system("which sshpass >/dev/null 2>&1")
        if sshpass_check != 0:
            print("Warning: sshpass not found. Installing...")
            os.system("sudo apt-get update && sudo apt-get install -y sshpass")

    try:
        auditor = JumpHostAuditor()

        # Load configuration
        auditor.load_environment()
        auditor.load_routers_from_csv()

        if not auditor.routers:
            logger.error("No routers loaded from CSV file")
            return

        # Run audit
        if auditor.run_audit():
            auditor.generate_reports()
            print(f"\n✅ Audit completed successfully!")
        else:
            print(f"\n❌ Audit failed - check logs for details")

    except KeyboardInterrupt:``
        print("\n\n🛑 Audit interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Audit failed: {e}")


if __name__ == "__main__":
    main()