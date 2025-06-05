#!/usr/bin/env python3
"""
Cisco IOS Commands Demo - Async Line Section Extraction
=======================================================

This script demonstrates what the actual Cisco IOS commands would return
when executed on a router with async line configurations.

Commands demonstrated:
1. show running-config | section ^line 0\/1\/
2. show running-config | section ^line 1\/0\/  
3. show run | include ^line [01]\/[01]\/

This simulates the exact output you would see on the router console.
"""

import re
from typing import List


class CiscoCommandSimulator:
    """Simulates Cisco IOS command execution on router configs."""
    
    def __init__(self, config_file: str = "dummy-router-configs"):
        try:
            with open(config_file, 'r') as f:
                self.config = f.read()
        except FileNotFoundError:
            print(f"Error: Config file {config_file} not found!")
            self.config = ""
    
    def execute_section_command(self, pattern: str) -> str:
        """Simulate: show running-config | section ^pattern"""
        if not self.config:
            return "% Config file not loaded"
            
        lines = self.config.split('\n')
        result_lines = []
        in_section = False
        
        # Convert pattern for regex matching
        regex_pattern = pattern.replace(r'\/', '/')
        
        print(f"Router# show running-config | section {pattern}")
        
        for line in lines:
            # Check if line matches our pattern
            if re.match(regex_pattern, line.strip()):
                in_section = True
                result_lines.append(line)
            elif in_section:
                # Continue until we hit a line starting with ! or another line command
                if line.strip() == '!' or (line.startswith('line ') and not re.match(regex_pattern, line.strip())):
                    result_lines.append('!')
                    in_section = False
                    # Don't include the next line command that doesn't match
                    if line.startswith('line ') and not re.match(regex_pattern, line.strip()):
                        continue
                else:
                    result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def execute_include_command(self, pattern: str) -> str:
        """Simulate: show run | include ^pattern"""
        if not self.config:
            return "% Config file not loaded"
            
        lines = self.config.split('\n')
        result_lines = []
        
        # Convert pattern for regex matching
        regex_pattern = pattern.replace(r'\/', '/').replace(r'\d+', r'\d+')
        
        print(f"Router# show run | include {pattern}")
        
        for line in lines:
            if re.match(regex_pattern, line.strip()):
                result_lines.append(line.strip())
                
        return '\n'.join(result_lines)

    def demo_all_commands(self):
        """Run all three command demonstrations."""
        print("=" * 80)
        print("🔧 CISCO IOS ASYNC LINE AUDIT COMMANDS DEMONSTRATION")
        print("=" * 80)
        print("📄 Source: dummy-router-configs file")
        print()
        
        # Command 1: Section 0/1/*
        print("📌 COMMAND 1: Extract all async lines for Slot 0 / PA 1")
        print("-" * 50)
        section_0_1 = self.execute_section_command(r'^line 0\/1\/')
        print(section_0_1)
        print()
        
        # Command 2: Section 1/0/*  
        print("📌 COMMAND 2: Extract all async lines for Slot 1 / PA 0")
        print("-" * 50)
        section_1_0 = self.execute_section_command(r'^line 1\/0\/')
        print(section_1_0)
        print()
        
        # Command 3: Include headers only
        print("📌 COMMAND 3: Quick head-count of async line headers")
        print("-" * 50)
        include_headers = self.execute_include_command(r'^line [01]\/[01]\/')
        print(include_headers)
        print()
        
        # Analysis
        self._analyze_results(section_0_1, section_1_0, include_headers)
    
    def _analyze_results(self, section_0_1: str, section_1_0: str, headers: str):
        """Analyze the command results."""
        print("=" * 80)
        print("📊 COMMAND RESULTS ANALYSIS")
        print("=" * 80)
        
        # Count lines in each section
        section_0_1_lines = [line for line in section_0_1.split('\n') if line.startswith('line 0/1/')]
        section_1_0_lines = [line for line in section_1_0.split('\n') if line.startswith('line 1/0/')]
        header_lines = [line for line in headers.split('\n') if line.startswith('line ')]
        
        print(f"📈 Line Count Summary:")
        print(f"   • Slot 0/PA 1 lines found: {len(section_0_1_lines)}")
        print(f"   • Slot 1/PA 0 lines found: {len(section_1_0_lines)}") 
        print(f"   • Total async lines: {len(header_lines)}")
        print(f"   • Expected per slot: 23 (channels 0-22)")
        
        # Check for telnet enablement
        telnet_count_0_1 = section_0_1.count('transport input telnet') + section_0_1.count('transport input ssh telnet')
        telnet_count_1_0 = section_1_0.count('transport input telnet') + section_1_0.count('transport input ssh telnet')
        total_telnet = telnet_count_0_1 + telnet_count_1_0
        
        print(f"\n🌐 Telnet Enablement:")
        print(f"   • Slot 0/PA 1 telnet lines: {telnet_count_0_1}")
        print(f"   • Slot 1/PA 0 telnet lines: {telnet_count_1_0}")
        print(f"   • Total telnet-enabled: {total_telnet}")
        
        # Security analysis
        no_login_count = section_0_1.count('no login') + section_1_0.count('no login')
        acl_count = section_0_1.count('access-class') + section_1_0.count('access-class')
        
        print(f"\n🔒 Security Analysis:")
        print(f"   • Lines with 'no login': {no_login_count}")
        print(f"   • Lines with access-class ACLs: {acl_count}")
        
        # Rotary groups
        rotary_matches_0_1 = re.findall(r'rotary (\d+)', section_0_1)
        rotary_matches_1_0 = re.findall(r'rotary (\d+)', section_1_0)
        unique_rotary = set(rotary_matches_0_1 + rotary_matches_1_0)
        
        print(f"\n🔄 Rotary Groups:")
        print(f"   • Unique rotary groups found: {sorted(unique_rotary)}")
        print(f"   • Slot 0/PA 1 rotary groups: {sorted(set(rotary_matches_0_1))}")
        print(f"   • Slot 1/PA 0 rotary groups: {sorted(set(rotary_matches_1_0))}")
        
        print()

    def show_practical_usage(self):
        """Show practical usage scenarios."""
        print("=" * 80)
        print("💡 PRACTICAL USAGE SCENARIOS")
        print("=" * 80)
        
        print("🎯 Use Case 1: Security Audit")
        print("   Run the section commands to identify:")
        print("   • Lines with telnet but no authentication")
        print("   • Missing access-class ACLs")
        print("   • Inconsistent security policies")
        print()
        
        print("🎯 Use Case 2: Console Server Verification") 
        print("   Check for proper console server setup:")
        print("   • 'no exec' + rotary group configuration")
        print("   • Consistent speed/flow control settings")
        print("   • Reverse-telnet port mapping")
        print()
        
        print("🎯 Use Case 3: Capacity Planning")
        print("   Verify all expected async ports are configured:")
        print("   • 23 lines per slot/PA (channels 0-22)")
        print("   • No missing or extra channel numbers")
        print("   • Proper slot/PA numbering")
        print()
        
        print("🎯 Use Case 4: Troubleshooting")
        print("   Quick identification of line issues:")
        print("   • Speed mismatches")
        print("   • Missing flow control")
        print("   • Conflicting rotary groups")
        print()


def main():
    """Main function to run the Cisco command demonstration."""
    simulator = CiscoCommandSimulator()
    
    # Run the demo
    simulator.demo_all_commands()
    
    # Show practical usage
    simulator.show_practical_usage()
    
    print("✅ Demo completed successfully!")
    

if __name__ == "__main__":
    main() 