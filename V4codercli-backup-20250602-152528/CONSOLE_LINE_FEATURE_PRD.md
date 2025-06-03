# Console Line Collection Feature - Product Requirements Document (PRD)

## 📋 **Project Overview**

**Feature Name**: Console Line Configuration Collector  
**Project Code**: V4CLI-CONSOLE-v1.0  
**Created**: 2025-05-31  
**Status**: Planning Phase  
**Priority**: High  

### **Objective**
Add a new data collection layer to V4codercli that extracts console line configurations from Cisco IOS routers with NM4 console cards, gathering both "show line" output and individual line configurations.

## 🎯 **Business Requirements**

### **Primary Goals**
1. **Console Line Discovery**: Collect comprehensive "show line" information
2. **Configuration Extraction**: Extract running configuration for each console line
3. **Data Persistence**: Store results in both JSON and text formats
4. **Integration**: Seamlessly integrate with existing V4codercli architecture
5. **Cross-Platform**: Maintain compatibility across Windows/Linux/macOS

### **Target Devices**
- Cisco IOS routers with NM4 console cards
- Line numbering: x/y/z format where:
  - x: 0 or 1 (slot)
  - y: 0 or 1 (subslot)  
  - z: 0 to 22 (port number)

## 🔧 **Technical Requirements**

### **Data Collection Specifications**

#### **Primary Commands**
1. `show line` - Discover all available console lines
2. `show run | section line x/y/z` - Extract configuration for each line

#### **Output Format Requirements**
- **JSON File**: Structured data with line details and configurations
- **Text File**: Human-readable format for each router
- **File Naming**: `{device_ip}_console_lines.{json|txt}`

#### **Data Structure**
```json
{
  "device": "172.16.39.100",
  "timestamp": "2025-05-31T23:00:00Z",
  "show_line_output": "...",
  "console_lines": {
    "0/0/0": {
      "line_type": "con",
      "status": "available",
      "configuration": "..."
    },
    "0/0/1": {
      "line_type": "aux",
      "status": "available", 
      "configuration": "..."
    }
  },
  "summary": {
    "total_lines": 23,
    "configured_lines": 15,
    "success_rate": "100%"
  }
}
```

## 📝 **Technical Architecture**

### **Integration Points**
1. **New Layer**: Add "console" as 8th data collection layer
2. **Collector Class**: `ConsoleLineCollector` inheriting from `BaseCollector`
3. **CLI Integration**: Extend existing CLI commands to support console layer
4. **Menu Integration**: Add console collection to interactive startup manager

### **Dependencies**
- **Existing**: Nornir, Netmiko, pyATS/Genie, NAPALM, Paramiko
- **Core Modules**: BaseCollector, ConnectionManager, TaskExecutor
- **No New Dependencies**: Reuse existing infrastructure

## 📊 **Implementation Plan**

### **Phase 1: Core Collector Development**
- Create `console_line_collector.py`
- Implement line discovery logic
- Add configuration extraction methods
- Create data processing functions

### **Phase 2: Integration & Testing**
- Update main CLI script
- Add console layer to layer list
- Update interactive startup manager
- Create unit tests

### **Phase 3: Documentation & Deployment**
- Update all documentation
- Add usage examples
- Create troubleshooting guides
- Test across all platforms

## 🎛️ **User Interface Requirements**

### **CLI Command Extensions**
```bash
# Include console layer in collections
python3 rr4-complete-enchanced-v4-cli.py collect-all --layers health,interfaces,console

# Console-only collection
python3 rr4-complete-enchanced-v4-cli.py collect-all --layers console

# Interactive menu option
python3 start_rr4_cli.py
# Select option 3 (Full Collection) - now includes console layer
```

### **Output Requirements**
- Console data included in all collection reports
- Separate console-specific summaries
- Error handling for unsupported devices
- Progress indication during collection

## 📈 **Success Criteria**

### **Functional Requirements**
- ✅ Successfully collect "show line" from all devices
- ✅ Extract configuration for each available line
- ✅ Generate JSON and text output files
- ✅ 100% compatibility with existing features
- ✅ Cross-platform functionality

### **Performance Requirements**
- Collection time: < 2 minutes for 8 devices
- Memory usage: < 100MB additional
- Error rate: < 5% for supported devices
- Data accuracy: 100% for collected information

### **Quality Requirements**
- Code coverage: > 90%
- Documentation: Complete with examples
- Error handling: Graceful failures
- Logging: Comprehensive debugging info

## 🚨 **Risk Assessment**

### **Technical Risks**
| Risk | Impact | Mitigation |
|------|---------|------------|
| **Device Compatibility** | Medium | Device-specific command validation |
| **Line Discovery Failures** | Low | Fallback to manual line specification |
| **Configuration Parsing** | Medium | Robust regex and error handling |
| **Integration Complexity** | Low | Reuse existing architecture |

### **Business Risks**
| Risk | Impact | Mitigation |
|------|---------|------------|
| **Feature Creep** | Low | Strict scope adherence |
| **Timeline Delays** | Medium | Phased implementation |
| **Resource Constraints** | Low | Reuse existing codebase |

## 📅 **Timeline**

### **Development Schedule**
| Phase | Duration | Deliverables |
|-------|----------|--------------|
| **Planning** | 1 day | PRD, Task List, Architecture |
| **Development** | 2 days | Core collector, Integration |
| **Testing** | 1 day | Unit tests, Integration tests |
| **Documentation** | 1 day | User guides, Examples |
| **Deployment** | 0.5 days | Final testing, Git commit |

**Total Duration**: 5.5 days

## 📋 **Acceptance Criteria**

### **Must Have**
- [ ] Console line collector implemented
- [ ] JSON and text output generation
- [ ] Integration with existing CLI
- [ ] Cross-platform compatibility
- [ ] Comprehensive error handling

### **Should Have**
- [ ] Interactive menu integration
- [ ] Progress reporting
- [ ] Detailed logging
- [ ] Performance optimization
- [ ] Documentation updates

### **Could Have**
- [ ] Console line filtering options
- [ ] Custom output formats
- [ ] Historical comparison
- [ ] Advanced analytics

## 📚 **Documentation Requirements**

### **Technical Documentation**
- Code documentation (docstrings)
- Architecture diagrams
- API reference
- Configuration guide

### **User Documentation**
- Usage examples
- Troubleshooting guide
- Best practices
- FAQ section

---

**Document Version**: 1.0  
**Last Updated**: 2025-05-31  
**Next Review**: After implementation completion 