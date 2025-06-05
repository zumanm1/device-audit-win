# EVE-NG Router Connectivity Guide

## Issue: Filtered Management Interfaces

Your EVE-NG lab has all router management interfaces (SSH/Telnet) filtered by default.
This is a security feature but prevents external management access.

## Solutions:

### Option 1: Enable Management Access on Routers
Connect to each router via console and configure:

```
enable
configure terminal
!
! Enable SSH
ip domain-name lab.local
crypto key generate rsa modulus 1024
username cisco password cisco
username cisco privilege 15
!
! Configure VTY lines
line vty 0 15
 transport input ssh telnet
 login local
 privilege level 15
!
! Optional: Configure management ACL
access-list 100 permit tcp any any eq 22
access-list 100 permit tcp any any eq 23
interface vlan1
 ip access-group 100 in
!
end
write memory
```

### Option 2: Use EVE-NG Console Access
1. Access routers via EVE-NG web console
2. Configure devices from console interface
3. Use V4codercli with console connections

### Option 3: Configure Network Access
From EVE-NG topology:
1. Add management network connections
2. Configure proper routing
3. Remove security filters if in lab environment

## Testing Connectivity

Use the provided test script:
```bash
python3 test_enhanced_connectivity.py
```

This will test legacy SSH connectivity to your routers.

## V4codercli Configuration

Once connectivity is established, V4codercli will automatically use the enhanced
SSH configuration for legacy algorithm support.

## Common Issues:

1. **SSH Key Exchange Failure**: Fixed by legacy algorithm support
2. **Connection Timeout**: Check network routing and firewall rules  
3. **Authentication Failure**: Verify username/password credentials
4. **Port Filtered**: Enable SSH/Telnet on router management interface

## For Production Networks:
- Use proper SSH key authentication
- Configure appropriate access controls
- Enable logging and monitoring
- Regular security updates
