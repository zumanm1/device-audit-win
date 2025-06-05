# Task List - V5evscriptcli EVE-NG Automation Enhancement

## Document Information
- **Project**: V5evscriptcli - EVE-NG MPLS L3VPN Automation Enhancement
- **Version**: 1.0
- **Date**: 2025-01-16
- **Last Updated**: 2025-01-16

## Overview
This document provides a comprehensive breakdown of all tasks required to enhance the EVE-NG automation script with correct interface mapping for c3725 routers.

## Task Priority Legend
- **P0**: Critical (Must be done for the fix to be effective)
- **P1**: High (Important for usability and robustness)
- **P2**: Medium (Nice to have)
- **P3**: Low (Future enhancement)

## Status Legend
- **To Do**: Not started
- **In Progress**: Currently being worked on
- **Testing**: Implementation complete, under testing
- **Done**: Completed and verified
- **Blocked**: Waiting for dependency or external factor

---

## Phase 1: Core Analysis & Design

### T1: Analyze & Confirm EVE-NG Interface Indexing for c3725+NM-1FE-TX
**Priority**: P0 | **Status**: To Do | **Est. Effort**: 0.5 day | **Assigned**: TBD

#### Subtasks:
- **T1.1**: Review existing script error logs
  - Analyze "Interfaces Data" output during failed verifications
  - Document the structure EVE-NG returns
  - Identify the pattern: `'ethernet': {'0': {'name': 'fa0/0'}, '1': {'name': 'fa0/1'}, '16': {'name': 'fa1/0'}, '32': {'name': 'fa2/0'}}`

- **T1.2**: Validate interface mapping via SSH (Optional but Recommended)
  - SSH to EVE-NG: `ssh root@172.16.39.128` (password: eve)
  - Manually create c3725 node with NM-1FE-TX in slots 1 and 2
  - Identify lab ID and node ID from EVE-NG UI

- **T1.3**: Direct API verification
  - Use EVE-NG CLI wrapper to query interfaces
  - Command structure: `/opt/unetlab/wrappers/unl_wrapper -a getnodeinterfaces -F /opt/unetlab/labs/<lab_uuid>/<lab_file.unl> -N <node_id>`
  - Document exact JSON structure and indices

- **T1.4**: Document confirmed mapping
  - f0/0 -> API index '0'
  - f0/1 -> API index '1'
  - f1/0 -> API index '16' (NM-1FE-TX in slot 1)
  - f2/0 -> API index '32' (NM-1FE-TX in slot 2)

**Dependencies**: None  
**Deliverables**: Interface mapping documentation, API structure analysis

---

### T2: Design Enhanced Script Architecture
**Priority**: P0 | **Status**: To Do | **Est. Effort**: 0.5 day | **Assigned**: TBD

#### Subtasks:
- **T2.1**: Review current script structure
  - Analyze existing `connect_node_to_network` function
  - Identify interface mapping logic location
  - Document current approach and limitations

- **T2.2**: Design improved interface mapping
  - Create configurable interface mapping dictionary
  - Design error handling for unknown interfaces
  - Plan logging improvements for troubleshooting

- **T2.3**: Plan SSH integration
  - Design SSH helper functions for troubleshooting
  - Plan direct EVE-NG API access capabilities
  - Create fallback verification methods

**Dependencies**: T1  
**Deliverables**: Enhanced script design document, architecture diagram

---

## Phase 2: Core Implementation

### T3: Update Interface Mapping Logic
**Priority**: P0 | **Status**: To Do | **Est. Effort**: 1 day | **Assigned**: TBD

#### Subtasks:
- **T3.1**: Locate and modify `connect_node_to_network` function
  - Find current interface_mapping dictionary
  - Replace problematic mapping: `{'f0/0': '0', 'f0/1': '1', 'f1/0': '2', 'f1/1': '3', 'f2/0': '4', 'f2/1': '5'}`
  - Implement correct mapping: `{'f0/0': '0', 'f0/1': '1', 'f1/0': '16', 'f2/0': '32'}`

- **T3.2**: Enhance interface mapping logic
  - Add validation for interface names
  - Implement error handling for unmapped interfaces
  - Add debug logging for interface resolution

- **T3.3**: Update payload construction
  - Ensure correct interface_key derivation from mapping
  - Verify API request payload format
  - Add request/response logging

- **T3.4**: Review dependent functions
  - Check if other functions rely on old mapping
  - Update any hardcoded interface references
  - Ensure consistency across the script

