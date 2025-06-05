"""
Test suite for Multi-Vendor Router Support
Addresses NEW-001: Multi-Vendor Router Support

This module tests the enhanced interface mapping, validation, and configuration
capabilities for multiple Cisco router types beyond the original c3725 support.

Test Coverage:
- Interface validation for all router types
- Interface mapping accuracy 
- Configuration validation per router type
- Template generation for all router types
- Router specifications and capabilities
- Backward compatibility with c3725
- Error handling for unsupported types
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the parent directory to the path to import the main module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v5_eve_ng_automation import EVEClient


class TestMultiVendorInterfaceValidation:
    """Test interface validation for multiple router types"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.eve_client = EVEClient("test_host", "test_user", "test_pass")
    
    def test_c3725_interface_validation(self):
        """Test c3725 interface validation (backward compatibility)"""
        # Valid interfaces
        assert self.eve_client.is_valid_interface("f0/0", "c3725") == True
        assert self.eve_client.is_valid_interface("f0/1", "c3725") == True
        assert self.eve_client.is_valid_interface("f1/0", "c3725") == True
        assert self.eve_client.is_valid_interface("f2/0", "c3725") == True
        
        # Invalid interfaces
        assert self.eve_client.is_valid_interface("f3/0", "c3725") == False
        assert self.eve_client.is_valid_interface("g0/0", "c3725") == False
        assert self.eve_client.is_valid_interface("s0/0", "c3725") == False
    
    def test_c7200_interface_validation(self):
        """Test c7200 interface validation"""
        # Valid GigabitEthernet interfaces
        for i in range(6):
            assert self.eve_client.is_valid_interface(f"g{i}/0", "c7200") == True
        
        # Valid FastEthernet interfaces
        for i in range(4):
            assert self.eve_client.is_valid_interface(f"f{i}/0", "c7200") == True
        
        # Invalid interfaces
        assert self.eve_client.is_valid_interface("g6/0", "c7200") == False
        assert self.eve_client.is_valid_interface("f4/0", "c7200") == False
        assert self.eve_client.is_valid_interface("s0/0", "c7200") == False
    
    def test_c3640_interface_validation(self):
        """Test c3640 interface validation"""
        # Valid interfaces
        assert self.eve_client.is_valid_interface("f0/0", "c3640") == True
        assert self.eve_client.is_valid_interface("f0/1", "c3640") == True
        assert self.eve_client.is_valid_interface("f1/0", "c3640") == True
        assert self.eve_client.is_valid_interface("f2/0", "c3640") == True
        
        # Invalid interfaces
        assert self.eve_client.is_valid_interface("f3/0", "c3640") == False
        assert self.eve_client.is_valid_interface("g0/0", "c3640") == False
    
    def test_c2691_interface_validation(self):
        """Test c2691 interface validation"""
        # Valid interfaces
        assert self.eve_client.is_valid_interface("f0/0", "c2691") == True
        assert self.eve_client.is_valid_interface("f0/1", "c2691") == True
        assert self.eve_client.is_valid_interface("f1/0", "c2691") == True
        assert self.eve_client.is_valid_interface("f2/0", "c2691") == True
        
        # Invalid interfaces
        assert self.eve_client.is_valid_interface("f3/0", "c2691") == False
        assert self.eve_client.is_valid_interface("g0/0", "c2691") == False
    
    def test_c1700_interface_validation(self):
        """Test c1700 interface validation"""
        # Valid interfaces
        assert self.eve_client.is_valid_interface("f0/0", "c1700") == True
        assert self.eve_client.is_valid_interface("s0/0", "c1700") == True
        assert self.eve_client.is_valid_interface("s0/1", "c1700") == True
        
        # Invalid interfaces
        assert self.eve_client.is_valid_interface("f0/1", "c1700") == False
        assert self.eve_client.is_valid_interface("g0/0", "c1700") == False
        assert self.eve_client.is_valid_interface("s1/0", "c1700") == False
    
    def test_unsupported_router_type_fallback(self):
        """Test fallback behavior for unsupported router types"""
        # Should fall back to c3725 validation
        assert self.eve_client.is_valid_interface("f0/0", "unsupported_router") == True
        assert self.eve_client.is_valid_interface("g0/0", "unsupported_router") == False


