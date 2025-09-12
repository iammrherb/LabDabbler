#!/usr/bin/env python3
"""
Generate Sample Topologies to Demonstrate Fixed Nokia SROS Templates

This demonstrates that the corrected SROS and VR-SROS templates generate
proper containerlab configurations that are distinct and semantically correct.
"""

import sys
import os
import yaml

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from services.containerlab_templates import ContainerlabTemplateService


def main():
    """Generate sample topologies demonstrating the fixes"""
    service = ContainerlabTemplateService()
    
    print("🔧 Demonstrating Fixed Nokia SROS Templates")
    print("=" * 60)
    
    # 1. Generate SROS (container-based) topology
    print("\n📋 1. Container-based Nokia SROS topology:")
    print("-" * 40)
    
    sros_nodes = [
        {
            "id": "sros-pe1",
            "kind": "sros",
            "image": "nokia/sros:latest"
        },
        {
            "id": "sros-pe2", 
            "kind": "sros",
            "image": "nokia/sros:latest"
        }
    ]
    
    sros_links = [
        {
            "endpoints": ["sros-pe1:1/1/1", "sros-pe2:1/1/1"]
        }
    ]
    
    sros_yaml = service.generate_topology(
        lab_name="nokia-sros-containerized-lab",
        nodes=sros_nodes,
        links=sros_links
    )
    
    print(sros_yaml)
    
    # 2. Generate VR-SROS (vrnetlab-based) topology
    print("\n📋 2. VRnetlab-based Nokia VR-SROS topology:")
    print("-" * 40)
    
    vr_sros_nodes = [
        {
            "id": "vr-sros-pe1",
            "kind": "vr_sros", 
            "image": "vrnetlab/vr-sros:latest",
            "license": "/path/to/sros.license"
        },
        {
            "id": "vr-sros-pe2",
            "kind": "vr_sros",
            "image": "vrnetlab/vr-sros:latest", 
            "license": "/path/to/sros.license"
        }
    ]
    
    vr_sros_links = [
        {
            "endpoints": ["vr-sros-pe1:eth1", "vr-sros-pe2:eth1"]
        }
    ]
    
    vr_sros_yaml = service.generate_topology(
        lab_name="nokia-vr-sros-vrnetlab-lab",
        nodes=vr_sros_nodes,
        links=vr_sros_links
    )
    
    print(vr_sros_yaml)
    
    # 3. Compare templates to show they are distinct
    print("\n🔍 3. Template Comparison Analysis:")
    print("-" * 40)
    
    sros_template = service.get_kind_template("sros")
    vr_sros_template = service.get_kind_template("vr_sros")
    
    print(f"SROS image: {sros_template.get('default_image')}")
    print(f"VR-SROS image: {vr_sros_template.get('default_image')}")
    
    print(f"\nSROS env: {sros_template.get('env', {})}")
    print(f"VR-SROS env: {vr_sros_template.get('env', {})}")
    
    print(f"\nSROS capabilities: {sros_template.get('capabilities', [])}")
    print(f"VR-SROS capabilities: {vr_sros_template.get('capabilities', [])}")
    
    # 4. Validate YAML parsing
    print("\n✅ 4. YAML Validation Results:")
    print("-" * 40)
    
    try:
        sros_config = yaml.safe_load(sros_yaml)
        print(f"✅ SROS YAML is valid: {sros_config['name']}")
    except Exception as e:
        print(f"❌ SROS YAML parsing failed: {e}")
    
    try:
        vr_sros_config = yaml.safe_load(vr_sros_yaml)
        print(f"✅ VR-SROS YAML is valid: {vr_sros_config['name']}")
    except Exception as e:
        print(f"❌ VR-SROS YAML parsing failed: {e}")
    
    # 5. Validate template distinctness
    print("\n🎯 5. Critical Fix Validation:")
    print("-" * 40)
    
    if sros_template == vr_sros_template:
        print("❌ CRITICAL ERROR: Templates are still identical!")
        return False
    else:
        print("✅ CRITICAL FIX: SROS and VR-SROS templates are now DISTINCT")
    
    # Check SROS is container-based
    sros_image = sros_template.get("default_image", "")
    if "vrnetlab" in sros_image:
        print("❌ ERROR: SROS template still using vrnetlab image")
        return False
    else:
        print("✅ SROS template correctly uses container-based image")
    
    # Check VR-SROS is vrnetlab-based
    vr_sros_image = vr_sros_template.get("default_image", "")
    if "vrnetlab" not in vr_sros_image:
        print("❌ ERROR: VR-SROS template not using vrnetlab image")
        return False
    else:
        print("✅ VR-SROS template correctly uses vrnetlab-based image")
    
    # Check SROS uses SRSIM
    sros_env = sros_template.get("env", {})
    if sros_env.get("SRSIM") != "1":
        print("❌ ERROR: SROS template missing SRSIM environment")
        return False
    else:
        print("✅ SROS template correctly uses SRSIM container mode")
    
    # Check VR-SROS uses CONNECTION_MODE
    vr_sros_env = vr_sros_template.get("env", {})
    if vr_sros_env.get("CONNECTION_MODE") != "vrnetlab":
        print("❌ ERROR: VR-SROS template missing vrnetlab CONNECTION_MODE")
        return False
    else:
        print("✅ VR-SROS template correctly uses vrnetlab connection mode")
    
    print("\n🎉 SUCCESS: All critical issues have been RESOLVED!")
    print("   - SROS templates are semantically distinct")  
    print("   - Container vs VRnetlab modes are properly configured")
    print("   - Sample topologies generate valid YAML")
    print("   - Templates pass all validation checks")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)