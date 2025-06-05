# Product Requirements Document (PRD) - EVE-NG Automation Script Enhancement

## Document Information
- **Project**: V5evscriptcli - EVE-NG MPLS L3VPN Automation Enhancement
- **Version**: 1.0
- **Date**: 2025-01-16
- **Author**: MPLS L3VPN Automation Team
- **Status**: Approved

## 1. Introduction

This document outlines the requirements for enhancing the eve-ng-automationv01.py script. The script aims to automate the deployment of a predefined MPLS L3VPN topology in EVE-NG. The current version successfully provisions routers but fails to establish all specified network connections, particularly those involving interfaces located in network module slots (e.g., f1/0, f2/0). This enhancement focuses on rectifying these connectivity issues and improving the script's reliability.

## 2. Goals

### Primary Goal
Ensure the script correctly establishes all defined P2P and management network connections for the MPLS L3VPN topology, specifically addressing the interface mapping for c3725 routers with NM-1FE-TX modules.

### Secondary Goal
Improve the accuracy of connection verification and final topology reporting within the script's logging.

### Tertiary Goal
Maintain the existing functionality of lab creation, node provisioning, and cleanup while adding enhanced troubleshooting capabilities.

## 3. Target Audience

- **Network Engineers**: Using EVE-NG for lab automation and MPLS testing
- **Students and Professionals**: Learning or testing MPLS L3VPN configurations
- **EVE-NG Administrators**: Managing EVE-NG environments who need to deploy standardized topologies
- **Automation Engineers**: Building network automation workflows

## 4. User Stories

### US1: Correct Interface Connectivity
**As a user**, I want the script to correctly connect all routers (CE, PE, P, RR) as per the TOPOLOGY_CONNECTIONS definition, including links utilizing f1/0 interfaces, so that the core MPLS network is fully meshed as designed.

**Acceptance Criteria:**
- All connections defined in TOPOLOGY_CONNECTIONS are successfully established
- No "Cannot link node (20034)" errors occur
- Interface mapping correctly handles slotted interfaces

### US2: Management Network Access
**As a user**, I want the script to correctly connect all routers to the MANAGEMENT_NETWORK using their specified mgmt_interface (including f2/0 interfaces), so that all nodes are accessible for out-of-band management.

**Acceptance Criteria:**
- All routers connect to management network
- Management interfaces are correctly mapped
- Console access information is provided

### US3: Accurate Status Reporting
**As a user**, I want the script's log output for "Verifying connection" and the "MPLS L3VPN TOPOLOGY - FINAL STATE" to accurately reflect the true connection status in the EVE-NG lab.

**Acceptance Criteria:**
- Connection verification reports accurate status
- Final topology summary matches actual lab state
- Interface status correctly displayed

### US4: Error-Free Execution
**As a user**, I want the script to complete its execution without "Cannot link node (20034)" errors related to incorrect interface mapping.

**Acceptance Criteria:**
- Script executes without critical API errors
- All defined connections are established
- Error handling provides clear feedback

### US5: SSH Troubleshooting Access
**As a user**, I want the ability to SSH into the EVE-NG host for manual verification and troubleshooting when issues occur.

**Acceptance Criteria:**
- SSH access instructions provided
- Direct EVE-NG API commands documented
- Troubleshooting guide available

## 5. Functional Requirements (FR)

### FR1: Correct Interface Mapping for c3725 NM-1FE-TX
The script MUST use the correct EVE-NG API interface indices for c3725 routers:
- `f0/0` -> API index `0`
- `f0/1` -> API index `1`
- `f1/0` (slot 1) -> API index `16`
- `f2/0` (slot 2) -> API index `32`

### FR2: Full P2P Link Establishment
All connections defined in TOPOLOGY_CONNECTIONS MUST be successfully created without errors.

### FR3: Full Management Network Connectivity
All routers specified in TOPOLOGY_ROUTERS MUST be successfully connected to the MANAGEMENT_NETWORK_NAME using their defined mgmt_interface.

### FR4: Accurate Connection Verification
The verify_connection function MUST correctly parse the EVE-NG API response to determine if a node interface is connected to the specified network ID.

### FR5: Accurate Final State Reporting
The show_final_topology function MUST accurately display the connection status of each interface based on data retrieved from the EVE-NG API.

### FR6: Enhanced Error Handling
The script should continue to log API errors clearly if they occur for reasons other than incorrect interface mapping, and provide actionable troubleshooting information.

### FR7: SSH Integration for Troubleshooting
The script MUST provide SSH access capabilities to the EVE-NG host for direct API verification and troubleshooting.

## 6. Non-Functional Requirements (NFR)

### NFR1: Compatibility
The solution MUST remain compatible with:
- EVE-NG version 6.2.0-4 (as per logs)
- c3725 Dynamips image
- NM-1FE-TX network modules
- Python 3.6+

### NFR2: Performance
- The changes should not significantly degrade the script's overall execution time
- Connection establishment should complete within reasonable timeframes
- API calls should include appropriate timeouts

### NFR3: Robustness
- The script should be robust to minor variations in API response structures
- Fail gracefully with clear logs when encountering errors
- Provide retry mechanisms where appropriate

### NFR4: Maintainability
- Code should be well-documented with clear comments
- Interface mapping should be easily configurable
- Logging should provide sufficient detail for troubleshooting

### NFR5: Security
- SSH credentials should be handled securely
- API credentials should be configurable
- No hardcoded sensitive information

## 7. Technical Specifications

