#!/usr/bin/env python3
"""
Phased Audit Tool

This tool performs a 5-phase security audit on network devices.
Phases:
1. Connectivity Verification
2. Authentication Testing
3. Configuration Audit
4. Risk Assessment
5. Reporting and Recommendations
"""

import sqlite3
import datetime
import json
import uuid
import subprocess # Added for Phase 1
import re # Added for Phase 1 RTT parsing
import csv
import os
import sys
import time
import threading
import traceback
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException, SSHException
from flask import Flask, render_template, jsonify, request, Response, redirect, url_for

DATABASE_NAME = 'phased_audit_results.sqlite'

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'phased_audit_secret_key'
app.config['PORT'] = 5012

def initialize_database():
    """Initializes the SQLite database and creates the audit_phase_results table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_phase_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            audit_run_id TEXT NOT NULL,
            router_hostname TEXT NOT NULL,
            router_ip TEXT,
            phase_number INTEGER NOT NULL,
            phase_name TEXT NOT NULL,
            status TEXT NOT NULL, 
            summary TEXT,
            details TEXT, 
            error_message TEXT,
            start_time DATETIME,
            end_time DATETIME
        )
    ''')
    conn.commit()
    conn.close()
    print(f"Database {DATABASE_NAME} initialized/verified.")

def log_phase_result(audit_run_id, router_hostname, router_ip, phase_number, phase_name, status, summary="", details=None, error_message="", start_time=None, end_time=None):
    """Logs the result of an audit phase to the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    current_time = datetime.datetime.now()
    if start_time is None:
        start_time = current_time
    if end_time is None and status not in ["IN_PROGRESS"]:
        end_time = current_time

    details_json = json.dumps(details) if details is not None else None

    cursor.execute('''
        INSERT INTO audit_phase_results 
            (audit_run_id, router_hostname, router_ip, phase_number, phase_name, status, summary, details, error_message, start_time, end_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (audit_run_id, router_hostname, router_ip, phase_number, phase_name, status, summary, details_json, error_message, start_time, end_time))
    conn.commit()
    conn.close()

# --- Phase 1: Helper Function ---
def _ping_device_via_jump_server(ip_address, jump_host_creds):
    """Pings an IP address through the jump server and returns status, summary, details, and error."""
    try:
        print(f"Connecting to jump server {jump_host_creds['ip']} to ping {ip_address}...")
        # Connect to the jump server
        jump_conn = connect_to_jump_server(jump_host_creds)
        
        if isinstance(jump_conn, tuple) and jump_conn[0] is None:
            # Connection to jump server failed
            status = "FAILURE"
            summary = f"Failed to connect to jump server: {jump_conn[1]}"
            details = None
            error = jump_conn[1]
            return status, summary, details, error
        
        # Successfully connected to jump server, now ping the target device
        ping_cmd = f"ping -c 4 {ip_address}"
        print(f"Executing on jump server: {ping_cmd}")
        ping_output = jump_conn.send_command(ping_cmd, delay_factor=2)
        
        # Check ping results
        if "64 bytes from" in ping_output and ("0% packet loss" in ping_output or "0.0% packet loss" in ping_output):
            status = "SUCCESS"
            summary = f"Successfully pinged {ip_address} via jump server."
            # Try to extract RTT avg from output
            rtt_match = re.search(r'min/avg/max/(?:mdev|stddev) = [\d\.]+/([\d\.]+)/[\d\.]+', ping_output)
            if rtt_match:
                avg_rtt = rtt_match.group(1)
                details = {"rtt_avg_ms": avg_rtt, "output": ping_output}
                summary += f" RTT avg: {avg_rtt} ms"
            else:
                details = {"output": ping_output}
            error = ""
        else:
            status = "FAILURE"
            summary = f"Ping failed: No reply from {ip_address} via jump server."
            details = {"output": ping_output}
            error = f"No reply from {ip_address} via jump server."
        
        # Disconnect from jump server
        jump_conn.disconnect()
        
    except Exception as e:
        status = "FAILURE"
        summary = f"Error during ping operation: {str(e)}"
        details = None
        error = f"Exception while pinging via jump server: {str(e)}"
    
    return status, summary, details, error

# --- Phase 1: Connectivity Verification ---
def execute_phase1_connectivity(audit_run_id, router_config, jump_host_creds=None):
    """Verifies basic network connectivity to the router via jump server (e.g., ICMP ping)."""
    hostname = router_config.get('hostname')
    ip_address = router_config.get('ip')
    phase_name = "Connectivity Verification"
    print(f"Starting Phase 1: {phase_name} for {hostname} ({ip_address})")
    start_time = datetime.datetime.now()

    if not ip_address:
        status = "FAILURE"
        summary = "IP address not provided for router."
        details = None
        error = "Missing IP address in router configuration."
    elif not jump_host_creds:
        status = "FAILURE"
        summary = "Jump server credentials not provided."
        details = None
        error = "Missing jump server configuration."
    else:
        # Use the jump server to perform connectivity check
        print(f"Using jump server {jump_host_creds['ip']} to check connectivity to {hostname} ({ip_address})")
        status, summary, details, error = _ping_device_via_jump_server(ip_address, jump_host_creds)

    log_phase_result(audit_run_id, hostname, ip_address, 1, phase_name, status, summary, details, error, start_time)
    return {"status": status, "details": details, "error": error}

# --- Jump Server Connection ---
def connect_to_jump_server(jump_host_config):
    """Establishes a connection to the jump server."""
    if not jump_host_config:
        return None, "No jump host configuration provided."
    
    jump_ip = jump_host_config.get('ip')
    jump_username = jump_host_config.get('username')
    jump_password = jump_host_config.get('password')
    jump_port = jump_host_config.get('port', 22)
    
    if not all([jump_ip, jump_username, jump_password]):
        return None, "Missing required jump host credentials (IP, username, or password)."
    
    jump_device = {
        'device_type': 'linux',
        'host': jump_ip,
        'username': jump_username,
        'password': jump_password,
        'port': jump_port,
        'timeout': 20,  # Increase timeout for better reliability
        'session_log': 'jump_server_session.log'  # Log session for debugging
    }
    
    try:
        print(f"Connecting to jump server {jump_ip}...")
        connection = ConnectHandler(**jump_device)
        # Verify connection by running a simple command
        output = connection.send_command('hostname')
        print(f"Successfully connected to jump server: {output.strip()}")
        return connection
    except NetmikoTimeoutException:
        error_msg = f"Timeout connecting to jump server {jump_ip}"
        print(error_msg)
        return None, error_msg
    except NetmikoAuthenticationException:
        error_msg = f"Authentication failed for jump server {jump_ip}"
        print(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"Error connecting to jump server {jump_ip}: {str(e)}"
        print(error_msg)
        return None, error_msg

# --- Phase 2: Authentication Testing ---
def execute_phase2_authentication(audit_run_id, router_config, phase1_result, jump_host_creds=None):
    """Attempts to authenticate to the router using provided credentials via a jump server."""
    hostname = router_config.get('hostname')
    ip_address = router_config.get('ip')
    phase_name = "Authentication Testing"
    print(f"Starting Phase 2: {phase_name} for {hostname}")
    start_time = datetime.datetime.now()
    net_connect = None # Initialize net_connect
    jump_connection = None

    if phase1_result.get('status') != "SUCCESS":
        status = "SKIPPED"
        summary = "Skipped due to Phase 1 failure (device unreachable)."
        details = None
        error = phase1_result.get('error', "Connectivity failed.")
        log_phase_result(audit_run_id, hostname, ip_address, 2, phase_name, status, summary, details, error, start_time)
        return {"status": status, "details": details, "error": error, "connection": net_connect, "jump_connection": jump_connection}

    # Extract router config (from Phase 1 results if available)
    hostname = router_config.get('hostname')
    ip_address = router_config.get('ip')
    
    # Use default credentials if not specified in router config
    username = router_config.get('username', default_router_creds.get('username', ''))
    password = router_config.get('password', default_router_creds.get('password', ''))
    secret = router_config.get('secret', default_router_creds.get('secret', ''))
    device_type = router_config.get('device_type', default_router_creds.get('device_type', 'cisco_ios'))
    port = router_config.get('port', 22)
    
    print(f"  [DEBUG] Using credentials for {hostname}: username={username}, device_type={device_type}")
    if not username or not password:
        print(f"  [WARNING] Missing username or password for {hostname}, authentication will likely fail")

    if not all([ip_address, username, password]):
        status = "FAILURE"
        summary = "Missing required credentials (IP, username, or password) for SSH."
        details = None
        error = "Incomplete router configuration for authentication."
        log_phase_result(audit_run_id, hostname, ip_address, 2, phase_name, status, summary, details, error, start_time)
        return {"status": status, "details": details, "error": error, "connection": net_connect, "jump_connection": jump_connection}
    
    # First connect to jump server if credentials are provided
    if jump_host_creds:
        print(f"  Connecting to jump server {jump_host_creds.get('ip')} using credentials: {jump_host_creds.get('username')}")
        jump_connection, jump_error = connect_to_jump_server(jump_host_creds)
        
        if not jump_connection:
            status = "FAILURE"
            summary = f"Failed to connect to jump server {jump_host_creds.get('ip')}."
            details = {
                "jump_host": jump_host_creds.get('ip'),
                "jump_user": jump_host_creds.get('username'),
                "jump_device_type": jump_host_creds.get('device_type')
            }
            error = f"Jump server connection error: {jump_error}"
            print(f"  ERROR: {error}")
            log_phase_result(audit_run_id, hostname, ip_address, 2, phase_name, status, summary, details, error, start_time)
            return {"status": status, "details": details, "error": error, "connection": net_connect, "jump_connection": jump_connection}
        
        # Now connect to the router through the jump server using ProxyCommand
        device = {
            'device_type': device_type,
            'host': ip_address,
            'username': username,
            'password': password,
            'secret': secret,
            'port': router_config.get('port', 22),
            'global_delay_factor': 2,
            'session_log': f'logs/{hostname}_session.log',
            # Use the jump server as a proxy
            'ssh_config_file': None,  # Don't use local SSH config
            'conn_timeout': 15,
        }
        
        try:
            print(f"  [DEBUG] Authentication Phase: Attempting SSH to {ip_address} through jump server as {username}...")
            print(f"  [DEBUG] Device connection parameters: type={device_type}, host={ip_address}, port={device.get('port', 22)}")
            
            # Adjust the timeout to prevent hanging indefinitely
            device['conn_timeout'] = 30  # 30 seconds timeout
            device['auth_timeout'] = 20  # 20 seconds auth timeout
            device['banner_timeout'] = 15  # 15 seconds banner timeout
            
            print(f"  [DEBUG] Setting connection timeouts: conn={device['conn_timeout']}s, auth={device['auth_timeout']}s")
            print(f"  [DEBUG] Initiating ConnectHandler... This may take a moment.")
            
            # For Netmiko, we'll use a direct connection since we already have the jump server connection
            start_connect = datetime.datetime.now()
            net_connect = ConnectHandler(**device)
            connect_time = (datetime.datetime.now() - start_connect).total_seconds()
            
            print(f"  [DEBUG] ConnectHandler completed in {connect_time:.2f} seconds")
            
            # Verify connection is active
            if net_connect.is_alive():
                print(f"  [DEBUG] Connection verified as alive")
                status = "SUCCESS"
                summary = f"Successfully authenticated to {ip_address} via SSH through jump server in {connect_time:.2f}s."
                details = {
                    "auth_method": "ssh_password", 
                    "device_type": device_type, 
                    "jump_server": jump_host_creds.get('ip'),
                    "connection_time": f"{connect_time:.2f}s"
                }
                error = ""
                print(f"  SSH connection successful for {hostname} through jump server.")
            else:
                print(f"  [ERROR] Connection created but not alive")
                status = "FAILURE"
                summary = f"Connected to {ip_address} but connection not alive."
                details = {"auth_method": "ssh_password", "device_type": device_type}
                error = "Connection not alive after creation"
                net_connect = None
        except NetmikoTimeoutException as e:
            status = "FAILURE"
            summary = f"Connection timeout while connecting to {ip_address} through jump server."
            details = {
                "exception_type": "NetmikoTimeoutException",
                "jump_server": jump_host_creds.get('ip'),
                "target_device": ip_address,
                "timeout_settings": f"conn={device.get('conn_timeout', 'default')}s, auth={device.get('auth_timeout', 'default')}s"
            }
            error = f"Timeout error: {str(e)}"
            print(f"  [ERROR] Connection timeout to {hostname} through jump server: {error}")
            print(f"  [DEBUG] This usually indicates network connectivity issues, firewall blocks, or incorrect IP")
        except NetmikoAuthenticationException as e:
            status = "FAILURE"
            summary = f"Authentication failed for {ip_address} through jump server."
            details = {
                "exception_type": "NetmikoAuthenticationException",
                "jump_server": jump_host_creds.get('ip'),
                "username": username,
                "device_type": device_type
            }
            error = f"Authentication error: {str(e)}"
            print(f"  [ERROR] Authentication failed for {hostname}: {error}")
            print(f"  [DEBUG] This usually indicates incorrect username/password or privilege issues")
        except Exception as e:
            status = "FAILURE"
            summary = f"Failed to connect to {ip_address} through jump server."
            details = {
                "exception_type": str(type(e).__name__),
                "jump_server": jump_host_creds.get('ip'),
                "target_device": ip_address
            }
            error = str(e)
            print(f"  [ERROR] Exception connecting to {hostname} through jump server: {error}")
            print(f"  [DEBUG] Exception type: {type(e).__name__}")
            print(f"  [DEBUG] Exception details: {repr(e)}")
            
            # Log traceback for more detailed debugging
            import traceback
            traceback_text = traceback.format_exc()
            print(f"  [DEBUG] Traceback:\n{traceback_text}")
            details["traceback"] = traceback_text
    else:
        # Direct connection without jump server (fallback)
        device = {
            'device_type': device_type,
            'host': ip_address,
            'username': username,
            'password': password,
            'secret': secret,
            'port': router_config.get('port', 22),
            'global_delay_factor': 2,
        }

        try:
            print(f"  Attempting direct SSH to {ip_address} as {username}...")
            net_connect = ConnectHandler(**device)
            status = "SUCCESS"
            summary = f"Successfully authenticated to {ip_address} via direct SSH."
            details = {"auth_method": "ssh_password", "device_type": device_type}
            error = ""
            print(f"  Direct SSH connection successful for {hostname}.")
        except NetmikoAuthenticationException as e:
            status = "FAILURE"
            summary = f"Authentication failed for {ip_address}. Invalid credentials or SSH configuration issue."
            details = {"exception_type": "NetmikoAuthenticationException"}
            error = str(e)
            print(f"  Authentication failed for {hostname}: {error}")
        except NetmikoTimeoutException as e:
            status = "FAILURE"
            summary = f"SSH connection timed out for {ip_address}. Device may be unreachable or SSH service not responding."
            details = {"exception_type": "NetmikoTimeoutException"}
            error = str(e)
            print(f"  SSH timeout for {hostname}: {error}")
        except SSHException as e: # More generic SSH library errors (e.g. no matching key exchange, etc.)
            status = "FAILURE"
            summary = f"An SSH protocol error occurred for {ip_address}."
            details = {"exception_type": "SSHException"}
            error = str(e)
            print(f"  SSH protocol error for {hostname}: {error}")
        except Exception as e:
            status = "FAILURE"
            summary = f"An unexpected error occurred during SSH connection to {ip_address}."
            details = {"exception_type": str(type(e).__name__)}
            error = str(e)
            print(f"  Unexpected SSH error for {hostname}: {error}")

    log_phase_result(audit_run_id, hostname, ip_address, 2, phase_name, status, summary, details, error, start_time)
    # If connection failed, net_connect will be None. If successful, it's the active connection object.
    return {"status": status, "details": details, "error": error, "connection": net_connect}

# --- Phase 3: Configuration Audit ---
def execute_phase3_config_audit(audit_run_id, router_config, phase2_result):
    """Audits the device AUX port configuration to identify telnet security issues."""
    hostname = router_config.get('hostname')
    ip_address = router_config.get('ip')
    net_connect = phase2_result.get('connection') # Get connection from Phase 2
    phase_name = "Configuration Audit"
    print(f"Starting Phase 3: {phase_name} for {hostname} ({ip_address})")
    start_time = datetime.datetime.now()
    collected_data = {}
    
    # Initialize security findings that Phase 4 will use
    telnet_allowed = "UNKNOWN"
    login_method = "unknown"
    exec_timeout = "default"
    risk_level = "UNKNOWN"

    if phase2_result.get('status') != "SUCCESS" or not net_connect:
        status = "SKIPPED"
        summary = "Skipped due to Phase 2 (Authentication) failure or no connection object."
        details = None
        error = phase2_result.get('error', "Authentication failed or connection not available.")
        if net_connect: # Should not happen if status is not SUCCESS, but good practice to close if it exists and we skip
            try:
                net_connect.disconnect()
                print(f"  Closed stray connection to {hostname} before skipping Phase 3.")
            except Exception as e_disc:
                print(f"  Error disconnecting stray connection for {hostname}: {e_disc}")
        log_phase_result(audit_run_id, hostname, ip_address, 3, phase_name, status, summary, details, error, start_time)
        return {"status": status, "details": details, "error": error}

    try:
        # Correctly access secret from router_config for enable mode
        enable_secret = router_config.get('secret', '')
        if net_connect.check_enable_mode() is False:
            if enable_secret:
                print(f"  Entering enable mode on {hostname}...")
                net_connect.enable()
            else:
                print(f"  Enable mode not entered on {hostname} as no secret was provided. Skipping enable-only commands or proceeding with caution.")

        # Define commands for AUX port security audit - focused specifically on telnet access
        commands_to_run = [
            "show line aux 0",
            "show running-config | include ^line aux",
            "show running-config | include ^ transport input",
            "show running-config | include ^ login", 
            "show running-config | include ^ exec-timeout",
            "show running-config | include aaa new-model", 
            "show running-config | include ^username", 
            "show users" # See current logged-in users (might show AUX activity)
        ]

        print(f"  Collecting configurations from {hostname}...")
        for cmd in commands_to_run:
            print(f"    Executing: {cmd}")
            try:
                # For commands that might not exist or fail on some devices/privilege levels, 
                # use send_command_timing or add error handling per command if needed.
                # For simplicity, direct send_command is used here.
                output = net_connect.send_command(cmd, read_timeout=20) # Increased read_timeout for potentially long configs
                collected_data[cmd] = output
            except Exception as cmd_e:
                print(f"    Error executing command '{cmd}': {str(cmd_e)}")
                collected_data[cmd] = f"ERROR: {str(cmd_e)}"
        
        # Analyze the collected data for AUX port telnet security
        aux_line_config = ""
        for cmd, output in collected_data.items():
            if "include ^line aux" in cmd or "show line aux 0" in cmd:
                aux_line_config += output + "\n"
        
        # 1. Check if telnet is allowed on AUX port
        if "transport input none" in aux_line_config.lower():
            telnet_allowed = "NO"
        elif "transport input ssh" in aux_line_config.lower() and "transport input telnet" not in aux_line_config.lower() and "transport input all" not in aux_line_config.lower():
            telnet_allowed = "NO"
        elif "transport input telnet" in aux_line_config.lower() or "transport input all" in aux_line_config.lower():
            telnet_allowed = "YES"
        
        # 2. Check login method on AUX port
        if "no login" in aux_line_config.lower():
            login_method = "none"
        elif "login local" in aux_line_config.lower():
            login_method = "local"
        elif "login authentication" in aux_line_config.lower():
            login_method = "aaa"
        elif "login" in aux_line_config.lower() and "password" in aux_line_config.lower():
            login_method = "line_password"
        
        # 3. Check exec timeout on AUX port
        if "exec-timeout 0 0" in aux_line_config.lower() or "no exec-timeout" in aux_line_config.lower():
            exec_timeout = "never"
        elif "exec-timeout" in aux_line_config.lower():
            # Extract the timeout value for reference
            exec_timeout_match = re.search(r'exec-timeout (\d+) (\d+)', aux_line_config)
            if exec_timeout_match:
                minutes = exec_timeout_match.group(1)
                seconds = exec_timeout_match.group(2)
                exec_timeout = f"{minutes}m {seconds}s"
        
        # 4. Determine overall risk level based on findings
        risk_level = "LOW"
        if telnet_allowed == "YES" and login_method == "none":
            risk_level = "CRITICAL"
        elif telnet_allowed == "YES":
            risk_level = "HIGH"
        elif login_method == "none" or login_method == "line_password":
            risk_level = "MEDIUM"
        elif exec_timeout == "never":
            risk_level = "MEDIUM"
        
        # Set status based on risk level
        if risk_level == "CRITICAL" or risk_level == "HIGH":
            status = "WARNING"
        elif risk_level == "MEDIUM":
            status = "INFO"
        else:
            status = "SUCCESS"
            
        summary = f"AUX port security analysis: telnet={telnet_allowed}, login={login_method}, timeout={exec_timeout}, risk={risk_level}"
        
        # Store both raw data and analyzed findings
        details = {
            "collected_configs": collected_data,
            "telnet_allowed": telnet_allowed,
            "login_method": login_method, 
            "exec_timeout": exec_timeout,
            "risk_level": risk_level
        }
        
        error = ""
        print(f"  Completed AUX port security analysis for {hostname}.")

    except Exception as e:
        status = "FAILURE"
        summary = f"Error during configuration collection from {hostname}."
        details = {"exception_type": str(type(e).__name__)}
        error = str(e)
        print(f"  Error in Phase 3 for {hostname}: {error}")
    finally:
        # IMPORTANT: Close the connection after Phase 3 is done with it.
        if net_connect:
            try:
                net_connect.disconnect()
                print(f"  Disconnected SSH session from {hostname} after Phase 3.")
            except Exception as e_disc:
                print(f"  Error disconnecting from {hostname} after Phase 3: {e_disc}")

    log_phase_result(audit_run_id, hostname, ip_address, 3, phase_name, status, summary, details, error, start_time)
    return {"status": status, "details": details, "error": error, "connection": net_connect}

# --- Phase 4: Risk Assessment ---
def execute_phase4_risk_assessment(audit_run_id, router_config, phase3_result):
    """Assesses AUX port telnet security risks based on findings from the configuration audit."""
    hostname = router_config.get('hostname')
    ip_address = router_config.get('ip')
    phase_name = "Risk Assessment"
    print(f"Starting Phase 4: {phase_name} for {hostname} ({ip_address})")
    start_time = datetime.datetime.now()
    risks_found = []

    if phase3_result.get('status') not in ['SUCCESS', 'WARNING', 'INFO']:
        status = "SKIPPED"
        summary = "Risk assessment skipped due to config audit failure or being skipped."
        details = None
        error = f"Skipped due to issues in Phase 3: {phase3_result.get('error')}"
        log_phase_result(audit_run_id, hostname, ip_address, 4, phase_name, status, summary, details, error, start_time)
        return {"status": status, "details": details, "error": error}

    # Get AUX port security data from Phase 3
    aux_data = phase3_result.get('details', {})
    if not aux_data or 'telnet_allowed' not in aux_data:
        status = "FAILURE"
        summary = "No AUX port security data available from Phase 3 to assess risks."
        details = None
        error = "Missing AUX port security data from configuration audit phase."
        log_phase_result(audit_run_id, hostname, ip_address, 4, phase_name, status, summary, details, error, start_time)
        return {"status": status, "details": details, "error": error}
    
    # Extract AUX port security settings
    telnet_allowed = aux_data.get('telnet_allowed', 'UNKNOWN')
    login_method = aux_data.get('login_method', 'unknown')
    exec_timeout = aux_data.get('exec_timeout', 'default')
    risk_level = aux_data.get('risk_level', 'UNKNOWN')
    
    # --- Perform Risk Checks based on telnet security issues ---
    # Risk 1: Telnet allowed on AUX port (major security vulnerability)
    if telnet_allowed == "YES":
        risks_found.append({
            "risk_id": "RA001",
            "severity": "HIGH",
            "description": "AUX port allows telnet connections, which are unencrypted and insecure."
        })

    # Risk 2: Weak or no authentication on AUX port
    if login_method in ["none", "unknown"]:
        risks_found.append({
            "risk_id": "RA002",
            "severity": "CRITICAL",
            "description": "AUX port has no authentication configured, allowing unauthenticated access."
        })
    elif login_method == "line_password":
        risks_found.append({
            "risk_id": "RA003",
            "severity": "HIGH",
            "description": "AUX port uses simple line password authentication instead of AAA or local authentication."
        })

    # Risk 3: No exec timeout on AUX port (DoS risk)
    if exec_timeout == "never":
        risks_found.append({
            "risk_id": "RA004",
            "severity": "MEDIUM",
            "description": "AUX port has no exec timeout (set to 0 0), which can lead to DoS if sessions are left open."
        })
        
    # Generate specific recommendations based on findings
    recommendations = []
    if telnet_allowed == "YES":
        recommendations.append("Configure 'transport input ssh' or 'transport input none' on AUX port to disable telnet.")
    if login_method in ["none", "unknown"]:
        recommendations.append("Configure 'login local' or 'login authentication default' on AUX port for proper authentication.")
    if login_method == "line_password":
        recommendations.append("Replace line password with AAA or local authentication for stronger security.")
    if exec_timeout == "never":
        recommendations.append("Set a reasonable exec-timeout (e.g., 'exec-timeout 10 0' for 10 minutes) on AUX port.")
    if telnet_allowed == "NO" and login_method in ["local", "aaa"] and exec_timeout != "never":
        recommendations.append("Current AUX port configuration follows security best practices.")

    # Determine overall risk level (simplified)
    if any(r['severity'] == "HIGH" for r in risks_found):
        overall_risk_level = "HIGH"
    elif any(r['severity'] == "MEDIUM" for r in risks_found):
        overall_risk_level = "MEDIUM"

    status = "SUCCESS"
    summary = f"Risk assessment completed. Found {len(risks_found)} potential risk(s). Overall risk: {overall_risk_level}."
    details = {"risks": risks_found, "overall_risk": overall_risk_level, "config_source_count": len(collected_configs)}
    error = ""

    log_phase_result(audit_run_id, hostname, ip_address, 4, phase_name, status, summary, details, error, start_time)
    return {"status": status, "details": details, "error": error}

# --- Phase 5: Reporting and Recommendations ---
def execute_phase5_reporting(audit_run_id, router_config, phase1_res, phase2_res, phase3_res, phase4_res):
    """Generates a final AUX port telnet security report and recommendations."""
    hostname = router_config.get('hostname')
    ip_address = router_config.get('ip')
    phase_name = "Reporting and Recommendations"
    print(f"Starting Phase 5: {phase_name} for {hostname} ({ip_address})")
    start_time = datetime.datetime.now()
    
    # Aggregate results from all phases
    all_phase_results = {
        "phase1": phase1_res,
        "phase2": phase2_res,
        "phase3": phase3_res,
        "phase4": phase4_res
    }
    
    # Default values
    status = "SUCCESS"  # Even if other phases failed, reporting itself can succeed
    error = ""
    
    # Get AUX port security data from Phase 4
    aux_security_data = phase4_res.get('details', {}) if phase4_res.get('status') != "SKIPPED" else {}
    
    # Extract security settings
    telnet_allowed = aux_security_data.get('telnet_allowed', 'UNKNOWN')
    login_method = aux_security_data.get('login_method', 'unknown')
    exec_timeout = aux_security_data.get('exec_timeout', 'default')
    risk_level = aux_security_data.get('risk_level', 'UNKNOWN')
    risks = aux_security_data.get('risks', [])
    recommendations = aux_security_data.get('recommendations', [])
    
    # Check for authentication failure
    auth_error = None
    if phase2_res.get('status') != 'SUCCESS':
        auth_error = phase2_res.get('error', 'Unknown authentication error')
        print(f"  [DEBUG] Authentication failed for {hostname}: {auth_error}")
        # Add specific recommendations for authentication issues
        if 'timeout' in auth_error.lower():
            recommendations.append("Check network connectivity to the jump server and target device")
            recommendations.append("Verify the IP address and port settings are correct")
            recommendations.append("Ensure firewall rules allow SSH traffic to and from the jump server")
        elif 'authentication' in auth_error.lower():
            recommendations.append("Verify the username and password for the target device")
            recommendations.append("Ensure the device type is correctly specified")
            recommendations.append("Check if the device supports the SSH version being used")
        else:
            recommendations.append("Troubleshoot SSH connection to the jump server")
            recommendations.append("Verify all connection parameters are correct")
    
    # If Phase 4 was skipped, generate basic recommendations
    if not recommendations:
        recommendations = [
            "Configure 'transport input ssh' or 'transport input none' on AUX port to disable telnet.",
            "Use AAA or local authentication on all lines including AUX port.",
            "Set reasonable exec-timeout values on all lines including AUX port.",
            "Consider disabling the AUX port completely if not in use with 'no line aux 0'."
        ]
    
    # Generate a detailed report
    issues_count = len(risks)
    
    # Format the report with ASCII borders and clear sections
    report_content = f"""
╔════════════════════════════════════════════════════════════════╗
║                  AUX PORT TELNET SECURITY AUDIT                ║
╚════════════════════════════════════════════════════════════════╝

  Device: {hostname} ({ip_address})
  Audit Run ID: {audit_run_id}
  Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

╔════════════════════════════════════════════════════════════════╗
║                      SECURITY FINDINGS                         ║
╚════════════════════════════════════════════════════════════════╝

  • AUX Port Telnet Access: {telnet_allowed}
  • Authentication Method: {login_method}
  • Exec Timeout Setting: {exec_timeout}
  • Overall Risk Level: {risk_level}
  • Issues Found: {issues_count}

╔════════════════════════════════════════════════════════════════╗
║                       SECURITY RISKS                           ║
╚════════════════════════════════════════════════════════════════╝
"""

    if risks:
        for i, risk in enumerate(risks, 1):
            report_content += f"\n  {i}. [{risk.get('severity')}] {risk.get('description')}"
    else:
        report_content += "\n  No specific risks identified."

    report_content += f"""

╔════════════════════════════════════════════════════════════════╗
║                     RECOMMENDATIONS                           ║
╚════════════════════════════════════════════════════════════════╝
"""

    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            report_content += f"\n  {i}. {rec}"
    else:
        report_content += "\n  No specific recommendations available."

    if risk_level == "CRITICAL" or risk_level == "HIGH":
        summary = f"CRITICAL SECURITY RISK: The AUX port on {hostname} has severe security vulnerabilities that require immediate attention."
    elif risk_level == "MEDIUM":
        summary = f"MODERATE SECURITY RISK: The AUX port on {hostname} has security configuration issues that should be addressed."
    elif risk_level == "LOW":
        summary = f"LOW SECURITY RISK: The AUX port on {hostname} follows security best practices with minimal issues."
    else:
        if auth_error:
            summary = f"ASSESSMENT INCOMPLETE: Unable to assess the AUX port security on {hostname} due to authentication failure.\nError: {auth_error}"
        else:
            summary = f"UNKNOWN RISK LEVEL: Unable to fully assess the AUX port security on {hostname}."

    report_content += f"""

╔════════════════════════════════════════════════════════════════╗
║                          SUMMARY                              ║
╚════════════════════════════════════════════════════════════════╝

  {summary}

╔════════════════════════════════════════════════════════════════╗
║                     END OF REPORT                             ║
╚════════════════════════════════════════════════════════════════╝
"""

    details = {
        "telnet_allowed": telnet_allowed,
        "login_method": login_method,
        "exec_timeout": exec_timeout,
        "risk_level": risk_level,
        "risks": risks,
        "recommendations": recommendations,
        "report": report_content,
        "summary": summary
    }

    log_phase_result(audit_run_id, hostname, ip_address, 5, phase_name, status, summary, details, error, start_time)
    return {"status": status, "details": details, "error": error}


# --- Web Interface Routes ---
@app.route('/')
def index():
    """Main page of the Phased Audit Tool web interface."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Phased Audit Tool</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1, h2, h3 { color: #2c3e50; }
            .container { max-width: 1200px; margin: 0 auto; }
            .button-container { margin: 20px 0; }
            .btn {
                display: inline-block; 
                padding: 10px 15px; 
                background-color: #3498db; 
                color: white; 
                text-decoration: none; 
                border-radius: 4px;
                margin-right: 10px;
                margin-bottom: 10px;
            }
            .about-section {
                margin-top: 40px;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f9f9f9;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Phased Audit Tool</h1>
            <div class="button-container">
                <a href="/run-audit" class="btn">Run Audit</a>
                <a href="/view-results" class="btn">View Past Results</a>
                <a href="/edit-jump-server" class="btn">Edit Jump Server Settings</a>
                <a href="/edit-inventory" class="btn">Edit Router Inventory</a>
                <a href="/router-credentials" class="btn">Set Router Credentials</a>
            </div>
            
            <div class="about-section">
                <h2>About This Tool</h2>
                <p>The Phased Audit Tool performs a comprehensive 5-phase security audit on network devices:</p>
                <ol>
                    <li><strong>Connectivity Verification</strong>: Checks basic network connectivity to devices.</li>
                    <li><strong>Authentication Testing</strong>: Verifies authentication credentials.</li>
                    <li><strong>Configuration Audit</strong>: Examines device configurations against security best practices.</li>
                    <li><strong>Risk Assessment</strong>: Evaluates security risks based on the findings.</li>
                    <li><strong>Reporting</strong>: Generates detailed reports and recommendations.</li>
                </ol>
                <p>The tool uses a jump server to connect to the target routers and audits multiple devices in sequence.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/run-audit')
def run_audit():
    """Start the audit process and show a page that will display progress."""
    # Start the audit process in a background thread
    import threading
    audit_run_id = str(uuid.uuid4())
    
    # Store progress in a global variable that can be accessed by the progress endpoint
    global audit_progress
    audit_progress = {
        'status': 'initializing',
        'run_id': audit_run_id,
        'routers': {},
        'completed': False,
        'results': {}
    }
    
    def run_audit_task():
        global audit_progress
        initialize_database()
        
        # Load router inventory
        inventory_file = os.path.join('inventories', 'router.csv')
        routers_to_audit = load_inventory_from_csv(inventory_file)
        
        if not routers_to_audit:
            audit_progress['status'] = 'error'
            audit_progress['message'] = 'No routers found in inventory!'
            return
        
        audit_progress['status'] = 'running'
        audit_progress['message'] = f'Starting audit run {audit_run_id}'
        overall_results = {}
        
        # Log the jump server configuration being used
        print(f"Using jump server: {jump_host_creds['ip']} with username {jump_host_creds['username']}")
        audit_progress['message'] = f"Starting audit via jump server {jump_host_creds['ip']}"
        
        # Test connection to jump server first
        try:
            print("Testing connection to jump server...")
            test_conn = connect_to_jump_server(jump_host_creds)
            if isinstance(test_conn, tuple) and test_conn[0] is None:
                error_msg = f"Cannot connect to jump server: {test_conn[1]}"
                audit_progress['status'] = 'error'
                audit_progress['message'] = error_msg
                print(error_msg)
                return
            
            print("Successfully connected to jump server!")
            test_conn.disconnect()
        except Exception as e:
            error_msg = f"Jump server connection test failed: {str(e)}"
            audit_progress['status'] = 'error'
            audit_progress['message'] = error_msg
            print(error_msg)
            return
        
        for router_config in routers_to_audit:
            hostname = router_config.get('hostname')
            ip_address = router_config.get('ip')
            router_results = {}
            
            # Initialize router progress
            if hostname not in audit_progress['routers']:
                audit_progress['routers'][hostname] = {
                    'ip': ip_address,
                    'phases': {
                        '1': {'status': 'pending', 'name': 'Connectivity', 'message': 'Pending'},
                        '2': {'status': 'pending', 'name': 'Authentication', 'message': 'Pending'},
                        '3': {'status': 'pending', 'name': 'Configuration Audit', 'message': 'Pending'},
                        '4': {'status': 'pending', 'name': 'Risk Assessment', 'message': 'Pending'},
                        '5': {'status': 'pending', 'name': 'Reporting', 'message': 'Pending'}
                    }
                }
            
            # Phase 1: Connectivity
            audit_progress['routers'][hostname]['phases']['1'] = {
                'status': 'running', 
                'name': 'Connectivity',
                'message': f'Checking connectivity to {ip_address} via jump server...'
            }
            phase1_res = execute_phase1_connectivity(audit_run_id, router_config, jump_host_creds)
            router_results['phase1'] = phase1_res
            audit_progress['routers'][hostname]['phases']['1'] = {
                'status': phase1_res.get('status'),
                'name': 'Connectivity',
                'message': f'Status: {phase1_res.get("status")}'
            }
            
            # Phase 2: Authentication
            phase2_status = 'running' if phase1_res.get('status') == 'SUCCESS' else 'skipped'
            audit_progress['routers'][hostname]['phases']['2'] = {
                'status': phase2_status,
                'name': 'Authentication',
                'message': 'Attempting to authenticate via jump server...' if phase2_status == 'running' else 'Skipped due to connectivity failure'
            }
            try:
                print(f"  [DEBUG] Setting maximum timeout for authentication phase: 60 seconds")
                auth_start_time = datetime.datetime.now()
                
                # Set a timeout for the authentication phase
                import threading
                import _thread
                auth_timeout_seconds = 60  # 60 second timeout for authentication phase
                
                # Store the result in a list so it can be accessed from the timeout function
                result_container = [None]
                auth_exception = [None]
                auth_completed = [False]
                
                def auth_worker():
                    try:
                        print(f"  [DEBUG] Authentication worker thread started for {hostname} ({ip_address})")
                        print(f"  [DEBUG] Jump server details: {jump_host_creds['ip']}:{jump_host_creds.get('port', 22)} ({jump_host_creds['device_type']})")
                        print(f"  [DEBUG] Router details: {ip_address}:{router_config.get('port', 22)} ({router_config.get('device_type', 'cisco_ios')})")
                        
                        # Add debug messages in the execute_phase2_authentication function
                        result = execute_phase2_authentication(audit_run_id, router_config, phase1_res, jump_host_creds)
                        
                        print(f"  [DEBUG] Authentication function returned status: {result.get('status')}")
                        if result.get('status') != 'SUCCESS':
                            print(f"  [DEBUG] Authentication error: {result.get('error')}")
                        
                        # Store the result and mark as completed
                        result_container[0] = result
                        auth_completed[0] = True
                    except Exception as e:
                        auth_exception[0] = e
                        tb = traceback.format_exc()
                        print(f"  [ERROR] Exception in authentication worker thread: {str(e)}")
                        print(f"  [DEBUG] Exception type: {type(e).__name__}")
                        print(f"  [DEBUG] Traceback:\n{tb}")
                
                # Start authentication in a separate thread
                auth_thread = threading.Thread(target=auth_worker)
                auth_thread.daemon = True
                auth_thread.start()
                
                # Wait for authentication to complete or timeout
                for _ in range(auth_timeout_seconds):
                    if auth_completed[0]:
                        break
                    time.sleep(1)
                    elapsed = (datetime.datetime.now() - auth_start_time).total_seconds()
                    print(f"  [DEBUG] Authentication in progress... {elapsed:.1f}s elapsed")
                    # Update progress message with elapsed time
                    audit_progress['routers'][hostname]['phases']['2']['message'] = f"Authentication in progress ({elapsed:.1f}s elapsed)..."
                
                # Check if authentication completed
                if auth_completed[0]:
                    auth_time = (datetime.datetime.now() - auth_start_time).total_seconds()
                    print(f"  [DEBUG] Authentication completed in {auth_time:.1f}s")
                    phase2_res = result_container[0]
                    
                    # If authentication failed, add more detailed debugging info
                    if phase2_res.get('status') != 'SUCCESS':
                        print(f"  [DEBUG] Authentication failed with status: {phase2_res.get('status')}")
                        print(f"  [DEBUG] Error details: {phase2_res.get('error')}")
                        print(f"  [DEBUG] Device: {ip_address}, Device type: {router_config.get('device_type', 'cisco_ios')}")
                elif auth_exception[0]:
                    # Authentication encountered an exception
                    e = auth_exception[0]
                    tb = traceback.format_exc()
                    print(f"  [ERROR] Authentication exception: {str(e)}")
                    print(f"  [DEBUG] Exception type: {type(e).__name__}")
                    print(f"  [DEBUG] Traceback:\n{tb}")
                    
                    phase2_res = {
                        "status": "FAILURE",
                        "error": f"Authentication error: {str(e)}",
                        "details": {
                            "exception_type": type(e).__name__,
                            "device": ip_address,
                            "jump_server": jump_host_creds.get('ip'),
                            "traceback": tb
                        },
                        "connection": None
                    }
                else:
                    # Authentication timed out
                    print(f"  [ERROR] Authentication timed out after {auth_timeout_seconds}s")
                    print(f"  [DEBUG] Device: {ip_address}, Jump server: {jump_host_creds.get('ip')}")
                    print(f"  [DEBUG] This could indicate network connectivity issues, incorrect credentials, or device unreachability")
                    
                    phase2_res = {
                        "status": "FAILURE",
                        "error": f"Authentication timed out after {auth_timeout_seconds} seconds",
                        "details": {
                            "timeout": auth_timeout_seconds,
                            "device": ip_address,
                            "jump_server": jump_host_creds.get('ip')
                        },
                        "connection": None
                    }
                    
                    # Log timeout to database
                    log_phase_result(audit_run_id, hostname, ip_address, 2, "Authentication Testing", 
                                     "FAILURE", "Authentication timed out", phase2_res["details"], 
                                     phase2_res["error"], auth_start_time)
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                print(f"  [ERROR] Exception during authentication phase setup: {str(e)}")
                print(f"  [DEBUG] Traceback:\n{tb}")
                phase2_res = {
                    "status": "FAILURE",
                    "error": f"Authentication error: {str(e)}",
                    "details": {"exception": str(e), "traceback": tb},
                    "connection": None
                }
                
            router_results['phase2'] = phase2_res
            audit_progress['routers'][hostname]['phases']['2'] = {
                'status': phase2_res.get('status'),
                'name': 'Authentication',
                'message': f'Status: {phase2_res.get("status")}'
            }
            
            # Phase 3: Configuration Audit
            phase3_status = 'running' if phase2_res.get('status') == 'SUCCESS' else 'skipped'
            audit_progress['routers'][hostname]['phases']['3'] = {
                'status': phase3_status,
                'name': 'Configuration Audit',
                'message': 'Collecting configuration via jump server...' if phase3_status == 'running' else 'Skipped due to authentication failure'
            }
            phase3_res = execute_phase3_config_audit(audit_run_id, router_config, phase2_res)
            router_results['phase3'] = phase3_res
            audit_progress['routers'][hostname]['phases']['3'] = {
                'status': phase3_res.get('status'),
                'name': 'Configuration Audit',
                'message': f'Status: {phase3_res.get("status")}'
            }
            
            # Phase 4: Risk Assessment
            phase4_status = 'running' if phase3_res.get('status') == 'SUCCESS' else 'skipped'
            audit_progress['routers'][hostname]['phases']['4'] = {
                'status': phase4_status,
                'name': 'Risk Assessment',
                'message': 'Analyzing risks...' if phase4_status == 'running' else 'Skipped due to config audit failure'
            }
            phase4_res = execute_phase4_risk_assessment(audit_run_id, router_config, phase3_res)
            router_results['phase4'] = phase4_res
            audit_progress['routers'][hostname]['phases']['4'] = {
                'status': phase4_res.get('status'),
                'name': 'Risk Assessment',
                'message': f'Status: {phase4_res.get("status")}'
            }
            
            # Phase 5: Reporting
            audit_progress['routers'][hostname]['phases']['5'] = {
                'status': 'running',
                'name': 'Reporting',
                'message': 'Generating report...'
            }
            phase5_res = execute_phase5_reporting(audit_run_id, router_config, phase1_res, phase2_res, phase3_res, phase4_res)
            router_results['phase5'] = phase5_res
            audit_progress['routers'][hostname]['phases']['5'] = {
                'status': phase5_res.get('status'),
                'name': 'Reporting',
                'message': f'Status: {phase5_res.get("status")}'
            }
            
            overall_results[hostname] = router_results
        
        # Mark audit as completed
        audit_progress['status'] = 'completed'
        audit_progress['results'] = overall_results
        audit_progress['completed'] = True
    
    # Start the audit in a background thread
    audit_thread = threading.Thread(target=run_audit_task)
    audit_thread.daemon = True
    audit_thread.start()
    
    # Return a page that will poll for progress updates
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Audit Progress</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1, h2, h3 { color: #2c3e50; }
            .container { max-width: 1200px; margin: 0 auto; }
            .progress-container { 
                margin-top: 20px; 
                border: 1px solid #ddd; 
                padding: 15px;
                border-radius: 4px;
            }
            .router-progress {
                margin-bottom: 20px;
                padding: 10px;
                border: 1px solid #eee;
                border-radius: 4px;
            }
            .phase-progress {
                margin: 5px 0;
                padding: 5px;
                border-left: 3px solid #3498db;
                padding-left: 10px;
            }
            .success { color: green; }
            .failure { color: red; }
            .skipped { color: orange; }
            .running { color: blue; }
            .pending { color: gray; }
            .error { color: red; font-weight: bold; }
            .back-btn {
                display: inline-block; 
                padding: 10px 15px; 
                background-color: #3498db; 
                color: white; 
                text-decoration: none; 
                border-radius: 4px;
                margin: 10px 0;
            }
            .hidden { display: none; }
            #final-results {
                margin-top: 20px;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 4px;
                display: none;
            }
        </style>
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                var progressContainer = document.getElementById('progress-container');
                var finalResults = document.getElementById('final-results');
                var statusMessage = document.getElementById('status-message');
                var routerProgress = {};
                var pollInterval;
                
                // Start polling for progress updates
                pollInterval = setInterval(checkProgress, 1000);
                
                function checkProgress() {
                    fetch('/audit-progress')
                        .then(response => response.json())
                        .then(data => {
                            updateProgressUI(data);
                            
                            // If audit is completed, stop polling and show final results
                            if (data.completed) {
                                clearInterval(pollInterval);
                                statusMessage.textContent = 'Audit completed!';
                                showFinalResults();
                            }
                        })
                        .catch(error => {
                            console.error('Error fetching progress:', error);
                        });
                }
                
                function updateProgressUI(data) {
                    statusMessage.textContent = data.message || 'Running audit...';
                    
                    // Update progress for each router
                    for (var hostname in data.routers) {
                        var router = data.routers[hostname];
                        var routerId = hostname.replace(/[^a-zA-Z0-9]/g, '_');
                        
                        // Create router progress container if it doesn't exist
                        if (!routerProgress[routerId]) {
                            routerProgress[routerId] = document.createElement('div');
                            routerProgress[routerId].className = 'router-progress';
                            routerProgress[routerId].innerHTML = '<h3>Router: ' + hostname + ' (' + router.ip + ')</h3>' +
                                '<div id="phase1_' + routerId + '" class="phase-progress pending">Phase 1: Connectivity - Pending</div>' +
                                '<div id="phase2_' + routerId + '" class="phase-progress pending">Phase 2: Authentication - Pending</div>' +
                                '<div id="phase3_' + routerId + '" class="phase-progress pending">Phase 3: Configuration Audit - Pending</div>' +
                                '<div id="phase4_' + routerId + '" class="phase-progress pending">Phase 4: Risk Assessment - Pending</div>' +
                                '<div id="phase5_' + routerId + '" class="phase-progress pending">Phase 5: Reporting - Pending</div>';
                            progressContainer.appendChild(routerProgress[routerId]);
                        }
                        
                        // Update phase status for this router
                        for (var phaseNum in router.phases) {
                            var phase = router.phases[phaseNum];
                            var phaseElement = document.getElementById('phase' + phaseNum + '_' + routerId);
                            if (phaseElement) {
                                phaseElement.className = 'phase-progress ' + phase.status.toLowerCase();
                                phaseElement.innerHTML = 'Phase ' + phaseNum + ': ' + phase.name + ' - ' + phase.status;
                                if (phase.message) {
                                    phaseElement.innerHTML += '<br><span class="message">' + phase.message + '</span>';
                                }
                            }
                        }
                    }
                }
                
                function showFinalResults() {
                    fetch('/audit-results')
                        .then(response => response.text())
                        .then(html => {
                            finalResults.style.display = 'block';
                            finalResults.innerHTML = '<h2>Final Results</h2>' + html;
                        })
                        .catch(error => {
                            console.error('Error fetching results:', error);
                            finalResults.innerHTML = '<h2>Error</h2><p>Failed to load final results.</p>';
                        });
                }
            });
        </script>
    </head>
    <body>
        <div class="container">
            <h1>Audit Progress</h1>
            <a href="/" class="back-btn">Back to Home</a>
            <p id="status-message">Starting audit process...</p>
            <div id="progress-container" class="progress-container">
                <p>Initializing audit...</p>
            </div>
            <div id="final-results"></div>
        </div>
    </body>
    </html>
    """
    return html

# Global variables to store audit progress and settings
audit_progress = {
    'status': 'idle',
    'run_id': '',
    'routers': {},
    'completed': False,
    'results': {},
    'message': 'No audit running'
}

# Default router credentials (used for all routers if not specified in inventory)
default_router_creds = {
    'username': 'cisco',
    'password': 'cisco',
    'secret': 'cisco',
    'device_type': 'cisco_ios'
}

# Jump server credentials
jump_host_creds = {
    'hostname': 'JumpServer',
    'ip': '172.16.39.128',  # Default to example from manual command collection
    'username': 'admin',
    'password': 'admin',
    'device_type': 'linux',
    'port': 22
}

# Default router credentials (used for all routers if not specified in inventory)
default_router_creds = {
    'username': 'cisco',
    'password': 'cisco',
    'secret': 'cisco',
    'device_type': 'cisco_ios'
}

@app.route('/router-credentials', methods=['GET', 'POST'])
def router_credentials():
    """Edit default router credentials that will be used for all routers unless specified in inventory."""
    global default_router_creds
    
    if request.method == 'POST':
        # Update router credentials
        default_router_creds['username'] = request.form.get('username')
        default_router_creds['device_type'] = request.form.get('device_type')
        
        # Only update password if a new one was provided
        new_password = request.form.get('password')
        if new_password:
            default_router_creds['password'] = new_password
            
        # Only update enable secret if a new one was provided
        new_secret = request.form.get('secret')
        if new_secret:
            default_router_creds['secret'] = new_secret
            
        return redirect(url_for('index'))
    
    # Default colors
    text_color = '#2c3e50'
    bg_color = '#ecf0f1'
    button_color = '#3498db'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Router Credentials - Phased Audit Tool</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: {bg_color}; margin: 0; padding: 20px; }}
            h1, h2 {{ color: {text_color}; }}
            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; background-color: white; border-radius: 5px; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); }}
            .btn {{ display: inline-block; padding: 10px 15px; background-color: {button_color}; color: white; text-decoration: none; border-radius: 3px; margin-right: 10px; }}
            .btn:hover {{ background-color: #2980b9; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; color: {text_color}; }}
            input[type="text"], input[type="password"], input[type="number"] {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
            .home-link {{ color: {button_color}; text-decoration: none; }}
            .home-link:hover {{ text-decoration: underline; }}
            .alert {{ padding: 10px; background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; border-radius: 3px; margin-bottom: 15px; }}
            .success {{ background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .password-note {{ font-size: 12px; color: #666; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Router Credentials</h1>
                <a href="/" class="home-link">Back to Home</a>
            </div>
            
            <p>Configure default credentials that will be used for all routers during authentication unless specified in the router inventory.</p>
            
            <form method="POST">
                <div class="form-group">
                    <label for="username">Username:</label>
                    <input type="text" id="username" name="username" value="{default_router_creds['username']}" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" placeholder="Enter new password (leave empty to keep current)">
                    <p class="password-note">Current password: {default_router_creds['password']}</p>
                </div>
                
                <div class="form-group">
                    <label for="secret">Enable Secret:</label>
                    <input type="password" id="secret" name="secret" placeholder="Enter new enable secret (leave empty to keep current)">
                    <p class="password-note">Current secret: {default_router_creds['secret']}</p>
                </div>
                
                <div class="form-group">
                    <label for="device_type">Device Type:</label>
                    <input type="text" id="device_type" name="device_type" value="{default_router_creds['device_type']}" required>
                </div>
                
                <button type="submit" class="btn">Save Router Credentials</button>
            </form>
        </div>
    </body>
    </html>
    """
    
    return html

@app.route('/edit-jump-server', methods=['GET', 'POST'])
def edit_jump_server():
    """Edit jump server settings."""
    global jump_host_creds
    
    if request.method == 'POST':
        # Update jump server settings from form
        jump_host_creds['hostname'] = request.form.get('hostname')
        jump_host_creds['ip'] = request.form.get('ip')
        jump_host_creds['username'] = request.form.get('username')
        
        # Only update password if provided
        new_password = request.form.get('password')
        if new_password and new_password.strip():
            jump_host_creds['password'] = new_password
            
        jump_host_creds['device_type'] = request.form.get('device_type')
        jump_host_creds['port'] = int(request.form.get('port', 22))
        
        return redirect('/')
    
    # GET request - show form with current settings
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Edit Jump Server Settings</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #2c3e50; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            input[type="text"], input[type="password"], input[type="number"] {{ 
                width: 100%; 
                padding: 8px; 
                border: 1px solid #ddd; 
                border-radius: 4px;
            }}
            .btn {{
                display: inline-block; 
                padding: 10px 15px; 
                background-color: #3498db; 
                color: white; 
                text-decoration: none; 
                border-radius: 4px;
                margin-right: 10px;
                border: none;
                cursor: pointer;
            }}
            .btn-cancel {{
                background-color: #95a5a6;
            }}
            .back-btn {{
                display: inline-block; 
                padding: 10px 15px; 
                background-color: #3498db; 
                color: white; 
                text-decoration: none; 
                border-radius: 4px;
                margin: 10px 0;
            }}
            .help-text {{
                margin-top: 20px;
                padding: 15px;
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            .example-output {{
                background-color: #f5f5f5; 
                padding: 10px; 
                border-radius: 4px; 
                overflow-x: auto;
                font-family: monospace;
                white-space: pre;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Edit Jump Server Settings</h1>
            <a href="/" class="back-btn">Back to Home</a>
            
            <form method="POST">
                <div class="form-group">
                    <label for="hostname">Hostname:</label>
                    <input type="text" id="hostname" name="hostname" value="{jump_host_creds['hostname']}" required>
                </div>
                
                <div class="form-group">
                    <label for="ip">IP Address:</label>
                    <input type="text" id="ip" name="ip" value="{jump_host_creds['ip']}" required>
                </div>
                
                <div class="form-group">
                    <label for="username">Username:</label>
                    <input type="text" id="username" name="username" value="{jump_host_creds['username']}" required>
                </div>
                
                <div class="form-group">
                    <label for="password">Password (leave empty to keep current):</label>
                    <input type="password" id="password" name="password" placeholder="Enter new password">
                </div>
                
                <div class="form-group">
                    <label for="device_type">Device Type:</label>
                    <input type="text" id="device_type" name="device_type" value="{jump_host_creds['device_type']}" required>
                </div>
                
                <div class="form-group">
                    <label for="port">SSH Port:</label>
                    <input type="number" id="port" name="port" value="{jump_host_creds['port']}" required>
                </div>
                
                <button type="submit" class="btn">Save Settings</button>
                <a href="/" class="btn btn-cancel">Cancel</a>
            </form>
            
            <div style="margin-top: 30px;">
                <h2>Using Jump Server</h2>
                <p>The jump server is used as an intermediary to connect to routers. Based on the manual command collection, the jump server (172.16.39.128) is able to ping and SSH to the target routers.</p>
                <p>Example from manual collection:</p>
                <pre style="background-color: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto;">
root@jump-host:~# ifconfig | grep 172.16.39
        inet 172.16.39.128  netmask 255.255.255.0  broadcast 172.16.39.255

root@jump-host:~# ping 172.16.39.100
PING 172.16.39.100 (172.16.39.100) 56(84) bytes of data.
64 bytes from 172.16.39.100: icmp_seq=1 ttl=255 time=8.67 ms
64 bytes from 172.16.39.100: icmp_seq=2 ttl=255 time=39.2 ms
64 bytes from 172.16.39.100: icmp_seq=3 ttl=255 time=9.93 ms
                </pre>
            </div>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/edit-inventory', methods=['GET', 'POST'])
def edit_inventory():
    """View and edit router inventory CSV file."""
    inventory_file = 'router.csv'
    inventory_path = os.path.join('inventories', inventory_file)
    # Define color variables to avoid NameError
    primary_color = "#3498db"
    text_color = "#2c3e50"
    light_bg_color = "#f9f9f9"
    code_bg_color = "#f5f5f5"
    cancel_color = "#95a5a6"
    
    if request.method == 'POST':
        # Update the CSV file with the data from the form
        csv_content = request.form.get('csv_content')
        
        # Ensure the inventories directory exists
        os.makedirs('inventories', exist_ok=True)
        
        # Write the updated content to the file
        with open(inventory_path, 'w') as f:
            f.write(csv_content)
            
        return redirect('/')
    
    # Read the current CSV file
    csv_content = ""
    try:
        with open(inventory_path, 'r') as f:
            csv_content = f.read()
    except FileNotFoundError:
        # Create a sample CSV if it doesn't exist
        os.makedirs('inventories', exist_ok=True)
        sample_csv = """hostname,ip,device_type,username,password,secret,ios_version,notes
R0,172.16.39.100,cisco_ios,cisco,cisco,cisco,15.1,Default entry
R1,172.16.39.101,cisco_ios,cisco,cisco,cisco,15.1,Default entry
R2,172.16.39.102,cisco_ios,cisco,cisco,cisco,15.1,Default entry
"""
        with open(inventory_path, 'w') as f:
            f.write(sample_csv)
        csv_content = sample_csv
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Edit Router Inventory</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2 {{ color: {text_color}; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            textarea {{ 
                width: 100%; 
                height: 300px; 
                padding: 8px; 
                border: 1px solid #ddd; 
                border-radius: 4px;
                font-family: monospace;
            }}
            .btn {{
                display: inline-block; 
                padding: 10px 15px; 
                background-color: {primary_color}; 
                color: white; 
                text-decoration: none; 
                border-radius: 4px;
                margin-right: 10px;
                border: none;
                cursor: pointer;
            }}
            .btn-cancel {{
                background-color: {cancel_color};
            }}
            .back-btn {{
                display: inline-block; 
                padding: 10px 15px; 
                background-color: {primary_color}; 
                color: white; 
                text-decoration: none; 
                border-radius: 4px;
                margin: 10px 0;
            }}
            .help-text {{
                margin-top: 20px;
                padding: 15px;
                background-color: {light_bg_color};
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            .example-output {{
                background-color: {code_bg_color}; 
                padding: 10px; 
                border-radius: 4px; 
                overflow-x: auto;
                font-family: monospace;
                white-space: pre;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Edit Router Inventory</h1>
            <a href="/" class="back-btn">Back to Home</a>
            
            <form method="POST">
                <div class="form-group">
                    <label for="csv_content">Router Inventory CSV Content:</label>
                    <textarea id="csv_content" name="csv_content" required>{csv_content}</textarea>
                </div>
                
                <button type="submit" class="btn">Save Inventory</button>
                <a href="/" class="btn btn-cancel">Cancel</a>
            </form>
            
            <div class="help-text">
                <h2>Router Inventory Format</h2>
                <p>The CSV file should have the following columns:</p>
                <ul>
                    <li><strong>hostname</strong>: Router hostname (e.g., R0, R1)</li>
                    <li><strong>ip</strong>: IP address of the router</li>
                    <li><strong>device_type</strong>: Device type (usually cisco_ios)</li>
                    <li><strong>username</strong>: Username for authentication</li>
                    <li><strong>password</strong>: Password for authentication</li>
                    <li><strong>secret</strong>: Enable secret password</li>
                    <li><strong>ios_version</strong>: IOS version (optional)</li>
                    <li><strong>notes</strong>: Additional notes (optional)</li>
                </ul>
                
                <h3>Sample Router Output</h3>
                <p>The example below shows sample output from routers in the manual command collection:</p>
                <div class="example-output">R0#show line
   Tty Typ     Tx/Rx    A Modem  Roty AccO AccI   Uses   Noise  Overruns   Int
      0 CTY              -    -      -    -    -      0       2     0/0       -
     97 AUX   9600/9600  -    -      -    -    -      0       0     0/0       -
*    98 VTY              -    -      -    -    -    131       0     0/0       -
     99 VTY              -    -      -    -    -      6       0     0/0       -</div>
            </div>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/audit-progress')
def get_audit_progress():
    """Return the current audit progress as JSON."""
    global audit_progress
    return jsonify(audit_progress)

@app.route('/audit-results')
def get_audit_results():
    """Return the final audit results as HTML."""
    global audit_progress
    if not audit_progress['completed']:
        return "<p>Audit is still in progress...</p>"
    
    html_results = ""
    for router_name, results in audit_progress['results'].items():
        html_results += f"<h2>Results for {router_name}:</h2>"
        for phase, result in results.items():
            status_class = "success" if result.get('status') == "SUCCESS" else "failure" if result.get('status') == "FAILURE" else "skipped"
            summary_text = (result.get('details') or {}).get('summary', 'No summary')
            html_results += f"<div class='phase'>"
            html_results += f"<h3>{phase.capitalize()}</h3>"
            html_results += f"<p class='{status_class}'>Status: {result.get('status')}</p>"
            html_results += f"<p>Summary: {summary_text}</p>"
            if result.get('error'):
                html_results += f"<p class='error'>Error: {result.get('error')}</p>"
            html_results += "</div>"
    
    return html_results

@app.route('/view-results')
def view_results():
    """View past audit results from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get unique audit run IDs
    cursor.execute("SELECT DISTINCT audit_run_id FROM audit_phase_results ORDER BY start_time DESC")
    audit_runs = cursor.fetchall()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Past Audit Results</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1, h2 { color: #2c3e50; }
            .container { max-width: 1200px; margin: 0 auto; }
            .audit-run { 
                margin: 20px 0; 
                padding: 15px; 
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            .phase { margin-left: 20px; }
            .success { color: green; }
            .failure { color: red; }
            .skipped { color: orange; }
            .back-btn {
                display: inline-block; 
                padding: 10px 15px; 
                background-color: #3498db; 
                color: white; 
                text-decoration: none; 
                border-radius: 4px;
                margin: 10px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Past Audit Results</h1>
            <a href="/" class="back-btn">Back to Home</a>
    """
    
    if not audit_runs:
        html += "<p>No audit results found in the database.</p>"
    else:
        for audit_run in audit_runs:
            audit_run_id = audit_run['audit_run_id']
            html += f'<div class="audit-run"><h2>Audit Run: {audit_run_id}</h2>'
            
            # Get results for this audit run
            cursor.execute("""
                SELECT * FROM audit_phase_results 
                WHERE audit_run_id = ? 
                ORDER BY router_hostname, phase_number
            """, (audit_run_id,))
            results = cursor.fetchall()
            
            current_hostname = None
            for result in results:
                if result['router_hostname'] != current_hostname:
                    if current_hostname:
                        html += '</div>'  # Close previous device div
                    current_hostname = result['router_hostname']
                    html += f'<div class="device"><h3>Device: {current_hostname} ({result["router_ip"]})</h3>'
                
                status_class = "success" if result['status'] == "SUCCESS" else "failure" if result['status'] == "FAILURE" else "skipped"
                html += f'<div class="phase"><h4>Phase {result["phase_number"]}: {result["phase_name"]}</h4>'
                html += f'<p class="{status_class}">Status: {result["status"]}</p>'
                html += f'<p>Summary: {result["summary"]}</p>'
                if result['error']:
                    html += f'<p class="failure">Error: {result["error"]}</p>'
                html += '</div>'  # Close phase div
            
            if current_hostname:
                html += '</div>'  # Close last device div
            html += '</div>'  # Close audit run div
    
    html += """
        </div>
    </body>
    </html>
    """
    
    conn.close()
    return html

# --- Inventory Management ---
def load_inventory_from_csv(inventory_file):
    """
    Load router inventory from a CSV file.
    Expected CSV format: hostname,ip,device_type,username,password,secret,ios_version,notes
    Works on both Windows and Linux with relative paths.
    """
    routers = []
    
    try:
        # Handle relative paths in a cross-platform way
        if not os.path.isabs(inventory_file):
            # If it's just a filename without directory, look in inventories/
            if os.path.dirname(inventory_file) == "":
                inventory_path = os.path.join('inventories', inventory_file)
            else:
                inventory_path = inventory_file
        else:
            inventory_path = inventory_file
        
        # Ensure the inventories directory exists
        if not os.path.exists('inventories'):
            os.makedirs('inventories', exist_ok=True)
            print("Created inventories directory")
            
        # Create a default inventory file if it doesn't exist
        if not os.path.exists(inventory_path):
            # Create default inventory if not exists
            with open(inventory_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['hostname', 'ip', 'device_type', 'username', 'password', 'secret', 'ios_version', 'notes'])
                writer.writerow(['R0', '172.16.39.100', 'cisco_ios', 'cisco', 'cisco', 'cisco', '15.1', 'Default entry'])
                writer.writerow(['R1', '172.16.39.101', 'cisco_ios', 'cisco', 'cisco', 'cisco', '15.1', 'Default entry'])
                writer.writerow(['R2', '172.16.39.102', 'cisco_ios', 'cisco', 'cisco', 'cisco', '15.1', 'Default entry'])
            print(f"Created default inventory file: {inventory_path}")
        
        # Read the inventory file
        with open(inventory_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip empty rows
                if not row.get('hostname') or not row.get('ip'):
                    continue
                    
                router = {
                    'hostname': row.get('hostname'),
                    'ip': row.get('ip'),
                    'device_type': row.get('device_type', 'cisco_ios'),
                    'username': row.get('username'),
                    'password': row.get('password'),
                    'secret': row.get('secret', ''),
                    'ios_version': row.get('ios_version', ''),
                    'notes': row.get('notes', ''),
                    'port': int(row.get('port', 22))
                }
                routers.append(router)
        
        print(f"Loaded {len(routers)} routers from {inventory_path}")
    except Exception as e:
        print(f"Error loading inventory from {inventory_file}: {str(e)}")
    
    return routers

# --- Main Audit Orchestrator ---
def perform_phased_audit(routers_to_audit, jump_host_creds=None):
    """Orchestrates the 5-phase audit for a list of routers via a jump server."""
    initialize_database()
    audit_run_id = str(uuid.uuid4())
    overall_results = {}
    
    # Validate jump server credentials first
    if not jump_host_creds:
        print("ERROR: Jump server credentials are required but not provided.")
        return {}
        
    print(f"Using jump server {jump_host_creds['ip']} with username {jump_host_creds['username']}")
    
    # Test connection to jump server before starting audits
    try:
        print("Testing connection to jump server...")
        test_conn = connect_to_jump_server(jump_host_creds)
        if isinstance(test_conn, tuple) and test_conn[0] is None:
            print(f"ERROR: Cannot connect to jump server: {test_conn[1]}")
            return {}
            
        print("✓ Successfully verified connection to jump server!")
        print(f"Jump server will be used to connect to all target routers.")
        test_conn.disconnect()
    except Exception as e:
        print(f"ERROR: Jump server connection test failed: {str(e)}")
        return {}
    
    for router_config in routers_to_audit:
        hostname = router_config.get('hostname')
        ip_address = router_config.get('ip')
        router_results = {}
        
        print(f"\n--- Beginning audit for {hostname} ({ip_address}) via jump server ---")
        
        # Phase 1: Connectivity Verification via jump server
        phase1_res = execute_phase1_connectivity(audit_run_id, router_config, jump_host_creds)
        router_results['phase1'] = phase1_res
        
        # Phase 2: Authentication Testing via jump server
        phase2_res = execute_phase2_authentication(audit_run_id, router_config, phase1_res, jump_host_creds)
        router_results['phase2'] = phase2_res
        
        # Phase 3: Configuration Audit via jump server
        phase3_res = execute_phase3_config_audit(audit_run_id, router_config, phase2_res)
        router_results['phase3'] = phase3_res
        
        # Phase 4: Risk Assessment based on collected data
        phase4_res = execute_phase4_risk_assessment(audit_run_id, router_config, phase3_res)
        router_results['phase4'] = phase4_res
        
        # Phase 5: Reporting and Recommendations
        phase5_res = execute_phase5_reporting(audit_run_id, router_config, phase1_res, phase2_res, phase3_res, phase4_res)
        router_results['phase5'] = phase5_res
        
        overall_results[hostname] = router_results
        
        print(f"\n{'-'*20} Audit Report for {hostname} {'-'*20}")
        print(f"Audit Report for {hostname} ({ip_address})")
        print(f"Audit Run ID: {audit_run_id}")
        print(f"Jump Server: {jump_host_creds['ip']}")
        print(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print("--- Phase Summaries ---")
        print(f"Phase 1 (Connectivity): {phase1_res.get('status')} - {(phase1_res.get('details') or {}).get('summary', 'N/A')}")
        print(f"Phase 2 (Authentication): {phase2_res.get('status')} - {(phase2_res.get('details') or {}).get('summary', 'N/A')}")
        print(f"Phase 3 (Config Audit): {phase3_res.get('status')} - {(phase3_res.get('details') or {}).get('summary', 'N/A')}")
        print(f"Phase 4 (Risk Assessment): {phase4_res.get('status')} - {(phase4_res.get('details') or {}).get('summary', 'N/A')}")
        risk_level = (phase4_res.get('details') or {}).get('risk_level', 'UNKNOWN')
        print(f"  Overall Risk Level: {risk_level}\n")
        
        print("--- Risks Found ---")
        risks = (phase4_res.get('details') or {}).get('risks', [])
        if risks and phase4_res.get('status') == 'SUCCESS':
            for risk in risks:
                print(f"  • {risk}")
        else:
            print("Risk assessment was skipped or failed, so no specific risks can be listed.")
        
        print("\n--- Recommendations ---")
        recommendations = (phase5_res.get('details') or {}).get('recommendations', [])
        if recommendations and phase5_res.get('status') == 'SUCCESS':
            for rec in recommendations:
                print(f"  • {rec}")
        else:
            print("No specific recommendations generated based on the findings.")
            
        print("\n" + "-"*60 + "\n")
    
    print(f"Completed audit of {len(routers_to_audit)} routers via jump server {jump_host_creds['ip']}")
    return overall_results

# --- Main Execution ---
if __name__ == '__main__':
    
    # Load router inventory from CSV file - use OS-agnostic path
    inventory_file = os.path.join('inventories', 'router.csv')
    routers = load_inventory_from_csv(inventory_file)
    
    if not routers:
        print(f"No routers found in inventory file. Using default sample routers.")
        # Fallback to sample routers if CSV loading fails
        routers = [
            {
                'hostname': 'R0',
                'ip': '172.16.39.100',
                'device_type': 'cisco_ios',
                'username': 'cisco',
                'password': 'cisco',
                'secret': 'cisco',
                'ios_version': '15.1',
                'notes': 'Default entry'
            },
            {
                'hostname': 'R1',
                'ip': '172.16.39.101',
                'device_type': 'cisco_ios',
                'username': 'cisco',
                'password': 'cisco',
                'secret': 'cisco',
                'ios_version': '15.1',
                'notes': 'Default entry'
            },
            {
                'hostname': 'R2',
                'ip': '172.16.39.102',
                'device_type': 'cisco_ios',
                'username': 'cisco',
                'password': 'cisco',
                'secret': 'cisco',
                'ios_version': '15.1',
                'notes': 'Default entry'
            }
        ]
    
    # Check if running as a script or as a web server
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--cli':
        # Run in CLI mode
        print("Starting Phased Audit Tool...")
        initialize_database()
        audit_summary = perform_phased_audit(routers, jump_host_creds)

        print("\n--- Audit Summary ---")
        for router_name, results in audit_summary.items():
            print(f"\nResults for {router_name}:")
            for phase, result in results.items():
                # Apply the same fix here for accessing summary safely
                summary_text = (result.get('details') or {}).get('summary', 'No summary')
                print(f"  {phase.capitalize()}: {result.get('status')} - {summary_text}")
                if result.get('error'):
                    print(f"    Error: {result.get('error')}")

        print("\nTo view detailed results, query the database: phased_audit_results.sqlite, table: audit_phase_results")
    else:
        # Run as web server
        print(f"Starting Phased Audit Tool Web Server on port {app.config['PORT']}...")
        initialize_database()
        app.run(host='0.0.0.0', port=app.config['PORT'], debug=True)
