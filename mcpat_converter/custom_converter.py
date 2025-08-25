import json
import re
import sys
import xml.etree.ElementTree as ET

def parse_stats(stats_file):
    """
    Parses the stats.txt file into a dictionary for easy lookup.
    """
    stats = {}
    with open(stats_file, 'r') as f:
        for line in f:
            # Skip lines that are just headers or comments
            if not line.strip() or '----------' in line:
                continue
            
            # Use regex to find a key-value pair.
            # This handles different formats and ensures correct parsing of numbers.
            match = re.match(r'^\s*([a-zA-Z0-9_.:-]+)\s+([\d.]+e?[-+]?\d*)\s*', line)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                try:
                    stats[key] = float(value)
                except ValueError:
                    # In case the value is not a number, like '0x1000'
                    pass
    return stats

def get_stat_value(stats, key, default=0):
    """
    Safely retrieves a numeric value from the stats dictionary.
    Handles potential parsing errors and varying gem5 stat formats.
    """
    # Define a map for common variations of stat names in gem5
    stats_map = {
        'total_cycles': ['system.cpu.numCycles', 'system.cpu_clk_domain.num_cycles'],
        'committedInsts': ['system.cpu.committedInsts', 'sim_insts'],
        'int_insts': ['system.cpu.committed_int_insts'],
        'fp_insts': ['system.cpu.committed_fp_insts'],
        'branches': ['system.cpu.branches'],
        'branchMispredicts': ['system.cpu.branchMispredictions'],
        'icache.ReadReq::total': ['system.l1icaches.ReadReq::total'],
        'icache.ReadReq::miss': ['system.l1icaches.ReadReq::miss'],
        'dcache.ReadReq::total': ['system.l1dcaches.ReadReq::total'],
        'dcache.ReadReq::miss': ['system.l1dcaches.ReadReq::miss'],
        'dcache.WriteReq::total': ['system.l1dcaches.WriteReq::total'],
        'dcache.WriteReq::miss': ['system.l1dcaches.WriteReq::miss'],
        'l2cache.ReadReq::total': ['system.l2cache.ReadReq::total'],
        'l2cache.ReadReq::miss': ['system.l2cache.ReadReq::miss'],
        'l2cache.WriteReq::total': ['system.l2cache.WriteReq::total'],
        'l2cache.WriteReq::miss': ['system.l2cache.WriteReq::miss']
    }

    if key in stats:
        return stats[key]
    
    # Check for alternate names if direct key is not found
    for name_candidate in stats_map.get(key, []):
        if name_candidate in stats:
            return stats[name_candidate]

    print(f"Warning: Stat '{key}' not found. Returning default value '{default}'.")
    return float(default)

def parse_config(config_file):
    with open(config_file, 'r') as f:
        config_data = json.load(f)

    if isinstance(config_data, list):
        if config_data:
            return config_data[0]
        else:
            raise ValueError("config.json is an empty list.")
    else:
        return config_data