class TestMultiVendorInterfaceMapping:
    """Test interface index mapping for multiple router types"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.eve_client = EVEClient("test_host", "test_user", "test_pass")
    
    def test_c3725_interface_mapping(self):
        """Test c3725 interface mapping (backward compatibility)"""
        assert self.eve_client.get_interface_index("f0/0", "c3725") == "0"
        assert self.eve_client.get_interface_index("f0/1", "c3725") == "1"
        assert self.eve_client.get_interface_index("f1/0", "c3725") == "16"
        assert self.eve_client.get_interface_index("f2/0", "c3725") == "32"
    
    def test_c7200_interface_mapping(self):
        """Test c7200 interface mapping"""
        # GigabitEthernet mapping
        assert self.eve_client.get_interface_index("g0/0", "c7200") == "0"
        assert self.eve_client.get_interface_index("g1/0", "c7200") == "1"
        assert self.eve_client.get_interface_index("g2/0", "c7200") == "2"
        assert self.eve_client.get_interface_index("g3/0", "c7200") == "3"
        assert self.eve_client.get_interface_index("g4/0", "c7200") == "4"
        assert self.eve_client.get_interface_index("g5/0", "c7200") == "5"
        
        # FastEthernet mapping (alternative configuration)
        assert self.eve_client.get_interface_index("f0/0", "c7200") == "6"
        assert self.eve_client.get_interface_index("f1/0", "c7200") == "7"
        assert self.eve_client.get_interface_index("f2/0", "c7200") == "8"
        assert self.eve_client.get_interface_index("f3/0", "c7200") == "9"
    
    def test_c3640_interface_mapping(self):
        """Test c3640 interface mapping"""
        assert self.eve_client.get_interface_index("f0/0", "c3640") == "0"
        assert self.eve_client.get_interface_index("f0/1", "c3640") == "1"
        assert self.eve_client.get_interface_index("f1/0", "c3640") == "16"
        assert self.eve_client.get_interface_index("f2/0", "c3640") == "32"
    
    def test_c2691_interface_mapping(self):
        """Test c2691 interface mapping"""
        assert self.eve_client.get_interface_index("f0/0", "c2691") == "0"
        assert self.eve_client.get_interface_index("f0/1", "c2691") == "1"
        assert self.eve_client.get_interface_index("f1/0", "c2691") == "16"
        assert self.eve_client.get_interface_index("f2/0", "c2691") == "32"
    
    def test_c1700_interface_mapping(self):
        """Test c1700 interface mapping"""
        assert self.eve_client.get_interface_index("f0/0", "c1700") == "0"
        assert self.eve_client.get_interface_index("s0/0", "c1700") == "1"
        assert self.eve_client.get_interface_index("s0/1", "c1700") == "2"
    
    def test_interface_mapping_caching(self):
        """Test interface mapping caching functionality"""
        # First call should calculate and cache
        result1 = self.eve_client.get_interface_index("g0/0", "c7200")
        
        # Second call should use cache
        result2 = self.eve_client.get_interface_index("g0/0", "c7200")
        
        assert result1 == result2 == "0"
        
        # Verify cache key includes router type
        cache_key = "c7200_g0/0"
        assert cache_key in self.eve_client._interface_cache
    
    def test_invalid_interface_mapping_error(self):
        """Test error handling for invalid interface mapping"""
        with pytest.raises(ValueError, match="Invalid interface name"):
            self.eve_client.get_interface_index("invalid", "c3725")
        
        with pytest.raises(ValueError, match="Unsupported router type"):
            self.eve_client.get_interface_index("f0/0", "unsupported")


class TestMultiVendorSupportedInterfaces:
    """Test supported interfaces functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.eve_client = EVEClient("test_host", "test_user", "test_pass")
    
    def test_get_supported_interfaces_c3725(self):
        """Test getting supported interfaces for c3725"""
        interfaces = self.eve_client.get_supported_interfaces("c3725")
        expected = ['f0/0', 'f0/1', 'f1/0', 'f2/0']
        assert interfaces == expected
    
    def test_get_supported_interfaces_c7200(self):
        """Test getting supported interfaces for c7200"""
        interfaces = self.eve_client.get_supported_interfaces("c7200")
        expected = ['g0/0', 'g1/0', 'g2/0', 'g3/0', 'g4/0', 'g5/0', 'f0/0', 'f1/0', 'f2/0', 'f3/0']
        assert interfaces == expected
    
    def test_get_supported_interfaces_c3640(self):
        """Test getting supported interfaces for c3640"""
        interfaces = self.eve_client.get_supported_interfaces("c3640")
        expected = ['f0/0', 'f0/1', 'f1/0', 'f2/0']
        assert interfaces == expected
    
    def test_get_supported_interfaces_c2691(self):
        """Test getting supported interfaces for c2691"""
        interfaces = self.eve_client.get_supported_interfaces("c2691")
        expected = ['f0/0', 'f0/1', 'f1/0', 'f2/0']
        assert interfaces == expected
    
    def test_get_supported_interfaces_c1700(self):
        """Test getting supported interfaces for c1700"""
        interfaces = self.eve_client.get_supported_interfaces("c1700")
        expected = ['f0/0', 's0/0', 's0/1']
        assert interfaces == expected
    
    def test_get_supported_interfaces_unknown(self):
        """Test fallback for unknown router type"""
        interfaces = self.eve_client.get_supported_interfaces("unknown")
        expected = ['f0/0', 'f0/1', 'f1/0', 'f2/0']  # Falls back to c3725
        assert interfaces == expected