### 7.1 Interface Mapping Implementation
```python
interface_mapping = {
    'f0/0': '0',   # Onboard FastEthernet0/0
    'f0/1': '1',   # Onboard FastEthernet0/1
    'f1/0': '16',  # NM-1FE-TX in slot 1
    'f2/0': '32',  # NM-1FE-TX in slot 2
}
```

### 7.2 EVE-NG API Endpoints
- Node creation: `POST /api/labs/{lab_path}/nodes`
- Network creation: `POST /api/labs/{lab_path}/networks`
- Interface connection: `PUT /api/labs/{lab_path}/nodes/{node_id}/interfaces`
- Interface verification: `GET /api/labs/{lab_path}/nodes/{node_id}/interfaces`

### 7.3 SSH Access Configuration
- Host: 172.16.39.128
- Username: root
- Password: eve
- Purpose: Direct EVE-NG API verification

## 8. Topology Specifications

### 8.1 Router Configuration
- **Router Type**: Cisco 3725 (Dynamips)
- **Template**: c3725
- **Image**: c3725-adventerprisek9-mz.124-15.T14.image
- **RAM**: 256MB
- **Network Modules**: NM-1FE-TX in slots 1 and 2

### 8.2 Network Topology
```
    CE-4 ---- PE1 ---- P ---- RR1
               |       |
    CE-5 ---- PE2 ----+
               |
         Management Network
```

### 8.3 Connection Matrix
| Source | Interface | Destination | Interface | Network |
|--------|-----------|-------------|-----------|---------|
| CE-4   | f1/0      | PE1         | f1/0      | Link_CE4_PE1 |
| PE1    | f0/0      | P           | f0/0      | Link_PE1_P |
| P      | f0/1      | PE2         | f0/1      | Link_P_PE2 |
| P      | f1/0      | RR1         | f1/0      | Link_P_RR1 |
| PE2    | f0/0      | CE-5        | f0/0      | Link_PE2_CE5 |

## 9. Assumptions

1. The EVE-NG API uses a consistent interface indexing scheme (0, 1, 16, 32) for c3725 routers with NM-1FE-TX modules
2. The EVE-NG instance at 172.16.39.128 is accessible and functioning correctly
3. SSH credentials (root/eve) remain valid for direct EVE-NG system access
4. Python environment supports the required libraries

## 10. Constraints

1. Solution must work with existing EVE-NG infrastructure
2. Cannot modify EVE-NG core system configurations
3. Must maintain backward compatibility with existing lab structures
4. Limited to c3725 router platform with specific network modules

## 11. Risks

### Risk 1: API Version Compatibility
**Risk**: Future EVE-NG API versions might change the interface indexing
**Impact**: High
**Mitigation**: Document the dependency, make mapping configurable, implement version detection

### Risk 2: Hardware Template Variations
**Risk**: Other Dynamips node types or network modules might use different indexing schemes
**Impact**: Medium
**Mitigation**: Clearly scope the fix to c3725 with NM-1FE-TX, provide template detection

### Risk 3: Network Connectivity Issues
**Risk**: SSH or API connectivity problems during execution
**Impact**: Medium
**Mitigation**: Implement robust error handling, connection retries, and fallback options

## 12. Success Metrics

### Primary Metrics
- 100% of connections defined in TOPOLOGY_CONNECTIONS are successfully established
- 100% of routers are successfully connected to management network
- Zero "Cannot link node (20034)" errors related to interface linking

### Secondary Metrics
- Script logs show successful verification for all established links
- Visual inspection of lab in EVE-NG UI confirms all connections are present
- Console access works for all deployed routers

### Quality Metrics
- Script execution time remains under 5 minutes for full topology
- Error messages provide actionable troubleshooting information
- Documentation completeness score > 95%

## 13. Acceptance Criteria

1. **Interface Mapping**: All slotted interfaces (f1/0, f2/0) connect successfully
2. **Error Elimination**: No "Cannot link node" errors during normal execution
3. **Verification Accuracy**: Connection verification reports match actual lab state
4. **Management Access**: All routers accessible via management network
5. **Documentation**: Complete PRD, task list, activity tracker, and README
6. **SSH Integration**: Working SSH access for troubleshooting
7. **Code Quality**: Well-commented, maintainable code structure

## 14. Out of Scope

1. Support for router platforms other than c3725
2. Network modules other than NM-1FE-TX
3. EVE-NG versions prior to 6.2.0
4. Automated router configuration beyond interface connectivity
5. Integration with external network management systems
6. Multi-lab or distributed topologies

## 15. Dependencies

### Internal Dependencies
- Existing EVE-NG infrastructure
- c3725 router images
- NM-1FE-TX module support

### External Dependencies
- Python 3.6+ runtime environment
- Network connectivity to EVE-NG host
- Required Python packages (requests, paramiko, etc.)

## 16. Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1: Analysis & Design | 2 days | Interface mapping confirmation, design document |
| Phase 2: Implementation | 3 days | Enhanced script with correct mapping |
| Phase 3: Testing & Validation | 2 days | Full regression testing, validation |
| Phase 4: Documentation | 1 day | Complete documentation package |
| **Total** | **8 days** | **Production-ready solution** |

## 17. Approval

This PRD has been reviewed and approved by:

- [ ] Technical Lead
- [ ] Network Engineering Team
- [ ] Quality Assurance Team
- [ ] Project Manager

---

**Document Classification**: Internal Use  
**Next Review Date**: 2025-04-16  
**Related Documents**: TASK_LIST.md, ACTIVITY_TRACKER.md, CHANGELOG.md 