**Dependencies**: T1, T2  
**Deliverables**: Updated script with correct interface mapping

---

### T4: Implement SSH Troubleshooting Capabilities
**Priority**: P1 | **Status**: To Do | **Est. Effort**: 0.5 day | **Assigned**: TBD

#### Subtasks:
- **T4.1**: Add SSH client functionality
  - Import paramiko or use subprocess for SSH
  - Create SSH connection helper functions
  - Implement secure credential handling

- **T4.2**: Create direct EVE-NG API access functions
  - SSH-based interface query functions
  - Direct CLI wrapper access methods
  - API response comparison utilities

- **T4.3**: Add troubleshooting commands
  - Function to check node interfaces via SSH
  - Network status verification commands
  - Lab state validation methods

**Dependencies**: T3  
**Deliverables**: SSH integration module, troubleshooting utilities

---

## Phase 3: Testing & Validation

### T5: Test Core P2P Link Creation
**Priority**: P0 | **Status**: To Do | **Est. Effort**: 1 day | **Assigned**: TBD

#### Subtasks:
- **T5.1**: Prepare test environment
  - Ensure clean EVE-NG lab environment
  - Verify c3725 template availability
  - Check NM-1FE-TX module support

- **T5.2**: Test critical connections
  - Focus on f1/0 interface connections:
    - CE-4(f1/0) <-> PE1(f1/0)
    - P(f1/0) <-> RR1(f1/0)
  - Verify connection success in logs
  - Visual inspection in EVE-NG UI

- **T5.3**: Validate error elimination
  - Check for absence of "Cannot link node (20034)" errors
  - Verify all connections are established
  - Test connection persistence

- **T5.4**: Performance testing
  - Measure script execution time
  - Test with multiple lab deployments
  - Verify resource usage

**Dependencies**: T3, T4  
**Deliverables**: Test results, performance metrics

---

### T6: Test Management Network Connectivity
**Priority**: P0 | **Status**: To Do | **Est. Effort**: 0.5 day | **Assigned**: TBD

#### Subtasks:
- **T6.1**: Test management interface connections
  - Focus on f2/0 interfaces (PE1, PE2, P, RR1)
  - Verify management network creation
  - Check all routers connect to management network

- **T6.2**: Validate console access
  - Test telnet console ports
  - Verify port calculations
  - Document access methods

- **T6.3**: Management network verification
  - Visual inspection in EVE-NG UI
  - API-based verification
  - SSH-based validation

**Dependencies**: T3, T4, T5  
**Deliverables**: Management network test results

---

### T7: Enhance Connection Verification Functions
**Priority**: P1 | **Status**: To Do | **Est. Effort**: 0.5 day | **Assigned**: TBD

#### Subtasks:
- **T7.1**: Update `verify_connection` function
  - Analyze JSON structure from EVE-NG API
  - Update parsing logic for `interfaces_data['ethernet'][interface_api_index]['network_id']`
  - Handle different API response formats

- **T7.2**: Improve error handling
  - Add timeout handling for API calls
  - Implement retry mechanisms
  - Enhance error messages

- **T7.3**: Test verification accuracy
  - Compare API responses with actual lab state
  - Test with intentionally failed connections
  - Validate positive and negative cases

**Dependencies**: T5, T6  
**Deliverables**: Enhanced verification functions

---

### T8: Update Final Topology Display
**Priority**: P1 | **Status**: To Do | **Est. Effort**: 0.5 day | **Assigned**: TBD

#### Subtasks:
- **T8.1**: Review `show_final_topology` function
  - Analyze current interface display logic
  - Update to use correct interface mapping
  - Improve connection status reporting

- **T8.2**: Enhance topology summary
  - Add network information display
  - Include interface status details
  - Show management network connections

- **T8.3**: Improve console access information
  - Update port calculation logic
  - Add SSH access instructions
  - Include troubleshooting commands

**Dependencies**: T7  
**Deliverables**: Enhanced topology display function

---

## Phase 4: Comprehensive Testing

### T9: Full Regression Testing
**Priority**: P0 | **Status**: To Do | **Est. Effort**: 1 day | **Assigned**: TBD

#### Subtasks:
- **T9.1**: End-to-end testing
  - Clean lab environment setup
  - Full script execution from start to finish
  - Verify all components work together

- **T9.2**: Comprehensive validation
  - Lab creation verification
  - All 6 routers created successfully
  - All 5 P2P links established
  - All 6 routers connected to management network