def create_mcpat_xml(stats_data, config):
    if isinstance(config, list) and len(config) > 0:
        config = config[0]
    elif not isinstance(config, dict):
        raise TypeError("config object must be a dictionary.")

    mcpat_template = """<?xml version="1.0" ?>
<component id="root" name="root">
    <component id="system" name="system">
        <param name="number_of_cores" value="1"/>
        <param name="number_of_L1Directories" value="0"/>
        <param name="number_of_L2Directories" value="0"/>
        <param name="number_of_L2s" value="1"/>
        <param name="Private_L2" value="0"/>
        <param name="number_of_L3s" value="0"/>
        <param name="number_of_NoCs" value="0"/>
        <param name="homogeneous_cores" value="1"/>
        <param name="homogeneous_L2s" value="1"/>
        <param name="homogeneous_L1Directories" value="0"/>
        <param name="homogeneous_L2Directories" value="0"/>
        <param name="homogeneous_L3s" value="0"/>
        <param name="homogeneous_ccs" value="0"/>
        <param name="core_tech_node" value="40"/>
        <param name="target_core_clockrate" value="1000.0"/>
        <param name="temperature" value="340"/>
        <param name="number_cache_levels" value="2"/>
        <param name="interconnect_projection_type" value="1"/>
        <param name="device_type" value="2"/>
        <param name="longer_channel_device" value="1"/>
        <param name="Embedded" value="1"/>
        <param name="opt_clockrate" value="1"/>
        <param name="machine_bits" value="32"/>
        <param name="virtual_address_width" value="32"/>
        <param name="physical_address_width" value="32"/>
        <param name="virtual_memory_page_size" value="4096"/>
        <stat name="total_cycles" value="100000"/>
        <stat name="idle_cycles" value="0"/>
        <stat name="busy_cycles" value="100000"/>
        <component id="system.core0" name="core0">
            <param name="clock_rate" value="1000.0"/>
            <param name="opt_local" value="0"/>
            <param name="instruction_length" value="32"/>
            <param name="opcode_width" value="7"/>
            <param name="x86" value="0"/>
            <param name="micro_opcode_width" value="8"/>
            <param name="machine_type" value="0"/>
            <param name="number_hardware_threads" value="1"/>
            <param name="fetch_width" value="2"/>
            <param name="number_instruction_fetch_ports" value="1"/>
            <param name="decode_width" value="2"/>
            <param name="issue_width" value="4"/>
            <param name="peak_issue_width" value="7"/>
            <param name="commit_width" value="4"/>
            <param name="fp_issue_width" value="1"/>
            <param name="prediction_width" value="1"/> 
            <param name="pipelines_per_core" value="1,1"/>
            <param name="pipeline_depth" value="8,8"/>
            <param name="ALU_per_core" value="3"/>
            <param name="MUL_per_core" value="1"/>
            <param name="FPU_per_core" value="1"/>
            <param name="instruction_buffer_size" value="32"/>
            <param name="decoded_stream_buffer_size" value="16"/>
            <param name="instruction_window_scheme" value="0"/>
            <param name="instruction_window_size" value="20"/>
            <param name="fp_instruction_window_size" value="15"/>
            <param name="ROB_size" value="0"/>
            <param name="archi_Regs_IRF_size" value="32"/>          
            <param name="archi_Regs_FRF_size" value="32"/>
            <param name="phy_Regs_IRF_size" value="64"/>
            <param name="phy_Regs_FRF_size" value="64"/>
            <param name="rename_scheme" value="0"/>
            <param name="checkpoint_depth" value="1"/>
            <param name="register_windows_size" value="0"/>
            <param name="LSU_order" value="inorder"/>
            <param name="store_buffer_size" value="4"/>
            <param name="load_buffer_size" value="0"/>
            <param name="memory_ports" value="1"/>
            <param name="RAS_size" value="4"/>                      
            <stat name="total_instructions" value="400000"/>
            <stat name="int_instructions" value="200000"/>
            <stat name="fp_instructions" value="100000"/>
            <stat name="branch_instructions" value="100000"/>
            <stat name="branch_mispredictions" value="0"/>
            <stat name="load_instructions" value="0"/>
            <stat name="store_instructions" value="50000"/>
            <stat name="committed_instructions" value="400000"/>
            <stat name="committed_int_instructions" value="200000"/>
            <stat name="committed_fp_instructions" value="100000"/>
            <stat name="pipeline_duty_cycle" value="1"/>
            <stat name="total_cycles" value="100000"/>
            <stat name="idle_cycles" value="0"/>
            <stat name="busy_cycles" value="100000"/>
            <stat name="ROB_reads" value="400000"/>
            <stat name="ROB_writes" value="400000"/>
            <stat name="rename_reads" value="800000"/>
            <stat name="rename_writes" value="400000"/>
            <stat name="fp_rename_reads" value="200000"/>
            <stat name="fp_rename_writes" value="100000"/>
            <stat name="inst_window_reads" value="400000"/>
            <stat name="inst_window_writes" value="400000"/>
            <stat name="inst_window_wakeup_accesses" value="800000"/>
            <stat name="fp_inst_window_reads" value="200000"/>
            <stat name="fp_inst_window_writes" value="200000"/>
            <stat name="fp_inst_window_wakeup_accesses" value="400000"/>
            <stat name="int_regfile_reads" value="600000"/>
            <stat name="float_regfile_reads" value="100000"/>
            <stat name="int_regfile_writes" value="300000"/>
            <stat name="float_regfile_writes" value="50000"/>
            <stat name="function_calls" value="5"/>
            <stat name="context_switches" value="260343"/>
            <stat name="ialu_accesses" value="300000"/>         
            <stat name="fpu_accesses" value="100000"/>
            <stat name="mul_accesses" value="200000"/>
            <stat name="cdb_alu_accesses" value="300000"/>
            <stat name="cdb_mul_accesses" value="200000"/>
            <stat name="cdb_fpu_accesses" value="100000"/>
            <stat name="IFU_duty_cycle" value="0.9"/>
            <stat name="BR_duty_cycle" value="0.72"/>
            <stat name="LSU_duty_cycle" value="0.71"/>
            <stat name="MemManU_I_duty_cycle" value="0.9"/>
            <stat name="MemManU_D_duty_cycle" value="0.71"/>
            <stat name="ALU_duty_cycle" value="0.76"/>
            <stat name="MUL_duty_cycle" value="0.82"/>
            <stat name="FPU_duty_cycle" value="0.0"/>
            <stat name="ALU_cdb_duty_cycle" value="0.76"/>
            <stat name="MUL_cdb_duty_cycle" value="0.82"/>
            <stat name="FPU_cdb_duty_cycle" value="0.0"/>
            <param name="number_of_BPT" value="2"/>
            <component id="system.core0.predictor" name="PBT">
                <param name="local_predictor_size" value="10,3"/>
                <param name="local_predictor_entries" value="4"/>
                <param name="global_predictor_entries" value="4096"/>
                <param name="global_predictor_bits" value="2"/>
                <param name="chooser_predictor_entries" value="4096"/>
                <param name="chooser_predictor_bits" value="2"/>
            </component>
            <component id="system.core0.itlb" name="itlb">
                <param name="number_entries" value="64"/>
                <stat name="total_accesses" value="200000"/>
                <stat name="total_misses" value="4"/>
                <stat name="conflicts" value="0"/>
            </component>
            <component id="system.core0.icache" name="icache">
                <param name="icache_config" value="32768,64,8,1,10,10,64,0"/>
                <param name="buffer_sizes" value="4, 4, 4,0"/>
                <stat name="read_accesses" value="200000"/>
                <stat name="read_misses" value="0"/>
                <stat name="conflicts" value="0"/>              
            </component>
            <component id="system.core0.dtlb" name="dtlb">
                <param name="number_entries" value="64"/>
                <stat name="total_accesses" value="400000"/>
                <stat name="total_misses" value="4"/>
                <stat name="conflicts" value="0"/>  
            </component>
            <component id="system.core0.dcache" name="dcache">
                <param name="dcache_config" value="32768,64,8,1,10,10,64,1"/>
                <param name="buffer_sizes" value="4, 4, 4, 4"/>
                <stat name="read_accesses" value="800000"/>
                <stat name="write_accesses" value="27276"/>
                <stat name="read_misses" value="1632"/>
                <stat name="write_misses" value="183"/>
                <stat name="conflicts" value="0"/>
            </component>
            <param name="number_of_BTB" value="2"/>
            <component id="system.core0.BTB" name="BTB">
                <param name="BTB_config" value="4096,4,2, 2, 1,1"/> 
                <stat name="read_accesses" value="400000"/>
                <stat name="write_accesses" value="0"/>
            </component>
        </component>
        <component id="system.L20" name="L20">
                <param name="L2_config" value="1048576,32, 8, 8, 8, 23, 32, 1"/> 
                <param name="buffer_sizes" value="16, 16, 16, 16"/>
                <param name="clockrate" value="3400"/>
                <param name="ports" value="1,1,1"/>
                <param name="device_type" value="0"/>
                <stat name="read_accesses" value="200000"/>
                <stat name="write_accesses" value="27276"/>
                <stat name="read_misses" value="1632"/>
                <stat name="write_misses" value="183"/>
                <stat name="conflicts" value="0"/>  
                <stat name="duty_cycle" value="1.0"/>   
        </component>
        <component id="system.mc" name="mc">
            <param name="type" value="1"/>
            <param name="mc_clock" value="400"/>
            <param name="peak_transfer_rate" value="6400"/>
            <param name="block_size" value="64"/>
            <param name="number_mcs" value="0"/>
            <param name="memory_channels_per_mc" value="1"/>
            <param name="number_ranks" value="0"/>
            <param name="req_window_size_per_channel" value="32"/>
            <param name="IO_buffer_size_per_channel" value="32"/>
            <param name="databus_width" value="128"/>
            <param name="addressbus_width" value="51"/>
            <stat name="memory_accesses" value="66666"/>
            <stat name="memory_reads" value="33333"/>
            <stat name="memory_writes" value="33333"/>
            <param name="withPHY" value="1"/>
        </component>
    </component>
</component>
"""
    tree = ET.ElementTree(ET.fromstring(mcpat_template))
    root = tree.getroot()

    # Get cache line size from the system configuration
    cache_line_size = config.get('board', {}).get('cache_line_size', 64)

    cores_list = config.get('board', {}).get('processor', {}).get('cores', [])
    num_cores = len(cores_list) if isinstance(cores_list, list) else 1

    # System parameters
    system_node = root.find(".//component[@name='system']")
    if system_node:
        system_node.find(".//param[@name='number_of_cores']").attrib['value'] = str(num_cores)
        
        # Get total cycles from sim_ticks
        total_cycles = get_stat_value(stats_data, 'total_cycles', default=0)
        system_node.find(".//stat[@name='total_cycles']").attrib['value'] = str(int(total_cycles))
        system_node.find(".//stat[@name='busy_cycles']").attrib['value'] = str(int(total_cycles))
        
        # Get clock rate
        clock_rate_hz = get_stat_value(stats_data, 'system.clk_domain.clock', 1000000000)
        clock_rate_mhz = clock_rate_hz / 1000000.0
        system_node.find(".//param[@name='target_core_clockrate']").attrib['value'] = str(clock_rate_mhz)

    # Core parameters
    for i in range(num_cores):
        core_node_path = f".//component[@name='core{i}']"
        core_node = root.find(core_node_path)
        if core_node:
            core_node.find(".//param[@name='clock_rate']").attrib['value'] = str(clock_rate_mhz)
            
            # Core stats
            committed_insts = get_stat_value(stats_data, 'committedInsts')
            committed_int = get_stat_value(stats_data, 'int_insts')
            committed_fp = get_stat_value(stats_data, 'fp_insts')
            branches = get_stat_value(stats_data, 'branches')
            branch_mispredicts = get_stat_value(stats_data, 'branchMispredicts')
            dcache_reads = get_stat_value(stats_data, f'system.l1dcaches{i}.ReadReq::total')
            dcache_writes = get_stat_value(stats_data, f'system.l1dcaches{i}.WriteReq::total')
            
            core_node.find(".//stat[@name='total_instructions']").attrib['value'] = str(int(committed_insts))
            core_node.find(".//stat[@name='int_instructions']").attrib['value'] = str(int(committed_int))
            core_node.find(".//stat[@name='fp_instructions']").attrib['value'] = str(int(committed_fp))
            core_node.find(".//stat[@name='branch_instructions']").attrib['value'] = str(int(branches))
            core_node.find(".//stat[@name='branch_mispredictions']").attrib['value'] = str(int(branch_mispredicts))
            core_node.find(".//stat[@name='load_instructions']").attrib['value'] = str(int(dcache_reads))
            core_node.find(".//stat[@name='store_instructions']").attrib['value'] = str(int(dcache_writes))
            core_node.find(".//stat[@name='committed_instructions']").attrib['value'] = str(int(committed_insts))
            core_node.find(".//stat[@name='committed_int_instructions']").attrib['value'] = str(int(committed_int))
            core_node.find(".//stat[@name='committed_fp_instructions']").attrib['value'] = str(int(committed_fp))
            
            core_node.find(".//stat[@name='total_cycles']").attrib['value'] = str(int(total_cycles))
            core_node.find(".//stat[@name='busy_cycles']").attrib['value'] = str(int(total_cycles))

            # L1I and L1D cache parameters
            icache_config_node = core_node.find(f".//component[@name='icache']")
            dcache_config_node = core_node.find(f".//component[@name='dcache']")

            if icache_config_node:
                try:
                    l1i_config = config['board']['cache_hierarchy']['l1icaches'][i]
                    size = int(l1i_config['size'].replace('B', '')) if isinstance(l1i_config['size'], str) else l1i_config['size']
                    assoc = l1i_config['assoc']
                    icache_config_node.find(".//param[@name='icache_config']").attrib['value'] = f"{size},{cache_line_size},{assoc},1,10,10,{cache_line_size},0"
                except (KeyError, IndexError):
                    print("Warning: Could not find L1I cache config. Using defaults.")

            if dcache_config_node:
                try:
                    l1d_config = config['board']['cache_hierarchy']['l1dcaches'][i]
                    size = int(l1d_config['size'].replace('B', '')) if isinstance(l1d_config['size'], str) else l1d_config['size']
                    assoc = l1d_config['assoc']
                    dcache_config_node.find(".//param[@name='dcache_config']").attrib['value'] = f"{size},{cache_line_size},{assoc},1,10,10,{cache_line_size},1"
                except (KeyError, IndexError):
                    print("Warning: Could not find L1D cache config. Using defaults.")

    # L2 Cache
    num_l2s = int(system_node.find(".//param[@name='number_of_L2s']").attrib['value'])
    for i in range(num_l2s):
        l2_node_path = f".//component[@name='L2{i}']"
        l2_node = root.find(l2_node_path)
        if l2_node:
            l2_reads = get_stat_value(stats_data, f'system.l2cache.ReadReq::total')
            l2_writes = get_stat_value(stats_data, f'system.l2cache.WriteReq::total')
            l2_node.find(".//stat[@name='read_accesses']").attrib['value'] = str(int(l2_reads))
            l2_node.find(".//stat[@name='write_accesses']").attrib['value'] = str(int(l2_writes))

    return ET.tostring(root, encoding='unicode')

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python mcpat_converter.py <stats.txt> <config.json>")
        sys.exit(1)

    stats_file = sys.argv[1]
    config_file = sys.argv[2]

    try:
        stats_data = parse_stats(stats_file)
        config_data = parse_config(config_file)
        
        xml_output = create_mcpat_xml(stats_data, config_data)
        
        with open("mcpat_output.xml", "w") as f:
            f.write(xml_output)
            
        print("mcpat_output.xml created successfully.")
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)