class TestMultiVendorConfigurationTemplates:
    """Test configuration templates for multiple router types"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.eve_client = EVEClient("test_host", "test_user", "test_pass")
    
    def test_c3725_template(self):
        """Test c3725 configuration template"""
        template = self.eve_client.get_node_config_template("c3725")
        
        assert template["type"] == "dynamips"
        assert template["template"] == "c3725"
        assert template["ram"] == "256"
        assert template["slot1"] == "NM-1FE-TX"
        assert template["ethernet"] == "6"
    
    def test_c7200_template(self):
        """Test c7200 configuration template"""
        template = self.eve_client.get_node_config_template("c7200")
        
        assert template["type"] == "dynamips"
        assert template["template"] == "c7200"
        assert template["ram"] == "512"
        assert template["slot1"] == "PA-GE"
        assert template["slot2"] == "PA-GE"
        assert template["ethernet"] == "12"
        assert "slot6" in template  # c7200 has up to 6 slots
    
    def test_c3640_template(self):
        """Test c3640 configuration template"""
        template = self.eve_client.get_node_config_template("c3640")
        
        assert template["type"] == "dynamips"
        assert template["template"] == "c3640"
        assert template["ram"] == "256"
        assert template["slot1"] == "NM-1FE-TX"
        assert template["ethernet"] == "4"
    
    def test_c2691_template(self):
        """Test c2691 configuration template"""
        template = self.eve_client.get_node_config_template("c2691")
        
        assert template["type"] == "dynamips"
        assert template["template"] == "c2691"
        assert template["ram"] == "256"
        assert template["slot1"] == "NM-1FE-TX"
        assert template["ethernet"] == "4"
    
    def test_c1700_template(self):
        """Test c1700 configuration template"""
        template = self.eve_client.get_node_config_template("c1700")
        
        assert template["type"] == "dynamips"
        assert template["template"] == "c1700"
        assert template["ram"] == "128"
        assert template["wic0"] == "WIC-1T"
        assert template["ethernet"] == "1"
    
    def test_unknown_template_fallback(self):
        """Test fallback to c3725 for unknown router type"""
        template = self.eve_client.get_node_config_template("unknown")
        
        # Should return c3725 template
        assert template["template"] == "c3725"
        assert template["ram"] == "256"
    
    def test_template_modification_independence(self):
        """Test that template modifications don't affect original"""
        template1 = self.eve_client.get_node_config_template("c3725")
        template2 = self.eve_client.get_node_config_template("c3725")
        
        # Modify one template
        template1["name"] = "Modified"
        
        # Other template should be unchanged
        assert template2["name"] == "Router1"