- **T9.3**: Error scenario testing
  - Test with missing templates
  - Test with network connectivity issues
  - Test with API timeout scenarios

- **T9.4**: Performance validation
  - Script execution time under 5 minutes
  - Memory usage within acceptable limits
  - API call efficiency

**Dependencies**: T5, T6, T7, T8  
**Deliverables**: Comprehensive test report, performance metrics

---

### T10: SSH Integration Testing
**Priority**: P1 | **Status**: To Do | **Est. Effort**: 0.5 day | **Assigned**: TBD

#### Subtasks:
- **T10.1**: SSH connectivity testing
  - Test SSH connection to 172.16.39.128
  - Verify root/eve credentials
  - Test command execution

- **T10.2**: Direct API verification testing
  - Test SSH-based interface queries
  - Compare with REST API responses
  - Validate data consistency

- **T10.3**: Troubleshooting workflow testing
  - Test manual verification procedures
  - Validate troubleshooting commands
  - Test fallback mechanisms

**Dependencies**: T4, T9  
**Deliverables**: SSH integration test results

---

## Phase 5: Documentation & Finalization

### T11: Update Script Documentation
**Priority**: P1 | **Status**: To Do | **Est. Effort**: 0.5 day | **Assigned**: TBD

#### Subtasks:
- **T11.1**: Code documentation
  - Add comprehensive comments to interface mapping logic
  - Document API response parsing changes
  - Add troubleshooting function documentation

- **T11.2**: Inline help and usage
  - Update script help text
  - Add command-line argument documentation
  - Include configuration examples

- **T11.3**: Error message improvements
  - Make error messages more actionable
  - Add troubleshooting hints
  - Include SSH access suggestions

**Dependencies**: T9, T10  
**Deliverables**: Well-documented script

---

### T12: Complete Project Documentation
**Priority**: P0 | **Status**: To Do | **Est. Effort**: 0.5 day | **Assigned**: TBD

#### Subtasks:
- **T12.1**: Finalize README.md
  - Update with final features and capabilities
  - Add complete usage instructions
  - Include troubleshooting section

- **T12.2**: Update requirements.txt
  - Ensure all dependencies are listed
  - Add version constraints
  - Include optional development dependencies

- **T12.3**: Create CHANGELOG.md
  - Document all changes from v0.1.0 to v0.2.0
  - Include bug fixes and enhancements
  - Add migration notes if needed

**Dependencies**: T11  
**Deliverables**: Complete documentation package

---

### T13: Final Validation & Release Preparation
**Priority**: P0 | **Status**: To Do | **Est. Effort**: 0.5 day | **Assigned**: TBD

#### Subtasks:
- **T13.1**: Code quality review
  - Run code quality tools (flake8, black)
  - Review for security issues
  - Validate error handling

- **T13.2**: Final testing round
  - Fresh environment testing
  - Cross-platform compatibility check
  - Documentation accuracy verification

- **T13.3**: Release preparation
  - Create git tags
  - Prepare release notes
  - Update version numbers

**Dependencies**: T12  
**Deliverables**: Production-ready release

---

## Summary

### Phase Summary
| Phase | Tasks | Total Effort | Critical Path |
|-------|-------|--------------|---------------|
| Phase 1: Analysis & Design | T1, T2 | 1 day | T1 → T2 |
| Phase 2: Implementation | T3, T4 | 1.5 days | T3 → T4 |
| Phase 3: Testing & Validation | T5, T6, T7, T8 | 2.5 days | T5 → T6 → T7 → T8 |
| Phase 4: Comprehensive Testing | T9, T10 | 1.5 days | T9 → T10 |
| Phase 5: Documentation | T11, T12, T13 | 1.5 days | T11 → T12 → T13 |
| **Total** | **13 tasks** | **8 days** | **Linear dependency chain** |

### Risk Mitigation Tasks
- **T1**: Critical for understanding the correct interface mapping
- **T5**: Essential for validating the core fix
- **T9**: Comprehensive validation before release

### Success Criteria
- [ ] All P0 tasks completed successfully
- [ ] Zero "Cannot link node (20034)" errors in testing
- [ ] 100% connection success rate
- [ ] Complete documentation package
- [ ] SSH troubleshooting capabilities working

---

**Next Actions**: Start with T1 (Interface mapping analysis)  
**Key Dependencies**: EVE-NG host access, c3725 templates  
**Review Schedule**: Daily during implementation phases 