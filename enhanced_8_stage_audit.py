#!/usr/bin/env python3
"""
Enhanced 8-Stage Audit Module for NetAuditPro
Implements comprehensive device audit workflow as requested
"""

import os
import time
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
import paramiko

def create_device_extraction_folder(script_directory: str) -> str:
    """A5: Create unique timestamped folder for device data extraction"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"device-extracted-{timestamp}"
    folder_path = os.path.join(script_directory, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    print(f"📁 Created extraction folder: {folder_name}")
    return folder_path

def parse_line_telnet_output(output: str, device_name: str, line_type: str) -> List[Dict[str, Any]]:
    """Parse VTY or CON line telnet audit output"""
    try:
        lines = output.strip().split('\n')
        line_configs = []
        current_line = None
        current_config = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('show run') or line.endswith('#') or line.endswith('>'):
                continue
                
            if line.startswith(f"line {line_type}"):
                # Save previous line config if exists
                if current_line and current_config:
                    line_analysis = analyze_line_config(current_line, current_config, device_name, line_type)
                    line_configs.append(line_analysis)
                
                # Start new line config
                current_line = line
                current_config = [line]
            elif current_line and (line.startswith(" ") or line.startswith("\t")):
                current_config.append(line)
        
        # Process last line config
        if current_line and current_config:
            line_analysis = analyze_line_config(current_line, current_config, device_name, line_type)
            line_configs.append(line_analysis)
        
        return line_configs
        
    except Exception as e:
        return [{
            "hostname": device_name,
            "line": f"ERROR parsing {line_type}",
            "telnet_allowed": "ERROR",
            "error": str(e)
        }]

def analyze_line_config(line_header: str, config_lines: List[str], device_name: str, line_type: str) -> Dict[str, Any]:
    """Analyze individual line configuration for telnet security"""
    telnet_allowed = "NO"
    login_method = "unknown"
    exec_timeout = "default"
    transport_input = "N/A"
    
    config_text = "\n".join(config_lines)
    
    for line in config_lines:
        line = line.strip()
        if "transport input" in line:
            transport_input = line
            if re.search(r"transport input.*(all|telnet)", line, re.IGNORECASE):
                telnet_allowed = "YES"
            elif re.search(r"transport input.*(ssh|none)", line, re.IGNORECASE):
                telnet_allowed = "NO"
        elif line == "login":
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
    
    # Risk assessment
    risk_level = assess_aux_risk(telnet_allowed, login_method, exec_timeout)
    
    # Generate analysis
    if telnet_allowed == "YES":
        if login_method in ["unknown", "none"]:
            analysis = f"🚨 CRITICAL: {line_type.upper()} telnet enabled with no authentication"
        elif login_method == "line_password":
            analysis = f"⚠️ HIGH: {line_type.upper()} telnet enabled with line password only"
        else:
            analysis = f"⚠️ MEDIUM: {line_type.upper()} telnet enabled with authentication"
    else:
        analysis = f"✅ SECURE: {line_type.upper()} telnet disabled or SSH-only"
    
    return {
        "hostname": device_name,
        "line": line_header,
        "line_type": line_type,
        "telnet_allowed": telnet_allowed,
        "login_method": login_method,
        "exec_timeout": exec_timeout,
        "transport_input": transport_input,
        "risk_level": risk_level,
        "analysis": analysis,
        "config_text": config_text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def assess_aux_risk(telnet_allowed, login_method, exec_timeout):
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

def execute_8_stage_device_audit(jump_client, device, device_index, total_devices, 
                                 core_commands, log_func, progress_func, 
                                 ping_func, connect_func, parse_aux_func, script_dir):
    """
    Execute comprehensive 8-stage audit process for each device:
    A1. Ping test (record failures but continue to A2)
    A2. SSH connection and credential verification
    A3. Authorization test with 'show line' command
    A4. Wait 3 seconds after command execution
    A5. Data collection and save to timestamped folder
    A6. Data processing for dashboard updates
    A7. Core telnet security analysis (aux, vty, con lines)
    A8. Generate comprehensive report for all stages
    """
    device_name = device.get("hostname", f"device_{device_index+1}")
    device_ip = device.get("ip_address", "")
    
    # Initialize comprehensive audit results
    audit_stages = {
        "A1_ping": {"status": "pending", "details": None, "error": None},
        "A2_ssh_auth": {"status": "pending", "details": None, "error": None},
        "A3_authorization": {"status": "pending", "details": None, "error": None},
        "A4_wait_confirm": {"status": "pending", "details": None, "error": None},
        "A5_data_collection": {"status": "pending", "details": None, "error": None},
        "A6_data_processing": {"status": "pending", "details": None, "error": None},
        "A7_telnet_analysis": {"status": "pending", "details": None, "error": None},
        "A8_reporting": {"status": "pending", "details": None, "error": None}
    }
    
    device_results = {
        "device_name": device_name,
        "device_ip": device_ip,
        "timestamp": datetime.now().isoformat(),
        "audit_stages": audit_stages,
        "commands": {},
        "telnet_audit": {},
        "overall_status": "in_progress",
        "stage_failures": [],
        "extraction_folder": None
    }
    
    log_func(f"\n🚀 Starting 8-Stage Audit for {device_name} ({device_ip})")
    log_func("="*60)
    
    try:
        # ===== STAGE A1: PING TEST =====
        log_func(f"📍 Stage A1: ICMP Connectivity Test for {device_name}")
        progress_func(device_name, device_index, total_devices, f"A1: Ping test - {device_name}")
        
        try:
            ping_success = ping_func(jump_client, device_ip)
            if ping_success:
                audit_stages["A1_ping"]["status"] = "success"
                audit_stages["A1_ping"]["details"] = f"Device {device_ip} responds to ping"
                log_func(f"✅ A1: ICMP successful for {device_name}")
            else:
                audit_stages["A1_ping"]["status"] = "failed"
                audit_stages["A1_ping"]["details"] = f"Device {device_ip} does not respond to ping"
                audit_stages["A1_ping"]["error"] = "ICMP timeout or unreachable"
                device_results["stage_failures"].append("A1_ping")
                log_func(f"❌ A1: ICMP failed for {device_name} - Continuing to A2 as requested")
        except Exception as ping_error:
            audit_stages["A1_ping"]["status"] = "error"
            audit_stages["A1_ping"]["error"] = str(ping_error)
            device_results["stage_failures"].append("A1_ping")
            log_func(f"⚠️ A1: ICMP test error for {device_name}: {ping_error} - Continuing to A2")
        
        # ===== STAGE A2: SSH CONNECTION AND AUTHENTICATION =====
        log_func(f"📍 Stage A2: SSH Connection & Authentication for {device_name}")
        progress_func(device_name, device_index, total_devices, f"A2: SSH Auth - {device_name}")
        
        try:
            device_connection, failure_reason = connect_func(jump_client, device)
            
            if device_connection:
                audit_stages["A2_ssh_auth"]["status"] = "success"
                audit_stages["A2_ssh_auth"]["details"] = "SSH connection established and credentials verified"
                log_func(f"✅ A2: SSH authentication successful for {device_name}")
                log_func(f"🔐 A2: Router terminal access confirmed for {device_name}")
            else:
                audit_stages["A2_ssh_auth"]["status"] = "failed"
                audit_stages["A2_ssh_auth"]["error"] = failure_reason
                device_results["stage_failures"].append("A2_ssh_auth")
                log_func(f"❌ A2: SSH authentication failed for {device_name}: {failure_reason}")
                
                # If SSH fails, we cannot continue with remaining stages
                for stage in ["A3_authorization", "A4_wait_confirm", "A5_data_collection", "A6_data_processing", "A7_telnet_analysis"]:
                    audit_stages[stage]["status"] = "skipped"
                    audit_stages[stage]["error"] = "Skipped due to SSH authentication failure"
                
                # Jump to A8 for failure reporting
                audit_stages["A8_reporting"]["status"] = "completed"
                audit_stages["A8_reporting"]["details"] = "Generated failure report due to SSH authentication failure"
                device_results["overall_status"] = "failed"
                return device_results
                
        except Exception as ssh_error:
            audit_stages["A2_ssh_auth"]["status"] = "error"
            audit_stages["A2_ssh_auth"]["error"] = str(ssh_error)
            device_results["stage_failures"].append("A2_ssh_auth")
            log_func(f"⚠️ A2: SSH connection error for {device_name}: {ssh_error}")
            
            # Skip remaining stages and generate error report
            for stage in ["A3_authorization", "A4_wait_confirm", "A5_data_collection", "A6_data_processing", "A7_telnet_analysis"]:
                audit_stages[stage]["status"] = "skipped"
                audit_stages[stage]["error"] = "Skipped due to SSH connection error"
            
            audit_stages["A8_reporting"]["status"] = "completed"
            audit_stages["A8_reporting"]["details"] = "Generated error report due to SSH connection failure"
            device_results["overall_status"] = "error"
            return device_results
        
        # ===== STAGE A3: AUTHORIZATION TEST =====
        log_func(f"📍 Stage A3: Authorization Test for {device_name}")
        progress_func(device_name, device_index, total_devices, f"A3: Authorization - {device_name}")
        
        try:
            log_func(f"⚡ A3: Executing 'show line' command on {device_name}")
            show_line_output = device_connection.send_command('show line', read_timeout=30)
            
            if show_line_output and len(show_line_output.strip()) > 0:
                audit_stages["A3_authorization"]["status"] = "success"
                audit_stages["A3_authorization"]["details"] = "Authorization confirmed - device responds to commands"
                device_results["commands"]["show_line"] = {
                    "command": "show line",
                    "output": show_line_output,
                    "status": "success",
                    "timestamp": datetime.now().isoformat()
                }
                log_func(f"✅ A3: Authorization successful for {device_name}")
                log_func(f"📊 A3: Device {device_name} is available and responding to commands")
            else:
                audit_stages["A3_authorization"]["status"] = "failed"
                audit_stages["A3_authorization"]["error"] = "No response from 'show line' command"
                device_results["stage_failures"].append("A3_authorization")
                log_func(f"❌ A3: Authorization failed for {device_name} - No command response")
                
        except Exception as auth_error:
            audit_stages["A3_authorization"]["status"] = "error"
            audit_stages["A3_authorization"]["error"] = str(auth_error)
            device_results["stage_failures"].append("A3_authorization")
            log_func(f"⚠️ A3: Authorization error for {device_name}: {auth_error}")
        
        # ===== STAGE A4: WAIT AND CONFIRM DATA COLLECTION =====
        log_func(f"📍 Stage A4: Wait and Confirm Data Collection for {device_name}")
        progress_func(device_name, device_index, total_devices, f"A4: Wait Confirm - {device_name}")
        
        try:
            log_func(f"⏳ A4: Waiting 3 seconds before confirming data collection for {device_name}")
            time.sleep(3)
            
            audit_stages["A4_wait_confirm"]["status"] = "success"
            audit_stages["A4_wait_confirm"]["details"] = "3-second wait completed, ready for data collection"
            log_func(f"✅ A4: Wait period completed for {device_name}")
            
        except Exception as wait_error:
            audit_stages["A4_wait_confirm"]["status"] = "error"
            audit_stages["A4_wait_confirm"]["error"] = str(wait_error)
            log_func(f"⚠️ A4: Wait confirmation error for {device_name}: {wait_error}")
        
        # ===== STAGE A5: DATA COLLECTION AND SAVE =====
        log_func(f"📍 Stage A5: Data Collection and Save for {device_name}")
        progress_func(device_name, device_index, total_devices, f"A5: Data Collection - {device_name}")
        
        try:
            # Create extraction folder if not exists
            if not device_results["extraction_folder"]:
                device_results["extraction_folder"] = create_device_extraction_folder(script_dir)
            
            # Execute all audit commands
            log_func(f"🔍 A5: Collecting comprehensive data from {device_name}")
            
            for cmd_name, command in core_commands.items():
                if cmd_name == 'show_line':  # Already executed in A3
                    continue
                    
                try:
                    log_func(f"⚡ A5: Executing '{cmd_name}' on {device_name}")
                    output = device_connection.send_command(command, read_timeout=60)
                    
                    device_results["commands"][cmd_name] = {
                        "command": command,
                        "output": output,
                        "status": "success",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Save individual command output to extraction folder
                    cmd_filename = f"{device_name}_{cmd_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    cmd_filepath = os.path.join(device_results["extraction_folder"], cmd_filename)
                    
                    with open(cmd_filepath, 'w', encoding='utf-8') as f:
                        f.write(f"Device: {device_name}\n")
                        f.write(f"Command: {command}\n")
                        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                        f.write("="*50 + "\n")
                        f.write(output)
                    
                    log_func(f"💾 A5: Saved '{cmd_name}' output for {device_name}")
                    
                except Exception as cmd_error:
                    log_func(f"❌ A5: Command '{cmd_name}' failed on {device_name}: {cmd_error}")
                    device_results["commands"][cmd_name] = {
                        "command": command,
                        "output": f"ERROR: {cmd_error}",
                        "status": "error",
                        "timestamp": datetime.now().isoformat()
                    }
            
            audit_stages["A5_data_collection"]["status"] = "success"
            audit_stages["A5_data_collection"]["details"] = f"Data collected and saved to {device_results['extraction_folder']}"
            log_func(f"✅ A5: Data collection completed for {device_name}")
            
        except Exception as collection_error:
            audit_stages["A5_data_collection"]["status"] = "error"
            audit_stages["A5_data_collection"]["error"] = str(collection_error)
            device_results["stage_failures"].append("A5_data_collection")
            log_func(f"⚠️ A5: Data collection error for {device_name}: {collection_error}")
        
        # ===== STAGE A6: DATA PROCESSING FOR DASHBOARD =====
        log_func(f"📍 Stage A6: Data Processing for Dashboard Updates for {device_name}")
        progress_func(device_name, device_index, total_devices, f"A6: Data Processing - {device_name}")
        
        try:
            # Process collected data for dashboard updates
            processed_data = {
                "device_info": {
                    "hostname": device_name,
                    "ip_address": device_ip,
                    "timestamp": datetime.now().isoformat()
                },
                "command_summary": {},
                "telnet_findings": {},
                "security_status": "unknown"
            }
            
            # Summarize command results
            for cmd_name, cmd_data in device_results["commands"].items():
                processed_data["command_summary"][cmd_name] = {
                    "status": cmd_data["status"],
                    "output_length": len(cmd_data["output"]),
                    "timestamp": cmd_data["timestamp"]
                }
            
            audit_stages["A6_data_processing"]["status"] = "success"
            audit_stages["A6_data_processing"]["details"] = "Data processed for dashboard and reporting updates"
            log_func(f"✅ A6: Data processing completed for {device_name}")
            
        except Exception as processing_error:
            audit_stages["A6_data_processing"]["status"] = "error"
            audit_stages["A6_data_processing"]["error"] = str(processing_error)
            device_results["stage_failures"].append("A6_data_processing")
            log_func(f"⚠️ A6: Data processing error for {device_name}: {processing_error}")
        
        # ===== STAGE A7: CORE TELNET SECURITY ANALYSIS =====
        log_func(f"📍 Stage A7: Core Telnet Security Analysis for {device_name}")
        progress_func(device_name, device_index, total_devices, f"A7: Telnet Analysis - {device_name}")
        
        try:
            telnet_findings = {
                "aux_lines": [],
                "vty_lines": [],
                "con_lines": [],
                "telnet_enabled_count": 0,
                "high_risk_lines": [],
                "security_violations": []
            }
            
            # Analyze AUX lines
            if "aux_telnet_audit" in device_results["commands"]:
                aux_output = device_results["commands"]["aux_telnet_audit"]["output"]
                aux_analysis = parse_aux_func(aux_output, device_name)
                aux_analysis["ip_address"] = device_ip
                device_results["telnet_audit"]["aux"] = aux_analysis
                telnet_findings["aux_lines"].append(aux_analysis)
                
                if aux_analysis.get("telnet_allowed") == "YES":
                    telnet_findings["telnet_enabled_count"] += 1
                    if aux_analysis.get("risk_level") in ["CRITICAL", "HIGH"]:
                        telnet_findings["high_risk_lines"].append({
                            "line_type": "aux",
                            "line": aux_analysis.get("line", "aux 0"),
                            "risk_level": aux_analysis.get("risk_level"),
                            "reason": aux_analysis.get("analysis")
                        })
            
            # Analyze VTY lines
            if "vty_telnet_audit" in device_results["commands"]:
                vty_output = device_results["commands"]["vty_telnet_audit"]["output"]
                vty_analysis = parse_line_telnet_output(vty_output, device_name, "vty")
                device_results["telnet_audit"]["vty"] = vty_analysis
                telnet_findings["vty_lines"].extend(vty_analysis)
                
                for vty_line in vty_analysis:
                    if vty_line.get("telnet_allowed") == "YES":
                        telnet_findings["telnet_enabled_count"] += 1
                        if vty_line.get("risk_level") in ["CRITICAL", "HIGH"]:
                            telnet_findings["high_risk_lines"].append({
                                "line_type": "vty",
                                "line": vty_line.get("line", "vty"),
                                "risk_level": vty_line.get("risk_level"),
                                "reason": vty_line.get("analysis")
                            })
            
            # Analyze CON lines
            if "con_telnet_audit" in device_results["commands"]:
                con_output = device_results["commands"]["con_telnet_audit"]["output"]
                con_analysis = parse_line_telnet_output(con_output, device_name, "con")
                device_results["telnet_audit"]["con"] = con_analysis
                telnet_findings["con_lines"].extend(con_analysis)
                
                for con_line in con_analysis:
                    if con_line.get("telnet_allowed") == "YES":
                        telnet_findings["telnet_enabled_count"] += 1
                        if con_line.get("risk_level") in ["CRITICAL", "HIGH"]:
                            telnet_findings["high_risk_lines"].append({
                                "line_type": "con",
                                "line": con_line.get("line", "con"),
                                "risk_level": con_line.get("risk_level"),
                                "reason": con_line.get("analysis")
                            })
            
            device_results["telnet_audit"]["summary"] = telnet_findings
            
            audit_stages["A7_telnet_analysis"]["status"] = "success"
            audit_stages["A7_telnet_analysis"]["details"] = f"Found {telnet_findings['telnet_enabled_count']} lines with telnet enabled"
            
            log_func(f"✅ A7: Telnet analysis completed for {device_name}")
            log_func(f"📊 A7: Found {telnet_findings['telnet_enabled_count']} telnet-enabled lines on {device_name}")
            
            if telnet_findings["high_risk_lines"]:
                log_func(f"🚨 A7: {len(telnet_findings['high_risk_lines'])} high-risk telnet configurations found on {device_name}")
            
        except Exception as analysis_error:
            audit_stages["A7_telnet_analysis"]["status"] = "error"
            audit_stages["A7_telnet_analysis"]["error"] = str(analysis_error)
            device_results["stage_failures"].append("A7_telnet_analysis")
            log_func(f"⚠️ A7: Telnet analysis error for {device_name}: {analysis_error}")
        
        # ===== STAGE A8: COMPREHENSIVE REPORTING =====
        log_func(f"📍 Stage A8: Comprehensive Reporting for {device_name}")
        progress_func(device_name, device_index, total_devices, f"A8: Reporting - {device_name}")
        
        try:
            # Generate comprehensive report
            report_data = {
                "device_summary": {
                    "hostname": device_name,
                    "ip_address": device_ip,
                    "audit_timestamp": datetime.now().isoformat(),
                    "overall_status": "success" if not device_results["stage_failures"] else "partial"
                },
                "stage_results": audit_stages,
                "telnet_security_summary": device_results["telnet_audit"].get("summary", {}),
                "failed_stages": device_results["stage_failures"],
                "recommendations": []
            }
            
            # Generate recommendations based on findings
            if device_results["telnet_audit"].get("summary", {}).get("telnet_enabled_count", 0) > 0:
                report_data["recommendations"].append("Review and disable unnecessary telnet access")
            
            if device_results["telnet_audit"].get("summary", {}).get("high_risk_lines"):
                report_data["recommendations"].append("Immediate attention required for high-risk telnet configurations")
            
            if audit_stages["A1_ping"]["status"] == "failed":
                report_data["recommendations"].append("Investigate network connectivity issues")
            
            # Save comprehensive report
            if device_results["extraction_folder"]:
                report_filename = f"{device_name}_comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                report_filepath = os.path.join(device_results["extraction_folder"], report_filename)
                
                with open(report_filepath, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, default=str)
                
                log_func(f"📄 A8: Comprehensive report saved for {device_name}")
            
            audit_stages["A8_reporting"]["status"] = "success"
            audit_stages["A8_reporting"]["details"] = "Comprehensive report generated and saved"
            
            # Determine overall status
            if not device_results["stage_failures"]:
                device_results["overall_status"] = "success"
                log_func(f"🎉 A8: All stages completed successfully for {device_name}")
            elif len(device_results["stage_failures"]) < 4:  # Allow some failures
                device_results["overall_status"] = "partial"
                log_func(f"⚠️ A8: Partial success for {device_name} - {len(device_results['stage_failures'])} stage(s) failed")
            else:
                device_results["overall_status"] = "failed"
                log_func(f"❌ A8: Multiple failures for {device_name} - {len(device_results['stage_failures'])} stage(s) failed")
            
        except Exception as reporting_error:
            audit_stages["A8_reporting"]["status"] = "error"
            audit_stages["A8_reporting"]["error"] = str(reporting_error)
            log_func(f"⚠️ A8: Reporting error for {device_name}: {reporting_error}")
        
        # Close device connection
        try:
            device_connection.disconnect()
            log_func(f"🔌 Disconnected from {device_name}")
        except Exception as disconnect_error:
            log_func(f"⚠️ Error disconnecting from {device_name}: {disconnect_error}")
        
        log_func(f"🏁 8-Stage audit completed for {device_name}")
        log_func("="*60)
        
        return device_results
        
    except Exception as critical_error:
        log_func(f"🚨 CRITICAL ERROR during 8-stage audit for {device_name}: {critical_error}")
        device_results["overall_status"] = "critical_error"
        device_results["critical_error"] = str(critical_error)
        
        # Mark all pending stages as failed
        for stage_name, stage_data in audit_stages.items():
            if stage_data["status"] == "pending":
                stage_data["status"] = "failed"
                stage_data["error"] = f"Failed due to critical error: {critical_error}"
        
        return device_results 