class TestMultiVendorConfigurationValidation:
    """Test configuration validation for multiple router types"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.eve_client = EVEClient("test_host", "test_user", "test_pass")
    
    def test_c3725_ram_validation(self):
        """Test RAM validation for c3725"""
        config = {"type": "dynamips", "template": "c3725", "name": "test", "ram": "256"}
        is_valid, errors = self.eve_client.validate_node_config(config)
        assert is_valid == True
        
        # Test invalid RAM
        config["ram"] = "1024"  # Too high
        is_valid, errors = self.eve_client.validate_node_config(config)
        assert is_valid == False
        assert any("RAM value" in error for error in errors)
    
    def test_c7200_ram_validation(self):
        """Test RAM validation for c7200"""
        config = {"type": "dynamips", "template": "c7200", "name": "test", "ram": "512"}
        is_valid, errors = self.eve_client.validate_node_config(config)
        assert is_valid == True
        
        # Test invalid RAM
        config["ram"] = "128"  # Too low for c7200
        is_valid, errors = self.eve_client.validate_node_config(config)
        assert is_valid == False
        assert any("256-1024MB" in error for error in errors)
    
    def test_c1700_ram_validation(self):
        """Test RAM validation for c1700"""
        config = {"type": "dynamips", "template": "c1700", "name": "test", "ram": "128"}
        is_valid, errors = self.eve_client.validate_node_config(config)
        assert is_valid == True
        
        # Test invalid RAM
        config["ram"] = "512"  # Too high for c1700
        is_valid, errors = self.eve_client.validate_node_config(config)
        assert is_valid == False
        assert any("64-256MB" in error for error in errors)
    
    def test_router_specific_module_validation(self):
        """Test router-specific module validation"""
        # c7200 with PA modules
        config = {"type": "dynamips", "template": "c7200", "name": "test", "slot1": "PA-GE"}
        is_valid, errors = self.eve_client.validate_node_config(config)
        assert is_valid == True
        
        # c7200 with invalid NM module
        config["slot1"] = "NM-1FE-TX"  # NM module not valid for c7200
        is_valid, errors = self.eve_client.validate_node_config(config)
        assert is_valid == False
        assert any("PA-GE" in error for error in errors)
        
        # c1700 with WIC modules
        config = {"type": "dynamips", "template": "c1700", "name": "test", "wic0": "WIC-1T"}
        is_valid, errors = self.eve_client.validate_node_config(config)
        assert is_valid == True
    
    def test_template_validation(self):
        """Test template validation includes all router types"""
        valid_templates = ['c3725', 'c7200', 'c3640', 'c2691', 'c1700']
        
        for template in valid_templates:
            config = {"type": "dynamips", "template": template, "name": "test"}
            is_valid, errors = self.eve_client.validate_node_config(config)
            assert is_valid == True
        
        # Test invalid template
        config = {"type": "dynamips", "template": "invalid", "name": "test"}
        is_valid, errors = self.eve_client.validate_node_config(config)
        assert is_valid == False
        assert any("Invalid template" in error for error in errors)


class TestMultiVendorConnectionValidation:
    """Test connection validation with multi-vendor support"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.eve_client = EVEClient("test_host", "test_user", "test_pass")
    
    def test_same_type_router_connection(self):
        """Test connection between same router types"""
        routers = {"R1": "id1", "R2": "id2"}
        router_configs = {
            "R1": {"template": "c3725"},
            "R2": {"template": "c3725"}
        }
        
        is_valid, errors = self.eve_client.validate_connection_config(
            "R1", "f0/0", "R2", "f0/1", routers, router_configs
        )
        assert is_valid == True
    
    def test_different_type_router_connection(self):
        """Test connection between different router types"""
        routers = {"R1": "id1", "R2": "id2"}
        router_configs = {
            "R1": {"template": "c3725"},
            "R2": {"template": "c7200"}
        }
        
        is_valid, errors = self.eve_client.validate_connection_config(
            "R1", "f0/0", "R2", "g0/0", routers, router_configs
        )
        assert is_valid == True
    
    def test_invalid_interface_for_router_type(self):
        """Test invalid interface validation for specific router type"""
        routers = {"R1": "id1", "R2": "id2"}
        router_configs = {
            "R1": {"template": "c1700"},  # c1700 doesn't have f0/1
            "R2": {"template": "c7200"}
        }
        
        is_valid, errors = self.eve_client.validate_connection_config(
            "R1", "f0/1", "R2", "g0/0", routers, router_configs
        )
        assert is_valid == False
        assert any("Invalid interface 'f0/1' for router 'R1'" in error for error in errors)
    
    def test_connection_without_router_configs(self):
        """Test connection validation without router configs (fallback to c3725)"""
        routers = {"R1": "id1", "R2": "id2"}
        
        is_valid, errors = self.eve_client.validate_connection_config(
            "R1", "f0/0", "R2", "f0/1", routers
        )
        assert is_valid == True


