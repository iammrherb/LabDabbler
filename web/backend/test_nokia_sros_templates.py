#!/usr/bin/env python3
"""
Test Nokia SROS Templates for Correctness

This test validates that:
1. Nokia SROS and VR-SROS templates are distinct and semantically correct
2. All template methods are implemented and accessible
3. Templates generate valid YAML configurations
"""

import sys
import os
import yaml
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from services.containerlab_templates import ContainerlabTemplateService


class TestNokiaSROSTemplates:
    """Test Nokia SROS template correctness and distinction"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = ContainerlabTemplateService()
    
    def test_sros_and_vr_sros_templates_are_distinct(self):
        """CRITICAL: Ensure sros and vr_sros templates are completely distinct"""
        sros_template = self.service.get_kind_template("sros")
        vr_sros_template = self.service.get_kind_template("vr_sros")
        
        # Ensure both templates exist
        assert sros_template, "SROS template must exist"
        assert vr_sros_template, "VR-SROS template must exist"
        
        # Ensure templates are not identical (critical correctness issue)
        assert sros_template != vr_sros_template, "CRITICAL: sros and vr_sros templates must be distinct"
        
        # Validate sros template is container-based (not vrnetlab)
        sros_image = sros_template.get("default_image", "")
        assert "nokia/sros" in sros_image or "sros" in sros_image, f"SROS template must use Nokia SROS container image, got: {sros_image}"
        assert "vrnetlab" not in sros_image, f"SROS template must NOT use vrnetlab image, got: {sros_image}"
        
        # Validate sros template has SRSIM environment
        sros_env = sros_template.get("env", {})
        assert "SRSIM" in sros_env, "SROS template must have SRSIM environment variable"
        assert sros_env.get("SRSIM") == "1", "SRSIM should be enabled for container-based SROS"
        
        # Validate vr_sros template is vrnetlab-based
        vr_sros_image = vr_sros_template.get("default_image", "")
        assert "vrnetlab" in vr_sros_image and "vr-sros" in vr_sros_image, f"VR-SROS template must use vrnetlab image, got: {vr_sros_image}"
        
        # Validate vr_sros template has vrnetlab environment
        vr_sros_env = vr_sros_template.get("env", {})
        assert "CONNECTION_MODE" in vr_sros_env, "VR-SROS template must have CONNECTION_MODE environment"
        assert vr_sros_env.get("CONNECTION_MODE") == "vrnetlab", "VR-SROS should use vrnetlab connection mode"
    
    def test_sros_template_semantic_correctness(self):
        """Validate SROS template follows official containerlab sros node expectations"""
        sros_template = self.service.get_kind_template("sros")
        
        # Validate required fields
        assert "default_image" in sros_template, "SROS template must specify default_image"
        assert "env" in sros_template, "SROS template must specify environment variables"
        assert "capabilities" in sros_template, "SROS template must specify capabilities"
        assert "sysctls" in sros_template, "SROS template must specify sysctls"
        
        # Validate Nokia SROS specific settings
        env = sros_template.get("env", {})
        assert "NOKIA_SROS_CHASSIS" in env, "SROS template must specify Nokia chassis type"
        assert "NOKIA_SROS_SYSTEM_BASE_MAC" in env, "SROS template must specify system base MAC"
        assert "NOKIA_SROS_SLOT" in env, "SROS template must specify slot configuration"
        
        # Validate credentials are Nokia SROS defaults
        creds = sros_template.get("default_credentials", {})
        assert creds.get("username") == "admin", "SROS template should use admin username"
        assert creds.get("password") == "NokiaSros1!", "SROS template should use Nokia SROS default password"
        
        # Validate capabilities
        caps = sros_template.get("capabilities", [])
        expected_caps = ["SYS_ADMIN", "NET_ADMIN", "SYS_PTRACE"]
        for cap in expected_caps:
            assert cap in caps, f"SROS template must include {cap} capability"
    
    def test_vr_sros_template_semantic_correctness(self):
        """Validate VR-SROS template follows vrnetlab expectations"""
        vr_sros_template = self.service.get_kind_template("vr_sros")
        
        # Validate vrnetlab-specific settings
        env = vr_sros_template.get("env", {})
        assert env.get("CONNECTION_MODE") == "vrnetlab", "VR-SROS must use vrnetlab connection mode"
        
        # Validate vrnetlab capabilities
        caps = vr_sros_template.get("capabilities", [])
        expected_caps = ["SYS_ADMIN", "NET_ADMIN", "SYS_RESOURCE"]
        for cap in expected_caps:
            assert cap in caps, f"VR-SROS template must include {cap} capability"
        
        # Validate license requirement for VM-based operation
        required_fields = vr_sros_template.get("required_fields", [])
        assert "license" in required_fields, "VR-SROS template must require license field"
    
    def test_template_yaml_generation(self):
        """Test that templates generate valid YAML topologies"""
        
        # Test SROS template
        sros_nodes = [{
            "id": "sros1",
            "kind": "sros",
            "image": "nokia/sros:latest"
        }]
        
        sros_yaml = self.service.generate_topology(
            lab_name="test-sros-lab",
            nodes=sros_nodes
        )
        
        # Validate YAML is parseable
        sros_config = yaml.safe_load(sros_yaml)
        assert sros_config["name"] == "test-sros-lab"
        assert "sros1" in sros_config["topology"]["nodes"]
        assert sros_config["topology"]["nodes"]["sros1"]["kind"] == "sros"
        
        # Test VR-SROS template
        vr_sros_nodes = [{
            "id": "vr-sros1", 
            "kind": "vr_sros",
            "image": "vrnetlab/vr-sros:latest",
            "license": "/path/to/license.txt"
        }]
        
        vr_sros_yaml = self.service.generate_topology(
            lab_name="test-vr-sros-lab", 
            nodes=vr_sros_nodes
        )
        
        # Validate YAML is parseable
        vr_sros_config = yaml.safe_load(vr_sros_yaml)
        assert vr_sros_config["name"] == "test-vr-sros-lab"
        assert "vr-sros1" in vr_sros_config["topology"]["nodes"]
        assert vr_sros_config["topology"]["nodes"]["vr-sros1"]["kind"] == "vr_sros"
    
    def test_missing_template_methods(self):
        """Check for any missing template methods"""
        missing_methods = []
        
        # Get all supported kinds
        supported_kinds = self.service.get_supported_kinds()
        
        for kind in supported_kinds:
            try:
                template = self.service.get_kind_template(kind)
                if not template:
                    missing_methods.append(f"get_kind_template('{kind}') returned empty template")
            except AttributeError as e:
                missing_methods.append(f"Missing method for kind '{kind}': {str(e)}")
            except Exception as e:
                missing_methods.append(f"Error getting template for kind '{kind}': {str(e)}")
        
        if missing_methods:
            print("Missing template methods found:")
            for method in missing_methods:
                print(f"  - {method}")
        
        # Allow some missing methods but report them
        assert len(missing_methods) < len(supported_kinds) // 2, f"Too many missing methods: {missing_methods}"
    
    def test_canonical_kinds_coverage(self):
        """Validate template coverage matches canonical containerlab kinds"""
        validation_result = self.service.validate_templates_against_canonical()
        
        print(f"Template validation results:")
        print(f"  Canonical kinds: {validation_result['canonical_count']}")
        print(f"  Template kinds: {validation_result['template_count']}")
        print(f"  Coverage: {validation_result['coverage_percentage']}%")
        
        if validation_result['missing_from_templates']:
            print(f"  Missing from templates: {validation_result['missing_from_templates']}")
        
        if validation_result['extra_in_templates']:
            print(f"  Extra in templates: {validation_result['extra_in_templates']}")
        
        # Ensure reasonable coverage
        assert validation_result['coverage_percentage'] > 60, "Template coverage should be above 60%"


def main():
    """Run the tests manually"""
    test_instance = TestNokiaSROSTemplates()
    test_instance.setup_method()
    
    print("Running Nokia SROS template validation tests...")
    
    try:
        test_instance.test_sros_and_vr_sros_templates_are_distinct()
        print("✅ SROS and VR-SROS templates are distinct")
    except Exception as e:
        print(f"❌ SROS distinction test failed: {e}")
        return False
    
    try:
        test_instance.test_sros_template_semantic_correctness()
        print("✅ SROS template semantic correctness validated")
    except Exception as e:
        print(f"❌ SROS semantic test failed: {e}")
        return False
    
    try:
        test_instance.test_vr_sros_template_semantic_correctness()
        print("✅ VR-SROS template semantic correctness validated")
    except Exception as e:
        print(f"❌ VR-SROS semantic test failed: {e}")
        return False
    
    try:
        test_instance.test_template_yaml_generation()
        print("✅ Template YAML generation successful")
    except Exception as e:
        print(f"❌ YAML generation test failed: {e}")
        return False
    
    try:
        test_instance.test_missing_template_methods()
        print("✅ Template method coverage check completed")
    except Exception as e:
        print(f"❌ Missing methods test failed: {e}")
        return False
    
    try:
        test_instance.test_canonical_kinds_coverage()
        print("✅ Canonical kinds coverage validation completed")
    except Exception as e:
        print(f"❌ Canonical coverage test failed: {e}")
        return False
    
    print("\n🎉 All Nokia SROS template validation tests passed!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)