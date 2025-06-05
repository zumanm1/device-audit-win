"""
Test suite for configuration validation functionality
Addresses BUG-006: No Configuration Validation
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path to import main script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v5_eve_ng_automation import EVEClient

@pytest.fixture
def eve_client():
    """Create a mock EVE-NG client for testing"""
    return EVEClient("172.16.39.128", "admin", "eve")

@pytest.mark.unit
def test_validate_node_config_valid(eve_client):
    """Test validation of a valid node configuration"""
    valid_config = {
        "type": "dynamips",
        "template": "c3725",
        "name": "Router1",
        "image": "c3725-adventerprisek9-mz.124-15.T14.image",
        "ram": "256",
        "left": "400",
        "top": "200",
        "slot1": "NM-1FE-TX"
    }
    
    is_valid, errors = eve_client.validate_node_config(valid_config)
    
    assert is_valid == True
    assert len(errors) == 0

@pytest.mark.unit
def test_validate_node_config_missing_required_fields(eve_client):
    """Test validation with missing required fields"""
    invalid_config = {
        "template": "c3725",
        "name": "Router1"
        # Missing 'type' field
    }
    
    is_valid, errors = eve_client.validate_node_config(invalid_config)
    
    assert is_valid == False
    assert "Missing required field: type" in errors

@pytest.mark.unit
def test_validate_node_config_invalid_name(eve_client):
    """Test validation with invalid node name"""
    invalid_configs = [
        {"type": "dynamips", "template": "c3725", "name": "Router@1"},  # Invalid character
        {"type": "dynamips", "template": "c3725", "name": "R" * 51},   # Too long
        {"type": "dynamips", "template": "c3725", "name": ""}          # Empty
    ]
    
    for config in invalid_configs:
        is_valid, errors = eve_client.validate_node_config(config)
        assert is_valid == False
        assert len(errors) > 0

@pytest.mark.unit
def test_validate_node_config_invalid_template(eve_client):
    """Test validation with invalid template"""
    invalid_config = {
        "type": "dynamips",
        "template": "invalid_template",
        "name": "Router1"
    }
    
    is_valid, errors = eve_client.validate_node_config(invalid_config)
    
    assert is_valid == False
    assert any("Invalid template" in error for error in errors)

@pytest.mark.unit
def test_validate_node_config_invalid_ram(eve_client):
    """Test validation with invalid RAM values"""
    invalid_configs = [
        {"type": "dynamips", "template": "c3725", "name": "R1", "ram": "64"},    # Too low
        {"type": "dynamips", "template": "c3725", "name": "R1", "ram": "1024"},  # Too high
        {"type": "dynamips", "template": "c3725", "name": "R1", "ram": "abc"}   # Non-numeric
    ]
    
    for config in invalid_configs:
        is_valid, errors = eve_client.validate_node_config(config)
        assert is_valid == False
        assert any("RAM" in error for error in errors)

@pytest.mark.unit
def test_validate_node_config_invalid_position(eve_client):
    """Test validation with invalid position values"""
    invalid_config = {
        "type": "dynamips",
        "template": "c3725", 
        "name": "Router1",
        "left": "-100",
        "top": "3000"
    }
    
    is_valid, errors = eve_client.validate_node_config(invalid_config)
    
    assert is_valid == False
    assert any("Position left=-100 out of range" in error for error in errors)
    assert any("Position top=3000 out of range" in error for error in errors)

@pytest.mark.unit
def test_validate_lab_config_valid(eve_client):
    """Test validation of a valid lab configuration"""
    is_valid, errors = eve_client.validate_lab_config(
        name="test_lab",
        path="/",
        author="Test Author",
        description="Test description",
        version="1.0"
    )
    
    assert is_valid == True
    assert len(errors) == 0

@pytest.mark.unit
def test_validate_lab_config_invalid_name(eve_client):
    """Test validation with invalid lab names"""
    invalid_names = ["", "   ", "lab@name", "lab with spaces", "x" * 101]
    
    for name in invalid_names:
        is_valid, errors = eve_client.validate_lab_config(name=name)
        assert is_valid == False
        assert len(errors) > 0

@pytest.mark.unit
def test_validate_lab_config_invalid_path(eve_client):
    """Test validation with invalid lab path"""
    is_valid, errors = eve_client.validate_lab_config(
        name="test_lab",
        path="invalid_path"  # Should start with /
    )
    
    assert is_valid == False
    assert any("must start with '/'" in error for error in errors)

@pytest.mark.unit
def test_validate_lab_config_too_long_fields(eve_client):
    """Test validation with excessively long field values"""
    is_valid, errors = eve_client.validate_lab_config(
        name="test_lab",
        author="x" * 101,        # Too long
        description="x" * 501,   # Too long
        version="invalid.version.format.x.y.z"
    )
    
    assert is_valid == False
    assert any("Author name too long" in error for error in errors)
    assert any("Description too long" in error for error in errors)

@pytest.mark.unit
def test_validate_connection_config_valid(eve_client):
    """Test validation of a valid connection configuration"""
    routers = {"Router1": "1", "Router2": "2"}
    
    is_valid, errors = eve_client.validate_connection_config(
        "Router1", "f0/0", "Router2", "f1/0", routers
    )
    
    assert is_valid == True
    assert len(errors) == 0

@pytest.mark.unit
def test_validate_connection_config_router_not_found(eve_client):
    """Test validation with non-existent routers"""
    routers = {"Router1": "1"}
    
    is_valid, errors = eve_client.validate_connection_config(
        "Router1", "f0/0", "NonExistentRouter", "f1/0", routers
    )
    
    assert is_valid == False
    assert any("not found in topology" in error for error in errors)

@pytest.mark.unit
def test_validate_connection_config_invalid_interface(eve_client):
    """Test validation with invalid interfaces"""
    routers = {"Router1": "1", "Router2": "2"}
    
    is_valid, errors = eve_client.validate_connection_config(
        "Router1", "f3/0", "Router2", "g0/0", routers
    )
    
    assert is_valid == False
    assert any("Invalid interface 'f3/0'" in error for error in errors)
    assert any("Invalid interface 'g0/0'" in error for error in errors)

@pytest.mark.unit
def test_validate_connection_config_self_connection(eve_client):
    """Test validation with router connecting to itself"""
    routers = {"Router1": "1"}
    
    is_valid, errors = eve_client.validate_connection_config(
        "Router1", "f0/0", "Router1", "f0/1", routers
    )
    
    assert is_valid == False
    assert any("Cannot connect router 'Router1' to itself" in error for error in errors)

@pytest.mark.unit
def test_get_node_config_template(eve_client):
    """Test getting node configuration template"""
    template = eve_client.get_node_config_template("c3725")
    
    assert template["type"] == "dynamips"
    assert template["template"] == "c3725"
    assert template["slot1"] == "NM-1FE-TX"
    assert "name" in template
    assert "ram" in template

@pytest.mark.unit
def test_get_node_config_template_invalid_type(eve_client):
    """Test getting template for invalid router type"""
    # Instead of raising ValueError, it should return c3725 fallback template
    template = eve_client.get_node_config_template("invalid_type")
    
    # Should return c3725 fallback template
    assert template["template"] == "c3725"
    assert template["type"] == "dynamips"

@pytest.mark.integration
def test_validate_topology_config_valid(eve_client):
    """Test validation of a complete valid topology"""
    routers = {
        "R1": {
            "type": "dynamips",
            "template": "c3725",
            "left": "100",
            "top": "100"
        },
        "R2": {
            "type": "dynamips", 
            "template": "c3725",
            "left": "300",
            "top": "100"
        }
    }
    
    connections = [
        ("R1", "f0/0", "R2", "f0/0", "Link1")
    ]
    
    is_valid, errors = eve_client.validate_topology_config(routers, connections)
    
    assert is_valid == True
    assert len(errors) == 0

@pytest.mark.integration
def test_validate_topology_config_interface_conflict(eve_client):
    """Test validation detecting interface conflicts"""
    routers = {
        "R1": {"type": "dynamips", "template": "c3725"},
        "R2": {"type": "dynamips", "template": "c3725"},
        "R3": {"type": "dynamips", "template": "c3725"}
    }
    
    connections = [
        ("R1", "f0/0", "R2", "f0/0", "Link1"),
        ("R1", "f0/0", "R3", "f0/0", "Link2")  # R1:f0/0 used twice
    ]
    
    is_valid, errors = eve_client.validate_topology_config(routers, connections)
    
    assert is_valid == False
    # The actual error message format
    assert any("used multiple times" in error for error in errors)

@pytest.mark.integration
def test_validate_topology_config_invalid_connection_format(eve_client):
    """Test validation with invalid connection format"""
    routers = {"R1": {"type": "dynamips", "template": "c3725"}}
    
    connections = [
        ("R1", "f0/0")  # Missing required fields
    ]
    
    is_valid, errors = eve_client.validate_topology_config(routers, connections)
    
    assert is_valid == False
    assert any("Invalid connection format" in error for error in errors) 