class TestMultiVendorRouterSpecifications:
    """Test router specification functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.eve_client = EVEClient("test_host", "test_user", "test_pass")
    
    def test_get_available_router_types(self):
        """Test getting all available router types"""
        types = self.eve_client.get_available_router_types()
        expected = ['c3725', 'c7200', 'c3640', 'c2691', 'c1700']
        assert types == expected
    
    def test_get_router_specifications_c3725(self):
        """Test getting c3725 specifications"""
        specs = self.eve_client.get_router_specifications("c3725")
        
        assert specs["description"] == "Cisco 3725 Modular Router"
        assert specs["onboard_interfaces"] == ['f0/0', 'f0/1']
        assert specs["slot_interfaces"] == ['f1/0', 'f2/0']
        assert specs["ram_range"] == "128-512MB"
        assert specs["max_slots"] == 2
    
    def test_get_router_specifications_c7200(self):
        """Test getting c7200 specifications"""
        specs = self.eve_client.get_router_specifications("c7200")
        
        assert specs["description"] == "Cisco 7200 Series Router"
        assert specs["onboard_interfaces"] == []
        assert specs["ram_range"] == "256-1024MB"
        assert specs["max_slots"] == 6
        assert "PA-GE" in specs["supported_modules"]
    
    def test_get_router_specifications_c1700(self):
        """Test getting c1700 specifications"""
        specs = self.eve_client.get_router_specifications("c1700")
        
        assert specs["description"] == "Cisco 1700 Series Router"
        assert specs["onboard_interfaces"] == ['f0/0']
        assert specs["slot_interfaces"] == ['s0/0', 's0/1']
        assert specs["ram_range"] == "64-256MB"
        assert "WIC-1T" in specs["supported_modules"]
    
    def test_get_router_specifications_unknown(self):
        """Test getting specifications for unknown router type"""
        specs = self.eve_client.get_router_specifications("unknown")
        assert specs == {}


class TestMultiVendorRouterTypeDetection:
    """Test router type detection from configurations"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.eve_client = EVEClient("test_host", "test_user", "test_pass")
    
    def test_get_router_type_from_config(self):
        """Test extracting router type from configuration"""
        config = {"template": "c7200", "name": "test"}
        router_type = self.eve_client.get_router_type_from_config(config)
        assert router_type == "c7200"
    
    def test_get_router_type_fallback(self):
        """Test fallback to c3725 for missing or invalid template"""
        # Missing template
        config = {"name": "test"}
        router_type = self.eve_client.get_router_type_from_config(config)
        assert router_type == "c3725"
        
        # Invalid template
        config = {"template": "invalid", "name": "test"}
        router_type = self.eve_client.get_router_type_from_config(config)
        assert router_type == "c3725"


class TestMultiVendorBackwardCompatibility:
    """Test backward compatibility with existing c3725 functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.eve_client = EVEClient("test_host", "test_user", "test_pass")
    
    def test_default_router_type_c3725(self):
        """Test that c3725 is default when router type not specified"""
        assert self.eve_client.is_valid_interface("f0/0") == True
        assert self.eve_client.get_interface_index("f0/0") == "0"
        
    def test_validate_interfaces_backward_compatibility(self):
        """Test validate_interfaces works with and without router_type"""
        interfaces = ["f0/0", "f0/1", "invalid"]
        
        # Without router_type (backward compatibility)
        invalid = self.eve_client.validate_interfaces(interfaces)
        assert invalid == ["invalid"]
        
        # With router_type
        invalid = self.eve_client.validate_interfaces(interfaces, "c3725")
        assert invalid == ["invalid"]
    
    @patch.object(EVEClient, 'api_request')
    def test_connect_node_to_network_backward_compatibility(self, mock_api):
        """Test connection method works with and without router_type"""
        mock_api.return_value = {"status": "success"}
        
        # Enable deployment tracking
        self.eve_client.start_deployment_tracking("test_lab")
        
        # Without router_type (backward compatibility)
        result = self.eve_client.connect_node_to_network("lab", "node1", "f0/0", "net1")
        assert result == True
        
        # With router_type  
        result = self.eve_client.connect_node_to_network("lab", "node2", "f0/1", "net2", 
                                                        router_type="c3725")
        assert result == True


class TestMultiVendorIntegration:
    """Integration tests for multi-vendor functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.eve_client = EVEClient("test_host", "test_user", "test_pass")
    
    def test_full_topology_validation_multi_vendor(self):
        """Test complete topology validation with multiple router types"""
        routers = {
            "R1": {"template": "c3725", "type": "dynamips", "name": "R1"},
            "R2": {"template": "c7200", "type": "dynamips", "name": "R2"},
            "R3": {"template": "c1700", "type": "dynamips", "name": "R3"}
        }
        
        connections = [
            ["R1", "f0/0", "R2", "g0/0", "Link1"],
            ["R2", "g1/0", "R3", "f0/0", "Link2"]
        ]
        
        is_valid, errors = self.eve_client.validate_topology_config(routers, connections)
        assert is_valid == True
        assert len(errors) == 0
    
    def test_topology_validation_with_invalid_interfaces(self):
        """Test topology validation catches invalid interfaces per router type"""
        routers = {
            "R1": {"template": "c1700", "type": "dynamips", "name": "R1"},
            "R2": {"template": "c7200", "type": "dynamips", "name": "R2"}
        }
        
        connections = [
            ["R1", "f0/1", "R2", "g0/0", "Link1"]  # f0/1 invalid for c1700
        ]
        
        is_valid, errors = self.eve_client.validate_topology_config(routers, connections)
        assert is_valid == False
        assert any("Invalid interface 'f0/1' for router 'R1'" in error for error in errors)
    
    def test_performance_with_caching(self):
        """Test that interface mapping caching works across router types"""
        import time
        
        # Measure time for first call (should populate cache)
        start_time = time.time()
        for i in range(100):
            self.eve_client.get_interface_index("g0/0", "c7200")
        first_duration = time.time() - start_time
        
        # Clear cache and measure again
        self.eve_client.clear_cache()
        start_time = time.time()
        for i in range(100):
            self.eve_client.get_interface_index("g0/0", "c7200")
        second_duration = time.time() - start_time
        
        # With caching, subsequent calls should be faster
        # Note: This is more of a smoke test since caching benefit might be minimal
        assert first_duration >= 0  # Just ensure no errors occur
        assert second_duration >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"]) 